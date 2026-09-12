from __future__ import annotations

from datetime import date
import unittest

from src.career import CareerEngine
from src.interactive_events import event_state_for_engine, maybe_generate_interactive_event, resolve_interactive_event
from src.persistence import deserialize_game, serialize_game
from src.player import Player
from src.rng import RNG


class InteractiveEventPersistenceTests(unittest.TestCase):
    def _engine(self) -> CareerEngine:
        rng = RNG(60)
        player = Player.random("P1", rng)
        player.team = "키움 히어로즈"
        player.roster_level = "FARM"
        return CareerEngine(player, rng, phase="PRO")

    def test_pending_event_roundtrip_preserves_choices_and_rng_state(self):
        engine = self._engine()
        state = event_state_for_engine(engine)
        before_rng = engine.rng.get_state()
        event = maybe_generate_interactive_event(
            player=engine.player,
            state=state,
            seed=engine.rng.seed,
            season=2026,
            game_number=1,
            simulated_date=date(2026, 4, 1),
            level="FARM",
            opportunity_per_game=1.0,
        )
        self.assertIsNotNone(event)
        self.assertEqual(engine.rng.get_state(), before_rng)
        payload = serialize_game(engine)
        loaded = deserialize_game(payload)
        loaded_state = event_state_for_engine(loaded)
        self.assertEqual(state.as_dict(), loaded_state.as_dict())
        self.assertEqual(engine.rng.get_state(), loaded.rng.get_state())

    def test_resolved_event_roundtrip_preserves_resolution_and_effect_request(self):
        engine = self._engine()
        state = event_state_for_engine(engine)
        event = maybe_generate_interactive_event(
            player=engine.player,
            state=state,
            seed=engine.rng.seed,
            season=2026,
            game_number=1,
            simulated_date=date(2026, 4, 1),
            level="FARM",
            opportunity_per_game=1.0,
        )
        assert event is not None
        choice = event.choices[0]
        before_player = engine.player.as_dict()
        resolution = resolve_interactive_event(
            state=state,
            event_id=event.event_id,
            choice_id=choice.choice_id,
            resolved_at=date(2026, 4, 2),
        )
        self.assertEqual(engine.player.as_dict(), before_player)
        loaded = deserialize_game(serialize_game(engine))
        loaded_state = event_state_for_engine(loaded)
        self.assertEqual(loaded_state.events[0].selected_choice_id, choice.choice_id)
        self.assertEqual([effect.as_dict() for effect in resolution.effects], [effect.as_dict() for effect in choice.preview_effects])

    def test_old_save_without_interactive_event_state_loads_cleanly(self):
        engine = self._engine()
        payload = serialize_game(engine)
        payload.pop("interactive_event_state", None)
        loaded = deserialize_game(payload)
        self.assertEqual(event_state_for_engine(loaded).events, [])


if __name__ == "__main__":
    unittest.main()
