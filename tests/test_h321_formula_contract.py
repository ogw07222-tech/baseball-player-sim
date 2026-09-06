import unittest
from pathlib import Path

from src.hitting import parameters as P
from src.hitting.baserunning import (
    GameState,
    dp_completion_probability,
    first_to_third_probability,
    second_to_home_probability,
    steal_attempt_probability,
    steal_success_probability,
)
from src.hitting.defense import catch_probability


class H321FormulaContractTests(unittest.TestCase):
    """Freeze the validated Balance-Lab H3.2.1 gameplay contract in production."""

    def test_core_hitting_parameter_snapshot(self):
        self.assertEqual(P.STAT_REFERENCE, 100.0)
        self.assertEqual(P.ZONE_SWING_BASE, 0.67)
        self.assertEqual(P.BALL_CHASE_BASE, 0.245)
        self.assertEqual(P.DISCIPLINE_ZONE_WEIGHT, 0.0015)
        self.assertEqual(P.DISCIPLINE_CHASE_WEIGHT, 0.0045)
        self.assertEqual(P.TWO_STRIKE_PROTECTION_WEIGHT, 0.0065)
        self.assertEqual(P.TWO_STRIKE_PROTECTION_CAP, 0.25)
        self.assertEqual(P.CONTACT_SCALE, 0.0055)
        self.assertEqual(P.CONTACT_POSITIVE_SOFT, 70.0)
        self.assertEqual(P.POWER_SCALE, 0.0108)
        self.assertEqual(P.POWER_POSITIVE_SOFT, 85.0)
        self.assertEqual(P.HR_LOGIT_CENTER, 0.86)
        self.assertEqual(P.HR_LOGIT_SCALE, 0.30)

    def test_defense_parameter_snapshot(self):
        self.assertEqual(
            P.DIFFICULTY_BASE_CATCH,
            {
                "ROUTINE": 0.991,
                "EASY": 0.958,
                "AVERAGE": 0.550,
                "HARD": 0.430,
                "VERY_HARD": 0.150,
                "EXCEPTIONAL": 0.040,
            },
        )
        self.assertEqual(
            P.DIFFICULTY_DEFENSE_LEVERAGE,
            {
                "ROUTINE": 0.00011,
                "EASY": 0.00032,
                "AVERAGE": 0.00135,
                "HARD": 0.00400,
                "VERY_HARD": 0.00175,
                "EXCEPTIONAL": 0.00155,
            },
        )
        self.assertEqual(P.ROUTINE_MISS_ERROR_RATE, 0.985)
        self.assertEqual(P.EASY_MISS_ERROR_RATE, 0.86)
        self.assertEqual(P.DAMAGE_DEFENSE_SCALE, 0.0060)
        self.assertEqual(P.DAMAGE_BASE_3B_TO_2B, 0.19)
        self.assertEqual(P.DAMAGE_BASE_2B_TO_1B, 0.14)
        self.assertAlmostEqual(catch_probability("ROUTINE", 100), 0.991, places=12)
        self.assertAlmostEqual(catch_probability("HARD", 70), 0.31, places=12)
        self.assertAlmostEqual(catch_probability("HARD", 160), 0.67, places=12)
        self.assertAlmostEqual(catch_probability("EXCEPTIONAL", 160), 0.133, places=12)

    def test_contact_speed_parameter_snapshot(self):
        self.assertEqual(P.SLOW_DOUBLE_DOWNGRADE_AT_100, 0.020)
        self.assertEqual(P.SLOW_DOUBLE_DOWNGRADE_PER_POINT, 0.0120)
        self.assertEqual(P.SLOW_DOUBLE_DOWNGRADE_MAX, 0.72)
        self.assertEqual(P.FAST_TRIPLE_BASE, 0.020)
        self.assertEqual(P.FAST_TRIPLE_MAX, 0.235)
        self.assertEqual(P.FAST_TRIPLE_SOFT, 45.0)
        self.assertEqual(P.FAST_SINGLE_TO_DOUBLE_PER_POINT, 0.0220)
        self.assertEqual(P.FAST_SINGLE_TO_DOUBLE_MAX, 0.34)
        self.assertEqual(P.INFIELD_HIT_BASE, 0.030)
        self.assertEqual(P.INFIELD_HIT_LOW, 0.002)
        self.assertEqual(P.INFIELD_HIT_HIGH, 0.140)

    def test_h321_baserunning_parameter_snapshot(self):
        expected = {
            "STEAL_GATE_CENTER": 77.5,
            "STEAL_GATE_SCALE": 5.8,
            "STEAL_ATTEMPT_FLOOR": 0.0003,
            "STEAL_ATTEMPT_MAX": 0.205,
            "STEAL_ATTEMPT_CENTER": 108.0,
            "STEAL_ATTEMPT_SCALE": 17.0,
            "STEAL_SUCCESS_MIN": 0.48,
            "STEAL_SUCCESS_MAX": 0.91,
            "STEAL_SUCCESS_CENTER": 92.0,
            "STEAL_SUCCESS_SCALE": 18.0,
            "STEAL_SUCCESS_FLOOR": 0.42,
            "STEAL_SUCCESS_CEILING": 0.925,
            "FIRST_TO_THIRD_MIN": 0.20,
            "FIRST_TO_THIRD_MAX": 0.72,
            "FIRST_TO_THIRD_CENTER": 95.0,
            "FIRST_TO_THIRD_SCALE": 28.0,
            "SECOND_TO_HOME_MIN": 0.26,
            "SECOND_TO_HOME_MAX": 0.80,
            "SECOND_TO_HOME_CENTER": 92.0,
            "SECOND_TO_HOME_SCALE": 26.0,
            "DP_COMPLETION_MIN": 0.16,
            "DP_COMPLETION_MAX": 0.68,
            "DP_COMPLETION_CENTER": 92.0,
            "DP_COMPLETION_SCALE": 24.0,
            "RECOVERY_WEIGHT": 0.0015,
        }
        for name, value in expected.items():
            self.assertEqual(getattr(P, name), value, name)

    def test_representative_baserunning_probability_snapshots(self):
        state = GameState(
            inning=5,
            outs=1,
            score_diff=0,
            first_occupied=True,
            second_occupied=False,
            third_occupied=False,
        )
        # Close-score context contributes +0.018 to the gated attempt core.
        self.assertAlmostEqual(
            steal_attempt_probability(50, state), 0.0005123466845089249, places=12
        )
        self.assertAlmostEqual(
            steal_attempt_probability(100, state), 0.0951575521115054, places=12
        )
        self.assertAlmostEqual(
            steal_attempt_probability(140, state), 0.1962115429303369, places=12
        )
        self.assertAlmostEqual(
            steal_success_probability(100, state), 0.742006542992731, places=12
        )
        self.assertAlmostEqual(
            first_to_third_probability(100), 0.4831527941681041, places=12
        )
        self.assertAlmostEqual(
            second_to_home_probability(100), 0.5712138151500243, places=12
        )
        self.assertAlmostEqual(
            dp_completion_probability(100), 0.3770634926395964, places=12
        )

    def test_steal_requires_real_eligible_base_state(self):
        blocked = GameState(
            inning=5,
            outs=1,
            score_diff=0,
            first_occupied=True,
            second_occupied=True,
        )
        empty_first = GameState(
            inning=5,
            outs=1,
            score_diff=0,
            first_occupied=False,
            second_occupied=False,
        )
        self.assertEqual(steal_attempt_probability(160, blocked), 0.0)
        self.assertEqual(steal_attempt_probability(160, empty_first), 0.0)

    def test_production_has_no_balance_lab_runtime_import(self):
        root = Path(__file__).resolve().parents[1]
        production_files = [
            root / "src" / "simulation.py",
            root / "src" / "inning.py",
            *sorted((root / "src" / "hitting").glob("*.py")),
        ]
        for path in production_files:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("tools.balance_lab", text, str(path))


if __name__ == "__main__":
    unittest.main()
