from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import COOKIE_NAME, create_app
from src.api.store import SQLiteSessionStore
from src.persistence import deserialize_game, serialize_game
from src.production_advance import ProductionAdvanceService


CAREER = {
    "name": "Vertical Slice",
    "position": "SS",
    "bats": "RIGHT",
    "throws": "RIGHT",
    "traitCount": 1,
}


class ProductionApiVerticalSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "sessions.sqlite3"
        self.store = SQLiteSessionStore(self.db_path)
        self.client = TestClient(create_app(self.store))

    def tearDown(self) -> None:
        self.client.close()
        self.temp.cleanup()

    def create_career(self):
        session = self.client.get("/api/v1/session")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json(), {"has_career": False, "revision": None})
        response = self.client.post("/api/v1/career", json=CAREER)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["meta"]["revision"], 1)
        return response

    def session_id(self) -> str:
        value = self.client.cookies.get(COOKIE_NAME)
        self.assertIsNotNone(value)
        return str(value)

    def test_create_state_refresh_and_consistent_reads(self):
        created = self.create_career().json()
        first = self.client.get("/api/v1/state")
        second = self.client.get("/api/v1/state")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(first.json(), created)
        self.assertEqual(first.json()["data"]["dashboard"]["player"]["name"], CAREER["name"])

        restarted = TestClient(create_app(SQLiteSessionStore(self.db_path)))
        try:
            restarted.cookies.set(COOKIE_NAME, self.session_id())
            restored = restarted.get("/api/v1/state")
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.json(), first.json())
        finally:
            restarted.close()

    def test_next_game_revision_mutation_idempotency_and_stale_rejection(self):
        self.create_career()
        body = {
            "command": "next_game",
            "expected_revision": 1,
            "idempotency_key": "game-1",
        }
        first = self.client.post("/api/v1/advance", json=body)
        self.assertEqual(first.status_code, 200)
        first_json = first.json()
        self.assertEqual(first_json["meta"]["revision"], 2)
        self.assertEqual(first_json["data"]["dashboard"]["progress"]["game"], 1)

        stored = self.store.get(self.session_id())
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.revision, 2)
        engine = deserialize_game(stored.payload)
        self.assertIsNotNone(engine.current_session)
        assert engine.current_session is not None
        self.assertEqual(engine.current_session.games_completed, 1)

        replay = self.client.post("/api/v1/advance", json=body)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json(), first_json)
        stored_after_replay = self.store.get(self.session_id())
        assert stored_after_replay is not None
        self.assertEqual(stored_after_replay.revision, 2)
        replay_engine = deserialize_game(stored_after_replay.payload)
        assert replay_engine.current_session is not None
        self.assertEqual(replay_engine.current_session.games_completed, 1)

        stale = self.client.post(
            "/api/v1/advance",
            json={
                "command": "next_game",
                "expected_revision": 1,
                "idempotency_key": "stale-command",
            },
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["error"]["code"], "REVISION_CONFLICT")
        self.assertEqual(stale.json()["meta"]["revision"], 2)

    def test_same_idempotency_key_with_different_request_is_rejected(self):
        self.create_career()
        first = self.client.post(
            "/api/v1/advance",
            json={"command": "next_game", "expected_revision": 1, "idempotency_key": "same-key"},
        )
        self.assertEqual(first.status_code, 200)
        conflict = self.client.post(
            "/api/v1/advance",
            json={"command": "next_game", "expected_revision": 2, "idempotency_key": "same-key"},
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["error"]["code"], "SIMULATION_CONFLICT")

    def test_save_load_deterministic_resume(self):
        self.create_career()
        self.client.post(
            "/api/v1/advance",
            json={"command": "next_game", "expected_revision": 1, "idempotency_key": "first"},
        )
        stored = self.store.get(self.session_id())
        assert stored is not None
        a = deserialize_game(stored.payload)
        b = deserialize_game(stored.payload)
        ProductionAdvanceService(a).advance_one_game()
        ProductionAdvanceService(b).advance_one_game()
        self.assertEqual(serialize_game(a), serialize_game(b))

    def test_manual_save_conflict_and_current_revision(self):
        self.create_career()
        ok = self.client.post("/api/v1/save", json={"expected_revision": 1})
        self.assertEqual(ok.status_code, 204)
        stale = self.client.post("/api/v1/save", json={"expected_revision": 2})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["error"]["code"], "REVISION_CONFLICT")


if __name__ == "__main__":
    unittest.main()
