import unittest
from unittest.mock import patch

from src.hitting import parameters as H32P
from src.hitting.model import BattedBall, PlateAppearanceOutcome
from src.inning import PersistentInningEngine
from src.player import Player
from src.rng import RNG
from src.simulation import PitcherProfile
from src.stats import PlayerStats


def make_player(name: str, speed: int = 100) -> Player:
    return Player(
        name,
        24,
        PlayerStats(
            contact=100, power=100, discipline=100, speed=speed, defense=100,
            throwing=100, stamina=100, durability=100, mentality=100, talent=100,
        ),
        position="SS",
    )


def make_lineup(prefix: str, speed: int = 100) -> list[Player]:
    return [make_player(f"{prefix}{i}", speed) for i in range(9)]


def make_engine(seed: int = 1) -> PersistentInningEngine:
    return PersistentInningEngine(
        make_lineup("A"),
        make_lineup("H"),
        RNG(seed),
        away_pitcher=PitcherProfile(100, 100, 100, "R"),
        home_pitcher=PitcherProfile(100, 100, 100, "R"),
    )


def ground_out() -> PlateAppearanceOutcome:
    ball = BattedBall(
        contact_quality=0.0,
        exit_quality=0.0,
        ball_type="ground_ball",
        direction="center",
        depth="shallow",
        distance=0.5,
        difficulty_score=0.0,
        difficulty_tier="AVERAGE",
    )
    return PlateAppearanceOutcome("out", batted_ball=ball)


class PersistentInningTests(unittest.TestCase):
    def test_walk_forced_advancement(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        engine.state.second_runner = engine._runner("away", 6)
        engine.state.third_runner = engine._runner("away", 5)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("walk"))
        self.assertEqual(engine.state.away_score, 1)
        self.assertEqual(engine.state.first_runner.lineup_index, 0)
        self.assertEqual(engine.state.second_runner.lineup_index, 7)
        self.assertEqual(engine.state.third_runner.lineup_index, 6)
        self.assertEqual(engine.away_lines[0].BB, 1)
        self.assertEqual(engine.away_lines[0].RBI, 1)
        self.assertEqual(engine.away_lines[5].R, 1)

    def test_single_updates_base_state(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("single"))
        self.assertEqual(engine.state.first_runner.lineup_index, 0)
        self.assertIsNotNone(engine.state.second_runner or engine.state.third_runner)
        self.assertEqual(engine.away_lines[0].H, 1)

    def test_double_updates_base_state(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        engine.state.second_runner = engine._runner("away", 6)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("double"))
        self.assertEqual(engine.state.away_score, 1)
        self.assertEqual(engine.state.second_runner.lineup_index, 0)
        self.assertEqual(engine.state.third_runner.lineup_index, 7)
        self.assertEqual(engine.away_lines[0].doubles, 1)

    def test_triple_clears_existing_runners(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 8)
        engine.state.second_runner = engine._runner("away", 7)
        engine.state.third_runner = engine._runner("away", 6)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("triple"))
        self.assertEqual(engine.state.away_score, 3)
        self.assertIsNone(engine.state.first_runner)
        self.assertIsNone(engine.state.second_runner)
        self.assertEqual(engine.state.third_runner.lineup_index, 0)

    def test_home_run_scores_all_runners(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 8)
        engine.state.second_runner = engine._runner("away", 7)
        engine.state.third_runner = engine._runner("away", 6)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("home_run"))
        self.assertEqual(engine.state.away_score, 4)
        self.assertEqual(engine.away_lines[0].HR, 1)
        self.assertEqual(engine.away_lines[0].RBI, 4)
        self.assertEqual(engine.away_lines[0].R, 1)
        self.assertFalse(engine.state.runner_ids())

    def test_strikeout_adds_one_out(self):
        engine = make_engine()
        engine.resolve_plate_appearance(PlateAppearanceOutcome("strikeout"))
        self.assertEqual(engine.state.outs, 1)
        self.assertEqual(engine.away_lines[0].SO, 1)

    def test_three_outs_switch_half_inning(self):
        engine = make_engine()
        engine.state.outs = 2
        engine.resolve_plate_appearance(PlateAppearanceOutcome("strikeout"))
        self.assertEqual(engine.state.half, "bottom")
        self.assertEqual(engine.state.outs, 0)
        self.assertFalse(engine.state.runner_ids())

    def test_batting_order_persists_across_innings(self):
        engine = make_engine()
        engine.state.away_batting_order_index = 4
        engine.state.home_batting_order_index = 6
        engine.state.outs = 3
        engine._finish_half_inning()
        self.assertEqual(engine.state.half, "bottom")
        self.assertEqual(engine.state.home_batting_order_index, 6)
        engine.state.outs = 3
        engine._finish_half_inning()
        self.assertEqual(engine.state.inning, 2)
        self.assertEqual(engine.state.half, "top")
        self.assertEqual(engine.state.away_batting_order_index, 4)

    def test_first_to_third_uses_validated_h32_api(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        with patch("src.inning.apply_first_to_third_to_state") as apply_api:
            apply_api.return_value = type(
                "T", (), {"attempted": True, "success": True, "outs_added": 0}
            )()
            engine.resolve_plate_appearance(PlateAppearanceOutcome("single"))
        apply_api.assert_called_once()
        self.assertEqual(engine.state.third_runner.lineup_index, 7)

    def test_second_to_home_uses_validated_h32_api(self):
        engine = make_engine()
        engine.state.second_runner = engine._runner("away", 7)
        with patch("src.inning.apply_second_to_home_to_state") as apply_api:
            apply_api.return_value = type(
                "T", (), {"attempted": True, "success": True, "outs_added": 0}
            )()
            engine.resolve_plate_appearance(PlateAppearanceOutcome("single"))
        apply_api.assert_called_once()
        self.assertEqual(engine.state.away_score, 1)

    def test_double_play_uses_validated_h32_api(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        with patch("src.inning.apply_double_play_to_state") as apply_api:
            def complete_dp(speed, state, rng):
                state.first_occupied = False
                state.outs += 2
                return type(
                    "T", (), {"attempted": True, "success": True, "outs_added": 2}
                )()
            apply_api.side_effect = complete_dp
            engine.resolve_plate_appearance(ground_out())
        apply_api.assert_called_once()
        self.assertEqual(engine.state.outs, 2)
        self.assertEqual(engine.away_lines[0].GDP, 1)
        self.assertIsNone(engine.state.first_runner)

    def test_steal_mutates_persistent_state(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        with patch("src.inning.apply_steal_to_state") as apply_api:
            def steal_success(speed, state, rng, running_defense):
                state.first_occupied = False
                state.second_occupied = True
                return type(
                    "T", (), {
                        "attempted": True, "success": True,
                        "outs_added": 0, "runs_scored": 0,
                    }
                )()
            apply_api.side_effect = steal_success
            event = engine.attempt_steal_between_plate_appearances()
        self.assertTrue(event.steal_success)
        self.assertIsNone(engine.state.first_runner)
        self.assertEqual(engine.state.second_runner.lineup_index, 7)
        self.assertEqual(engine.away_lines[7].SB, 1)
        self.assertEqual(engine.away_lines[7].SB_attempts, 1)

    def test_same_seed_same_game(self):
        left = make_engine(909)
        right = make_engine(909)
        a = left.simulate_game()
        b = right.simulate_game()
        self.assertEqual(
            (a.away_score, a.home_score, a.final_inning, a.events),
            (b.away_score, b.home_score, b.final_inning, b.events),
        )
        self.assertEqual(
            [line.as_dict() for line in a.away_lines],
            [line.as_dict() for line in b.away_lines],
        )
        self.assertEqual(
            [line.as_dict() for line in a.home_lines],
            [line.as_dict() for line in b.home_lines],
        )

    def test_no_h32_formula_changes(self):
        self.assertEqual(H32P.STEAL_GATE_CENTER, 77.5)
        self.assertEqual(H32P.STEAL_GATE_SCALE, 5.8)
        self.assertEqual(H32P.STEAL_ATTEMPT_MAX, 0.205)
        self.assertEqual(H32P.FIRST_TO_THIRD_CENTER, 95.0)
        self.assertEqual(H32P.SECOND_TO_HOME_CENTER, 92.0)
        self.assertEqual(H32P.DP_COMPLETION_CENTER, 92.0)

    def test_full_game_smoke_and_invariants(self):
        engine = make_engine(20260906)
        previous_home = previous_away = 0
        for _ in range(2000):
            if engine.state.game_over:
                break
            engine.step()
            engine.state.validate()
            self.assertGreaterEqual(engine.state.home_score, previous_home)
            self.assertGreaterEqual(engine.state.away_score, previous_away)
            previous_home = engine.state.home_score
            previous_away = engine.state.away_score
        self.assertTrue(engine.state.game_over)
        self.assertGreaterEqual(engine.state.inning, 9)
        self.assertGreaterEqual(engine.state.home_score, 0)
        self.assertGreaterEqual(engine.state.away_score, 0)


if __name__ == "__main__":
    unittest.main()
