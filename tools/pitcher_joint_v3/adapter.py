from __future__ import annotations
from dataclasses import dataclass
from src.hitting.model import HitterSnapshot,HittingEngine,Pitch,PitcherSnapshot
from src.pitching.physical_velocity import snapshot as velocity_snapshot

STUFF_RAW_REFERENCE=109.0
CONTROL_RAW_REFERENCE=109.0
BREAKING_RAW_REFERENCE=109.0

@dataclass(frozen=True)
class JointWeights:
    w_control_zone:float=.50
    w_stuff_quality:float=.18
    w_stuff_contact:float=.03
    w_breaking_contact:float=.12
    w_breaking_quality:float=.08
    def as_dict(self): return self.__dict__.copy()

def normalize(raw:float,reference:float,points_per_raw:float)->float:
    return 100.0+(float(raw)-reference)*points_per_raw

class PitcherJointV3Adapter:
    """Separate raw career scale from H3 gameplay-neutral scale.

    Velocity uses the frozen physical km/h path. S/C/B are centered on their
    prime raw reference (~109) and only the listed semantic pathways are exposed.
    Stamina, resilience and talent have zero neutral-PA effect.
    """
    def __init__(self,stats,weights:JointWeights,physical_kmh_override:float|None=None):
        self.stats=stats;self.weights=weights
        self.velocity=velocity_snapshot(stats.velocity) if physical_kmh_override is None else None
        self.effective_kmh=float(physical_kmh_override) if physical_kmh_override is not None else self.velocity.effective_avg_kmh
    def pitcher_snapshot(self):
        control_gameplay=normalize(self.stats.control,CONTROL_RAW_REFERENCE,self.weights.w_control_zone)
        return PitcherSnapshot(stuff=100.0,control=control_gameplay,movement=100.0)
    def modifier(self,_pitch:Pitch,_strikes:int):
        velocity_contact=100.0-(100.0+(self.effective_kmh-146.0)*1.50)
        stuff_contact=-(self.stats.stuff-STUFF_RAW_REFERENCE)*self.weights.w_stuff_contact
        breaking_contact=-(self.stats.breaking-BREAKING_RAW_REFERENCE)*self.weights.w_breaking_contact
        stuff_quality=-(self.stats.stuff-STUFF_RAW_REFERENCE)*self.weights.w_stuff_quality
        breaking_quality=-(self.stats.breaking-BREAKING_RAW_REFERENCE)*self.weights.w_breaking_quality
        return velocity_contact+stuff_contact+breaking_contact,stuff_quality+breaking_quality
    def make_engine(self,hitter:HitterSnapshot,defense:float,rng):
        return HittingEngine(hitter,self.pitcher_snapshot(),defense,rng,pitch_stat_modifier=self.modifier)
