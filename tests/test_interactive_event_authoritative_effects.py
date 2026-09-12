from __future__ import annotations

from datetime import date
import copy
import unittest

from src.career import CareerEngine
from src.interactive_event_effects import (
    UnsupportedInteractiveEffect,
    advance_interactive_effects_one_game,
    apply_interactive_pre_form_effects,
    effect_state_for_engine,
    resolve_interactive_event_authoritatively,
)
from src.interactive_events import (
    EVENT_BY_TYPE,
    EVENT_STATUS_PENDING,
    EVENT_STATUS_RESOLVED,
    InteractiveEvent,
    event_state_for_engine,
)
from src.persistence import deserialize_game, serialize_game
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG


class InteractiveEventAuthoritativeEffectsTests(unittest.TestCase):
    def make_engine(self, seed: int = 44) -> CareerEngine:
        rng = RNG(seed)
        player = Player.random("Authority", rng)
        player.team = "키움 히어로즈"
        player.roster_level = "FARM"
        engine = CareerEngine(player, rng, phase="PRO")
        engine.start_pro_season()
        engine.drain_source_facts()
        return engine

    def attach_event(self, engine: CareerEngine, event_type: str) -> InteractiveEvent:
        archetype = EVENT_BY_TYPE[event_type]
        event = InteractiveEvent(
            event_id=f"test:{engine.year}:{event_type}:{len(event_state_for_engine(engine).events)}",
            event_type=archetype.event_type,
            category=archetype.category,
            title=archetype.title,
            description=archetype.description,
            occurred_at=date(engine.year, 4, 1).isoformat(),
            generated_at=date(engine.year, 4, 1).isoformat(),
            season=engine.year,
            game_number=1,
            importance=archetype.importance,
            trigger_context={},
            choices=archetype.choices,
            status=EVENT_STATUS_PENDING,
            dedupe_key=f"test:{engine.year}:{event_type}:{len(event_state_for_engine(engine).events)}",
        )
        event_state_for_engine(engine).events.append(event)
        return event

    def test_valid_pending_choice_applies_and_resolves(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "batting_training_intensity")
        resolution = resolve_interactive_event_authoritatively(
            engine=engine, event_id=event.event_id, choice_id="balanced", resolved_at=date(2026, 4, 2)
        )
        self.assertEqual(resolution.selected_choice_id, "balanced")
        self.assertEqual(event_state_for_engine(engine).events[0].status, EVENT_STATUS_RESOLVED)
        effects = effect_state_for_engine(engine).active_effects
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0].effect_type, "training_focus")
        self.assertEqual(effects[0].games_remaining, 14)

    def test_invalid_event_and_choice_are_rejected_without_mutation(self):
        engine = self.make_engine()
        before = serialize_game(engine)
        with self.assertRaises(KeyError):
            resolve_interactive_event_authoritatively(engine=engine, event_id="missing", choice_id="x", resolved_at=None)
        self.assertEqual(serialize_game(engine), before)
        event = self.attach_event(engine, "batting_training_intensity")
        before = serialize_game(engine)
        with self.assertRaises(ValueError):
            resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="missing", resolved_at=None)
        self.assertEqual(serialize_game(engine), before)

    def test_resolved_event_cannot_mutate_twice(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "batting_training_intensity")
        resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="balanced", resolved_at=None)
        before = serialize_game(engine)
        with self.assertRaises(RuntimeError):
            resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="balanced", resolved_at=None)
        self.assertEqual(serialize_game(engine), before)

    def test_unsupported_effect_rejected_atomically(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "media_interview")
        before_player = copy.deepcopy(engine.player.as_dict())
        with self.assertRaises(UnsupportedInteractiveEffect):
            resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="team", resolved_at=None)
        self.assertEqual(engine.player.as_dict(), before_player)
        self.assertEqual(event_state_for_engine(engine).events[0].status, EVENT_STATUS_PENDING)
        self.assertEqual(effect_state_for_engine(engine).active_effects, [])

    def test_training_focus_accrues_existing_growth_modifier_not_rating_delta(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "batting_training_intensity")
        before_stats = engine.player.stats.as_dict()
        resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="balanced", resolved_at=None)
        advance_interactive_effects_one_game(engine)
        self.assertEqual(engine.player.stats.as_dict(), before_stats)
        mods = engine.current_session.growth_modifiers.mean_by_stat
        self.assertGreater(mods["contact"], 0)
        self.assertGreater(mods["power"], 0)
        self.assertGreater(mods["discipline"], 0)

    def test_fatigue_modifier_uses_player_fatigue_contract(self):
        engine = self.make_engine()
        engine.player.fatigue = 50.0
        event = self.attach_event(engine, "fatigue_management")
        resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="rest", resolved_at=None)
        apply_interactive_pre_form_effects(engine)
        self.assertLess(engine.player.fatigue, 50.0)

    def test_form_modifier_path_and_career_fact_only_on_real_transition(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "slump_response")
        resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="simplify", resolved_at=None)
        self.assertEqual(engine.drain_source_facts(), ())
        engine.player.form = "slump"
        engine.player.form_games_remaining = 1
        engine.begin_source_fact_capture(date(2026, 4, 2), "post_game")
        apply_interactive_pre_form_effects(engine)
        facts = engine.drain_source_facts()
        self.assertEqual(engine.player.form, "normal")
        self.assertEqual([fact.fact_type for fact in facts], ["form_transition"])

    def test_development_modifier_accrues_existing_growth_contract(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "weakness_focus")
        resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="general", resolved_at=None)
        advance_interactive_effects_one_game(engine)
        self.assertTrue(engine.current_session.growth_modifiers.mean_by_stat)
        self.assertTrue(all(value > 0 for value in engine.current_session.growth_modifiers.mean_by_stat.values()))

    def test_temporary_effect_expiration_is_exact_games(self):
        engine = self.make_engine()
        event = self.attach_event(engine, "fatigue_management")
        resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="rest", resolved_at=None)
        durations = sorted(effect.games_remaining for effect in effect_state_for_engine(engine).active_effects)
        self.assertEqual(durations, [5, 7])
        for _ in range(5):
            advance_interactive_effects_one_game(engine)
        self.assertEqual([effect.games_remaining for effect in effect_state_for_engine(engine).active_effects], [2])
        for _ in range(2):
            advance_interactive_effects_one_game(engine)
        self.assertEqual(effect_state_for_engine(engine).active_effects, [])

    def test_save_load_preserves_pending_resolved_active_duration_and_no_duplicate(self):
        engine = self.make_engine()
        pending = self.attach_event(engine, "weakness_focus")
        resolved = self.attach_event(engine, "batting_training_intensity")
        resolve_interactive_event_authoritatively(engine=engine, event_id=resolved.event_id, choice_id="balanced", resolved_at=date(2026, 4, 2))
        advance_interactive_effects_one_game(engine)
        payload = serialize_game(engine)
        restored = deserialize_game(payload)
        statuses = {event.event_id: event.status for event in event_state_for_engine(restored).events}
        self.assertEqual(statuses[pending.event_id], EVENT_STATUS_PENDING)
        self.assertEqual(statuses[resolved.event_id], EVENT_STATUS_RESOLVED)
        self.assertEqual(effect_state_for_engine(restored).active_effects[0].games_remaining, 13)
        before = serialize_game(restored)
        with self.assertRaises(RuntimeError):
            resolve_interactive_event_authoritatively(engine=restored, event_id=resolved.event_id, choice_id="balanced", resolved_at=None)
        self.assertEqual(serialize_game(restored), before)

    def test_old_save_without_effect_state_is_compatible(self):
        engine = self.make_engine()
        payload = serialize_game(engine)
        payload.pop("interactive_career_effect_state", None)
        restored = deserialize_game(payload)
        self.assertEqual(effect_state_for_engine(restored).active_effects, [])

    def test_deterministic_replay(self):
        left = self.make_engine(78)
        right = deserialize_game(serialize_game(left))
        for engine in (left, right):
            event = self.attach_event(engine, "fatigue_management")
            resolve_interactive_event_authoritatively(engine=engine, event_id=event.event_id, choice_id="push", resolved_at=date(2026, 4, 2))
            apply_interactive_pre_form_effects(engine)
            advance_interactive_effects_one_game(engine)
        self.assertEqual(serialize_game(left), serialize_game(right))
        self.assertEqual(left.rng.get_state(), right.rng.get_state())

    def test_04_resolution_alone_still_does_not_apply_player_effect(self):
        from src.interactive_events import resolve_interactive_event
        engine = self.make_engine()
        event = self.attach_event(engine, "fatigue_management")
        before = engine.player.as_dict()
        resolve_interactive_event(state=event_state_for_engine(engine), event_id=event.event_id, choice_id="rest", resolved_at=None)
        self.assertEqual(engine.player.as_dict(), before)
        self.assertEqual(effect_state_for_engine(engine).active_effects, [])

    def test_service_uses_authoritative_resolution_contract(self):
        engine = self.make_engine()
        service = ProductionAdvanceService(engine)
        event = self.attach_event(engine, "batting_training_intensity")
        service.resolve_interactive_event(event.event_id, "balanced")
        self.assertEqual(event_state_for_engine(engine).events[0].status, EVENT_STATUS_RESOLVED)
        self.assertTrue(effect_state_for_engine(engine).active_effects)


if __name__ == "__main__":
    unittest.main()
