from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import COOKIE_NAME, create_app
from src.api.store import SQLiteSessionStore
from src.interactive_event_effects import InteractiveCareerEffectState
from src.interactive_events import (
    EventChoiceEffect,
    InteractiveEvent,
    InteractiveEventChoice,
    InteractiveEventState,
)
from src.persistence import deserialize_game, serialize_game


CAREER = {
    "name": "Interactive API",
    "position": "SS",
    "bats": "RIGHT",
    "throws": "RIGHT",
    "traitCount": 1,
}


def choice(
    choice_id: str,
    *,
    effect_type: str = "training_focus",
    target: str = "hitting",
    magnitude: str = "balanced",
    duration: int = 2,
) -> InteractiveEventChoice:
    return InteractiveEventChoice(
        choice_id=choice_id,
        label=choice_id,
        description=f"{choice_id} description",
        preview_effects=(EventChoiceEffect(effect_type, target, magnitude, duration),),
        risk_level="low",
        requirements=None,
    )


def event(
    event_id: str,
    *,
    season: int,
    game_number: int = 1,
    occurred_at: str = "2026-04-01",
    choices: tuple[InteractiveEventChoice, ...] | None = None,
) -> InteractiveEvent:
    return InteractiveEvent(
        event_id=event_id,
        event_type="test_training",
        category="training",
        title="훈련 선택",
        description="테스트 선택형 이벤트",
        occurred_at=occurred_at,
        generated_at=occurred_at,
        season=season,
        game_number=game_number,
        importance="normal",
        trigger_context={"source": "integration-test"},
        choices=choices or (choice("balanced"), choice("push", magnitude="high")),
        status="pending",
        expires_at=None,
        source="07-integration-test",
        dedupe_key=event_id,
        blocking=False,
    )


class InteractiveEventHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "sessions.sqlite3"
        self.store = SQLiteSessionStore(self.db_path)
        self.client = TestClient(create_app(self.store))
        created = self.client.post("/api/v1/career", json=CAREER)
        self.assertEqual(created.status_code, 201)
        self.initial_revision = created.json()["meta"]["revision"]

    def tearDown(self) -> None:
        self.client.close()
        self.temp.cleanup()

    def session_id(self) -> str:
        value = self.client.cookies.get(COOKIE_NAME)
        self.assertIsNotNone(value)
        return str(value)

    def stored(self):
        value = self.store.get(self.session_id())
        self.assertIsNotNone(value)
        return value

    def inject_events(self, *events: InteractiveEvent) -> int:
        stored = self.stored()
        engine = deserialize_game(stored.payload)
        if engine.current_session is None:
            engine.start_pro_season()
        engine.interactive_event_state = InteractiveEventState(events=list(events))
        committed = self.store.replace(self.session_id(), serialize_game(engine))
        return committed.revision

    def engine(self):
        return deserialize_game(self.stored().payload)

    def test_state_exposes_empty_and_multiple_pending_events_in_canonical_order(self):
        empty = self.client.get("/api/v1/state")
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json()["data"]["pending_events"], [])

        engine = self.engine()
        first = event("evt-1", season=engine.year, game_number=4)
        second = event("evt-2", season=engine.year, game_number=7)
        revision = self.inject_events(first, second)
        state = self.client.get("/api/v1/state")
        self.assertEqual(state.json()["meta"]["revision"], revision)
        pending = state.json()["data"]["pending_events"]
        self.assertEqual([row["event_id"] for row in pending], ["evt-1", "evt-2"])
        self.assertEqual(pending[0], first.as_dict())
        self.assertIn("choices", pending[0])
        self.assertIn("preview_effects", pending[0]["choices"][0])

    def test_next_game_returns_pending_events_separate_from_career_notable_events(self):
        engine = self.engine()
        pending = event("evt-existing", season=engine.year)
        revision = self.inject_events(pending)
        response = self.client.post(
            "/api/v1/advance",
            json={"command": "next_game", "expected_revision": revision, "idempotency_key": "advance-event"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()["mutation"]["result"]
        self.assertIn("notable_events", result)
        self.assertIn("pending_events", result)
        self.assertEqual(result["pending_events"][0]["event_id"], "evt-existing")
        self.assertIsInstance(result["notable_events"], list)
        self.assertIsInstance(result["pending_events"], list)

    def _period_generation(self, command: str):
        generated: list[InteractiveEvent] = []

        def fake_generate(**kwargs):
            if generated:
                return None
            created = event(
                f"evt-{command}",
                season=int(kwargs["season"]),
                game_number=int(kwargs["game_number"]),
                occurred_at=kwargs["simulated_date"].isoformat(),
            )
            kwargs["state"].events.append(created)
            generated.append(created)
            return created

        with patch("src.production_advance.maybe_generate_interactive_event", side_effect=fake_generate):
            response = self.client.post(
                "/api/v1/advance",
                json={
                    "command": command,
                    "expected_revision": self.initial_revision,
                    "idempotency_key": f"period-{command}",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(generated)
        pending = response.json()["mutation"]["result"]["pending_events"]
        self.assertEqual(pending[0], generated[0].as_dict())
        self.assertGreaterEqual(pending[0]["game_number"], 1)
        return response

    def test_week_returns_event_generated_mid_period(self):
        response = self._period_generation("week")
        self.assertGreater(response.json()["mutation"]["result"]["games_played"], 1)

    def test_month_returns_event_generated_mid_period(self):
        response = self._period_generation("month")
        self.assertGreater(response.json()["mutation"]["result"]["games_played"], 1)

    def test_valid_resolve_and_idempotent_retry_apply_effect_exactly_once(self):
        engine = self.engine()
        pending = event("evt-resolve", season=engine.year)
        revision = self.inject_events(pending)
        body = {"choice_id": "balanced", "expected_revision": revision, "idempotency_key": "resolve-once"}

        first = self.client.post("/api/v1/events/evt-resolve/resolve", json=body)
        self.assertEqual(first.status_code, 200)
        payload = first.json()
        self.assertEqual(payload["meta"]["revision"], revision + 1)
        result = payload["mutation"]["result"]
        self.assertEqual(result["resolved_event"]["status"], "resolved")
        self.assertEqual(result["pending_events"], [])
        self.assertEqual(len(result["applied_effects"]), 1)
        self.assertEqual(result["applied_effects"][0]["source_event_id"], "evt-resolve")

        committed = self.engine()
        self.assertEqual(len(committed.interactive_event_state.pending), 0)
        effects = committed.interactive_career_effect_state
        self.assertIsInstance(effects, InteractiveCareerEffectState)
        self.assertEqual(len(effects.active_effects), 1)

        replay = self.client.post("/api/v1/events/evt-resolve/resolve", json=body)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json(), payload)
        after_replay = self.engine()
        self.assertEqual(len(after_replay.interactive_career_effect_state.active_effects), 1)
        self.assertEqual(self.stored().revision, revision + 1)

    def test_same_idempotency_key_with_different_choice_conflicts(self):
        engine = self.engine()
        revision = self.inject_events(event("evt-conflict", season=engine.year))
        first = self.client.post(
            "/api/v1/events/evt-conflict/resolve",
            json={"choice_id": "balanced", "expected_revision": revision, "idempotency_key": "same-resolve-key"},
        )
        self.assertEqual(first.status_code, 200)
        conflict = self.client.post(
            "/api/v1/events/evt-conflict/resolve",
            json={"choice_id": "push", "expected_revision": revision, "idempotency_key": "same-resolve-key"},
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["error"]["code"], "SIMULATION_CONFLICT")

    def test_already_resolved_new_choice_is_rejected_without_second_effect(self):
        engine = self.engine()
        revision = self.inject_events(event("evt-double", season=engine.year))
        first = self.client.post(
            "/api/v1/events/evt-double/resolve",
            json={"choice_id": "balanced", "expected_revision": revision, "idempotency_key": "first-choice"},
        )
        self.assertEqual(first.status_code, 200)
        before = self.stored()
        second = self.client.post(
            "/api/v1/events/evt-double/resolve",
            json={"choice_id": "push", "expected_revision": before.revision, "idempotency_key": "second-choice"},
        )
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"]["code"], "EVENT_ALREADY_RESOLVED")
        after = self.stored()
        self.assertEqual(after.revision, before.revision)
        self.assertEqual(after.payload, before.payload)

    def test_invalid_event_choice_and_unsupported_effect_are_side_effect_free(self):
        engine = self.engine()
        unsupported = event(
            "evt-unsupported",
            season=engine.year,
            choices=(choice("unsupported", effect_type="temporary_trait_request", target="player", magnitude="temporary"),),
        )
        revision = self.inject_events(event("evt-valid", season=engine.year), unsupported)

        cases = [
            ("/api/v1/events/missing/resolve", "balanced", 404, "EVENT_NOT_FOUND"),
            ("/api/v1/events/evt-valid/resolve", "missing-choice", 400, "INVALID_EVENT_CHOICE"),
            ("/api/v1/events/evt-unsupported/resolve", "unsupported", 422, "UNSUPPORTED_EVENT_EFFECT"),
        ]
        for index, (path, choice_id, status, code) in enumerate(cases):
            before = self.stored()
            response = self.client.post(
                path,
                json={
                    "choice_id": choice_id,
                    "expected_revision": revision,
                    "idempotency_key": f"invalid-{index}",
                },
            )
            self.assertEqual(response.status_code, status)
            self.assertEqual(response.json()["error"]["code"], code)
            after = self.stored()
            self.assertEqual(after.revision, before.revision)
            self.assertEqual(after.payload, before.payload)

    def test_stale_revision_does_not_run_authoritative_mutator(self):
        engine = self.engine()
        revision = self.inject_events(event("evt-stale", season=engine.year))
        bumped = self.client.post(
            "/api/v1/advance",
            json={"command": "next_game", "expected_revision": revision, "idempotency_key": "bump-before-stale"},
        )
        self.assertEqual(bumped.status_code, 200)
        before = self.stored()
        response = self.client.post(
            "/api/v1/events/evt-stale/resolve",
            json={"choice_id": "balanced", "expected_revision": revision, "idempotency_key": "stale-resolve"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "REVISION_CONFLICT")
        after = self.stored()
        self.assertEqual(after.revision, before.revision)
        self.assertEqual(after.payload, before.payload)
        restored = self.engine()
        self.assertEqual(restored.interactive_event_state.pending[0].event_id, "evt-stale")
        self.assertFalse(hasattr(restored, "interactive_career_effect_state"))

    def test_client_cannot_inject_authoritative_effect_fields(self):
        engine = self.engine()
        revision = self.inject_events(event("evt-inject", season=engine.year))
        before = self.stored()
        response = self.client.post(
            "/api/v1/events/evt-inject/resolve",
            json={
                "choice_id": "balanced",
                "expected_revision": revision,
                "idempotency_key": "inject",
                "effect_type": "development_modifier",
                "target": "all",
                "magnitude": "upside_medium",
                "duration": 99,
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "INVALID_REQUEST")
        after = self.stored()
        self.assertEqual(after.payload, before.payload)
        self.assertEqual(after.revision, before.revision)

    def test_restart_preserves_resolved_event_and_active_duration(self):
        engine = self.engine()
        revision = self.inject_events(event("evt-restart", season=engine.year))
        response = self.client.post(
            "/api/v1/events/evt-restart/resolve",
            json={"choice_id": "balanced", "expected_revision": revision, "idempotency_key": "restart"},
        )
        self.assertEqual(response.status_code, 200)

        restarted = TestClient(create_app(SQLiteSessionStore(self.db_path)))
        try:
            restarted.cookies.set(COOKIE_NAME, self.session_id())
            state = restarted.get("/api/v1/state")
            self.assertEqual(state.status_code, 200)
            self.assertEqual(state.json()["data"]["pending_events"], [])
            stored = SQLiteSessionStore(self.db_path).get(self.session_id())
            self.assertIsNotNone(stored)
            restored = deserialize_game(stored.payload)
            self.assertEqual(restored.interactive_event_state.events[0].status, "resolved")
            self.assertEqual(restored.interactive_career_effect_state.active_effects[0].games_remaining, 2)
        finally:
            restarted.close()

    def test_old_save_without_interactive_states_loads_with_empty_pending(self):
        stored = self.stored()
        payload = dict(stored.payload)
        payload.pop("interactive_event_state", None)
        payload.pop("interactive_career_effect_state", None)
        committed = self.store.replace(self.session_id(), payload)
        state = self.client.get("/api/v1/state")
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.json()["meta"]["revision"], committed.revision)
        self.assertEqual(state.json()["data"]["pending_events"], [])


if __name__ == "__main__":
    unittest.main()
