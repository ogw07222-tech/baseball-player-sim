"""Balance regression tests carried forward and updated for v0.4 scale."""
import json,statistics,tempfile,unittest
from pathlib import Path
from src import config
from src.career import CareerEngine
from src.coaches import CoachingStaff,generate_batting_coach,generate_fielding_coach
from src.events import EVENT_BY_ID,resolve_event
from src.growth import apply_season_growth,growth_distribution
from src.persistence import load_game,save_game
from src.player import Player
from src.rng import RNG
from src.stats import PlayerStats

def base_player(talent=100,age=20):return Player('T',age,PlayerStats(80,80,80,80,80,80,80,80,80,talent),development_profile='normal')
def staff(kind):return CoachingStaff(generate_batting_coach(RNG(100),kind),generate_fielding_coach(RNG(200),'balanced'))
class BalanceV04Tests(unittest.TestCase):
    def test_starting_ability_scale_near_70_with_dispersion(self):
        vals=[Player.random('A',RNG(i)).stats.current_ability() for i in range(1000)];m=statistics.mean(vals);self.assertGreaterEqual(m,68);self.assertLessEqual(m,72);self.assertTrue(any(v<60 for v in vals));self.assertTrue(any(v>=80 for v in vals));self.assertLess(sum(v>=100 for v in vals)/len(vals),.01)
    def test_natural_growth_remains_weak(self):
        vals=[]
        for seed in range(250):vals.append(sum(apply_season_growth(base_player(),RNG(seed)).deltas.values())/9)
        self.assertLess(statistics.mean(vals),3.0);self.assertGreater(statistics.mean(vals),.3)
    def test_talent_mean_higher_but_high_talent_can_fail(self):
        low=[];high=[]
        for seed in range(350):low.append(apply_season_growth(base_player(70),RNG(seed)).deltas['contact']);high.append(apply_season_growth(base_player(160),RNG(seed)).deltas['contact'])
        self.assertGreater(statistics.mean(high),statistics.mean(low));self.assertTrue(any(v<=0 for v in high))
    def test_coach_types_change_direction(self):
        p=base_player(110);self.assertGreater(growth_distribution(p,'power',staff('power'))[0],growth_distribution(p,'power',staff('precision'))[0]);self.assertGreater(growth_distribution(p,'contact',staff('precision'))[0],growth_distribution(p,'contact',staff('power'))[0])
    def test_draft_distribution_not_extreme(self):
        rounds=[]
        for seed in range(300):
            r=RNG(10000+seed);d=CareerEngine(Player.random('A',r),r).evaluate_draft();rounds.append(d.round)
        und=sum(x is None for x in rounds)/len(rounds);first=sum(x==1 for x in rounds)/len(rounds);self.assertLess(und,.35);self.assertGreater(und,.10);self.assertLess(first,.15)
    def test_farm_baseline_is_raised_to_v04_scale(self):
        self.assertGreaterEqual(config.FARM_PLAY_BASELINE,70);p=base_player(90);p.stats=PlayerStats(71,71,71,71,71,71,71,71,71,90);p.team='키움 히어로즈';e=CareerEngine(p,RNG(1),phase='PRO');self.assertGreater(e._play_probability('FARM'),.70)
    def test_first_team_entry_not_easy_for_average_rookie(self):
        hits=0
        for seed in range(250):
            p=base_player(80,18);p.stats=PlayerStats(72,72,72,72,72,72,72,72,72,80);p.team='KIA 타이거즈';p.draft_info={'round':8};hits+=CareerEngine(p,RNG(seed),phase='PRO')._initial_first_team_chance()
        self.assertLess(hits/250,.20)
    def test_hamstring_risky_variance_exceeds_rehab(self):
        event=EVENT_BY_ID['hamstring_warning'];quality={o.id:o.quality for c in event.choices for o in c.outcomes};risk=[];safe=[]
        for seed in range(700):risk.append(quality[resolve_event(event,event.choices[0],base_player(),RNG(seed),2027).outcome_id]);safe.append(quality[resolve_event(event,event.choices[1],base_player(),RNG(seed+5000),2027).outcome_id])
        self.assertGreater(statistics.pstdev(risk),statistics.pstdev(safe));self.assertIn('disaster',{resolve_event(event,event.choices[0],base_player(),RNG(s),2027).outcome_id for s in range(500)})
    def test_event_history_and_v1_v2_save_compatibility(self):
        r=RNG(9);p=Player.random('A',r);e=CareerEngine(p,r);e.evaluate_draft();e.advance_pro_games(12)
        with tempfile.TemporaryDirectory() as tmp:
            for version in (1,2):
                path=Path(tmp)/f's{version}.json';save_game(path,e);data=json.loads(path.read_text());data['save_version']=version
                if version==1:data['player'].pop('event_history',None);data['player'].pop('development_profile',None);data['career'].pop('team_coaches',None)
                data['player'].pop('season_modifiers',None)
                if data['career'].get('current_session'):
                    for k in ('pending_event_id','pending_event_game','pending_event_phase','occurred_event_ids','cooldown_until','last_event_game','growth_modifiers','preseason_checked'):data['career']['current_session'].pop(k,None)
                path.write_text(json.dumps(data));loaded=load_game(path);self.assertEqual(loaded.player.development_profile,'normal' if version==1 else p.development_profile);self.assertEqual(loaded.player.season_modifiers,{})
if __name__=='__main__':unittest.main()
