"""High-school, draft, KBO season, coaching, in-season events, awards and retirement."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Mapping
from . import config
from .career_source_facts import CareerSourceFact
from .coaches import CoachingStaff, generate_batting_coach, generate_fielding_coach, generate_league_staffs
from .draft_scoring import evaluate_hitter_draft
from .events import CareerEvent, EventChoice, EventContext, EventResolution, EVENT_CATALOG, EVENT_BY_ID, auto_choose, eligible, event_weight, resolve_event
from .growth import GrowthExperience, GrowthModifiers, GrowthResult, apply_season_growth
from .player import InjuryStatus, Player
from .records import BattingLine, SeasonRecord
from .rng import RNG
from .simulation import logistic_range, simulate_player_game
from .traits import TRAIT_CATALOG, Trait, has_trait, traits_conflict

@dataclass(frozen=True)
class TournamentResult:name:str;games:int;line:BattingLine;champion:bool;mvp:bool
@dataclass(frozen=True)
class DraftResult:
    team:str;round:int|None;pick:int|None;status:str;scouting_score:float;scouted_talent:int
    def as_dict(self)->dict[str,object]:return {'team':self.team,'round':self.round,'pick':self.pick,'status':self.status,'scouting_score':round(self.scouting_score,3),'scouted_talent':self.scouted_talent}

@dataclass
class ProSeasonSession:
    year:int;record:SeasonRecord;games_completed:int=0;current_level:str='FARM'
    pending_event_id:str|None=None;pending_event_game:int|None=None;pending_event_phase:str|None=None
    occurred_event_ids:list[str]=field(default_factory=list);cooldown_until:dict[str,int]=field(default_factory=dict);last_event_game:int=-999
    growth_modifiers:GrowthModifiers=field(default_factory=GrowthModifiers);preseason_checked:bool=False
    @property
    def finished(self)->bool:return self.games_completed>=config.KBO_FIRST_TEAM_GAMES
    @property
    def has_pending_event(self)->bool:return self.pending_event_id is not None
    def as_dict(self)->dict[str,object]:
        return {'year':self.year,'record':self.record.as_dict(),'games_completed':self.games_completed,'current_level':self.current_level,'pending_event_id':self.pending_event_id,'pending_event_game':self.pending_event_game,'pending_event_phase':self.pending_event_phase,'occurred_event_ids':list(self.occurred_event_ids),'cooldown_until':dict(self.cooldown_until),'last_event_game':self.last_event_game,'growth_modifiers':self.growth_modifiers.as_dict(),'preseason_checked':self.preseason_checked}
    @classmethod
    def from_dict(cls,d:dict[str,object])->'ProSeasonSession':
        return cls(int(d['year']),SeasonRecord.from_dict(dict(d['record'])),int(d.get('games_completed',0)),str(d.get('current_level','FARM')),str(d['pending_event_id']) if d.get('pending_event_id') else None,int(d['pending_event_game']) if d.get('pending_event_game') is not None else None,str(d['pending_event_phase']) if d.get('pending_event_phase') else None,[str(x) for x in d.get('occurred_event_ids',[])],{str(k):int(v) for k,v in dict(d.get('cooldown_until',{})).items()},int(d.get('last_event_game',-999)),GrowthModifiers.from_dict(dict(d.get('growth_modifiers',{}))),bool(d.get('preseason_checked',False)))

EventDecider=Callable[[CareerEvent,Player],EventChoice]

@dataclass
class CareerEngineBase:
    player:Player;rng:RNG;year:int=config.START_YEAR;tournament_index:int=0;phase:str='HIGH_SCHOOL';tournament_results:list[dict[str,object]]=field(default_factory=list);current_session:ProSeasonSession|None=None;team_coaches:dict[str,CoachingStaff]=field(default_factory=dict);coach_history:list[dict[str,object]]=field(default_factory=list);last_event_resolutions:list[EventResolution]=field(default_factory=list)
    _source_facts:list[CareerSourceFact]=field(default_factory=list,init=False,repr=False)
    _source_fact_date:date|None=field(default=None,init=False,repr=False)
    _source_fact_phase:str=field(default='system',init=False,repr=False)
    _source_fact_ordinal:int=field(default=0,init=False,repr=False)
    def begin_source_fact_capture(self,simulated_date:date|None,phase:str='post_game')->None:
        self._source_fact_date=simulated_date;self._source_fact_phase=phase;self._source_fact_ordinal=0
    def _emit_source_fact(self,fact_type:str,*,before:Mapping[str,object]|None=None,after:Mapping[str,object]|None=None,authoritative_state_delta:Mapping[str,object]|None=None,phase:str|None=None,persistence_hint:str|None=None,existing_identity:str|None=None,game_number:int|None=None)->CareerSourceFact:
        session=self.current_session
        fact=CareerSourceFact(fact_type=fact_type,season=self.year,game_number=(session.games_completed if game_number is None and session is not None else game_number),simulated_date=self._source_fact_date,phase=phase or self._source_fact_phase,local_ordinal=self._source_fact_ordinal,player_identifier=self.player.name,team_identifier=self.player.team,before=dict(before or {}),after=dict(after or {}),authoritative_state_delta=dict(authoritative_state_delta or {}),persistence_hint=persistence_hint,existing_identity=existing_identity)
        self._source_fact_ordinal+=1;self._source_facts.append(fact);return fact
    def drain_source_facts(self)->tuple[CareerSourceFact,...]:
        facts=tuple(self._source_facts);self._source_facts.clear();self._source_fact_date=None;self._source_fact_phase='system';self._source_fact_ordinal=0;return facts
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
            games+=1;opp=self.rng.uniform(*config.HIGH_SCHOOL_PITCHER_LEVEL);simulate_player_game(self.player,opp,self.rng,line,pa_count=self.rng.randint(4,5));edge=(self.player.stats.current_ability()-opp)/150.;win=max(.25,min(.75,.50+edge+self.rng.gauss(0,.035)));alive=self.rng.random()<win
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
        self.finish_high_school()
        scouted=max(0,int(round(self.rng.gauss(self.player.stats.talent,24.))))
        evaluation=evaluate_hitter_draft(self.player.high_school_stats,self.player.position,scouted,self.player.stats.durability,self.tournament_results,self.rng)
        score=evaluation.score;t=config.DRAFT_THRESHOLDS
        if score>=t['round1']:round_no=1
        elif score>=t['round2_3']:round_no=self.rng.randint(2,3)
        elif score>=t['round4_7']:round_no=self.rng.randint(4,7)
        elif score>=t['round8_11']:round_no=self.rng.randint(8,11)
        else:round_no=None
        team=str(self.rng.choice(config.KBO_TEAMS)['name']);status='지명' if round_no else '미지명 육성선수 계약';pick=(round_no-1)*10+self.rng.randint(1,10) if round_no else None;draft=DraftResult(team,round_no,pick,status,score,scouted);self.player.draft_info=draft.as_dict();self.player.team=team;self.player.roster_level='FARM';self.player.team_history.append({'year':self.year,'team':team,'event':'KBO 입단'});self.phase='PRO';self._ensure_coaches();return draft
    def _team_config(self)->dict[str,object]:
        if not self.player.team:raise RuntimeError('player has no KBO team')
        return next(dict(t) for t in config.KBO_TEAMS if t['name']==self.player.team)
    def _initial_first_team_chance(self)->bool:
        team=self._team_config();ability=self.player.stats.current_ability();competition=float(team['depth'])+config.POSITION_COMPETITION.get(self.player.position,0)-config.FIRST_TEAM_INITIAL_OFFSET;chance=logistic_range(ability-competition,.015,.65,10.5)
        if self.player.draft_info and self.player.draft_info.get('round')==1:chance+=.07
        career_pa=self.player.first_team_career().PA
        if career_pa>=config.ESTABLISHED_FIRST_TEAM_PA and ability>=config.ESTABLISHED_FIRST_TEAM_ABILITY_FLOOR:chance=max(chance,logistic_range(ability-88.,.45,.97,7.5))
        return self.rng.random()<min(.97,chance)
    def start_pro_season(self)->ProSeasonSession:
        if self.phase=='HIGH_SCHOOL':self.evaluate_draft()
        if self.phase!='PRO':raise RuntimeError('career is not in professional phase')
        if self.current_session:return self.current_session
        level='FIRST' if self._initial_first_team_chance() else 'FARM';self.player.roster_level=level;self.player.clear_season_modifiers();self.current_session=ProSeasonSession(self.year,SeasonRecord(self.year,self.player.age,self.player.team or ''),0,level);self.last_event_resolutions=[];return self.current_session
    def _update_form(self)->None:
        before={'form':self.player.form,'games_remaining':self.player.form_games_remaining}
        if self.player.form_games_remaining>0:
            self.player.form_games_remaining-=1
            if self.player.form_games_remaining<=0:self.player.form='normal'
        else:
            mf=logistic_range(100-self.player.stats.mentality,.65,1.35,35);slump=config.SLUMP_BASE_CHANCE_PER_GAME*mf;hot=config.HOT_STREAK_BASE_CHANCE_PER_GAME/max(.7,mf)
            if has_trait(self.player.traits,'volatile'):slump*=1.55;hot*=1.35
            if has_trait(self.player.traits,'consistent'):slump*=.62;hot*=.72
            roll=self.rng.random()
            if roll<slump:self.player.form='slump';self.player.form_games_remaining=self.rng.randint(config.FORM_MIN_GAMES,config.FORM_MAX_GAMES)
            elif roll<slump+hot:self.player.form='hot';self.player.form_games_remaining=self.rng.randint(config.FORM_MIN_GAMES,config.FORM_MAX_GAMES)
        after={'form':self.player.form,'games_remaining':self.player.form_games_remaining}
        if before['form']!=after['form']:
            self._emit_source_fact('form_transition',before=before,after=after,authoritative_state_delta={'form':{'before':before['form'],'after':after['form']}})
    def _injury_chance(self)->float:
        d=logistic_range(100-self.player.stats.durability,.55,1.65,32.);f=1+max(0.,self.player.fatigue-50)/65.;a=1+max(0,self.player.age-30)*.045;c=config.INJURY_BASE_CHANCE_PER_GAME*d*f*a
        if has_trait(self.player.traits,'injury_risk'):c*=1.65
        return min(.08,c)
    def _maybe_injure(self)->None:
        if self.player.injury or self.rng.random()>=self._injury_chance():return
        severity=self.rng.weighted_choice((('경미',.72),('보통',.24),('중상',.04)))
        if severity=='경미':games=self.rng.randint(2,10);name=self.rng.choice(('가벼운 근육통','손목 염좌','발목 통증'))
        elif severity=='보통':games=self.rng.randint(12,45);name=self.rng.choice(('햄스트링 부상','어깨 염좌','손가락 골절'))
        else:games=self.rng.randint(60,150);name=self.rng.choice(('무릎 인대 부상','어깨 중상','발목 골절'))
        self.player.injury=InjuryStatus(name,severity,games);self.player.injury_history.append({'year':self.year,'age':self.player.age,'name':name,'severity':severity,'games':games,'source':'game'})
        identity=f'injury_history:{self.year}:{len(self.player.injury_history)-1}'
        after=self.player.injury.as_dict()
        self._emit_source_fact('injury_created',before={'injury':None},after={'injury':after},authoritative_state_delta={'injury':{'before':None,'after':after}},persistence_hint='injury_history',existing_identity=identity)
    def _recover_day(self)->None:
        self.player.fatigue=max(0.,self.player.fatigue-config.FATIGUE_REST_RECOVERY)
        if self.player.injury:
            injury_before=self.player.injury.as_dict();recovery=2 if has_trait(self.player.traits,'quick_recovery') and self.rng.random()<.25 else 1;self.player.injury.games_remaining-=recovery
            if self.player.injury.games_remaining<=0:
                self.player.injury=None
                self._emit_source_fact('injury_recovery_completed',before={'injury':injury_before},after={'injury':None},authoritative_state_delta={'injury':{'before':injury_before,'after':None}})
    def _play_probability(self,level:str)->float:
        ability=self.player.stats.current_ability();return logistic_range(ability-config.FIRST_TEAM_PLAY_BASELINE,.36,.90,15.) if level=='FIRST' else logistic_range(ability-config.FARM_PLAY_BASELINE,.55,.94,16.)
    def _fatigue_after_game(self)->None:self.player.fatigue=min(100.,self.player.fatigue+config.FATIGUE_PER_GAME_BASE*(100./(max(1,self.player.stats.stamina)+45.)))
