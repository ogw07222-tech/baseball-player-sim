"""High-school, draft, KBO season, coaching, career events, awards and retirement."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from . import config
from .coaches import CoachingStaff, generate_batting_coach, generate_fielding_coach, generate_league_staffs
from .events import CareerEvent, EventChoice, EventResolution, auto_choose, choose_season_events, resolve_event
from .growth import GrowthExperience, GrowthModifiers, GrowthResult, apply_season_growth
from .player import InjuryStatus, Player
from .records import BattingLine, SeasonRecord
from .rng import RNG
from .simulation import logistic_range, simulate_player_game
from .traits import TRAIT_CATALOG, Trait, has_trait, traits_conflict

@dataclass(frozen=True)
class TournamentResult:
    name:str; games:int; line:BattingLine; champion:bool; mvp:bool
@dataclass(frozen=True)
class DraftResult:
    team:str; round:int|None; pick:int|None; status:str; scouting_score:float; scouted_talent:int
    def as_dict(self)->dict[str,object]:return {'team':self.team,'round':self.round,'pick':self.pick,'status':self.status,'scouting_score':round(self.scouting_score,3),'scouted_talent':self.scouted_talent}
@dataclass
class ProSeasonSession:
    year:int; record:SeasonRecord; games_completed:int=0; current_level:str='FARM'
    @property
    def finished(self)->bool:return self.games_completed>=config.KBO_FIRST_TEAM_GAMES
    def as_dict(self)->dict[str,object]:return {'year':self.year,'record':self.record.as_dict(),'games_completed':self.games_completed,'current_level':self.current_level}
    @classmethod
    def from_dict(cls,data:dict[str,object])->'ProSeasonSession':return cls(int(data['year']),SeasonRecord.from_dict(dict(data['record'])),int(data.get('games_completed',0)),str(data.get('current_level','FARM')))

EventDecider=Callable[[CareerEvent,Player],EventChoice]

@dataclass
class CareerEngine:
    player:Player; rng:RNG; year:int=config.START_YEAR; tournament_index:int=0; phase:str='HIGH_SCHOOL'; tournament_results:list[dict[str,object]]=field(default_factory=list); current_session:ProSeasonSession|None=None; team_coaches:dict[str,CoachingStaff]=field(default_factory=dict); coach_history:list[dict[str,object]]=field(default_factory=list); last_event_resolutions:list[EventResolution]=field(default_factory=list)
    def _ensure_coaches(self)->None:
        if not self.team_coaches:self.team_coaches=generate_league_staffs(self.rng)
    def current_coaching_staff(self)->CoachingStaff:
        self._ensure_coaches()
        if not self.player.team:raise RuntimeError('player has no team')
        return self.team_coaches[self.player.team]
    def run_next_tournament(self)->TournamentResult:
        if self.phase!='HIGH_SCHOOL':raise RuntimeError('not in high-school phase')
        if self.tournament_index>=len(config.HIGH_SCHOOL_TOURNAMENTS):raise RuntimeError('all tournaments already completed')
        name=config.HIGH_SCHOOL_TOURNAMENTS[self.tournament_index];line=BattingLine();games=0;alive=True
        while alive and games<5:
            games+=1;opponent=self.rng.uniform(*config.HIGH_SCHOOL_PITCHER_LEVEL);simulate_player_game(self.player,opponent,self.rng,line,pa_count=self.rng.randint(4,5));edge=(self.player.stats.current_ability()-opponent)/150.;win=max(.25,min(.75,.50+edge+self.rng.gauss(0,.035)));alive=self.rng.random()<win
        champion=alive and games==5;mvp=games>=3 and line.PA>=12 and line.OPS>=1.05 and self.rng.random()<min(.85,.25+(line.OPS-1.0));self.player.high_school_stats.add(line)
        if mvp:self.player.awards.append({'year':self.year,'award':f'{name} MVP','level':'HIGH_SCHOOL'})
        result=TournamentResult(name,games,line,champion,mvp);self.tournament_results.append({'name':name,'games':games,'line':line.as_dict(),'champion':champion,'mvp':mvp});self.tournament_index+=1;return result
    def finish_high_school(self)->None:
        while self.tournament_index<len(config.HIGH_SCHOOL_TOURNAMENTS):self.run_next_tournament()
    def evaluate_draft(self)->DraftResult:
        if self.phase!='HIGH_SCHOOL':
            if self.player.draft_info:
                i=self.player.draft_info;return DraftResult(str(i['team']),int(i['round']) if i.get('round') else None,int(i['pick']) if i.get('pick') else None,str(i['status']),float(i['scouting_score']),int(i['scouted_talent']))
            raise RuntimeError('draft can only run after high school')
        self.finish_high_school();scouted=max(0,int(round(self.rng.gauss(self.player.stats.talent,24.))));ability=self.player.stats.current_ability();perf=72.+(self.player.high_school_stats.OPS-.75)*55.+min(12.,self.player.high_school_stats.HR*1.4);position=75.+config.POSITION_DRAFT_VALUE.get(self.player.position,0);w=config.DRAFT_WEIGHTS
        score=ability*w['current_ability']+scouted*w['scouted_talent']+perf*w['performance']+position*w['position']+self.player.stats.durability*w['health']+self.rng.gauss(0.,7.)+config.DRAFT_SCORE_OFFSET
        t=config.DRAFT_THRESHOLDS
        if score>=t['round1']:round_no=1
        elif score>=t['round2_3']:round_no=self.rng.randint(2,3)
        elif score>=t['round4_7']:round_no=self.rng.randint(4,7)
        elif score>=t['round8_11']:round_no=self.rng.randint(8,11)
        else:round_no=None
        team=str(self.rng.choice(config.KBO_TEAMS)['name']);status='지명' if round_no else '미지명 육성선수 계약';pick=(round_no-1)*10+self.rng.randint(1,10) if round_no else None;draft=DraftResult(team,round_no,pick,status,score,scouted)
        self.player.draft_info=draft.as_dict();self.player.team=team;self.player.roster_level='FARM';self.player.team_history.append({'year':self.year,'team':team,'event':'KBO 입단'});self.phase='PRO';self._ensure_coaches();return draft
    def _team_config(self)->dict[str,object]:
        if not self.player.team:raise RuntimeError('player has no KBO team')
        return next(dict(t) for t in config.KBO_TEAMS if t['name']==self.player.team)
    def _initial_first_team_chance(self)->bool:
        team=self._team_config();competition=float(team['depth'])+config.POSITION_COMPETITION.get(self.player.position,0)-config.FIRST_TEAM_INITIAL_OFFSET;chance=logistic_range(self.player.stats.current_ability()-competition,.02,.72,11.)
        if self.player.draft_info and self.player.draft_info.get('round')==1:chance+=.08
        return self.rng.random()<min(.82,chance)
    def start_pro_season(self)->ProSeasonSession:
        if self.phase=='HIGH_SCHOOL':self.evaluate_draft()
        if self.phase!='PRO':raise RuntimeError('career is not in professional phase')
        if self.current_session:return self.current_session
        level='FIRST' if self._initial_first_team_chance() else 'FARM';self.player.roster_level=level;self.current_session=ProSeasonSession(self.year,SeasonRecord(self.year,self.player.age,self.player.team or ''),0,level);return self.current_session
    def _update_form(self)->None:
        if self.player.form_games_remaining>0:
            self.player.form_games_remaining-=1
            if self.player.form_games_remaining<=0:self.player.form='normal'
            return
        mf=logistic_range(100-self.player.stats.mentality,.65,1.35,35);slump=config.SLUMP_BASE_CHANCE_PER_GAME*mf;hot=config.HOT_STREAK_BASE_CHANCE_PER_GAME/max(.7,mf)
        if has_trait(self.player.traits,'volatile'):slump*=1.55;hot*=1.35
        if has_trait(self.player.traits,'consistent'):slump*=.62;hot*=.72
        roll=self.rng.random()
        if roll<slump:self.player.form='slump';self.player.form_games_remaining=self.rng.randint(config.FORM_MIN_GAMES,config.FORM_MAX_GAMES)
        elif roll<slump+hot:self.player.form='hot';self.player.form_games_remaining=self.rng.randint(config.FORM_MIN_GAMES,config.FORM_MAX_GAMES)
    def _injury_chance(self)->float:
        d=logistic_range(100-self.player.stats.durability,.55,1.65,32.);f=1+max(0.,self.player.fatigue-50)/65.;a=1+max(0,self.player.age-30)*.045;chance=config.INJURY_BASE_CHANCE_PER_GAME*d*f*a
        if has_trait(self.player.traits,'injury_risk'):chance*=1.65
        return min(.08,chance)
    def _maybe_injure(self)->None:
        if self.player.injury or self.rng.random()>=self._injury_chance():return
        severity=self.rng.weighted_choice((('경미',.72),('보통',.24),('중상',.04)))
        if severity=='경미':games=self.rng.randint(2,10);name=self.rng.choice(('가벼운 근육통','손목 염좌','발목 통증'))
        elif severity=='보통':games=self.rng.randint(12,45);name=self.rng.choice(('햄스트링 부상','어깨 염좌','손가락 골절'))
        else:games=self.rng.randint(60,150);name=self.rng.choice(('무릎 인대 부상','어깨 중상','발목 골절'))
        self.player.injury=InjuryStatus(name,severity,games);self.player.injury_history.append({'year':self.year,'age':self.player.age,'name':name,'severity':severity,'games':games})
    def _recover_day(self)->None:
        self.player.fatigue=max(0.,self.player.fatigue-config.FATIGUE_REST_RECOVERY)
        if self.player.injury:
            recovery=2 if has_trait(self.player.traits,'quick_recovery') and self.rng.random()<.25 else 1;self.player.injury.games_remaining-=recovery
            if self.player.injury.games_remaining<=0:self.player.injury=None
    def _play_probability(self,level:str)->float:
        ability=self.player.stats.current_ability()
        return logistic_range(ability-config.FIRST_TEAM_PLAY_BASELINE,.38,.90,16.) if level=='FIRST' else logistic_range(ability-config.FARM_PLAY_BASELINE,.55,.94,16.)
    def _fatigue_after_game(self)->None:
        self.player.fatigue=min(100.,self.player.fatigue+config.FATIGUE_PER_GAME_BASE*(100./(max(1,self.player.stats.stamina)+45.)))
    def _reconsider_roster(self,session:ProSeasonSession)->None:
        if session.games_completed==0 or session.games_completed%10:return
        team=self._team_config();competition=float(team['depth'])+config.POSITION_COMPETITION.get(self.player.position,0)-config.CALLUP_COMPETITION_OFFSET;line=session.record.first_team if session.current_level=='FIRST' else session.record.farm;form_bonus=max(-12.,min(15.,(line.OPS-.75)*25.)) if line.PA>=20 else 0.;evaluation=self.player.stats.current_ability()+form_bonus+self.rng.gauss(0,5.5)
        if session.current_level=='FARM' and evaluation>=competition:
            session.current_level='FIRST';self.player.roster_level='FIRST';self.player.debut_year=self.player.debut_year or self.year
        elif session.current_level=='FIRST' and evaluation<competition-13 and line.PA>=30:session.current_level='FARM';self.player.roster_level='FARM'
    def advance_pro_games(self,count:int)->ProSeasonSession:
        if count<=0:raise ValueError('count must be positive')
        s=self.start_pro_season();team=self._team_config()
        for _ in range(min(count,config.KBO_FIRST_TEAM_GAMES-s.games_completed)):
            s.games_completed+=1
            if self.player.injury:self._recover_day();self._update_form();self._reconsider_roster(s);continue
            if self.rng.random()>=self._play_probability(s.current_level):self._recover_day();self._update_form();self._reconsider_roster(s);continue
            target=s.record.first_team if s.current_level=='FIRST' else s.record.farm;level=float(team['first_team_level'] if s.current_level=='FIRST' else team['farm_level']);simulate_player_game(self.player,level,self.rng,target)
            if s.current_level=='FIRST' and self.player.debut_year is None:self.player.debut_year=self.year
            self._fatigue_after_game();self._maybe_injure();self._update_form();self._reconsider_roster(s)
        return s
    def _determine_awards(self,record:SeasonRecord)->list[str]:
        line=record.first_team
        if line.PA<300:return []
        rivals=[]
        for _ in range(9):
            avg=max(.210,min(.360,self.rng.gauss(.275,.027)));hr=max(1.,self.rng.gauss(22,10));rbi=max(20.,self.rng.gauss(78,20));sb=max(0.,self.rng.gauss(14,11));ops=max(.600,min(1.080,self.rng.gauss(.790,.085)));defense=self.rng.gauss(100,13);rivals.append({'AVG':avg,'HR':hr,'RBI':rbi,'SB':sb,'DEF':defense,'MVP':ops*100+hr*.55+rbi*.10+sb*.05})
        a=[]
        if line.AVG>max(r['AVG'] for r in rivals):a.append('타격왕')
        if line.HR>max(r['HR'] for r in rivals):a.append('홈런왕')
        if line.RBI>max(r['RBI'] for r in rivals):a.append('타점왕')
        if line.SB>max(r['SB'] for r in rivals):a.append('도루왕')
        defense_score=self.player.stats.defense+(8 if has_trait(self.player.traits,'defense_sense') else 0)+self.rng.gauss(0,7)
        if line.G>=80 and defense_score>max(r['DEF'] for r in rivals):a.append('골든글러브')
        mvp=line.OPS*100+line.HR*.55+line.RBI*.10+line.SB*.05
        if mvp>max(r['MVP'] for r in rivals):a.append('MVP')
        return a
    def _maybe_change_trait(self)->None:
        if self.player.traits and self.rng.random()<.018:
            removed=self.rng.choice(self.player.traits);self.player.traits.remove(removed);self.player.trait_history.append({'year':self.year,'action':'lost','trait':removed.key})
        if len(self.player.traits)>=7 or self.rng.random()>=.045:return
        c=[t for t in TRAIT_CATALOG if t not in self.player.traits and not any(traits_conflict(t,e) for e in self.player.traits)]
        if c:
            gained=self.rng.choice(c);self.player.traits.append(gained);self.player.trait_history.append({'year':self.year,'action':'gained','trait':gained.key})
    def _process_events(self,record:SeasonRecord,event_decider:EventDecider|None)->GrowthModifiers:
        combined=GrowthModifiers();self.last_event_resolutions=[]
        for event in choose_season_events(self.player,record,self.rng):
            choice=event_decider(event,self.player) if event_decider else auto_choose(event,self.player,self.rng);resolution=resolve_event(event,choice,self.player,self.rng,self.year);combined.merge(resolution.growth_modifiers);self.last_event_resolutions.append(resolution)
        return combined
    def _maybe_replace_coaches(self)->None:
        self._ensure_coaches()
        for team,staff in list(self.team_coaches.items()):
            batting=staff.batting_coach;fielding=staff.fielding_coach;changes=[]
            if self.rng.random()<config.COACH_REPLACEMENT_CHANCE:batting=generate_batting_coach(self.rng);changes.append(f'batting:{batting.archetype}')
            if self.rng.random()<config.COACH_REPLACEMENT_CHANCE:fielding=generate_fielding_coach(self.rng);changes.append(f'fielding:{fielding.archetype}')
            if changes:
                self.team_coaches[team]=CoachingStaff(batting,fielding);entry={'year':self.year,'team':team,'changes':changes};self.coach_history.append(entry)
                if team==self.player.team:self.player.event_history.append({'year':self.year,'age':self.player.age,'event_id':'coach_change','event_name':'코칭스태프 교체','chosen_option':'none','result':','.join(changes),'stat_changes':{},'trait_changes':[],'injury_changes':'none'})
    def finish_pro_season(self,event_decider:EventDecider|None=None)->tuple[SeasonRecord,GrowthResult]:
        s=self.start_pro_season()
        if not s.finished:self.advance_pro_games(config.KBO_FIRST_TEAM_GAMES-s.games_completed)
        awards=self._determine_awards(s.record);s.record.awards.extend(awards)
        for award in awards:self.player.awards.append({'year':self.year,'award':award,'level':'KBO'})
        self.player.seasons.append(s.record);mods=self._process_events(s.record,event_decider);exp=GrowthExperience(s.record.first_team.PA,s.record.farm.PA);growth=apply_season_growth(self.player,self.rng,self.current_coaching_staff(),exp,mods);self._maybe_change_trait();self._maybe_replace_coaches();self.year+=1;self.current_session=None;self.player.form='normal';self.player.form_games_remaining=0;self.player.fatigue=max(0.,self.player.fatigue*.25);return s.record,growth
    def should_retire(self)->bool:
        if self.player.age>=config.RETIREMENT_HARD_AGE:return True
        recent=self.player.seasons[-2:];pa=sum(s.first_team.PA for s in recent);ability=self.player.stats.current_ability();chance=0.
        if self.player.age>=35:chance+=.05+(self.player.age-35)*.055
        if self.player.age>=30 and pa<80:chance+=.08
        if ability<72:chance+=.08
        if self.player.injury and self.player.injury.severity=='중상':chance+=.07
        if self.player.age<27:chance*=.05
        return self.rng.random()<min(.92,chance)
    def retire(self)->None:self.phase='RETIRED';self.player.roster_level='RETIRED';self.player.retirement_age=self.player.age
    def run_to_retirement(self,max_seasons:int=30)->Player:
        if self.phase=='HIGH_SCHOOL':self.evaluate_draft()
        seasons=0
        while self.phase=='PRO' and seasons<max_seasons:
            self.finish_pro_season();seasons+=1
            if self.should_retire():self.retire()
        if self.phase=='PRO':self.retire()
        return self.player
    def as_dict(self)->dict[str,object]:
        return {'year':self.year,'tournament_index':self.tournament_index,'phase':self.phase,'tournament_results':self.tournament_results,'current_session':self.current_session.as_dict() if self.current_session else None,'team_coaches':{k:v.as_dict() for k,v in self.team_coaches.items()},'coach_history':self.coach_history}
    def restore_state(self,data:dict[str,Any])->None:
        self.year=int(data.get('year',self.year));self.tournament_index=int(data.get('tournament_index',0));self.phase=str(data.get('phase','HIGH_SCHOOL'));self.tournament_results=[dict(v) for v in data.get('tournament_results',[])];self.current_session=ProSeasonSession.from_dict(dict(data['current_session'])) if data.get('current_session') else None;self.team_coaches={str(k):CoachingStaff.from_dict(dict(v)) for k,v in dict(data.get('team_coaches',{})).items()};self.coach_history=[dict(v) for v in data.get('coach_history',[])]
