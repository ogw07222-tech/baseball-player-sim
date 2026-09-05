import math,unittest
from tools.balance_lab.h3.h321_baserunning import H321StealModel,first_to_third_probability,second_to_home_probability,dp_completion_probability,simulate_h321_baserunning
from tools.balance_lab.h3.steal import H32StealModel,StealContext

class H321Tests(unittest.TestCase):
    def test_h32_success_curve_preserved(self):
        c=StealContext(7,0,1,False);a=H32StealModel();b=H321StealModel()
        for s in (50,80,100,120,160,220):self.assertEqual(a.success_probability(s,c),b.success_probability(s,c))
    def test_low_speed_attempts_suppressed(self):
        vals=[simulate_h321_baserunning(s,120000,77).as_metrics()['SB_attempts_per_600'] for s in (50,60,70,80)]
        self.assertLess(vals[0],1);self.assertLess(vals[1],2);self.assertLess(vals[2],3);self.assertLess(vals[3],6)
    def test_low_speed_steal_value_near_zero(self):
        for s in (50,60,70,80):self.assertLess(abs(simulate_h321_baserunning(s,200000,9).steal_value),.0003)
    def test_low_speed_baserunning_value_continuous(self):
        vals=[simulate_h321_baserunning(s,250000,19).total_baserunning_value for s in (50,60,70,80,90)]
        self.assertTrue(all(b>a for a,b in zip(vals,vals[1:])))
    def test_advancement_monotonic(self):
        self.assertTrue(all(first_to_third_probability(a)<first_to_third_probability(b) for a,b in zip((50,70,90,110,140),(70,90,110,140,170))))
        self.assertTrue(all(second_to_home_probability(a)<second_to_home_probability(b) for a,b in zip((50,70,90,110,140),(70,90,110,140,170))))
    def test_dp_risk_decreases(self):self.assertGreater(dp_completion_probability(50),dp_completion_probability(100));self.assertGreater(dp_completion_probability(100),dp_completion_probability(160))
    def test_high_speed_diminishing(self):
        vals={s:simulate_h321_baserunning(s,300000,31).total_baserunning_value for s in (130,140,150,160,170)}
        gains=[vals[b]-vals[a] for a,b in ((130,140),(140,150),(150,160),(160,170))]
        self.assertGreater(gains[0],gains[-1]);self.assertTrue(all(g>0 for g in gains))
    def test_deterministic(self):self.assertEqual(simulate_h321_baserunning(100,20000,123).as_metrics(),simulate_h321_baserunning(100,20000,123).as_metrics())
    def test_numerical_stability(self):
        for s in (30,40,50,70,100,130,160,190,220):
            m=simulate_h321_baserunning(s,10000,1000+s).as_metrics();self.assertTrue(all(math.isfinite(v) for v in m.values()));self.assertTrue(0<=m['SB_success%']<=1)
if __name__=='__main__':unittest.main()
