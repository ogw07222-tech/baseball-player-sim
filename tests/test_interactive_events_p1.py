from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import unittest

from src.career import CareerEngine
from src.event_timeline import CanonicalEventDTO
from src.interactive_events import (
    DEFAULT_SEASON_EVENT_CAP,
    EVENT_BY_TYPE,
    EVENT_CATALOG,
    EVENT_STATUS_PENDING,
    EVENT_STATUS_RESOLVED,
    InteractiveEvent,
    InteractiveEventState,
    deterministic_roll,
    eligible_event_types,
    event_state_for_engine,
    maybe_generate_interactive_event,
    resolve_interactive_event,
)
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG


@dataclass
class StubPlayer:
    form: str = "normal"
    fatigue: float = 20.0
    position: str = "SS"


def generate_for(
    state: InteractiveEventState,
    *,
    seed: int = 60,
    game: int = 1,
    player: object | None = None,
    level: str = "FIRST",
    cap: int = DEFAULT_SEASON_EVENT_CAP,
) -> InteractiveEvent | None:
    return maybe_generate_interactive_event(
        player=player or StubPlayer(),
        state=state,
        seed=seed,
        season=2026,
        game_number=game,
        simulated_date=date(2026, 4, min(28, game)),
        level=level,
        opportunity_per_game=1.0,
        season_event_cap=cap,
    )


class InteractiveEventP1Tests(unittest.TestCase):
    def test_catalog_has_diversified_archetypes_and_tradeoffs(self):
        self.assertGreaterEqual(len(EVENT_CATALOG), 8)
        self.assertLessEqual(len(EVENT_CATALOG), 12)
        self.assertGreaterEqual(len({event.category for event in EVENT_CATALOG}), 5)
        for event in EVENT_CATALOG:
            self.assertGreaterEqual(len(event.choices), 2)
            self.assertLessEqual(len(event.choices), 4)
            self.assertTrue(all(choice.preview_effects for choice in event.choices))

    def test_eligible_event_generated(self):
        state = InteractiveEventState()
        event = generate_for(state)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.status, EVENT_STATUS_PENDING)
        self.assertEqual(event.game_number, 1)
        self.assertEqual(event.event_id, event.dedupe_key)
        self.assertFalse(event.blocking)

    def test_ineligible_event_not_generated_or_eligible(self):
        state = InteractiveEventState()
        player = StubPlayer(form="normal", fatigue=10)
        eligible = eligible_event_types(player=player, state=state, season=2026, game_number=20, level="FIRST")
        self.assertNotIn("slump_response", eligible)
        self.assertNotIn("hot_streak_routine", eligible)
        self.assertNotIn("fatigue_management", eligible)

    def test_same_seed_is_byte_stable_and_parent_rng_is_not_consumed(self):
        rng = RNG(60)
        before = rng.get_state()
        left = generate_for(InteractiveEventState(), seed=rng.seed)
        middle = rng.get_state()
        right = generate_for(InteractiveEventState(), seed=rng.seed)
        after = rng.get_state()
        self.assertEqual(before, middle)
        self.assertEqual(middle, after)
        self.assertEqual(left.as_dict(), right.as_dict())

    def test_cooldown_and_duplicate_prevention(self):
        state = InteractiveEventState()
        first = generate_for(state, game=1)
        assert first is not None
        eligible_next = eligible_event_types(player=StubPlayer(), state=state, season=2026, game_number=2, level="FIRST")
        self.assertNotIn(first.event_type, eligible_next)
        same_type_count = sum(event.event_type == first.event_type for event in state.events)
        self.assertEqual(same_type_count, 1)

    def test_season_cap(self):
        state = InteractiveEventState()
        self.assertIsNone(generate_for(state, cap=0))

    def test_multiple_event_categories_can_be_generated(self):
        seen: set[str] = set()
        for seed in range(1, 80):
            event = generate_for(InteractiveEventState(), seed=seed, game=40, player=StubPlayer(fatigue=60))
            if event is not None:
                seen.add(event.category)
        self.assertGreaterEqual(len(seen), 3)

    def test_pending_to_resolved_and_effect_request_is_declarative(self):
        state = InteractiveEventState()
        event = generate_for(state)
        assert event is not None
        choice = event.choices[0]
        resolution = resolve_interactive_event(state=state, event_id=event.event_id, choice_id=choice.choice_id, resolved_at=date(2026, 4, 2))
        self.assertEqual(state.events[0].status, EVENT_STATUS_RESOLVED)
        self.assertEqual(state.events[0].selected_choice_id, choice.choice_id)
        self.assertEqual(resolution.effects, choice.preview_effects)
        self.assertTrue(all(effect.effect_type in {"training_focus", "fatigue_modifier", "form_modifier", "development_modifier", "temporary_trait_request"} for effect in resolution.effects))

    def test_invalid_choice_rejected_and_event_remains_pending(self):
        state = InteractiveEventState()
        event = generate_for(state)
        assert event is not None
        with self.assertRaises(ValueError):
            resolve_interactive_event(state=state, event_id=event.event_id, choice_id="invalid", resolved_at=date(2026, 4, 2))
        self.assertEqual(state.events[0].status, EVENT_STATUS_PENDING)

    def test_same_event_cannot_resolve_twice(self):
        state = InteractiveEventState()
        event = generate_for(state)
        assert event is not None
        choice_id = event.choices[0].choice_id
        resolve_interactive_event(state=state, event_id=event.event_id, choice_id=choice_id, resolved_at=date(2026, 4, 2))
        with self.assertRaises(RuntimeError):
            resolve_interactive_event(state=state, event_id=event.event_id, choice_id=choice_id, resolved_at=date(2026, 4, 3))

    def test_generation_and_resolution_do_not_mutate_player_state(self):
        rng = RNG(9)
        player = Player.random("T", rng)
        before = player.as_dict()
        state = InteractiveEventState()
        event = maybe_generate_interactive_event(
            player=player,
            state=state,
            seed=rng.seed,
            season=2026,
            game_number=20,
            simulated_date=date(2026, 4, 20),
            level="FIRST",
            opportunity_per_game=1.0,
        )
        assert event is not None
        resolve_interactive_event(state=state, event_id=event.event_id, choice_id=event.choices[0].choice_id, resolved_at=date(2026, 4, 20))
        self.assertEqual(player.as_dict(), before)

    def test_interactive_event_is_not_career_timeline_dto(self):
        state = InteractiveEventState()
        event = generate_for(state)
        assert event is not None
        self.assertIsInstance(event, InteractiveEvent)
        self.assertNotIsInstance(event, CanonicalEventDTO)
        self.assertNotIn("sequence", event.as_dict())
        self.assertNotIn("state_effects", event.as_dict())

    def _production_engine(self, seed: int = 60) -> CareerEngine:
        rng = RNG(seed)
        player = Player.random("P1", rng)
        player.team = "키움 히어로즈"
        player.roster_level = "FARM"
        return CareerEngine(player, rng, phase="PRO")

    def test_next_game_generates_at_exact_game_coordinate_and_is_nonblocking(self):
        engine = self._production_engine(60)
        service = ProductionAdvanceService(engine)
        summary = service.advance_one_game()
        generated = service.drain_generated_interactive_events()
        self.assertEqual(summary.games_played, 1)
        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0].game_number, 1)
        self.assertEqual(engine.current_session.games_completed, 1)
        self.assertEqual(len(service.pending_interactive_events), 1)

    def test_week_and_month_continue_after_pending_event_and_preserve_occurrence_coordinate(self):
        for command in ("week", "month"):
            engine = self._production_engine(60)
            service = ProductionAdvanceService(engine)
            summary = service.advance_one_week() if command == "week" else service.advance_one_month()
            generated = service.drain_generated_interactive_events()
            self.assertGreater(summary.games_played, 1)
            self.assertTrue(generated)
            self.assertEqual(generated[0].game_number, 1)
            self.assertEqual(generated[0].occurred_at, service.schedule.dates[0].isoformat())
            self.assertEqual(engine.current_session.games_completed, summary.games_played)

    def test_save_load_contract_state_object_is_attachable(self):
        engine = self._production_engine(60)
        state = event_state_for_engine(engine)
        event = generate_for(state)
        assert event is not None
        self.assertIs(engine.interactive_event_state, state)

    def test_deterministic_opportunity_reference_seed(self):
        self.assertLess(deterministic_roll(60, 2026, 1, "interactive-event-opportunity"), .04)


if __name__ == "__main__":
    unittest.main()
