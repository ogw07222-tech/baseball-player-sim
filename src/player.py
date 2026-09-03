"""Player aggregate for the career simulator."""
from __future__ import annotations
from dataclasses import dataclass, field
from . import config
from .records import BattingLine, SeasonRecord
from .rng import RNG
from .stats import PlayerStats, generate_random_stats
from .traits import Trait, generate_random_traits, trait_from_key

@dataclass
class InjuryStatus:
    name:str; severity:str; games_remaining:int
    def as_dict(self)->dict[str,object]:return {'name':self.name,'severity':self.severity,'games_remaining':self.games_remaining}
    @classmethod
    def from_dict(cls,data:dict[str,object])->'InjuryStatus':return cls(str(data['name']),str(data['severity']),int(data['games_remaining']))

@dataclass
class Player:
    name:str; age:int; stats:PlayerStats; traits:list[Trait]=field(default_factory=list); nationality:str='KOR'; position:str='SS'; bats_throws:str='R/R'; team:str|None=None; roster_level:str='HIGH_SCHOOL'; fatigue:float=0.; injury:InjuryStatus|None=None; form:str='normal'; form_games_remaining:int=0; seasons:list[SeasonRecord]=field(default_factory=list); high_school_stats:BattingLine=field(default_factory=BattingLine); growth_history:list[dict[str,object]]=field(default_factory=list); injury_history:list[dict[str,object]]=field(default_factory=list); trait_history:list[dict[str,object]]=field(default_factory=list); team_history:list[dict[str,object]]=field(default_factory=list); awards:list[dict[str,object]]=field(default_factory=list); event_history:list[dict[str,object]]=field(default_factory=list); draft_info:dict[str,object]|None=None; debut_year:int|None=None; retirement_age:int|None=None; initial_talent:int|None=None; development_profile:str='normal'
    def __post_init__(self)->None:
        if self.position not in config.POSITIONS: raise ValueError(f'unsupported position: {self.position}')
        if self.development_profile not in dict(config.DEVELOPMENT_PROFILE_WEIGHTS): raise ValueError(f'unknown development profile: {self.development_profile}')
        if self.initial_talent is None:self.initial_talent=self.stats.talent
    def advance_age(self,years:int=1)->None:
        if years<0:raise ValueError('years must be non-negative')
        self.age+=years
    @classmethod
    def random(cls,name:str,rng:RNG,position:str='SS',bats_throws:str='R/R',trait_count:int|None=None)->'Player':
        if bats_throws not in config.BATS_THROWS:raise ValueError(f'unsupported bats/throws: {bats_throws}')
        profile=rng.weighted_choice(config.DEVELOPMENT_PROFILE_WEIGHTS)
        return cls(name=name,age=config.START_AGE,stats=generate_random_stats(rng,position),traits=generate_random_traits(rng,trait_count),position=position,bats_throws=bats_throws,development_profile=profile)
    def first_team_career(self)->BattingLine:
        total=BattingLine()
        for s in self.seasons:total.add(s.first_team)
        return total
    def farm_career(self)->BattingLine:
        total=BattingLine()
        for s in self.seasons:total.add(s.farm)
        return total
    def best_season(self)->SeasonRecord|None:
        q=[s for s in self.seasons if s.first_team.PA>0]; return max(q,key=lambda s:(s.first_team.OPS,s.first_team.PA),default=None)
    def as_dict(self)->dict[str,object]:
        return {'name':self.name,'age':self.age,'nationality':self.nationality,'position':self.position,'bats_throws':self.bats_throws,'stats':self.stats.as_dict(),'traits':[t.key for t in self.traits],'team':self.team,'roster_level':self.roster_level,'fatigue':self.fatigue,'injury':self.injury.as_dict() if self.injury else None,'form':self.form,'form_games_remaining':self.form_games_remaining,'seasons':[s.as_dict() for s in self.seasons],'high_school_stats':self.high_school_stats.as_dict(),'growth_history':self.growth_history,'injury_history':self.injury_history,'trait_history':self.trait_history,'team_history':self.team_history,'awards':self.awards,'event_history':self.event_history,'draft_info':self.draft_info,'debut_year':self.debut_year,'retirement_age':self.retirement_age,'initial_talent':self.initial_talent,'development_profile':self.development_profile}
    @classmethod
    def from_dict(cls,data:dict[str,object])->'Player':
        return cls(name=str(data['name']),age=int(data['age']),stats=PlayerStats.from_dict(dict(data['stats'])),traits=[trait_from_key(str(k)) for k in data.get('traits',[])],nationality=str(data.get('nationality','KOR')),position=str(data.get('position','SS')),bats_throws=str(data.get('bats_throws','R/R')),team=data.get('team') and str(data['team']),roster_level=str(data.get('roster_level','HIGH_SCHOOL')),fatigue=float(data.get('fatigue',0.0)),injury=InjuryStatus.from_dict(dict(data['injury'])) if data.get('injury') else None,form=str(data.get('form','normal')),form_games_remaining=int(data.get('form_games_remaining',0)),seasons=[SeasonRecord.from_dict(dict(v)) for v in data.get('seasons',[])],high_school_stats=BattingLine.from_dict(dict(data.get('high_school_stats',{}))),growth_history=[dict(v) for v in data.get('growth_history',[])],injury_history=[dict(v) for v in data.get('injury_history',[])],trait_history=[dict(v) for v in data.get('trait_history',[])],team_history=[dict(v) for v in data.get('team_history',[])],awards=[dict(v) for v in data.get('awards',[])],event_history=[dict(v) for v in data.get('event_history',[])],draft_info=dict(data['draft_info']) if data.get('draft_info') else None,debut_year=int(data['debut_year']) if data.get('debut_year') is not None else None,retirement_age=int(data['retirement_age']) if data.get('retirement_age') is not None else None,initial_talent=int(data.get('initial_talent',dict(data['stats'])['talent'])),development_profile=str(data.get('development_profile','normal')))
