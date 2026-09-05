"""H3.2.1 post-contact baserunning layer. Balance-Lab only.

H3.1 infield hits, stretch doubles, single->double upgrades, and triples stay in
batting_value. This module adds only steals, advancement, and DP avoidance.
"""
from __future__ import annotations
from dataclasses import dataclass
import math, random
from tools.balance_lab.h3.steal import H32StealModel, H3RunningDefenseProfile, StealContext
from tools.balance_lab.h3 import h32_parameters as H32P
from tools.balance_lab.h3 import h321_parameters as P

def _clamp(x:float,lo:float,hi:float)->float:return max(lo,min(hi,x))
def _sigmoid(x:float)->float:
    if x>=60:return 1.0
    if x<=-60:return 0.0
    return 1.0/(1.0+math.exp(-x))

class H321StealModel(H32StealModel):
    """Preserve H3.2 success; only gate low-speed attempt frequency."""
    def attempt_probability(self,speed:float,c:StealContext)->float:
        gate=_sigmoid((speed-P.STEAL_GATE_CENTER)/P.STEAL_GATE_SCALE)
        core=P.STEAL_ATTEMPT_MAX*_sigmoid((speed-P.STEAL_ATTEMPT_CENTER)/P.STEAL_ATTEMPT_SCALE)
        context=_clamp(self.situational_attempt_modifier(c)*H32P.STEAL_CONTEXT_PROBABILITY_SCALE,-P.STEAL_CONTEXT_LIMIT,P.STEAL_CONTEXT_LIMIT)
        return _clamp(P.STEAL_ATTEMPT_FLOOR+gate*(core+context),0.0001,P.STEAL_ATTEMPT_MAX)

def first_to_third_probability(speed:float,recovery:float=100.0)->float:
    x=P.FIRST_TO_THIRD_MIN+(P.FIRST_TO_THIRD_MAX-P.FIRST_TO_THIRD_MIN)*_sigmoid((speed-P.FIRST_TO_THIRD_CENTER)/P.FIRST_TO_THIRD_SCALE)
    return _clamp(x-(recovery-100.0)*P.RECOVERY_WEIGHT,.12,.78)

def second_to_home_probability(speed:float,recovery:float=100.0)->float:
    x=P.SECOND_TO_HOME_MIN+(P.SECOND_TO_HOME_MAX-P.SECOND_TO_HOME_MIN)*_sigmoid((speed-P.SECOND_TO_HOME_CENTER)/P.SECOND_TO_HOME_SCALE)
    return _clamp(x-(recovery-100.0)*P.RECOVERY_WEIGHT,.16,.84)

def dp_completion_probability(speed:float)->float:
    return P.DP_COMPLETION_MIN+(P.DP_COMPLETION_MAX-P.DP_COMPLETION_MIN)*(1-_sigmoid((speed-P.DP_COMPLETION_CENTER)/P.DP_COMPLETION_SCALE))

DP_BASELINE_COMPLETION=dp_completion_probability(100.0)

@dataclass
class H321BaserunningLine:
    pa:int=0;steal_opportunities:int=0;steal_attempts:int=0;sb:int=0;cs:int=0
    first_to_third_opportunities:int=0;first_to_third_successes:int=0
    second_to_home_opportunities:int=0;second_to_home_successes:int=0
    dp_opportunities:int=0;dp_completed:int=0
    @property
    def steal_value(self)->float:return (P.SB_RUN_VALUE*self.sb+P.CS_RUN_VALUE*self.cs)/max(1,self.pa)
    @property
    def advancement_value(self)->float:return (P.FIRST_TO_THIRD_VALUE*self.first_to_third_successes+P.SECOND_TO_HOME_VALUE*self.second_to_home_successes)/max(1,self.pa)
    @property
    def dp_avoidance_value(self)->float:
        expected=DP_BASELINE_COMPLETION*self.dp_opportunities
        return (expected-self.dp_completed)*P.DP_AVOIDED_VALUE/max(1,self.pa)
    @property
    def total_baserunning_value(self)->float:return self.steal_value+self.advancement_value+self.dp_avoidance_value
    def as_metrics(self)->dict[str,float]:
        pa=max(1,self.pa);att=max(1,self.steal_attempts)
        return {'PA':self.pa,'SB':self.sb,'CS':self.cs,'SB_attempts':self.steal_attempts,
        'SB_per_600':self.sb/pa*600,'CS_per_600':self.cs/pa*600,'SB_attempts_per_600':self.steal_attempts/pa*600,'SB_success%':self.sb/att,
        'first_to_third_opportunities':self.first_to_third_opportunities,'first_to_third_successes':self.first_to_third_successes,'first_to_third_success%':self.first_to_third_successes/max(1,self.first_to_third_opportunities),
        'second_to_home_opportunities':self.second_to_home_opportunities,'second_to_home_successes':self.second_to_home_successes,'second_to_home_success%':self.second_to_home_successes/max(1,self.second_to_home_opportunities),
        'DP_opportunities':self.dp_opportunities,'DP_completed':self.dp_completed,'DP_avoided':self.dp_opportunities-self.dp_completed,'DP_completion%':self.dp_completed/max(1,self.dp_opportunities),
        'steal_value':self.steal_value,'advancement_value':self.advancement_value,'dp_avoidance_value':self.dp_avoidance_value,'total_baserunning_value':self.total_baserunning_value}

def simulate_h321_baserunning(speed:float,pa:int=100_000,seed:int=20260905,reach_factor:float=1.0,running_defense:float=100.0,recovery:float=100.0)->H321BaserunningLine:
    rng=random.Random(seed);line=H321BaserunningLine(pa=pa);steal=H321StealModel(H3RunningDefenseProfile(running_defense))
    steal_rate=_clamp(P.STEAL_OPPORTUNITY_RATE*reach_factor,0,.50);ftt_rate=_clamp(P.FIRST_TO_THIRD_OPP_RATE*reach_factor,0,.10);sth_rate=_clamp(P.SECOND_TO_HOME_OPP_RATE*reach_factor,0,.08)
    for _ in range(pa):
        if rng.random()<steal_rate:
            line.steal_opportunities+=1;c=steal.sample_context(rng)
            if steal.eligible(c) and rng.random()<steal.attempt_probability(speed,c):
                line.steal_attempts+=1
                if rng.random()<steal.success_probability(speed,c):line.sb+=1
                else:line.cs+=1
        if rng.random()<ftt_rate:
            line.first_to_third_opportunities+=1
            if rng.random()<first_to_third_probability(speed,recovery):line.first_to_third_successes+=1
        if rng.random()<sth_rate:
            line.second_to_home_opportunities+=1
            if rng.random()<second_to_home_probability(speed,recovery):line.second_to_home_successes+=1
        if rng.random()<P.DP_OPP_RATE:
            line.dp_opportunities+=1
            if rng.random()<dp_completion_probability(speed):line.dp_completed+=1
    return line
