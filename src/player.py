"""Player aggregate for the career simulator."""
from __future__ import annotations
from dataclasses import dataclass, field
from . import config
from .catcher import CATCHER_POSITION, generate_catcher_foundation
from .records import BattingLine, SeasonRecord
from .rng import RNG
from .stats import PlayerStats, generate_random_stats
from .traits import Trait, generate_random_traits, trait_from_key
@dataclass
class InjuryStatus:
    name:str;severity:str;games_remaining:int
    def as_dict(self)->dict[str,object]:return {'name':self.name,'severity':self.severity,'games_remaining':self.games_remaining}
    @classmethod
    def from_dict(cls,d:dict[str,object])->'InjuryStatus':return cls(str(d['name']),str(d['severity']),int(d['games_remaining']))
@dataclass
class Player:
    name:str;age:int;stats:PlayerStats;traits:list[Trait]=field(default_factory=list);nationality:str='KOR';position:str='SS';bats_throws:str='R/R';team:str|None=None;roster_level:str='HIGH_SCHOOL';fatigue:float=0.;injury:InjuryStatus|None=None;form:str='normal';form_games_remaining:int=0;seasons:list[SeasonRecord]=field(default_factory=list);high_school_stats:BattingLine=field(default_factory=BattingLine);growth_history:list[dict[str,object]]=field(default_factory=list);injury_history:list[dict[str,object]]=field(default_factory=list);trait_history:list[dict[str,object]]=field(default_factory=list);team_history:list[dict[str,object]]=field(default_factory=list);awards:list[dict[str,object]]=field(default_factory=list);event_history:list[dict[str,object]]=field(default_factory=list);career_history:list[dict[str,object]]=field(default_factory=list);draft_info:dict[str,object]|None=None;debut_year:int|None=None;retirement_age:int|None=None;initial_talent:int|None=None;development_profile:str='normal';season_modifiers:dict[str,int]=field(default_factory=dict);breakthrough_affinity:float=1.0;catcher_archetype:str|None=None
    def __post_init__(self)->None:
        if self.position not in config.POSITIONS:raise ValueError(f'unsupported position: {self.position}')
        if self.development_profile not in dict(config.DEVELOPMENT_PROFILE_WEIGHTS):raise ValueError(f'unknown development profile: {self.development_profile}')
        if self.initial_talent is None:self.initial_talent=self.stats.talent
    def advance_age(self,years:int=1)->None:
        if years<0:raise ValueError('years must be non-negative')
        self.age+=years
    @classmethod
    def random(cls,name:str,rng:RNG,position:str='SS',bats_throws:str='R/R',trait_count:int|None=None)->'Player':
        if bats_throws not in config.BATS_THROWS:raise ValueError(f'unsupported bats/throws: {bats_throws}')
        profile=rng.weighted_choice(config.DEVELOPMENT_PROFILE_WEIGHTS)
        player=cls(name=name,age=config.START_AGE,stats=generate_random_stats(rng,position),traits=generate_random_traits(rng,trait_count),position=position,bats_throws=bats_throws,development_profile=profile)
        if position==CATCHER_POSITION:
            foundation=generate_catcher_foundation(player.stats,rng);player.catcher_archetype=foundation.archetype
        player.breakthrough_affinity=float(rng.weighted_choice(config.BREAKTHROUGH_AFFINITY_WEIGHTS));return player
    def effective_stat(self,stat_name:str)->int:
        return max(config.STAT_MIN,getattr(self.stats,stat_name)+int(self.season_modifiers.get(stat_name,0)))
    def add_season_modifier(self,stat_name:str,delta:int)->int:
        self.season_modifiers[stat_name]=self.season_modifiers.get(stat_name,0)+int(delta);return self.season_modifiers[stat_name]
    def clear_season_modifiers(self)->None:self.season_modifiers.clear()
    def first_team_career(self)->BattingLine:
        total=BattingLine()
        for s in self.seasons:total.add(s.first_team)
        return total
    def farm_career(self)->BattingLine:
        total=BattingLine()
        for s in self.seasons:total.add(s.farm)
        return total
    def best_season(self)->SeasonRecord|None:
        q=[s for s in self.seasons if s.first_team.PA>0];return max(q,key=lambda s:(s.first_team.OPS,s.first_team.PA),default=None)
    def as_dict(self)->dict[str,object]:
        return {'name':self.name,'age':self.age,'nationality':self.nationality,'position':self.position,'bats_throws':self.bats_throws,'stats':self.stats.as_dict(),'traits':[t.key for t in self.traits],'team':self.team,'roster_level':self.roster_level,'fatigue':self.fatigue,'injury':self.injury.as_dict() if self.injury else None,'form':self.form,'form_games_remaining':self.form_games_remaining,'seasons':[s.as_dict() for s in self.seasons],'high_school_stats':self.high_school_stats.as_dict(),'growth_history':self.growth_history,'injury_history':self.injury_history,'trait_history':self.trait_history,'team_history':self.team_history,'awards':self.awards,'event_history':self.event_history,'career_history':self.career_history,'draft_info':self.draft_info,'debut_year':self.debut_year,'retirement_age':self.retirement_age,'initial_talent':self.initial_talent,'development_profile':self.development_profile,'season_modifiers':dict(self.season_modifiers),'breakthrough_affinity':self.breakthrough_affinity,'catcher_archetype':self.catcher_archetype}
    @classmethod
    def from_dict(cls,d:dict[str,object])->'Player':
        return cls(name=str(d['name']),age=int(d['age']),stats=PlayerStats.from_dict(dict(d['stats'])),traits=[trait_from_key(str(k)) for k in d.get('traits',[])],nationality=str(d.get('nationality','KOR')),position=str(d.get('position','SS')),bats_throws=str(d.get('bats_throws','R/R')),team=d.get('team') and str(d['team']),roster_level=str(d.get('roster_level','HIGH_SCHOOL')),fatigue=float(d.get('fatigue',0.0)),injury=InjuryStatus.from_dict(dict(d['injury'])) if d.get('injury') else None,form=str(d.get('form','normal')),form_games_remaining=int(d.get('form_games_remaining',0)),seasons=[SeasonRecord.from_dict(dict(v)) for v in d.get('seasons',[])],high_school_stats=BattingLine.from_dict(dict(d.get('high_school_stats',{}))),growth_history=[dict(v) for v in d.get('growth_history',[])],injury_history=[dict(v) for v in d.get('injury_history',[])],trait_history=[dict(v) for v in d.get('trait_history',[])],team_history=[dict(v) for v in d.get('team_history',[])],awards=[dict(v) for v in d.get('awards',[])],event_history=[dict(v) for v in d.get('event_history',[])],career_history=[dict(v) for v in d.get('career_history',[])],draft_info=dict(d['draft_info']) if d.get('draft_info') else None,debut_year=int(d['debut_year']) if d.get('debut_year') is not None else None,retirement_age=int(d['retirement_age']) if d.get('retirement_age') is not None else None,initial_talent=int(d.get('initial_talent',dict(d['stats'])['talent'])),development_profile=str(d.get('development_profile','normal')),season_modifiers={str(k):int(v) for k,v in dict(d.get('season_modifiers',{})).items()},breakthrough_affinity=float(d.get('breakthrough_affinity',1.0)),catcher_archetype=str(d['catcher_archetype']) if d.get('catcher_archetype') else None)
