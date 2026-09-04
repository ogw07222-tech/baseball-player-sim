"""H3.2 test-side stolen-base attempt and success model."""
from __future__ import annotations
from dataclasses import dataclass
import math,random
from . import h32_parameters as P

def _clamp(x,lo,hi):return max(lo,min(hi,x))
def _sigmoid(x):
    if x>=60:return 1.0
    if x<=-60:return 0.0
    return 1.0/(1.0+math.exp(-x))
@dataclass(frozen=True)
class H3RunningDefenseProfile:
    running_defense:float=100.0
@dataclass(frozen=True)
class StealContext:
    inning:int;score_diff:int;outs:int;second_occupied:bool=False
class H32StealModel:
    def __init__(self,running_defense:H3RunningDefenseProfile|None=None):self.running_defense=running_defense or H3RunningDefenseProfile()
    @staticmethod
    def sample_context(rng):
        inning=rng.randint(1,9);x=rng.random();outs=0 if x<.34 else 1 if x<.69 else 2;score=int(round(max(-6,min(6,rng.gauss(0,2.25)))))
        return StealContext(inning,score,outs,rng.random()<P.STEAL_SECOND_BASE_OCCUPIED_RATE)
    @staticmethod
    def eligible(c):return not c.second_occupied
    @staticmethod
    def situational_attempt_modifier(c):
        mod=0.0
        if abs(c.score_diff)<=1:
            mod+=P.STEAL_CONTEXT_CLOSE_BONUS
            if c.inning>=7:mod+=P.STEAL_CONTEXT_LATE_CLOSE_BONUS
        if c.outs==2:mod+=P.STEAL_CONTEXT_TWO_OUT_BONUS
        if c.score_diff>=4:mod+=P.STEAL_CONTEXT_BIG_LEAD_PENALTY
        elif c.score_diff<=-4:mod+=P.STEAL_CONTEXT_BIG_DEFICIT_PENALTY
        return mod
    def attempt_probability(self,speed,c):
        base=P.STEAL_ATTEMPT_MIN+(P.STEAL_ATTEMPT_MAX-P.STEAL_ATTEMPT_MIN)*_sigmoid((speed-P.STEAL_ATTEMPT_CENTER)/P.STEAL_ATTEMPT_SCALE)
        return _clamp(base+self.situational_attempt_modifier(c)*P.STEAL_CONTEXT_PROBABILITY_SCALE,P.STEAL_ATTEMPT_MIN,P.STEAL_ATTEMPT_MAX)
    def success_probability(self,speed,c):
        base=P.STEAL_SUCCESS_MIN+(P.STEAL_SUCCESS_MAX-P.STEAL_SUCCESS_MIN)*_sigmoid((speed-P.STEAL_SUCCESS_CENTER)/P.STEAL_SUCCESS_SCALE)
        adj=-(self.running_defense.running_defense-100)*P.STEAL_RUNNING_DEFENSE_WEIGHT
        if abs(c.score_diff)<=1 and c.inning>=7:adj+=P.STEAL_SUCCESS_CLOSE_PENALTY
        if c.outs==2:adj+=P.STEAL_SUCCESS_TWO_OUT_BONUS
        return _clamp(base+adj,P.STEAL_SUCCESS_FLOOR,P.STEAL_SUCCESS_CEILING)
    def resolve(self,speed,rng):
        c=self.sample_context(rng)
        if not self.eligible(c):return 'blocked',0.0,0.0,False
        ap=self.attempt_probability(speed,c)
        if rng.random()>=ap:return 'hold',ap,0.0,True
        sp=self.success_probability(speed,c)
        return ('SB' if rng.random()<sp else 'CS'),ap,sp,True
