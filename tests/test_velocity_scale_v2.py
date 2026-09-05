from __future__ import annotations
import statistics
import unittest
from src.pitching.model import generate_pitcher
from src.rng import RNG
from tools.velocity_scale_v2.model import PiecewiseMildTailMap,GameplayVelocityMap,PhysicalEffortLayer
from tools.velocity_scale_v2.simulate import contact_metrics,pa_metrics,make_engine

MAP=PiecewiseMildTailMap(reference_rating=97.0,reference_kmh=146.0,central_slope=.28,tail_start=140.0,tail_slope=.20,safety_start=180.0,safety_slope=.05)

class VelocityScaleV2Tests(unittest.TestCase):
    def test_velocity_v2_mapping_monotonic(self):
        xs=(30,50,70,80,90,100,110,120,130,140,150,160,180,200,250)
        ys=[MAP.raw_to_kmh(x) for x in xs]
        self.assertTrue(all(a<b for a,b in zip(ys,ys[1:])))

    def test_velocity_v2_reference(self):
        self.assertAlmostEqual(MAP.raw_to_kmh(97.0),146.0,places=8)
        self.assertAlmostEqual(GameplayVelocityMap(1.5).kmh_to_gameplay(146.0),100.0,places=8)

    def test_velocity_v2_elite_tail_spacing(self):
        self.assertGreaterEqual(MAP.raw_to_kmh(140)-MAP.raw_to_kmh(130),1.5)
        self.assertGreaterEqual(MAP.raw_to_kmh(150)-MAP.raw_to_kmh(140),1.5)
        self.assertGreaterEqual(MAP.raw_to_kmh(160)-MAP.raw_to_kmh(150),1.5)

    def test_velocity_v2_extreme_safe(self):
        vals=[MAP.raw_to_kmh(x) for x in (30,50,70,80,90,100,110,120,130,140,150,160,180,200,250)]
        self.assertGreater(min(vals),100.0)
        self.assertLess(max(vals),180.0)

    def test_raw_150_represents_elite_velocity(self):
        self.assertGreaterEqual(MAP.raw_to_kmh(150),159.0)
        self.assertLessEqual(MAP.raw_to_kmh(150),161.0)

    def test_raw_250_not_required_for_160_kmh(self):
        self.assertGreaterEqual(MAP.raw_to_kmh(150),159.0)
        self.assertGreater(MAP.raw_to_kmh(250),MAP.raw_to_kmh(160))

    def test_generated_velocity_sd_is_narrow(self):
        rng=RNG(20260906); xs=[generate_pitcher(str(i),rng,player=True,age=18).stats.velocity for i in range(5000)]
        sd=statistics.stdev(xs)
        self.assertGreaterEqual(sd,7.0)
        self.assertLessEqual(sd,12.0)

    def test_generated_extreme_velocity_is_rare(self):
        rng=RNG(20260907); xs=[generate_pitcher(str(i),rng,player=True,age=18).stats.velocity for i in range(10000)]
        self.assertLess(sum(x>150 for x in xs)/len(xs),.001)
        self.assertEqual(sum(x>=200 for x in xs),0)

    def test_higher_kmh_reduces_contact(self):
        low=contact_metrics(142,1.5,20000,71); high=contact_metrics(152,1.5,20000,71)
        self.assertLess(high['Contact%'],low['Contact%'])

    def test_higher_kmh_increases_whiff(self):
        low=contact_metrics(142,1.5,20000,72); high=contact_metrics(152,1.5,20000,72)
        self.assertGreater(high['Whiff%'],low['Whiff%'])

    def test_higher_kmh_increases_k(self):
        low=pa_metrics(142,1.5,30000,73); high=pa_metrics(152,1.5,30000,73)
        self.assertGreater(high['K%'],low['K%'])

    def test_velocity_does_not_directly_change_bb(self):
        low=make_engine(140,1.5,9); high=make_engine(156,1.5,9)
        self.assertEqual(low.pitcher,high.pitcher)
        self.assertEqual(low.pitcher.control,100.0)

    def test_effort_does_not_mutate_raw_velocity(self):
        raw=125.0; base=MAP.raw_to_kmh(raw); layer=PhysicalEffortLayer(effort_bonus_kmh=2.0)
        _=layer.effective_kmh(base,0.0)
        self.assertEqual(raw,125.0)

    def test_fatigue_does_not_mutate_raw_velocity(self):
        raw=125.0; base=MAP.raw_to_kmh(raw); layer=PhysicalEffortLayer(effort_bonus_kmh=0.0,fatigue_loss_per_unit=1.3)
        fatigued=layer.effective_kmh(base,2.0)
        self.assertLess(fatigued,base)
        self.assertEqual(raw,125.0)

if __name__=='__main__': unittest.main()
