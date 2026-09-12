from __future__ import annotations

import unittest

from src.career import CareerEngine
from src.interactive_events import event_state_for_engine
from src.player import Player
from src.production_advance import ProductionAdvanceService
from src.rng import RNG


class InteractiveEventSeasonResetTests(unittest.TestCase):
    def test_new_season_resets_season_scoped_controls_but_keeps_history(self):
        rng = RNG(60)
        player = Player.random("P1", rng)
        player.team = "키움 히어로즈"
        player.roster_level = "FARM"
        engine = CareerEngine(player, rng, phase="PRO")
        service = ProductionAdvanceService(engine)
        state = event_state_for_engine(engine)
        state.event_cooldown_until["x"] = 99
        state.category_cooldown_until["training"] = 99
        state.season_counts["x"] = 2
        history_before = list(state.events)

        # start_next_season requires the previous lifecycle to have cleared current_session.
        engine.current_session = None
        engine.year += 1
        service.start_next_season()

        self.assertEqual(state.event_cooldown_until, {})
        self.assertEqual(state.category_cooldown_until, {})
        self.assertEqual(state.season_counts, {})
        self.assertEqual(state.events, history_before)


if __name__ == "__main__":
    unittest.main()
