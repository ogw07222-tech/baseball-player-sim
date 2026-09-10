from __future__ import annotations

import os
import threading
import time
import unittest
from uuid import uuid4

import psycopg

from src.api.store import (
    IdempotencyConflict,
    PostgresSessionStore,
    RevisionConflict,
)


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(TEST_DATABASE_URL, "TEST_DATABASE_URL is required for Postgres adapter tests")
class PostgresSessionStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database_url = str(TEST_DATABASE_URL)
        cls.store = PostgresSessionStore(cls.database_url)
        cls.store._ensure_initialized()

    def setUp(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE baseball_sim_idempotency, baseball_sim_sessions CASCADE")

    @staticmethod
    def payload(counter: int = 0) -> dict[str, object]:
        return {"save_version": 7, "counter": counter}

    def test_replace_get_and_restart_recovery(self):
        session_id = uuid4().hex
        stored = self.store.replace(session_id, self.payload())
        self.assertEqual(stored.revision, 1)
        self.assertEqual(stored.save_version, 7)

        restarted = PostgresSessionStore(self.database_url)
        recovered = restarted.get(session_id)
        self.assertIsNotNone(recovered)
        assert recovered is not None
        self.assertEqual(recovered.payload, self.payload())
        self.assertEqual(recovered.revision, 1)
        self.assertEqual(recovered.save_version, 7)

    def test_idempotency_replay_and_stale_revision(self):
        session_id = uuid4().hex
        self.store.replace(session_id, self.payload())
        calls = 0

        def mutate(payload):
            nonlocal calls
            calls += 1
            next_payload = dict(payload)
            next_payload["counter"] = int(next_payload["counter"]) + 1
            return next_payload, {"data": {"counter": next_payload["counter"]}}

        first = self.store.mutate(
            session_id,
            expected_revision=1,
            idempotency_key="same-key",
            fingerprint="fp",
            mutator=mutate,
        )
        replay = self.store.mutate(
            session_id,
            expected_revision=1,
            idempotency_key="same-key",
            fingerprint="fp",
            mutator=mutate,
        )
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(first.response, replay.response)
        self.assertEqual(first.revision, 2)
        self.assertEqual(calls, 1)

        with self.assertRaises(IdempotencyConflict):
            self.store.mutate(
                session_id,
                expected_revision=2,
                idempotency_key="same-key",
                fingerprint="different",
                mutator=mutate,
            )

        with self.assertRaises(RevisionConflict) as context:
            self.store.mutate(
                session_id,
                expected_revision=1,
                idempotency_key="stale-key",
                fingerprint="stale",
                mutator=mutate,
            )
        self.assertEqual(context.exception.revision, 2)
        self.assertEqual(calls, 1)

    def test_concurrent_same_revision_executes_exactly_one_mutator(self):
        session_id = uuid4().hex
        self.store.replace(session_id, self.payload())
        barrier = threading.Barrier(2)
        mutator_calls = 0
        calls_lock = threading.Lock()
        results: list[str] = []

        def mutate(payload):
            nonlocal mutator_calls
            with calls_lock:
                mutator_calls += 1
            time.sleep(0.15)
            next_payload = dict(payload)
            next_payload["counter"] = int(next_payload["counter"]) + 1
            return next_payload, {"data": {"counter": next_payload["counter"]}}

        def worker(key: str):
            barrier.wait()
            try:
                self.store.mutate(
                    session_id,
                    expected_revision=1,
                    idempotency_key=key,
                    fingerprint=key,
                    mutator=mutate,
                )
                results.append("committed")
            except RevisionConflict:
                results.append("conflict")

        threads = [
            threading.Thread(target=worker, args=("race-a",)),
            threading.Thread(target=worker, args=("race-b",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(sorted(results), ["committed", "conflict"])
        self.assertEqual(mutator_calls, 1)
        current = self.store.get(session_id)
        assert current is not None
        self.assertEqual(current.revision, 2)
        self.assertEqual(current.payload["counter"], 1)

    def test_concurrent_same_idempotency_key_replays_without_second_mutation(self):
        session_id = uuid4().hex
        self.store.replace(session_id, self.payload())
        barrier = threading.Barrier(2)
        mutator_calls = 0
        calls_lock = threading.Lock()
        commits = []

        def mutate(payload):
            nonlocal mutator_calls
            with calls_lock:
                mutator_calls += 1
            time.sleep(0.15)
            next_payload = dict(payload)
            next_payload["counter"] = int(next_payload["counter"]) + 1
            return next_payload, {"data": {"counter": next_payload["counter"]}}

        def worker():
            barrier.wait()
            commits.append(
                self.store.mutate(
                    session_id,
                    expected_revision=1,
                    idempotency_key="retry-key",
                    fingerprint="retry-fp",
                    mutator=mutate,
                )
            )

        threads = [threading.Thread(target=worker), threading.Thread(target=worker)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(len(commits), 2)
        self.assertEqual(mutator_calls, 1)
        self.assertEqual({commit.revision for commit in commits}, {2})
        self.assertEqual(sum(commit.replayed for commit in commits), 1)
        self.assertEqual(commits[0].response, commits[1].response)


if __name__ == "__main__":
    unittest.main()
