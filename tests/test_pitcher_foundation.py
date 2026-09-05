import math
import unittest
from src.rng import RNG
from src.draft_scoring import score_pitcher_performance as score_pitcher_draft_performance
from src.pitching import (
    HitterMatchupProfile,Pitcher,PitcherStats,apply_pitcher_season_growth,
    generate_pitcher_stats,outcome_probabilities,recovery_days,simulate_outing,
)
from src.pitching.fatigue import effective_stats
from src.pitching.performance import score_pitcher_performance

class PitcherFoundationTests(unittest.TestCase):
    def stats(self,**kw):
        d=dict(velocity=100,stuff=100,control=100,breaking=100,stamina=100,resilience=100,talent=100);d.update(kw);return PitcherStats(**d)
    def test_ability_derived_and_role_does_not_mutate_stats(self):
        p=Pitcher("P",18,self.stats(),"starter");before=p.stats.as_dict();p.set_usage_role("reliever");self.assertEqual(before,p.stats.as_dict())
    def test_serialization_round_trip(self):
        p=Pitcher("P",19,self.stats(velocity=123,resilience=88),"reliever","power",12.5);self.assertEqual(p.as_dict(),Pitcher.from_dict(p.as_dict()).as_dict())
    def test_velocity_stuff_control_breaking_monotonic(self):
        low=outcome_probabilities(self.stats(velocity=80));high=outcome_probabilities(self.stats(velocity=120));self.assertLess(low["so"],high["so"])
        low=outcome_probabilities(self.stats(stuff=80));high=outcome_probabilities(self.stats(stuff=120));self.assertLess(low["so"],high["so"]);self.assertGreater(low["hit"],high["hit"])
        low=outcome_probabilities(self.stats(control=80));high=outcome_probabilities(self.stats(control=120));self.assertGreater(low["bb"],high["bb"])
        low=outcome_probabilities(self.stats(breaking=80));high=outcome_probabilities(self.stats(breaking=120));self.assertLess(low["so"],high["so"]);self.assertGreater(low["hr"],high["hr"])
    def test_stamina_and_resilience_roles(self):
        low=Pitcher("L",18,self.stats(stamina=60));high=Pitcher("H",18,self.stats(stamina=140))
        low_ip=sum(simulate_outing(low,RNG(i)).IP for i in range(120))/120;high_ip=sum(simulate_outing(high,RNG(i)).IP for i in range(120))/120;self.assertLess(low_ip,high_ip)
        self.assertGreater(recovery_days(105,60,"starter"),recovery_days(105,140,"starter"))
    def test_reliever_boost_and_faster_drain(self):
        s=self.stats();a=effective_stats(s,"starter",30);b=effective_stats(s,"reliever",30);self.assertGreater(b.velocity,a.velocity);self.assertGreater(b.stuff,a.stuff);self.assertGreater(b.fatigue_ratio,a.fatigue_ratio)
    def test_generation_player_spread_and_mean(self):
        rp=RNG(20260905);rn=RNG(20260906);pa=[];na=[]
        for _ in range(600):pa.append(generate_pitcher_stats(rp,True)[0].current_ability());na.append(generate_pitcher_stats(rn,False)[0].current_ability())
        self.assertGreater(sum(pa)/len(pa),sum(na)/len(na)+6);self.assertGreater(max(pa)-min(pa),max(na)-min(na))
    def test_extreme_probability_safety(self):
        for value in (30,50,100,150,200,250):
            for name in ("velocity","stuff","control","breaking"):
                q=outcome_probabilities(self.stats(**{name:value}))
                for key in ("bb","so","hr","hit","double","triple"):self.assertTrue(0<=q[key]<=1);self.assertTrue(math.isfinite(q[key]))
    def test_deterministic_outing(self):
        p=Pitcher("P",18,self.stats());a=simulate_outing(p,RNG(77)).as_dict();b=simulate_outing(p,RNG(77)).as_dict();self.assertEqual(a,b)
    def test_growth_and_performance(self):
        p=Pitcher("P",20,self.stats(talent=120));r=apply_pitcher_season_growth(p,RNG(9));self.assertEqual(r.age_after,21);self.assertEqual(set(r.deltas),{"velocity","stuff","control","breaking","stamina","resilience"})
        line=simulate_outing(Pitcher("Q",18,self.stats(stuff=130,control=120,breaking=120)),RNG(44));score=score_pitcher_performance(line,"starter");self.assertTrue(math.isfinite(score.score))
        common=score_pitcher_draft_performance(line,"starter");self.assertEqual(common.evaluation_mode,"PITCHER_ROLE_AWARE");self.assertAlmostEqual(common.score,score.score)

if __name__=="__main__":unittest.main()
