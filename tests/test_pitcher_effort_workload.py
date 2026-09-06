from __future__ import annotations

from dataclasses import dataclass
import unittest

from tools.pitcher_calibration.effort import EffortModel, EffortProfile


@dataclass
class DummyPitcher:
    velocity: float = 120.0
    stuff: float = 120.0
    control: float = 100.0
    breaking: float = 100.0
    stamina: float = 100.0


class PitcherEffortWorkloadTests(unittest.TestCase):
    def test_stamina_modulates_workload(self):
        model = EffortModel(EffortProfile(1.0))
        low = DummyPitcher(stamina=70)
        high = DummyPitcher(stamina=130)
        self.assertGreater(model.workload_state(low, 30).fatigue,
                           model.workload_state(high, 30).fatigue)

    def test_workload_declines_effective_velocity_and_stuff(self):
        model = EffortModel(EffortProfile(1.0))
        pitcher = DummyPitcher()
        early = model.workload_state(pitcher, 15)
        late = model.workload_state(pitcher, 60)
        self.assertGreater(early.effective_velocity, late.effective_velocity)
        self.assertGreater(early.effective_stuff, late.effective_stuff)

    def test_reliever_is_stronger_early_but_costlier(self):
        pitcher = DummyPitcher()
        starter = EffortModel(EffortProfile(0.0, 4.0, 4.0, 1.90))
        reliever = EffortModel(EffortProfile(1.0, 4.0, 4.0, 1.90))
        s = starter.workload_state(pitcher, 15)
        r = reliever.workload_state(pitcher, 15)
        self.assertGreater(r.effective_velocity, s.effective_velocity)
        self.assertGreater(r.effective_stuff, s.effective_stuff)
        self.assertGreater(r.fatigue, s.fatigue)
        self.assertGreaterEqual(r.fatigue / s.fatigue, 1.5)
        self.assertLessEqual(r.fatigue / s.fatigue, 2.3)

    def test_base_rating_never_mutates_across_workload(self):
        pitcher = DummyPitcher()
        before = dict(pitcher.__dict__)
        model = EffortModel(EffortProfile(1.0))
        for pitches in (0, 15, 30, 60, 90):
            model.workload_state(pitcher, pitches)
        self.assertEqual(before, pitcher.__dict__)


if __name__ == "__main__":
    unittest.main()
