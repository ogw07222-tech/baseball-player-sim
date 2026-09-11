import json
import unittest

from src.hitting import parameters as P
from src.hitting.model import HitterSnapshot, HittingEngine, Pitch, PitcherSnapshot
from src.rng import RNG
from tools.count_swing_diagnostic import run_neutral


def pitch(is_strike: bool, hittable: float) -> Pitch:
    return Pitch(is_strike, "middle", "fastball", 0.0, 0.0, 0.0, hittable)


class Phase1CountSituationalTests(unittest.TestCase):
    def engine(self, discipline=100):
        return HittingEngine(
            HitterSnapshot(100, 100, discipline, 100),
            PitcherSnapshot(),
            100.0,
            RNG(20260911),
        )

    def test_explicit_count_modifier_table_is_sparse(self):
        self.assertEqual(
            set(P.COUNT_SWING_MODIFIERS),
            {(2, 0), (0, 2), (1, 2), (2, 2), (3, 0), (3, 1), (3, 2)},
        )
        self.assertEqual(self.engine()._count_swing_adjustment(pitch(True, .72), 1, 1), 0.0)
        self.assertEqual(self.engine()._count_swing_adjustment(pitch(False, -.82), 1, 1), 0.0)

    def test_three_ball_and_two_strike_ordering(self):
        e = self.engine()
        strike = pitch(True, .72)
        ball = pitch(False, -.82)
        p30 = e._swing_probability(strike, 3, 0)
        p31 = e._swing_probability(strike, 3, 1)
        p11 = e._swing_probability(strike, 1, 1)
        p32 = e._swing_probability(strike, 3, 2)
        self.assertLess(p30, p31)
        self.assertLess(p31, p11)
        self.assertGreater(p32, p30)
        self.assertLess(e._swing_probability(ball, 3, 2), e._swing_probability(ball, 0, 2))

    def test_two_strike_zone_protection_without_chase_explosion(self):
        e = self.engine()
        strike = pitch(True, .72)
        ball = pitch(False, -.82)
        self.assertGreater(e._swing_probability(strike, 0, 2), e._swing_probability(strike, 0, 1))
        self.assertGreater(e._swing_probability(strike, 1, 2), e._swing_probability(strike, 1, 1))
        self.assertGreater(e._swing_probability(strike, 2, 2), e._swing_probability(strike, 2, 1))
        self.assertLess(e._swing_probability(ball, 0, 2) - e._swing_probability(ball, 0, 1), .02)
        self.assertLessEqual(e._swing_probability(ball, 1, 2), e._swing_probability(ball, 1, 1) + .01)
        self.assertLessEqual(e._swing_probability(ball, 2, 2), e._swing_probability(ball, 2, 1))

    def test_discipline_identity_survives_same_count(self):
        ball = pitch(False, -.82)
        for count in ((0, 0), (2, 0), (3, 0), (3, 1), (0, 2), (3, 2)):
            poor = self.engine(75)._swing_probability(ball, *count)
            neutral = self.engine(100)._swing_probability(ball, *count)
            good = self.engine(125)._swing_probability(ball, *count)
            self.assertGreater(poor, neutral, count)
            self.assertGreater(neutral, good, count)

    def test_three_zero_is_suppressed_but_not_hard_zero(self):
        strike = pitch(True, .72)
        low_discipline = self.engine(75)._swing_probability(strike, 3, 0)
        neutral = self.engine(100)._swing_probability(strike, 3, 0)
        high_discipline = self.engine(125)._swing_probability(strike, 3, 0)
        self.assertGreater(low_discipline, 0.0)
        self.assertGreater(neutral, 0.0)
        self.assertGreater(high_discipline, 0.0)
        self.assertNotEqual(low_discipline, neutral)
        self.assertNotEqual(neutral, high_discipline)

    def test_batted_ball_and_hr_constants_remain_frozen(self):
        self.assertEqual(P.HR_LOGIT_CENTER, 0.86)
        self.assertEqual(P.HR_LOGIT_SCALE, 0.30)
        self.assertEqual(P.DEEP_THRESHOLD, 0.56)
        self.assertEqual(P.DOUBLE_BASE, 0.112)
        self.assertEqual(P.TRIPLE_CANDIDATE_GAP_BONUS, 0.018)

    def test_representative_actual_count_rates_and_global_metrics(self):
        report = run_neutral(seed=20260911, pas=40_000)
        by_count = report["by_count"]
        global_rates = report["global"]
        print("COUNT_SITUATIONAL_SANITY", json.dumps(report, sort_keys=True))

        self.assertGreater(by_count["3-0"]["opportunities"], 300)
        self.assertLess(by_count["3-0"]["swing_pct"], by_count["3-1"]["swing_pct"])
        self.assertLess(by_count["3-1"]["swing_pct"], by_count["1-1"]["swing_pct"])
        self.assertGreater(by_count["3-2"]["z_swing_pct"], by_count["3-0"]["z_swing_pct"])
        self.assertLess(by_count["3-2"]["chase_pct"], by_count["0-2"]["chase_pct"])
        self.assertLess(by_count["3-0"]["chase_pct"], .12)

        # Guardrails: this task should reshape counts, not destroy the Phase-1 global profile.
        self.assertGreater(global_rates["swing_pct"], .42)
        self.assertLess(global_rates["swing_pct"], .52)
        self.assertGreater(global_rates["out_zone_swing_pct"], .16)
        self.assertLess(global_rates["out_zone_swing_pct"], .24)
        self.assertGreater(global_rates["in_zone_swing_pct"], .62)
        self.assertLess(global_rates["in_zone_swing_pct"], .72)
        self.assertGreater(global_rates["contact_pct"], .75)
        self.assertLess(global_rates["contact_pct"], .82)
        self.assertGreater(global_rates["BB_pct"], .07)
        self.assertLess(global_rates["BB_pct"], .11)
        self.assertGreater(global_rates["K_pct"], .14)
        self.assertLess(global_rates["K_pct"], .21)
        self.assertGreater(global_rates["HBP_pct"], .006)
        self.assertLess(global_rates["HBP_pct"], .020)
        self.assertGreater(global_rates["pitches_per_PA"], 3.0)
        self.assertLess(global_rates["pitches_per_PA"], 3.8)


if __name__ == "__main__":
    unittest.main()