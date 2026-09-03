import json,math,statistics,tempfile,unittest
from pathlib import Path
from src import config
from src.career import CareerEngine
from src.coaches import CoachingStaff,FieldingCoach,generate_batting_coach,generate_fielding_coach
from src.events import EVENT_BY_ID,resolve_event
from src.growth import GrowthExperience,apply_season_growth,growth_distribution
from src.persistence import load_game,save_game
from src.player import Player
from src.rng import RNG
from src.simulation import logistic_range
from src.stats import PlayerStats

def base_player(talent=100,age=20):return Player('T',age,PlayerStats(80,80,80,80,80,80,80,80,80,talent),development_profile='normal')
def clone(p):return Player.from_dict(p.as_dict())
def staff(kind):return CoachingStaff(generate_batting_coach(RNG(100),kind),generate_fielding_coach(RNG(200),'balanced'))
class BalanceV03Tests(unittest.TestCase):
 def test_natural_growth_average_reduced(self):
  vals=[]
  for seed in range(300):
   p=base_player();r=apply_season_growth(p,RNG(seed));vals.append(sum(r.deltas.values())/9)
  avg=statistics.mean(vals);self.assertLess(avg,3.0);self.assertGreater(avg,.4)
 def test_talent_mean_higher_but_high_talent_can_fail(self):
  low=[];high=[]
  for seed in range(400):
   p1=base_player(70);p2=base_player(160);low.append(apply_season_growth(p1,RNG(seed)).deltas['contact']);high.append(apply_season_growth(p2,RNG(seed)).deltas['contact'])
  self.assertGreater(statistics.mean(high),statistics.mean(low));self.assertTrue(any(v<=0 for v in high))
 def test_coach_types_change_direction(self):
  p=base_player(110);power=staff('power');precision=staff('precision');mp=growth_distribution(p,'power',power)[0];mq=growth_distribution(p,'power',precision)[0];cp=growth_distribution(p,'contact',power)[0];cq=growth_distribution(p,'contact',precision)[0];self.assertGreater(mp,mq);self.assertGreater(cq,cp)
 def test_power_coach_raises_power_expectation(self):
  p=base_player();self.assertGreater(growth_distribution(p,'power',staff('power'))[0],growth_distribution(p,'power',staff('balanced'))[0])
 def test_power_coach_does_not_blanket_raise_contact(self):
  p=base_player();self.assertLess(growth_distribution(p,'contact',staff('power'))[0],growth_distribution(p,'contact',staff('balanced'))[0])
 def test_event_seed_reproducible(self):
  event=EVENT_BY_ID['hamstring_warning'];choice=event.choices[0];a=base_player();b=base_player();ra=resolve_event(event,choice,a,RNG(77),2027);rb=resolve_event(event,choice,b,RNG(77),2027);self.assertEqual(ra.stat_changes,rb.stat_changes);self.assertEqual(ra.outcome_id,rb.outcome_id);self.assertEqual(a.event_history,b.event_history)
 def test_risky_variance_exceeds_rehab(self):
  event=EVENT_BY_ID['hamstring_warning'];risk=[];safe=[]
  quality={o.id:o.quality for c in event.choices for o in c.outcomes}
  for seed in range(1000):
   risk.append(quality[resolve_event(event,event.choices[0],base_player(),RNG(seed),2027).outcome_id]);safe.append(quality[resolve_event(event,event.choices[1],base_player(),RNG(seed+5000),2027).outcome_id])
  self.assertGreater(statistics.pstdev(risk),statistics.pstdev(safe))
 def test_play_through_disaster_possible(self):
  event=EVENT_BY_ID['hamstring_warning'];outcomes={resolve_event(event,event.choices[0],base_player(),RNG(s),2027).outcome_id for s in range(500)};self.assertIn('disaster',outcomes)
 def test_rehab_extreme_loss_low(self):
  event=EVENT_BY_ID['hamstring_warning'];bad=0
  for s in range(1000):bad+=resolve_event(event,event.choices[1],base_player(),RNG(s),2027).outcome_id=='failure'
  self.assertLess(bad/1000,.07)
 def test_event_history_and_save(self):
  r=RNG(9);p=Player.random('A',r);e=CareerEngine(p,r);e.evaluate_draft();event=EVENT_BY_ID['hamstring_warning'];resolve_event(event,event.choices[1],p,r,e.year)
  self.assertEqual(p.event_history[-1]['event_id'],'hamstring_warning')
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'save.json';save_game(path,e);loaded=load_game(path);self.assertEqual(p.event_history,loaded.player.event_history)
 def test_v1_save_compatibility(self):
  r=RNG(11);p=Player.random('A',r);e=CareerEngine(p,r);e.evaluate_draft()
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'save.json';save_game(path,e);data=json.loads(path.read_text());data['save_version']=1;data['player'].pop('event_history',None);data['player'].pop('development_profile',None);data['career'].pop('team_coaches',None);path.write_text(json.dumps(data));loaded=load_game(path);self.assertEqual(loaded.player.development_profile,'normal')
 def test_coach_replacement_changes_modifier(self):
  r=RNG(22);p=Player.random('A',r);e=CareerEngine(p,r);e.evaluate_draft();team=p.team;before=e.team_coaches[team].as_dict();old=config.COACH_REPLACEMENT_CHANCE
  try:
   config.COACH_REPLACEMENT_CHANCE=1.0;e._maybe_replace_coaches()
  finally:config.COACH_REPLACEMENT_CHANCE=old
  self.assertNotEqual(before,e.team_coaches[team].as_dict())
 def test_draft_undrafted_rate_below_half(self):
  undrafted=0
  for seed in range(300):
   r=RNG(10000+seed);p=Player.random('A',r);d=CareerEngine(p,r).evaluate_draft();undrafted+=d.round is None
  self.assertLess(undrafted/300,.50)
 def test_farm_opportunity_increased(self):
  p=base_player(90);p.stats=PlayerStats(63,63,63,63,63,63,63,63,63,90);p.team='키움 히어로즈';e=CareerEngine(p,RNG(1),phase='PRO');new=e._play_probability('FARM');old=logistic_range(p.stats.current_ability()-68,.55,.94,16.);self.assertGreater(new,old)
 def test_first_team_entry_not_easy_for_low_ability(self):
  hits=0
  for seed in range(300):
   p=base_player(80);p.stats=PlayerStats(60,60,60,60,60,60,60,60,60,80);p.team='KIA 타이거즈';p.draft_info={'round':8};e=CareerEngine(p,RNG(seed),phase='PRO');hits+=e._initial_first_team_chance()
  self.assertLess(hits/300,.15)
if __name__=='__main__':unittest.main()
