from __future__ import annotations

import unittest

from tools.velocity_scale.model import (
    PiecewiseVelocityMap,
    SoftVelocityMap,
    VelocityGameplayContract,
    VelocityWorkloadModel,
)
from tools.velocity_scale.simulate import pa_metrics, pitch_contact_metrics


class VelocityScaleTests(unittest.TestCase):
    def setUp(self):
        self.mapping = SoftVelocityMap(raw_reference=84.0)

    def test_velocity_mapping_monotonic(self):
        ratings = [30, 50, 70, 100, 130, 160, 200, 250]
        kmh = [self.mapping.raw_to_kmh(v) for v in ratings]
        self.assertTrue(all(a < b for a, b in zip(kmh, kmh[1:])))

    def test_velocity_mapping_extreme_safe(self):
        for mapping in (self.mapping, PiecewiseVelocityMap(raw_reference=84.0)):
            for raw in (30, 50, 70, 100, 130, 160, 200, 250):
                value = mapping.raw_to_kmh(raw)
                self.assertGreaterEqual(value, 120.0)
                self.assertLess(value, 180.0)

    def test_velocity_reference_round_trip(self):
        for raw in (50, 70, 84, 100, 130, 160):
            kmh = self.mapping.raw_to_kmh(raw)
            self.assertAlmostEqual(self.mapping.kmh_to_raw(kmh), raw, places=6)
        contract = VelocityGameplayContract(gameplay_points_per_kmh=1.0)
        self.assertEqual(contract.kmh_to_gameplay(146.0), 100.0)
        self.assertEqual(contract.gameplay_to_kmh(100.0), 146.0)

    def test_higher_kmh_reduces_contact(self):
        low = VelocityGameplayContract(gameplay_points_per_kmh=1.0).contact_delta(142)
        high = VelocityGameplayContract(gameplay_points_per_kmh=1.0).contact_delta(150)
        self.assertLess(high, low)
        a = pitch_contact_metrics(142, 1.0, 12000, 9001)
        b = pitch_contact_metrics(150, 1.0, 12000, 9001)
        self.assertLess(b["Contact%"], a["Contact%"])

    def test_higher_kmh_increases_whiff(self):
        a = pitch_contact_metrics(142, 1.0, 12000, 9002)
        b = pitch_contact_metrics(150, 1.0, 12000, 9002)
        self.assertGreater(b["Whiff%"], a["Whiff%"])

    def test_higher_kmh_increases_k(self):
        a = pa_metrics(142, 1.0, 20000, 9003)
        b = pa_metrics(150, 1.0, 20000, 9003)
        self.assertGreater(b["K%"], a["K%"])

    def test_velocity_does_not_directly_change_bb(self):
        # Control is fixed at H3 neutral.  With common random numbers, only the
        # contact path moves; allow a small indirect count-distribution shift.
        a = pa_metrics(142, 1.0, 30000, 9004)
        b = pa_metrics(150, 1.0, 30000, 9004)
        self.assertLess(abs(b["BB%"] - a["BB%"]), 0.005)

    def test_effort_increases_effective_kmh(self):
        m = VelocityWorkloadModel()
        self.assertGreater(m.effective_kmh(146, 1.0, 0.0), m.effective_kmh(146, 0.0, 0.0))

    def test_fatigue_reduces_effective_kmh(self):
        m = VelocityWorkloadModel()
        self.assertLess(m.effective_kmh(146, 0.5, 1.0), m.effective_kmh(146, 0.5, 0.0))
        self.assertGreater(m.effective_kmh(146, 0.5, 1.0, 150), m.effective_kmh(146, 0.5, 1.0, 70))

    def test_base_velocity_rating_never_mutates(self):
        class P:
            velocity = 100
        p = P(); before = p.velocity
        base = self.mapping.raw_to_kmh(p.velocity)
        VelocityWorkloadModel().effective_kmh(base, 1.0, 1.0, 100)
        self.assertEqual(p.velocity, before)


if __name__ == "__main__":
    unittest.main()
