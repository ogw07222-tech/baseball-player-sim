"""Team coaching environments that shape growth distributions rather than grant stats."""
from __future__ import annotations
from dataclasses import dataclass
from . import config
from .rng import RNG

@dataclass(frozen=True)
class BattingCoach:
    archetype: str
    contact_development: int
    power_development: int
    discipline_development: int
    stability: int
    experimentation: int
    def as_dict(self)->dict[str,object]: return self.__dict__.copy()
    @classmethod
    def from_dict(cls,data:dict[str,object])->'BattingCoach': return cls(str(data['archetype']),int(data['contact_development']),int(data['power_development']),int(data['discipline_development']),int(data['stability']),int(data['experimentation']))

@dataclass(frozen=True)
class FieldingCoach:
    archetype: str
    defense_development: int
    throwing_development: int
    speed_development: int
    stability: int
    experimentation: int
    def as_dict(self)->dict[str,object]: return self.__dict__.copy()
    @classmethod
    def from_dict(cls,data:dict[str,object])->'FieldingCoach': return cls(str(data['archetype']),int(data['defense_development']),int(data['throwing_development']),int(data['speed_development']),int(data['stability']),int(data['experimentation']))

@dataclass(frozen=True)
class CoachingStaff:
    batting_coach: BattingCoach
    fielding_coach: FieldingCoach
    def as_dict(self)->dict[str,object]: return {'batting_coach':self.batting_coach.as_dict(),'fielding_coach':self.fielding_coach.as_dict()}
    @classmethod
    def from_dict(cls,data:dict[str,object])->'CoachingStaff': return cls(BattingCoach.from_dict(dict(data['batting_coach'])),FieldingCoach.from_dict(dict(data['fielding_coach'])))

def _jitter(rng:RNG,value:int)->int: return int(round(value+rng.gauss(0,3.0)))
def generate_batting_coach(rng:RNG,archetype:str|None=None)->BattingCoach:
    kind=archetype or rng.choice(tuple(config.COACH_ARCHETYPES)); base=config.COACH_ARCHETYPES[kind]
    return BattingCoach(kind,_jitter(rng,base['contact_development']),_jitter(rng,base['power_development']),_jitter(rng,base['discipline_development']),_jitter(rng,base['stability']),_jitter(rng,base['experimentation']))
def generate_fielding_coach(rng:RNG,archetype:str|None=None)->FieldingCoach:
    kind=archetype or rng.choice(tuple(config.FIELDING_COACH_ARCHETYPES)); base=config.FIELDING_COACH_ARCHETYPES[kind]
    return FieldingCoach(kind,_jitter(rng,base['defense_development']),_jitter(rng,base['throwing_development']),_jitter(rng,base['speed_development']),_jitter(rng,base['stability']),_jitter(rng,base['experimentation']))
def generate_staff(rng:RNG)->CoachingStaff:return CoachingStaff(generate_batting_coach(rng),generate_fielding_coach(rng))
def generate_league_staffs(rng:RNG)->dict[str,CoachingStaff]: return {str(t['name']):generate_staff(rng) for t in config.KBO_TEAMS}
def coach_growth_mean(staff:CoachingStaff,stat_name:str)->float:
    attr=f'{stat_name}_development'
    raw=getattr(staff.batting_coach,attr,0)+getattr(staff.fielding_coach,attr,0)
    return raw/config.COACH_MEAN_DIVISOR
def coach_variance_multiplier(staff:CoachingStaff)->float:
    stability=(staff.batting_coach.stability+staff.fielding_coach.stability)/2
    experimentation=(staff.batting_coach.experimentation+staff.fielding_coach.experimentation)/2
    return max(.55,min(1.65,1.0-stability*config.COACH_STABILITY_VARIANCE_SCALE+experimentation*config.COACH_EXPERIMENT_VARIANCE_SCALE))
