from __future__ import annotations
import math
import unittest
from tools.balance_lab.h3.model import H31Model, simulate_profile
from tools.balance_lab.h3.profiles import H3DefenseProfile, H3HitterProfile


class H31ExperimentalTests(unittest.TestCase):
    def test_deterministic(self):
        p = H3HitterProfile()
        self.assertEqual(simulate_profile(p, 3000, 17).as_metrics(), simulate_profile(p, 3000, 17).as_metrics())

    def test_baseline_finite(self):
        m = simulate_profile(H3HitterProfile(), 5000, 2).as_metrics()
        self.assertTrue(all(math.isfinite(float(v)) for v in m.values()))

    def test_contact_identity(self):
        lo = simulate_profile(H3HitterProfile(contact=90), 25000, 4).as_metrics()
        hi = simulate_profile(H3HitterProfile(contact=110), 25000, 4).as_metrics()
        self.assertGreater(hi["AVG"], lo["AVG"])
        self.assertLess(hi["K%"], lo["K%"])

    def test_power_identity(self):
        lo = simulate_profile(H3HitterProfile(power=90), 25000, 5).as_metrics()
        hi = simulate_profile(H3HitterProfile(power=110), 25000, 5).as_metrics()
        self.assertGreater(hi["HR%"], lo["HR%"])
        self.assertGreater(hi["SLG"], lo["SLG"])

    def test_discipline_identity(self):
        lo = simulate_profile(H3HitterProfile(discipline=90), 25000, 6).as_metrics()
        hi = simulate_profile(H3HitterProfile(discipline=110), 25000, 6).as_metrics()
        self.assertGreater(hi["BB%"], lo["BB%"])
        self.assertLess(hi["chase%"], lo["chase%"])

    def test_speed_low_zone_has_value(self):
        lo = simulate_profile(H3HitterProfile(speed=60), 35000, 7).as_metrics()
        hi = simulate_profile(H3HitterProfile(speed=70), 35000, 7).as_metrics()
        self.assertGreater(hi["offensive_value"], lo["offensive_value"])
        self.assertLess(hi["2B_to_1B_downgrade%"], lo["2B_to_1B_downgrade%"])

    def test_defense_is_monotonic_but_not_total_erasure(self):
        low = simulate_profile(H3HitterProfile(), 40000, 8, defense=70).as_metrics()
        high = simulate_profile(H3HitterProfile(), 40000, 8, defense=160).as_metrics()
        self.assertGreater(low["BABIP"], high["BABIP"])
        self.assertGreater(high["AVG"], 0.15)

    def test_errors_only_easy_tiers(self):
        line = simulate_profile(H3HitterProfile(), 100000, 9)
        self.assertEqual(sum(v for k,v in line.errors_by_difficulty.items() if k not in {"ROUTINE","EASY"}), 0)

    def test_power_does_not_control_triple_share(self):
        lo = simulate_profile(H3HitterProfile(power=60, speed=100), 50000, 10).as_metrics()
        hi = simulate_profile(H3HitterProfile(power=180, speed=100), 50000, 10).as_metrics()
        self.assertLess(abs(hi["3B_share_2B3B"]-lo["3B_share_2B3B"]), 0.03)

    def test_extreme_stats_stable(self):
        for x in (30,40,50,70,100,130,160,190,220):
            m = simulate_profile(H3HitterProfile(x,x,x,x), 1500, 100+x).as_metrics()
            self.assertTrue(all(math.isfinite(float(v)) for v in m.values()))


class H31StructuralRegressionTests(unittest.TestCase):
    def test_visible_stat_direction_is_simplified(self):
        from tools.balance_lab.h3.profiles import VISIBLE_STAT_DIRECTION
        self.assertEqual(VISIBLE_STAT_DIRECTION, ("contact", "power", "discipline", "speed", "defense", "resilience", "talent"))
        for removed in ("throwing", "stamina", "mentality", "durability"):
            self.assertNotIn(removed, VISIBLE_STAT_DIRECTION)

    def test_difficulty_catch_curve_has_expected_shape(self):
        low = H31Model(H3HitterProfile(), defense=H3DefenseProfile(70), seed=11)
        avg = H31Model(H3HitterProfile(), defense=H3DefenseProfile(100), seed=11)
        elite = H31Model(H3HitterProfile(), defense=H3DefenseProfile(160), seed=11)
        self.assertGreater(avg._catch_probability("ROUTINE"), 0.98)
        self.assertGreater(avg._catch_probability("EASY"), 0.94)
        self.assertLess(elite._catch_probability("EXCEPTIONAL"), 0.25)
        self.assertGreater(elite._catch_probability("HARD"), avg._catch_probability("HARD"))
        self.assertGreater(avg._catch_probability("HARD"), low._catch_probability("HARD"))

    def test_approach_location_interaction(self):
        from tools.balance_lab.h3.model import Pitch
        inside = Pitch(True, "inside", "fastball", 0.0, 0.0, 0.0, 0.22)
        outside = Pitch(True, "outside", "fastball", 0.0, 0.0, 0.0, 0.14)
        pull = H31Model(H3HitterProfile(approach="pull"), seed=12)
        opp = H31Model(H3HitterProfile(approach="opposite"), seed=12)
        _, pull_inside_bonus = pull._direction(inside)
        _, pull_outside_bonus = pull._direction(outside)
        _, opp_outside_bonus = opp._direction(outside)
        self.assertGreater(pull_inside_bonus, pull_outside_bonus)
        self.assertGreater(opp_outside_bonus, 0.0)

    def test_error_miss_accounting_excludes_infield_hits(self):
        line = simulate_profile(H3HitterProfile(), 60000, 13)
        for tier in ("ROUTINE", "EASY", "AVERAGE", "HARD", "VERY_HARD", "EXCEPTIONAL"):
            self.assertEqual(line.difficulty_misses[tier], line.errors_by_difficulty[tier] + line.hits_on_miss_by_difficulty[tier])


if __name__ == "__main__":
    unittest.main()
