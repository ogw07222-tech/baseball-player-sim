import unittest
from datetime import date
from unittest.mock import patch

from src.game_provider import DeterministicNeutralLineupProvider, GameFixture, ProductionGameProvider
from src.hitting.model import BattedBall, PlateAppearanceOutcome
from src.inning import PersistentInningEngine
from src.rng import RNG
from src.simulation import PitcherProfile


def _engine(seed: int = 1) -> PersistentInningEngine:
    lineups = DeterministicNeutralLineupProvider()
    away = lineups.lineup("Away", "FIRST")
    home = lineups.lineup("Home", "FIRST")
    return PersistentInningEngine(
        away,
        home,
        RNG(seed),
        away_pitcher=PitcherProfile(100, 100, 100, "R"),
        home_pitcher=PitcherProfile(100, 100, 100, "R"),
    )


def _fly_ball() -> BattedBall:
    return BattedBall(
        contact_quality=0.5,
        exit_quality=0.5,
        ball_type="fly_ball",
        direction="center",
        depth="deep",
        distance=0.7,
        difficulty_score=0.0,
        difficulty_tier="AVERAGE",
    )


def _ground_ball() -> BattedBall:
    return BattedBall(
        contact_quality=0.0,
        exit_quality=0.0,
        ball_type="ground_ball",
        direction="center",
        depth="shallow",
        distance=0.5,
        difficulty_score=0.0,
        difficulty_tier="AVERAGE",
    )


class RequiredFullGameContractTests(unittest.TestCase):
    def test_production_game_finishes(self):
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 1), "Away", "Home"), RNG(11)
        )
        self.assertGreaterEqual(result.innings_played, 9)
        self.assertGreater(result.event_count, 0)
        self.assertFalse(result.safety_cap_hit)

    def test_game_score_nonnegative(self):
        result = ProductionGameProvider().run_game(
            GameFixture(date(2026, 4, 2), "Away", "Home"), RNG(12)
        )
        self.assertGreaterEqual(result.away_score, 0)
        self.assertGreaterEqual(result.home_score, 0)

    def test_batting_order_persists(self):
        engine = _engine()
        engine.state.away_batting_order_index = 5
        engine.state.home_batting_order_index = 7
        engine.state.outs = 3
        engine._finish_half_inning()
        self.assertEqual(engine.state.home_batting_order_index, 7)
        engine.state.outs = 3
        engine._finish_half_inning()
        self.assertEqual(engine.state.away_batting_order_index, 5)

    def test_bases_clear_between_half_innings(self):
        engine = _engine()
        engine.state.first_runner = engine._runner("away", 8)
        engine.state.second_runner = engine._runner("away", 7)
        engine.state.outs = 2
        engine.resolve_plate_appearance(PlateAppearanceOutcome("strikeout"))
        self.assertEqual(engine.state.half, "bottom")
        self.assertFalse(engine.state.runner_ids())

    def test_walkoff_ends_game(self):
        engine = _engine()
        engine.state.inning = 9
        engine.state.half = "bottom"
        engine.state.away_score = 2
        engine.state.home_score = 2
        engine.resolve_plate_appearance(PlateAppearanceOutcome("home_run"))
        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.home_score, 3)

    def test_extra_inning_finishes(self):
        engine = _engine()
        engine.state.inning = 10
        engine.state.half = "bottom"
        engine.state.away_score = 3
        engine.state.home_score = 2
        engine.state.outs = 2
        engine.resolve_plate_appearance(PlateAppearanceOutcome("strikeout"))
        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.inning, 10)

    def test_steal_changes_real_base_state(self):
        engine = _engine()
        engine.state.first_runner = engine._runner("away", 8)
        with patch("src.inning.apply_steal_to_state") as api:
            def success(speed, state, rng, running_defense):
                state.first_occupied = False
                state.second_occupied = True
                return type("T", (), {"attempted": True, "success": True, "outs_added": 0})()
            api.side_effect = success
            event = engine.attempt_steal_between_plate_appearances()
        self.assertTrue(event.steal_success)
        self.assertIsNone(engine.state.first_runner)
        self.assertEqual(engine.state.second_runner.lineup_index, 8)

    def test_first_to_third_in_full_game(self):
        engine = _engine()
        engine.state.first_runner = engine._runner("away", 8)
        with patch("src.inning.apply_first_to_third_to_state") as api:
            api.return_value = type("T", (), {"attempted": True, "success": True, "outs_added": 0})()
            engine.resolve_plate_appearance(PlateAppearanceOutcome("single"))
        self.assertEqual(engine.state.third_runner.lineup_index, 8)

    def test_second_to_home_in_full_game(self):
        engine = _engine()
        engine.state.second_runner = engine._runner("away", 8)
        with patch("src.inning.apply_second_to_home_to_state") as api:
            api.return_value = type("T", (), {"attempted": True, "success": True, "outs_added": 0})()
            engine.resolve_plate_appearance(PlateAppearanceOutcome("single"))
        self.assertEqual(engine.state.away_score, 1)

    def test_double_play_changes_outs_and_bases(self):
        engine = _engine()
        engine.state.first_runner = engine._runner("away", 8)
        with patch("src.inning.apply_double_play_to_state") as api:
            def complete(speed, state, rng):
                state.first_occupied = False
                state.outs += 2
                return type("T", (), {"attempted": True, "success": True, "outs_added": 2})()
            api.side_effect = complete
            engine.resolve_plate_appearance(
                PlateAppearanceOutcome("out", batted_ball=_ground_ball())
            )
        self.assertEqual(engine.state.outs, 2)
        self.assertIsNone(engine.state.first_runner)

    def test_sac_fly_scores_runner(self):
        engine = _engine()
        engine.state.third_runner = engine._runner("away", 8)
        with patch("src.inning.tag_up_probability", return_value=1.0):
            engine.resolve_plate_appearance(
                PlateAppearanceOutcome("out", batted_ball=_fly_ball())
            )
        self.assertEqual(engine.state.away_score, 1)
        self.assertEqual(engine.away_lines[0].SF, 1)


if __name__ == "__main__":
    unittest.main()
