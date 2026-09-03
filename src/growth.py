"""Growth engine: weak natural growth plus talent, profile, coach, experience, events and luck."""
from __future__ import annotations
from dataclasses import dataclass, field
from . import config
from .coaches import CoachingStaff, coach_growth_mean, coach_variance_multiplier
from .player import Player
from .rng import RNG
from .traits import has_trait
GROWABLE_STATS=config.HITTER_STAT_NAMES

@dataclass(frozen=True)
class GrowthExperience:
    first_team_pa:int=0
    farm_pa:int=0

@dataclass
class GrowthModifiers:
    mean_by_stat:dict[str,float]=field(default_factory=dict)
    variance_multiplier:float=1.0
    explosion_multiplier:float=1.0
    def add_mean(self,stat_name:str,value:float)->None:self.mean_by_stat[stat_name]=self.mean_by_stat.get(stat_name,0.0)+value
    def merge(self,other:'GrowthModifiers')->None:
        for n,v in other.mean_by_stat.items():self.add_mean(n,v)
        self.variance_multiplier*=other.variance_multiplier; self.explosion_multiplier*=other.explosion_multiplier

@dataclass(frozen=True)
class GrowthResult:
    age_before:int; age_after:int; deltas:dict[str,int]; explosion:bool; ability_before:float=0.; ability_after:float=0.

def _age_bias(age:int)->float:
    for (low,high),bias in config.AGE_GROWTH_BIAS.items():
        if low<=age<=high:return bias
    return 0.0

def _profile_bias(player:Player)->float:
    for low,high,bias in config.DEVELOPMENT_PROFILE_AGE_BIAS[player.development_profile]:
        if low<=player.age<=high:return float(bias)
    return 0.0

def _trait_growth_bias(player:Player)->float:
    if has_trait(player.traits,'fast_growth'):return .45
    if has_trait(player.traits,'slow_growth'):return -.45
    return 0.0

def _experience_bias(player:Player,stat_name:str,experience:GrowthExperience|None)->float:
    if experience is None:return 0.0
    first=min(1.25,experience.first_team_pa/config.EXPERIENCE_FIRST_PA_REFERENCE)
    farm=min(1.25,experience.farm_pa/config.EXPERIENCE_FARM_PA_REFERENCE)
    if experience.first_team_pa+experience.farm_pa<60:return config.EXPERIENCE_LOW_PLAY_PENALTY
    batting=stat_name in {'contact','power','discipline'}
    field=stat_name in {'speed','defense','throwing','stamina'}
    young_farm=farm*(1.0 if player.age<=23 else .45)
    raw=(first*.30+young_farm*.22) if batting else (first*.18+young_farm*.16 if field else first*.08+young_farm*.08)
    return min(config.EXPERIENCE_MAX_MEAN_BONUS,raw)

def growth_distribution(player:Player,stat_name:str,coach:CoachingStaff|None=None,experience:GrowthExperience|None=None,modifiers:GrowthModifiers|None=None)->tuple[float,float]:
    current=getattr(player.stats,stat_name)
    talent_effect=(player.stats.talent-config.GROWTH_TALENT_REFERENCE)*config.GROWTH_TALENT_SCALE
    damping=max(0.0,current-100.)*config.GROWTH_CURRENT_STAT_DAMPING
    mean=_age_bias(player.age)+_profile_bias(player)+talent_effect+_trait_growth_bias(player)-damping
    mean+=_experience_bias(player,stat_name,experience)
    if coach is not None:mean+=coach_growth_mean(coach,stat_name)
    variance=config.GROWTH_BASE_STDDEV*(coach_variance_multiplier(coach) if coach else 1.0)
    if modifiers:
        mean+=modifiers.mean_by_stat.get(stat_name,0.0); variance*=modifiers.variance_multiplier
    if player.age>=32 and mean<0:mean*=config.AGING_MULTIPLIER.get(stat_name,1.0)
    return mean,max(.75,variance)

def _explosion_chance(player:Player,modifiers:GrowthModifiers|None=None)->float:
    chance=config.GROWTH_EXPLOSION_BASE_CHANCE+max(0,player.stats.talent-config.GROWTH_TALENT_REFERENCE)*config.GROWTH_EXPLOSION_TALENT_SCALE
    if has_trait(player.traits,'fast_growth'):chance*=1.25
    if has_trait(player.traits,'slow_growth'):chance*=.80
    if modifiers:chance*=modifiers.explosion_multiplier
    return max(.001,min(.12,chance))

def apply_season_growth(player:Player,rng:RNG,coach:CoachingStaff|None=None,experience:GrowthExperience|None=None,modifiers:GrowthModifiers|None=None)->GrowthResult:
    age_before=player.age; ability_before=player.stats.current_ability(); deltas={}
    for stat_name in GROWABLE_STATS:
        mean,std=growth_distribution(player,stat_name,coach,experience,modifiers)
        delta=int(round(rng.gauss(mean,std))); before=getattr(player.stats,stat_name); after=player.stats.apply_delta(stat_name,delta); deltas[stat_name]=after-before
    explosion=rng.random()<_explosion_chance(player,modifiers)
    if explosion:
        count=rng.randint(1,min(3,len(GROWABLE_STATS)))
        for stat_name in rng.sample(GROWABLE_STATS,count):
            bonus=rng.randint(config.GROWTH_EXPLOSION_MIN_BONUS,config.GROWTH_EXPLOSION_MAX_BONUS); before=getattr(player.stats,stat_name); after=player.stats.apply_delta(stat_name,bonus); deltas[stat_name]+=after-before
    player.advance_age(1); ability_after=player.stats.current_ability(); result=GrowthResult(age_before,player.age,deltas,explosion,ability_before,ability_after)
    player.growth_history.append({'age_before':age_before,'age_after':player.age,'deltas':dict(deltas),'explosion':explosion,'ability_before':round(ability_before,4),'ability_after':round(ability_after,4),'development_profile':player.development_profile})
    return result
