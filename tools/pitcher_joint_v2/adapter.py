from __future__ import annotations
from dataclasses import dataclass
from src.hitting.model import HitterSnapshot,HittingEngine,Pitch,PitcherSnapshot
from src.pitching.physical_velocity import snapshot as velocity_snapshot

@dataclass(frozen=True)
class JointWeights:
    w_control_zone:float=1.0
    w_stuff_quality:float=.20
    w_stuff_contact:float=.05
    w_breaking_contact:float=.15
    w_breaking_quality:float=.12
    def as_dict(self): return self.__dict__.copy()

class PitcherJointAdapter:
    """Velocity is frozen physical input; only Stuff/Control/Breaking weights vary."""
    def __init__(self,stats,weights:JointWeights,effort_bonus_kmh:float=0.0,fatigue_loss_kmh:float=0.0):
        self.stats=stats; self.weights=weights
        self.velocity=velocity_snapshot(stats.velocity,effort_bonus_kmh,fatigue_loss_kmh)
    def pitcher_snapshot(self):
        # Keep legacy H3 stuff/movement channels neutral; Control owns zone/location.
        return PitcherSnapshot(stuff=100.0,control=100.0+self.weights.w_control_zone*(self.stats.control-100.0),movement=100.0)
    def modifier(self,_pitch:Pitch,_strikes:int):
        # v2 physical Velocity is fixed at 1.50 gameplay points/km/h.
        velocity_contact=100.0-self.velocity.gameplay_velocity
        contact_delta=(velocity_contact
                       -self.weights.w_breaking_contact*(self.stats.breaking-100.0)
                       -self.weights.w_stuff_contact*(self.stats.stuff-100.0))
        quality_delta=-(self.weights.w_stuff_quality*(self.stats.stuff-100.0)
                        +self.weights.w_breaking_quality*(self.stats.breaking-100.0))
        return contact_delta,quality_delta
    def make_engine(self,hitter:HitterSnapshot,defense:float,rng):
        return HittingEngine(hitter,self.pitcher_snapshot(),defense,rng,pitch_stat_modifier=self.modifier)
