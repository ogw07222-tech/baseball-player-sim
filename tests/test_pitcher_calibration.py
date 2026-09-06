from __future__ import annotations

from dataclasses import dataclass
import random
import unittest

from src.hitting.model import HitterSnapshot
from tools.pitcher_calibration.adapter import CalibrationWeights, PitcherPAAdapter
from tools.pitcher_calibration.effort import EffortModel, EffortProfile


@dataclass
class DummyPitcher:
    velocity: float = 100.0
    stuff: float = 100.0
    control: float = 100.0
    breaking: float = 100.0
    stamina: float = 100.0
    resilience: float = 100.0
    talent: float = 100.0


def adapter_for(**kwargs) -> PitcherPAAdapter:
    return PitcherPAAdapter(DummyPitcher(**kwargs), CalibrationWeights())


class PitcherCalibrationTests(unittest.TestCase):
    def test_velocity_monotonicity(self):
        low = adapter_for(velocity=90).pitch_stat_modifier(None, 0)[0]
        high = adapter_for(velocity=110).pitch_stat_modifier(None, 0)[0]
        self.assertLess(high, low)
        self.assertEqual(adapter_for(velocity=90).pitcher_snapshot().control,
                         adapter_for(velocity=110).pitcher_snapshot().control)

    def test_stuff_quality_suppression(self):
        low = adapter_for(stuff=90).pitch_stat_modifier(None, 0)
        high = adapter_for(stuff=110).pitch_stat_modifier(None, 0)
        self.assertEqual(low[0], high[0])
        self.assertLess(high[1], low[1])

    def test_control_walk_suppression(self):
        low = adapter_for(control=90).pitcher_snapshot()
        high = adapter_for(control=110).pitcher_snapshot()
        self.assertGreater(high.control, low.control)
        self.assertEqual(high.stuff, 100.0)
        self.assertEqual(high.movement, 100.0)

    def test_breaking_contact_suppression(self):
        low = adapter_for(breaking=90).pitch_stat_modifier(None, 0)
        high = adapter_for(breaking=110).pitch_stat_modifier(None, 0)
        self.assertLess(high[0], low[0])
        self.assertLess(high[1], low[1])

    def test_stuff_not_universal_dominant(self):
        baseline = adapter_for().pitcher_snapshot()
        stuff = adapter_for(stuff=140)
        self.assertEqual(stuff.pitcher_snapshot(), baseline)
        contact_delta, quality_delta = stuff.pitch_stat_modifier(None, 0)
        self.assertEqual(contact_delta, 0.0)
        self.assertLess(quality_delta, 0.0)

    def test_velocity_stuff_synergy(self):
        a = adapter_for(velocity=150, stuff=70).pitch_stat_modifier(None, 0)
        b = adapter_for(velocity=70, stuff=150).pitch_stat_modifier(None, 0)
        c = adapter_for(velocity=120, stuff=120).pitch_stat_modifier(None, 0)
        self.assertLess(c[0], 0.0)
        self.assertLess(c[1], 0.0)
        self.assertGreater(a[1], 0.0)
        self.assertGreater(b[0], 0.0)

    def test_talent_no_direct_gameplay_effect(self):
        a = adapter_for(talent=30)
        b = adapter_for(talent=250)
        self.assertEqual(a.pitcher_snapshot(), b.pitcher_snapshot())
        self.assertEqual(a.pitch_stat_modifier(None, 0), b.pitch_stat_modifier(None, 0))

    def test_stamina_no_direct_neutral_pa_effect(self):
        a = adapter_for(stamina=30)
        b = adapter_for(stamina=250)
        self.assertEqual(a.pitcher_snapshot(), b.pitcher_snapshot())
        self.assertEqual(a.pitch_stat_modifier(None, 0), b.pitch_stat_modifier(None, 0))

    def test_resilience_no_direct_pa_effect(self):
        a = adapter_for(resilience=30)
        b = adapter_for(resilience=250)
        self.assertEqual(a.pitcher_snapshot(), b.pitcher_snapshot())
        self.assertEqual(a.pitch_stat_modifier(None, 0), b.pitch_stat_modifier(None, 0))

    def test_effort_boost_does_not_mutate_base_rating(self):
        p = DummyPitcher(velocity=120, stuff=115)
        before = dict(p.__dict__)
        EffortModel(EffortProfile(1.0)).effective_stats(p)
        self.assertEqual(p.__dict__, before)

    def test_higher_effort_increases_velocity(self):
        p = DummyPitcher()
        low = EffortModel(EffortProfile(0.25)).effective_stats(p)
        high = EffortModel(EffortProfile(0.90)).effective_stats(p)
        self.assertGreater(high.velocity, low.velocity)

    def test_higher_effort_increases_stuff(self):
        p = DummyPitcher()
        low = EffortModel(EffortProfile(0.25)).effective_stats(p)
        high = EffortModel(EffortProfile(0.90)).effective_stats(p)
        self.assertGreater(high.stuff, low.stuff)

    def test_higher_effort_increases_fatigue_cost(self):
        low = EffortModel(EffortProfile(0.25)).fatigue_gain(1.0, 100)
        high = EffortModel(EffortProfile(0.90)).fatigue_gain(1.0, 100)
        self.assertGreater(high, low)

    def test_fatigue_cost_curve_is_convex(self):
        f0 = EffortModel(EffortProfile(0.0)).fatigue_multiplier()
        f5 = EffortModel(EffortProfile(0.5)).fatigue_multiplier()
        f1 = EffortModel(EffortProfile(1.0)).fatigue_multiplier()
        self.assertGreater(f1 - f5, f5 - f0)

    def test_extreme_rating_safety(self):
        valid = {"walk", "strikeout", "home_run", "single", "double", "triple", "out", "reached_on_error"}
        hitter = HitterSnapshot(100, 100, 100, 100)
        for rating in (30, 50, 70, 100, 130, 160, 200, 250):
            p = DummyPitcher(rating, rating, rating, rating, rating, rating, rating)
            engine = PitcherPAAdapter(p, CalibrationWeights()).make_engine(hitter, 100, random.Random(rating))
            for _ in range(20):
                outcome = engine.simulate_plate_appearance()
                self.assertIn(outcome.result, valid)

    def test_probability_bounds(self):
        hitter = HitterSnapshot(250, 250, 250, 250)
        p = DummyPitcher(250, 250, 250, 250, 100, 100, 100)
        engine = PitcherPAAdapter(p, CalibrationWeights()).make_engine(hitter, 100, random.Random(9))
        for _ in range(100):
            self.assertIsNotNone(engine.simulate_plate_appearance().result)


if __name__ == "__main__":
    unittest.main()
