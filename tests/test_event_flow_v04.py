import tempfile,unittest
from pathlib import Path
from src import config
from src.career import CareerEngine
from src.events import CareerEvent,EventChoice,EventContext,Outcome,resolve_event
from src.persistence import load_game,save_game
from src.player import Player
from src.rng import RNG

class EventFlowV04Tests(unittest.TestCase):
    def make_engine(self,seed=100):
        r=RNG(seed);p=Player.random('Flow',r,'SS','R/R',1);e=CareerEngine(p,r);e.evaluate_draft();return e
    def force_preseason_pause(self,e):
        old=config.EVENT_PRESEASON_CHANCE
        try:
            config.EVENT_PRESEASON_CHANCE=1.0;s=e.advance_to_season_end(interactive=True)
        finally:config.EVENT_PRESEASON_CHANCE=old
        return s
    def test_interactive_season_advance_stops_on_event(self):
        e=self.make_engine(101);s=self.force_preseason_pause(e);self.assertTrue(s.has_pending_event);self.assertEqual(s.games_completed,0)
    def test_event_choice_then_same_season_resumes(self):
        e=self.make_engine(102);s=self.force_preseason_pause(e);event=e.pending_event();self.assertIsNotNone(event);e.resolve_pending_event(event.choices[0]);old1,old2=config.EVENT_PRESEASON_CHANCE,config.EVENT_BASE_CHANCE_PER_GAME
        try:
            config.EVENT_PRESEASON_CHANCE=0.;config.EVENT_BASE_CHANCE_PER_GAME=0.;e.advance_pro_games(3,stop_on_event=True)
        finally:config.EVENT_PRESEASON_CHANCE,config.EVENT_BASE_CHANCE_PER_GAME=old1,old2
        self.assertEqual(s.games_completed,3);self.assertFalse(s.has_pending_event)
    def test_event_stat_change_applies_before_next_game(self):
        e=self.make_engine(103);s=e.start_pro_season();s.preseason_checked=True;s.games_completed=50;s.pending_event_id='batting_mechanics_complete';s.pending_event_game=50;s.pending_event_phase='mid';event=e.pending_event();before=e.player.stats.contact;e.resolve_pending_event(event.choices[0]);self.assertGreater(e.player.stats.contact,before);changed=e.player.stats.contact;old=config.EVENT_BASE_CHANCE_PER_GAME
        try:config.EVENT_BASE_CHANCE_PER_GAME=0.;e.advance_pro_games(1)
        finally:config.EVENT_BASE_CHANCE_PER_GAME=old
        self.assertEqual(s.games_completed,51);self.assertEqual(e.player.stats.contact,changed)
    def test_injury_event_causes_real_missed_game(self):
        e=self.make_engine(104);s=e.start_pro_season();s.preseason_checked=True;s.games_completed=50;s.pending_event_id='hamstring_warning';s.pending_event_game=50;s.pending_event_phase='mid';event=e.pending_event();e.resolve_pending_event(event.choices[1]);self.assertIsNotNone(e.player.injury);g=s.record.first_team.G+s.record.farm.G;old=config.EVENT_BASE_CHANCE_PER_GAME
        try:config.EVENT_BASE_CHANCE_PER_GAME=0.;e.advance_pro_games(1)
        finally:config.EVENT_BASE_CHANCE_PER_GAME=old
        self.assertEqual(s.record.first_team.G+s.record.farm.G,g)
    def test_temporary_modifier_affects_only_current_season(self):
        e=self.make_engine(105);s=e.start_pro_season();s.preseason_checked=True
        custom=CareerEvent('test_temp','임시 효과','test','common','training','always',(EventChoice('x','x','stable',(Outcome('o','o',1.,1,temporary_ranges={'contact':(5,5)}),)),))
        res=resolve_event(custom,custom.choices[0],e.player,e.rng,e.year,EventContext(e.year,20,'early',s.current_level));s.growth_modifiers.merge(res.growth_modifiers);self.assertEqual(e.player.season_modifiers.get('contact'),5);e.finish_pro_season();self.assertEqual(e.player.season_modifiers,{})
    def test_auto_mode_handles_events_and_finishes_season(self):
        e=self.make_engine(106);record,_=e.finish_pro_season();self.assertGreaterEqual(record.first_team.G+record.farm.G,0);self.assertIsNone(e.current_session);self.assertEqual(len(e.player.seasons),1)
    def test_save_load_preserves_midseason_pending_event(self):
        e=self.make_engine(107);s=self.force_preseason_pause(e);self.assertTrue(s.has_pending_event)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'save.json';save_game(path,e);loaded=load_game(path);self.assertEqual(loaded.current_session.pending_event_id,s.pending_event_id);self.assertEqual(loaded.current_session.pending_event_game,s.pending_event_game);self.assertEqual(loaded.current_session.pending_event_phase,s.pending_event_phase)
    def test_save_load_preserves_rng_reproducibility(self):
        e=self.make_engine(108);e.advance_pro_games(17)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'save.json';save_game(path,e);loaded=load_game(path);self.assertAlmostEqual(e.rng.random(),loaded.rng.random())
    def test_same_seed_reproduces_event_game_numbers(self):
        def one(seed):
            r=RNG(seed);p=Player.random('A',r,'SS','R/R',2);e=CareerEngine(p,r);e.evaluate_draft();e.finish_pro_season();return [(x.get('event_id'),x.get('game_number')) for x in p.event_history if x.get('event_id')!='coach_change']
        self.assertEqual(one(109),one(109))
    def test_event_history_has_timeline_metadata(self):
        e=self.make_engine(110);e.finish_pro_season();events=[x for x in e.player.event_history if x.get('event_id')!='coach_change'];self.assertTrue(events)
        required={'year','age','game_number','season_phase','event_id','event_name','rarity','choice','outcome','stat_changes','trait_changes','injury_changes','temporary_effects'}
        self.assertTrue(required.issubset(events[0]))
    def test_once_per_season_prevents_duplicate_event_ids(self):
        e=self.make_engine(111);e.finish_pro_season();ids=[x['event_id'] for x in e.player.event_history if x.get('event_id')!='coach_change'];self.assertEqual(len(ids),len(set(ids)))
if __name__=='__main__':unittest.main()
