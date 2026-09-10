from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import COOKIE_NAME, DisabledProductionStore, _default_store, create_app
from src.api.store import PostgresSessionStore, SQLiteSessionStore


def clean_env(**values: str):
    return patch.dict(os.environ, values, clear=True)


class ProductionConfigurationTests(unittest.TestCase):
    def test_production_without_external_store_fails_closed(self):
        with clean_env(VERCEL="1", BASEBALL_SIM_SQLITE_PATH="/tmp/must-not-be-used.sqlite3"):
            store = _default_store()
            self.assertIsInstance(store, DisabledProductionStore)
            with TestClient(create_app(store)) as client:
                response = client.get("/api/v1/session")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "SAVE_FAILED")

    def test_production_database_url_selects_postgres_adapter(self):
        with clean_env(VERCEL="1", DATABASE_URL="postgresql://example.invalid/db"):
            store = _default_store()
        self.assertIsInstance(store, PostgresSessionStore)

    def test_local_sqlite_still_supported(self):
        with clean_env(BASEBALL_SIM_SQLITE_PATH=":memory:"):
            store = _default_store()
        self.assertIsInstance(store, SQLiteSessionStore)

    def test_production_cookie_is_opaque_persistent_secure_httponly(self):
        with clean_env(VERCEL="1"):
            with TestClient(create_app(SQLiteSessionStore(":memory:"))) as client:
                response = client.get("/api/v1/session")
        self.assertEqual(response.status_code, 200)
        cookie = response.headers["set-cookie"]
        self.assertIn(f"{COOKIE_NAME}=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=lax", cookie)
        self.assertIn("Path=/", cookie)
        self.assertIn("Max-Age=31536000", cookie)

    def test_unknown_api_route_returns_json_404_not_frontend_fallback(self):
        with clean_env():
            with TestClient(create_app(SQLiteSessionStore(":memory:"))) as client:
                response = client.get("/api/v1/not-a-route")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
