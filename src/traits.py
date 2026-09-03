"""Trait definitions, conflicts, and random assignment."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from . import config
from .rng import RNG
class TraitPolarity(str,Enum): POSITIVE='positive'; NEGATIVE='negative'
@dataclass(frozen=True)
class Trait:
    key:str; name:str; polarity:TraitPolarity; tags:frozenset[str]
    def as_dict(self)->dict[str,object]: return {'key':self.key,'name':self.name,'polarity':self.polarity.value,'tags':sorted(self.tags)}
TRAIT_CATALOG=(
Trait('fastball_specialist','직구 특화',TraitPolarity.POSITIVE,frozenset({'batting','pitch_type'})),Trait('fastball_weakness','직구 취약',TraitPolarity.NEGATIVE,frozenset({'batting','pitch_type'})),Trait('breaking_ball_response','변화구 대응',TraitPolarity.POSITIVE,frozenset({'batting','pitch_type'})),Trait('breaking_ball_weakness','변화구 취약',TraitPolarity.NEGATIVE,frozenset({'batting','pitch_type'})),Trait('high_velocity_strength','고속구 강점',TraitPolarity.POSITIVE,frozenset({'batting','velocity'})),Trait('high_velocity_weakness','고속구 취약',TraitPolarity.NEGATIVE,frozenset({'batting','velocity'})),Trait('low_pitch_strength','낮은 공 강점',TraitPolarity.POSITIVE,frozenset({'batting','zone'})),Trait('low_pitch_weakness','낮은 공 취약',TraitPolarity.NEGATIVE,frozenset({'batting','zone'})),Trait('inside_pitch_strength','몸쪽 공 강점',TraitPolarity.POSITIVE,frozenset({'batting','zone'})),Trait('inside_pitch_weakness','몸쪽 공 취약',TraitPolarity.NEGATIVE,frozenset({'batting','zone'})),Trait('vs_lhp_strength','좌완 강점',TraitPolarity.POSITIVE,frozenset({'batting','platoon'})),Trait('vs_lhp_weakness','좌완 취약',TraitPolarity.NEGATIVE,frozenset({'batting','platoon'})),Trait('vs_rhp_strength','우완 강점',TraitPolarity.POSITIVE,frozenset({'batting','platoon'})),Trait('vs_rhp_weakness','우완 취약',TraitPolarity.NEGATIVE,frozenset({'batting','platoon'})),Trait('two_strike_strength','2스트라이크 강점',TraitPolarity.POSITIVE,frozenset({'batting','count'})),Trait('clutch','클러치',TraitPolarity.POSITIVE,frozenset({'batting','pressure'})),Trait('pressure_weakness','압박 상황 취약',TraitPolarity.NEGATIVE,frozenset({'batting','pressure'})),Trait('steal_sense','도루 센스',TraitPolarity.POSITIVE,frozenset({'baserunning'})),Trait('defense_sense','수비 센스',TraitPolarity.POSITIVE,frozenset({'defense'})),Trait('fast_growth','빠른 성장',TraitPolarity.POSITIVE,frozenset({'growth'})),Trait('slow_growth','느린 성장',TraitPolarity.NEGATIVE,frozenset({'growth'})),Trait('volatile','기복이 심함',TraitPolarity.NEGATIVE,frozenset({'form'})),Trait('consistent','꾸준함',TraitPolarity.POSITIVE,frozenset({'form'})),Trait('injury_risk','부상 위험',TraitPolarity.NEGATIVE,frozenset({'injury'})),Trait('quick_recovery','회복이 빠름',TraitPolarity.POSITIVE,frozenset({'injury'})),)
TRAIT_BY_KEY={t.key:t for t in TRAIT_CATALOG}
CONFLICTS={frozenset(p) for p in (('fastball_specialist','fastball_weakness'),('breaking_ball_response','breaking_ball_weakness'),('high_velocity_strength','high_velocity_weakness'),('low_pitch_strength','low_pitch_weakness'),('inside_pitch_strength','inside_pitch_weakness'),('vs_lhp_strength','vs_lhp_weakness'),('vs_rhp_strength','vs_rhp_weakness'),('fast_growth','slow_growth'),('volatile','consistent'))}
def traits_conflict(a:Trait,b:Trait)->bool:return frozenset((a.key,b.key)) in CONFLICTS
def _weighted_trait(rng:RNG,candidates:list[Trait])->Trait:
    pos=[t for t in candidates if t.polarity==TraitPolarity.POSITIVE]; neg=[t for t in candidates if t.polarity==TraitPolarity.NEGATIVE]; pool=(pos if rng.random()<config.TRAIT_POSITIVE_SHARE else neg) or candidates
    return rng.weighted_choice([(t,config.TRAIT_WEIGHTS.get(t.key,config.TRAIT_DEFAULT_WEIGHT)) for t in pool])
def generate_random_traits(rng:RNG,count:int|None=None)->list[Trait]:
    if count is None: count=rng.randint(0,3)
    if count not in (0,1,2,3): raise ValueError('trait count must be 0..3')
    candidates=list(TRAIT_CATALOG); selected=[]
    while candidates and len(selected)<count:
        t=_weighted_trait(rng,candidates); candidates.remove(t)
        if any(traits_conflict(t,e) for e in selected):continue
        selected.append(t); candidates=[c for c in candidates if not traits_conflict(c,t)]
    if len(selected)!=count: raise RuntimeError('trait catalog cannot satisfy requested count')
    return selected
def has_trait(traits:list[Trait],key:str)->bool:return any(t.key==key for t in traits)
def trait_from_key(key:str)->Trait:
    try:return TRAIT_BY_KEY[key]
    except KeyError as exc:raise ValueError(f'unknown trait key: {key}') from exc
