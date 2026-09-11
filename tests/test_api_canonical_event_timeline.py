from __future__ import annotations

import sqlite3
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import COOKIE_NAME, create_app
from src.api.store import SQLiteSessionStore
from src.career import CareerEngine
from src.persistence import deserialize_game, serialize_game
from src.player import InjuryStatus
from src.production_advance import ProductionAdvanceService


CAREER = {
    "name": "Event HTTP",
    "position": "SS",
    "bats": "RIGHT",
    "throws": "RIGHT",
    "traitCount": 1,
}

CANONICAL_EVENT_KEYS = {
    "event_id",
    "event_type",
    "category",
    "occurred_at",
    "season",
    "game_number",
    "sequence",
    "title",
    "summary",
    "importance",
    "player_id",
    "team_id",
    "related_entity_ids",
    "state_effects",
    "rating_changes",
    "injury_effect",
    "trait_changes",
    "source_command",
    "presentation_priority",
    "persistence",
    "dedupe_key",
}


class CanonicalEventTimelineHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "sessions.sqlite3"
        self.store = SQLiteSessionStore(self.db_path)
        self.client = TestClient(create_app(self.store))
        self.client.get("/api/v1/session")
        created = self.client.post("/api/v1/career", json=CAREER)
        self.assertEqual(created.status_code, 201)

    def tearDown(self) -> None:
        self.client.close()
        self.temp.cleanup()

    def session_id(self) -> str:
        value = self.client.cookies.get(COOKIE_NAME)
        self.assertIsNotNone(value)
        return str(value)

    def load_engine(self) -> CareerEngine:
        stored = self.store.get(self.session_id())
        self.assertIsNotNone(stored)
        assert stored is not None
        return deserialize_game(stored.payload)

    def reset_engine_at_revision_one(self, engine: CareerEngine) -> None:
        stored = self.store.replace(self.session_id(), serialize_game(engine))
        self.assertEqual(stored.revision, 1)

    def idempotency_count(self, key: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM idempotency WHERE session_id = ? AND idempotency_key = ?",
                (self.session_id(), key),
            ).fetchone()
        assert row is not None
        return int(row[0])

    def assert_canonical_shape(self, event: dict[str, object]) -> None:
        self.assertEqual(set(event), CANONICAL_EVENT_KEYS)
        self.assertIsInstance(event["event_id"], str)
        self.assertIsInstance(event["event_type"], str)
        self.assertIsInstance(event["sequence"], int)
        self.assertIn(event["source_command"], {"next_game", "week", "month", "lifecycle"})

    @staticmethod
    def force_roster_roundtrip(self_engine: CareerEngine, session) -> None:
        if session.games_completed == 10 and session.current_level == "FARM":
            before = session.current_level
            session.current_level = "FIRST"
            self_engine.player.roster_level = "FIRST"
            self_engine._record_roster_transition(session, before, session.current_level)
        elif session.games_completed == 20 and session.current_level == "FIRST":
            before = session.current_level
            session.current_level = "FARM"
            self_engine.player.roster_level = "FARM"
            self_engine._record_roster_transition(session, before, session.current_level)

    def prepare_game_nine_farm(self, *, injured: bool = False) -> None:
        engine = self.load_engine()
        session = engine.start_pro_season()
        engine.drain_source_facts()
        session.current_level = "FARM"
        engine.player.roster_level = "FARM"
        session.games_completed = 9
        if injured:
            engine.player.injury = InjuryStatus("test", "경미", 1)
        service = ProductionAdvanceService(engine)
        service.state.current_date = service.schedule.dates[8]
        self.reset_engine_at_revision_one(engine)

    def test_next_game_returns_canonical_timeline_and_replays_byte_equivalently(self):
        engine = self.load_engine()
        engine.start_pro_season()
        engine.drain_source_facts()
        engine.player.injury = InjuryStatus("test", "경미", 1)
        ProductionAdvanceService(engine)
        self.reset_engine_at_revision_one(engine)

        body = {"command": "next_game", "expected_revision": 1, "idempotency_key": "canonical-next-game"}
        first = self.client.post("/api/v1/advance", json=body)
        self.assertEqual(first.status_code, 200)
        events = first.json()["mutation"]["result"]["notable_events"]
        self.assertIsInstance(events, list)
        self.assertGreaterEqual(len(events), 1)
        for event in events:
            self.assert_canonical_shape(event)
        recovery = [event for event in events if event["event_type"] == "injury_recovery_completed"]
        self.assertEqual(len(recovery), 1)
        self.assertEqual(recovery[0]["source_command"], "next_game")
        self.assertEqual(recovery[0]["persistence"], "transient")

        before_replay = self.store.get(self.session_id())
        assert before_replay is not None
        replay = self.client.post("/api/v1/advance", json=body)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.content, first.content)
        after_replay = self.store.get(self.session_id())
        assert after_replay is not None
        self.assertEqual(after_replay.revision, 2)
        self.assertEqual(after_replay.payload, before_replay.payload)
        self.assertEqual(self.idempotency_count("canonical-next-game"), 1)

    def test_week_preserves_mixed_persistent_and_transient_same_game_sequence(self):
        self.prepare_game_nine_farm(injured=True)
        original = CareerEngine._reconsider_roster
        try:
            with patch.object(CareerEngine, "_reconsider_roster", self.force_roster_roundtrip):
                response = self.client.post(
                    "/api/v1/advance",
                    json={"command": "week", "expected_revision": 1, "idempotency_key": "canonical-week"},
                )
        finally:
            CareerEngine._reconsider_roster = original
        self.assertEqual(response.status_code, 200)
        events = response.json()["mutation"]["result"]["notable_events"]
        for event in events:
            self.assert_canonical_shape(event)
        game_ten = [event for event in events if event["game_number"] == 10]
        types_seen = [event["event_type"] for event in game_ten]
        self.assertIn("injury_recovery_completed", types_seen)
        self.assertIn("roster_promotion", types_seen)
        sequences = [int(event["sequence"]) for event in game_ten]
        self.assertEqual(sequences, sorted(sequences))
        persistence = {event["event_type"]: event["persistence"] for event in game_ten}
        self.assertEqual(persistence["injury_recovery_completed"], "transient")
        self.assertEqual(persistence["roster_promotion"], "career_history")
        self.assertTrue(all(event["source_command"] == "week" for event in events))

    def test_month_preserves_farm_first_farm_and_persistent_history_once(self):
        self.prepare_game_nine_farm()
        body = {"command": "month", "expected_revision": 1, "idempotency_key": "canonical-month"}
        with patch.object(CareerEngine, "_reconsider_roster", self.force_roster_roundtrip):
            first = self.client.post("/api/v1/advance", json=body)
        self.assertEqual(first.status_code, 200)
        events = first.json()["mutation"]["result"]["notable_events"]
        roster = [event for event in events if event["event_type"] in {"roster_promotion", "roster_demotion"}]
        self.assertGreaterEqual(len(roster), 2)
        self.assertEqual([roster[0]["event_type"], roster[1]["event_type"]], ["roster_promotion", "roster_demotion"])
        self.assertEqual([roster[0]["game_number"], roster[1]["game_number"]], [10, 20])
        self.assertLess(int(roster[0]["sequence"]), int(roster[1]["sequence"]))
        self.assertTrue(all(event["source_command"] == "month" for event in events))

        stored = self.store.get(self.session_id())
        assert stored is not None
        committed = deserialize_game(stored.payload)
        relevant_before = [
            entry for entry in committed.player.career_history
            if entry.get("event_id") in {"first_team_callup", "farm_demotion"}
        ]
        self.assertGreaterEqual(len(relevant_before), 2)

        replay = self.client.post("/api/v1/advance", json=body)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.content, first.content)
        stored_after = self.store.get(self.session_id())
        assert stored_after is not None
        replayed = deserialize_game(stored_after.payload)
        relevant_after = [
            entry for entry in replayed.player.career_history
            if entry.get("event_id") in {"first_team_callup", "farm_demotion"}
        ]
        self.assertEqual(relevant_after, relevant_before)
        self.assertEqual(self.idempotency_count("canonical-month"), 1)

        restarted_store = SQLiteSessionStore(self.db_path)
        restarted = restarted_store.get(self.session_id())
        assert restarted is not None
        restarted_engine = deserialize_game(restarted.payload)
        restarted_relevant = [
            entry for entry in restarted_engine.player.career_history
            if entry.get("event_id") in {"first_team_callup", "farm_demotion"}
        ]
        self.assertEqual(restarted_relevant, relevant_before)

    def test_stale_revision_has_no_state_history_event_or_idempotency_commit(self):
        before = self.store.get(self.session_id())
        assert before is not None
        response = self.client.post(
            "/api/v1/advance",
            json={"command": "week", "expected_revision": 2, "idempotency_key": "canonical-stale"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "REVISION_CONFLICT")
        after = self.store.get(self.session_id())
        assert after is not None
        self.assertEqual(after.revision, before.revision)
        self.assertEqual(after.payload, before.payload)
        self.assertEqual(self.idempotency_count("canonical-stale"), 0)

    def test_same_key_different_fingerprint_keeps_existing_conflict_contract(self):
        first = self.client.post(
            "/api/v1/advance",
            json={"command": "next_game", "expected_revision": 1, "idempotency_key": "canonical-conflict"},
        )
        self.assertEqual(first.status_code, 200)
        conflict = self.client.post(
            "/api/v1/advance",
            json={"command": "week", "expected_revision": 2, "idempotency_key": "canonical-conflict"},
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["error"]["code"], "SIMULATION_CONFLICT")


if __name__ == "__main__":
    unittest.main()
