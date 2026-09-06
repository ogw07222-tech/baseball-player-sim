from __future__ import annotations

import subprocess
import unittest

from src.hitting.baserunning import GameState,steal_attempt_probability
from src.hitting.model import Pitch
from src.hitting.normalization import normalize_hitter
from src.pitching.model import PitcherStats
from tools.kbo_rating_inference.core import inverse_velocity_raw,velocity_contract,weighted_summary
from tools.kbo_rating_inference.generated_population import neutral_metrics
from tools.kbo_rating_inference.infer_hitters import actual_metrics,prior_penalty
from tools.pitcher_joint_v3.adapter import JointWeights,PitcherJointV3Adapter
from tools.pitcher_joint_v4.first_team_population import WeightedSeason,build_first_team_seasons

BASE_SHA='c6c69ceefb3c4f2f5fbe88a772b4508f842e58dd'

class KBORatingInferenceTests(unittest.TestCase):
 def test_first_team_population_excludes_zero_pa(self):
  rows=build_first_team_seasons(2,77001,3);self.assertTrue(all(r.pa>0 for r in rows))
 def test_first_team_population_pa_weighted(self):
  result=weighted_summary([80,120],[100,900]);self.assertAlmostEqual(result['mean'],116.0);self.assertGreater(result['p50'],100)
 def test_first_team_population_seed_stable(self):
  a=build_first_team_seasons(2,77002,2);b=build_first_team_seasons(2,77002,2);self.assertEqual([(x.age,x.pa,x.contact,x.power,x.discipline,x.speed) for x in a],[(x.age,x.pa,x.contact,x.power,x.discipline,x.speed) for x in b])
 def test_first_team_population_neutral_offense_sane(self):
  rows=[WeightedSeason(28,600,109,109,109,110,'R/R')];m=neutral_metrics(rows,15000,77003);self.assertTrue(.20<m['AVG']<.34);self.assertTrue(.25<m['OBP']<.43);self.assertTrue(.30<m['SLG']<.55);self.assertTrue(.04<m['BB%']<.15);self.assertTrue(.12<m['K%']<.30)
 def test_real_velocity_inverse_mapping(self):
  self.assertAlmostEqual(inverse_velocity_raw(146.0),97.0,places=5);raw=inverse_velocity_raw(152.3);self.assertAlmostEqual(velocity_contract(152.3)['avg_fastball_kmh'],152.3,places=5);self.assertTrue(110<raw<130)
 def test_measured_velocity_not_overridden_by_stat_fit(self):
  a=velocity_contract(147.0);b=velocity_contract(147.0);self.assertEqual(a,b);self.assertAlmostEqual(a['gp_velocity'],101.5,places=5)
 def test_contact_fit_identity(self):
  self.assertGreater(normalize_hitter(130,109,109,110).contact,normalize_hitter(90,109,109,110).contact)
 def test_power_fit_identity(self):
  self.assertGreater(normalize_hitter(109,140,109,110).power,normalize_hitter(109,90,109,110).power)
 def test_discipline_fit_identity(self):
  self.assertGreater(normalize_hitter(109,109,140,110).discipline,normalize_hitter(109,109,90,110).discipline)
 def test_speed_requires_running_evidence(self):
  no_running=actual_metrics({'PA':'400','AB':'360','H':'100','BB':'40','SO':'80','HR':'10','SB':'0','CS':'0'});self.assertNotIn('SB_attempt_pct',no_running);self.assertGreater(prior_penalty((109,109,109,165),no_running,400),prior_penalty((109,109,109,110),no_running,400));state=GameState(inning=5,outs=1,score_diff=0,first_occupied=True,second_occupied=False);self.assertGreater(steal_attempt_probability(140,state),steal_attempt_probability(80,state))
 def _adapter_delta(self,stuff=109,control=109,breaking=109):
  stats=PitcherStats(97,stuff,control,breaking,100,100,100);ad=PitcherJointV3Adapter(stats,JointWeights(),physical_kmh_override=146.0);pitch=Pitch(True,'middle','fastball',0,0,0,0);return ad,ad.modifier(pitch,0)
 def test_control_fit_bb_identity(self):
  low,_=self._adapter_delta(control=89);high,_=self._adapter_delta(control=129);self.assertGreater(high.pitcher_snapshot().control,low.pitcher_snapshot().control)
 def test_stuff_fit_contact_quality_identity(self):
  _,base=self._adapter_delta();_,high=self._adapter_delta(stuff=129);self.assertLess(high[1],base[1])
 def test_breaking_fit_whiff_identity(self):
  _,base=self._adapter_delta();_,high=self._adapter_delta(breaking=129);self.assertLess(high[0],base[0])
 def test_inverse_fit_extreme_safety(self):
  for kmh in (133.,140.,146.,152.,159.):self.assertTrue(30<=inverse_velocity_raw(kmh)<=250)
 def test_no_raw_mutation(self):
  raw=[123.,134.,117.,142.];before=tuple(raw);normalize_hitter(*raw);velocity_contract(150.);self.assertEqual(tuple(raw),before)
 def test_h32_formula_diff_none(self):
  try:result=subprocess.run(['git','diff','--exit-code',BASE_SHA,'--','src/hitting/model.py','src/hitting/parameters.py','src/hitting/baserunning.py'],capture_output=True,text=True,check=False)
  except FileNotFoundError:self.skipTest('git unavailable')
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
