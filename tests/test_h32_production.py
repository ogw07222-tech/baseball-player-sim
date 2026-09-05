import math
import unittest

from src.hitting.baserunning import (
    GameState,
    dp_completion_probability,
    first_to_third_probability,
    second_to_home_probability,
    steal_attempt_probability,
    steal_success_probability,
)
from src.hitting.defense import catch_probability
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.records import BattingLine
from src.rng import RNG


def run_profile(hitter: HitterSnapshot, pa: int, seed: int = 20260905, defense: float = 100.0):
    engine = HittingEngine(hitter, PitcherSnapshot(), defense, RNG(seed))
    counts = {key: 0 for key in (
        "walk", "strikeout", "out", "fielders_choice", "reached_on_error",
        "single", "double", "triple", "home_run",
    )}
    for _ in range(pa):
        counts[engine.simulate_plate_appearance().result] += 1
    hits = counts["single"] + counts["double"] + counts["triple"] + counts["home_run"]
    ab = pa - counts["walk"]
    total_bases = (
        counts["single"] + 2 * counts["double"] + 3 * counts["triple"]
        + 4 * counts["home_run"]
    )
    return {
        "AVG": hits / ab,
        "OBP": (hits + counts["walk"]) / pa,
        "SLG": total_bases / ab,
        "OPS": (hits + counts["walk"]) / pa + total_bases / ab,
        "HR%": counts["home_run"] / pa,
        "BB%": counts["walk"] / pa,
        "K%": counts["strikeout"] / pa,
        "H%": hits / pa,
        **counts,
    }


class H32ProductionPortTests(unittest.TestCase):
    def test_neutral_baseline_matches_balance_lab_band(self):
        m = run_profile(HitterSnapshot(100, 100, 100, 100), 100_000)
        self.assertAlmostEqual(m["AVG"], .2611, delta=.012)
        self.assertAlmostEqual(m["OBP"], .3207, delta=.012)
        self.assertAlmostEqual(m["SLG"], .3974, delta=.020)
        self.assertAlmostEqual(m["HR%"], .0275, delta=.005)
        self.assertAlmostEqual(m["BB%"], .0807, delta=.006)
        self.assertAlmostEqual(m["K%"], .2130, delta=.008)

    def test_contact_monotonicity(self):
        low = run_profile(HitterSnapshot(80, 100, 100, 100), 35_000, 11)
        high = run_profile(HitterSnapshot(120, 100, 100, 100), 35_000, 11)
        self.assertGreater(high["AVG"], low["AVG"])
        self.assertLess(high["K%"], low["K%"])

    def test_power_monotonicity(self):
        low = run_profile(HitterSnapshot(100, 80, 100, 100), 35_000, 12)
        high = run_profile(HitterSnapshot(100, 120, 100, 100), 35_000, 12)
        self.assertGreater(high["SLG"], low["SLG"])
        self.assertGreater(high["HR%"], low["HR%"])

    def test_discipline_monotonicity(self):
        low = run_profile(HitterSnapshot(100, 100, 80, 100), 35_000, 13)
        high = run_profile(HitterSnapshot(100, 100, 120, 100), 35_000, 13)
        self.assertGreater(high["BB%"], low["BB%"])
        self.assertLess(high["K%"], low["K%"])

    def test_speed_monotonicity(self):
        low = run_profile(HitterSnapshot(100, 100, 100, 60), 35_000, 14)
        high = run_profile(HitterSnapshot(100, 100, 100, 140), 35_000, 14)
        self.assertGreater(high["SLG"], low["SLG"])

    def test_defense_monotonicity(self):
        poor = run_profile(HitterSnapshot(100, 100, 100, 100), 35_000, 15, 70)
        good = run_profile(HitterSnapshot(100, 100, 100, 100), 35_000, 15, 130)
        self.assertGreater(poor["H%"], good["H%"])

    def test_steal_suppression_success_and_diminishing_returns(self):
        state = GameState(5, 1, 0, True, False, False)
        self.assertLess(steal_attempt_probability(60, state), steal_attempt_probability(100, state))
        self.assertLess(steal_attempt_probability(100, state), steal_attempt_probability(140, state))
        self.assertLess(steal_success_probability(60, state), steal_success_probability(140, state))
        self.assertLess(steal_success_probability(220, state), .926)
        self.assertLess(
            steal_attempt_probability(170, state) - steal_attempt_probability(150, state),
            steal_attempt_probability(120, state) - steal_attempt_probability(100, state),
        )

    def test_dp_and_advancement_improve_with_speed(self):
        self.assertGreater(dp_completion_probability(60), dp_completion_probability(140))
        self.assertLess(first_to_third_probability(60), first_to_third_probability(140))
        self.assertLess(second_to_home_probability(60), second_to_home_probability(140))

    def test_defense_tier_bounds(self):
        self.assertGreater(catch_probability("ROUTINE", 100), .98)
        self.assertLess(catch_probability("EXCEPTIONAL", 160), .25)
        self.assertGreater(catch_probability("HARD", 160), catch_probability("HARD", 70))

    def test_probability_safety(self):
        state = GameState(8, 1, 0, True, False, False)
        for stat in (30, 40, 50, 70, 100, 130, 160, 190, 220):
            values = (
                steal_attempt_probability(stat, state),
                steal_success_probability(stat, state),
                first_to_third_probability(stat),
                second_to_home_probability(stat),
                dp_completion_probability(stat),
            )
            self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1 for v in values))

    def test_deterministic_seed(self):
        a = run_profile(HitterSnapshot(100, 100, 100, 100), 10_000, 321)
        b = run_profile(HitterSnapshot(100, 100, 100, 100), 10_000, 321)
        self.assertEqual(a, b)

    def test_old_batting_line_save_load_defaults(self):
        old = {
            "G": 10, "PA": 20, "AB": 17, "H": 6, "2B": 2, "3B": 0,
            "HR": 1, "BB": 3, "SO": 4, "HBP": 0, "SB": 1, "CS": 0,
            "R": 3, "RBI": 4,
        }
        line = BattingLine.from_dict(old)
        self.assertEqual(line.ROE, 0)
        self.assertEqual(line.SB_attempts, 0)
        self.assertEqual(line.DP_avoided, 0)
        self.assertEqual(line.XBT, 0)
        restored = BattingLine.from_dict(line.as_dict())
        self.assertEqual(line.as_dict(), restored.as_dict())


if __name__ == "__main__":
    unittest.main()
