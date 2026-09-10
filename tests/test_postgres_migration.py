from __future__ import annotations

import os
import unittest
from pathlib import Path

import psycopg


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
MIGRATION_PATH = Path("migrations/0001_session_store.sql")


@unittest.skipUnless(TEST_DATABASE_URL, "TEST_DATABASE_URL is required for Postgres migration tests")
class PostgresMigrationTests(unittest.TestCase):
    def test_session_store_migration_applies_and_exposes_required_constraints(self):
        statements = [part.strip() for part in MIGRATION_PATH.read_text(encoding="utf-8").split(";") if part.strip()]
        with psycopg.connect(str(TEST_DATABASE_URL)) as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

                cursor.execute(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='baseball_sim_sessions'
                    ORDER BY ordinal_position
                    """
                )
                session_columns = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='baseball_sim_idempotency'
                    ORDER BY ordinal_position
                    """
                )
                idempotency_columns = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_schema='public' AND table_name='baseball_sim_idempotency'
                    """
                )
                constraint_types = {row[0] for row in cursor.fetchall()}

        self.assertEqual(
            [row[0] for row in session_columns],
            ["session_id", "save_payload", "revision", "save_version", "updated_at"],
        )
        self.assertEqual(
            [row[0] for row in idempotency_columns],
            [
                "session_id",
                "idempotency_key",
                "fingerprint",
                "response_payload",
                "resulting_revision",
                "created_at",
            ],
        )
        self.assertIn("PRIMARY KEY", constraint_types)
        self.assertIn("FOREIGN KEY", constraint_types)


if __name__ == "__main__":
    unittest.main()
