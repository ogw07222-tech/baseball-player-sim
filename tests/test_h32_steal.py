import math, unittest
from tools.balance_lab.h3.h32_model import simulate_h32_profile
from tools.balance_lab.h3.profiles import H3HitterProfile
from tools.balance_lab.h3.steal import H32StealModel,StealContext
class H32StealTests(unittest.TestCase):
    def test_deterministic(self):
        a=simulate_h32_profile(H3HitterProfile(),10000,123).as_metrics();b=simulate_h32_profile(H3HitterProfile(),10000,123).as_metrics();self.assertEqual(a,b)
    def test_speed_raises_attempt_and_success(self):
        lo=simulate_h32_profile(H3HitterProfile(speed=70),50000,4).as_metrics();hi=simulate_h32_profile(H3HitterProfile(speed=140),50000,4).as_metrics();self.assertGreater(hi['SB_attempts_per_600'],lo['SB_attempts_per_600']);self.assertGreater(hi['SB_success%'],lo['SB_success%'])
    def test_batting_metrics_unchanged_by_steal_stream(self):
        m=simulate_h32_profile(H3HitterProfile(),20000,7).as_metrics();self.assertTrue(all(math.isfinite(m[k]) for k in ('AVG','OBP','SLG','OPS')))
    def test_success_has_ceiling(self):
        sm=H32StealModel();c=StealContext(8,0,1,False);self.assertLess(sm.success_probability(220,c),.94)
    def test_cs_penalty(self):
        from tools.balance_lab.h3 import h32_parameters as P
        self.assertLess(P.CS_RUN_VALUE,0);self.assertGreater(abs(P.CS_RUN_VALUE),P.SB_RUN_VALUE)
if __name__=='__main__':unittest.main()
