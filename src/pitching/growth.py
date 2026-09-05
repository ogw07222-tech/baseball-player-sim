"""Pitcher growth adapter reusing the existing weak-growth philosophy."""
from __future__ import annotations
from dataclasses import dataclass
from .. import config
from ..rng import RNG
from . import parameters as P
from .model import Pitcher

@dataclass(frozen=True)
class PitcherGrowthResult:
    age_before:int; age_after:int; deltas:dict[str,int]; ability_before:float; ability_after:float

def _age_bias(age:int)->float:
    for (lo,hi),bias in config.AGE_GROWTH_BIAS.items():
        if lo<=age<=hi:return float(bias)
    return 0.0

def _stat_age_offset(stat:str,age:int)->float:
    if stat=="velocity": return .30 if age<=21 else 0.0 if age<=24 else -.35 if age<=27 else -.65 if age<=31 else -.50
    if stat=="stuff": return .15 if age<=22 else .20 if age<=27 else -.10 if age<=31 else 0.0
    if stat=="control": return -.20 if age<=21 else .35 if age<=27 else .20 if age<=31 else 0.0
    if stat=="breaking": return .10 if age<=22 else .35 if age<=27 else .10 if age<=31 else 0.0
    if stat=="stamina": return .15 if age<=24 else 0.0 if age<=28 else -.25 if age<=31 else 0.0
    return 0.0

def _scb_recenter_bonus(stat:str,age:int)->float:
    """Raise S/C/B representation toward a ~110 prime UI scale.

    Entry ratings are unchanged. The shift is earned during development and
    tapers before prime; Velocity is explicitly exempt because its raw scale is
    frozen to the physical km/h contract.
    """
    if stat=="stuff":
        return 1.50 if age<=25 else .80 if age<=27 else 0.0
    if stat=="control":
        return 1.95 if age<=25 else 1.25 if age<=27 else 0.0
    if stat=="breaking":
        return 1.55 if age<=25 else .85 if age<=27 else 0.0
    return 0.0

def growth_distribution(pitcher:Pitcher,stat:str)->tuple[float,float]:
    cur=getattr(pitcher.stats,stat); talent=(pitcher.stats.talent-config.GROWTH_TALENT_REFERENCE)*config.GROWTH_TALENT_SCALE; damping=max(0.0,cur-100)*config.GROWTH_CURRENT_STAT_DAMPING
    mean=_age_bias(pitcher.age)+_stat_age_offset(stat,pitcher.age)+_scb_recenter_bonus(stat,pitcher.age)+talent-damping
    if pitcher.age>=32 and mean<0: mean*=P.PITCHER_AGING_MULTIPLIER[stat]
    sd=P.VELOCITY_GROWTH_STDDEV if stat=="velocity" else max(.75,config.GROWTH_BASE_STDDEV)
    return mean,sd

def apply_pitcher_season_growth(pitcher:Pitcher,rng:RNG)->PitcherGrowthResult:
    before_age=pitcher.age; before=pitcher.stats.current_ability(); deltas={}
    for stat in P.PITCHER_STATS:
        mean,sd=growth_distribution(pitcher,stat); old=getattr(pitcher.stats,stat); new=pitcher.stats.apply_delta(stat,int(round(rng.gauss(mean,sd)))); deltas[stat]=new-old
    pitcher.age+=1; after=pitcher.stats.current_ability(); return PitcherGrowthResult(before_age,pitcher.age,deltas,before,after)
