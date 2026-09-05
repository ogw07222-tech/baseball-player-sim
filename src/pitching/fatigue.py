"""Pitcher in-game and recovery fatigue interpretation."""
from __future__ import annotations
from dataclasses import dataclass
from . import parameters as P
from .roles import role_modifiers

@dataclass(frozen=True)
class EffectivePitcherStats:
    velocity:float; stuff:float; control:float; breaking:float; fatigue_ratio:float

def effective_stats(stats,role:str,pitches:float)->EffectivePitcherStats:
    mod=role_modifiers(role); capacity=max(30.0,60.0+.45*float(stats.stamina)); ratio=pitches*mod.stamina_drain/capacity
    x=max(0.0,ratio-.55); penalty=x**1.35*10.0
    return EffectivePitcherStats(float(stats.velocity)+mod.velocity_bonus-penalty,float(stats.stuff)+mod.stuff_bonus-penalty,float(stats.control)-penalty*.38,float(stats.breaking)-penalty*.18,ratio)

def outing_pitch_cap(stamina:float,role:str)->float:
    if role=="starter": return P.STARTER_PITCH_BASE+P.STARTER_PITCH_STAMINA*stamina
    if role=="reliever": return P.RELIEVER_PITCH_BASE+P.RELIEVER_PITCH_STAMINA*stamina
    raise ValueError(f"unknown pitcher role: {role}")

def recovery_days(pitches:float,resilience:float,role:str,carried_load:float=0.0)->float:
    factor=P.RECOVERY_STARTER_FACTOR if role=="starter" else P.RECOVERY_RELIEVER_FACTOR if role=="reliever" else None
    if factor is None: raise ValueError(f"unknown pitcher role: {role}")
    load=max(0.0,carried_load)+max(0.0,pitches)*factor; daily=P.RECOVERY_BASE+P.RECOVERY_RESILIENCE*max(0.0,resilience)
    return load/max(1.0,daily)
