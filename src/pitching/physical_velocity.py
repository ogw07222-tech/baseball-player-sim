"""Production physical fastball-velocity contract and safety layer.

Velocity v2 mapping is frozen from VELOCITY_SCALE_V2_READY. Raw Velocity remains
career state; all caps apply only to physical km/h outputs.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

RAW_REFERENCE=97.0
LEAGUE_REFERENCE_KMH=146.0
KMH_SLOPE=0.29
MAPPING_COMPRESSION_SCALE=500.0
GAMEPLAY_POINTS_PER_KMH=1.50
BASE_SOFT_START=160.0
BASE_SOFT_SCALE=4.0
BASE_HARD_CAP=164.0
EFFECTIVE_SOFT_START=164.0
EFFECTIVE_SOFT_SCALE=3.0
EFFECTIVE_HARD_CAP=167.0
MAX_PITCH_HARD_CAP=170.0


def raw_to_uncapped_avg_kmh(raw_velocity:float)->float:
    d=float(raw_velocity)-RAW_REFERENCE
    return LEAGUE_REFERENCE_KMH + KMH_SLOPE*d/(1.0+abs(d)/MAPPING_COMPRESSION_SCALE)


def _soft_upper(value:float,start:float,scale:float,hard:float)->float:
    if value<=start:return value
    excess=value-start
    compressed=start + excess/(1.0+excess/scale)
    return min(hard,compressed)


def base_avg_kmh(raw_velocity:float)->float:
    return _soft_upper(raw_to_uncapped_avg_kmh(raw_velocity),BASE_SOFT_START,BASE_SOFT_SCALE,BASE_HARD_CAP)


def effective_avg_kmh(raw_velocity:float,effort_bonus_kmh:float=0.0,fatigue_loss_kmh:float=0.0)->float:
    base=base_avg_kmh(raw_velocity)
    candidate=base+float(effort_bonus_kmh)-max(0.0,float(fatigue_loss_kmh))
    return _soft_upper(candidate,EFFECTIVE_SOFT_START,EFFECTIVE_SOFT_SCALE,EFFECTIVE_HARD_CAP)


def gameplay_velocity(effective_kmh:float)->float:
    return 100.0+(float(effective_kmh)-LEAGUE_REFERENCE_KMH)*GAMEPLAY_POINTS_PER_KMH


def max_pitch_kmh(effective_avg:float,max_minus_avg:float)->float:
    return min(MAX_PITCH_HARD_CAP,float(effective_avg)+max(0.0,float(max_minus_avg)))

@dataclass(frozen=True)
class PhysicalVelocitySnapshot:
    raw_velocity:float
    base_avg_kmh:float
    effective_avg_kmh:float
    gameplay_velocity:float


def snapshot(raw_velocity:float,effort_bonus_kmh:float=0.0,fatigue_loss_kmh:float=0.0)->PhysicalVelocitySnapshot:
    base=base_avg_kmh(raw_velocity)
    eff=effective_avg_kmh(raw_velocity,effort_bonus_kmh,fatigue_loss_kmh)
    return PhysicalVelocitySnapshot(float(raw_velocity),base,eff,gameplay_velocity(eff))


def finite_monotonic_raw(xs:tuple[float,...])->bool:
    ys=[base_avg_kmh(x) for x in xs]
    return all(math.isfinite(y) for y in ys) and all(a<b for a,b in zip(ys,ys[1:]))
