"""H3.2 baserunning metrics layered on the frozen H3.1 line."""
from __future__ import annotations
from dataclasses import dataclass
from .metrics import H3Line
from . import h32_parameters as S
from . import parameters as P

@dataclass
class H32Line(H3Line):
    steal_opportunities:int=0
    steal_blocked:int=0
    steal_attempts:int=0
    sb:int=0
    cs:int=0
    steal_attempt_probability_sum:float=0.0
    steal_success_probability_sum:float=0.0

    @property
    def batting_value(self) -> float:
        if not self.pa: return 0.0
        w=P.OFFENSIVE_WEIGHTS
        return (w['BB']*self.bb+w['HBP']*self.hbp+w['1B']*self.singles+w['2B']*self.doubles+w['3B']*self.triples+w['HR']*self.hr+w['ROE']*self.roe)/self.pa
    @property
    def baserunning_value(self) -> float:
        return (S.SB_RUN_VALUE*self.sb + S.CS_RUN_VALUE*self.cs)/self.pa if self.pa else 0.0
    @property
    def total_offensive_value(self) -> float:
        return self.batting_value+self.baserunning_value
    @property
    def offensive_value(self) -> float:
        return self.total_offensive_value
    def as_metrics(self):
        m=super().as_metrics();pa=max(1,self.pa)
        m.update({
            'SB':self.sb,'CS':self.cs,'SB_attempts':self.steal_attempts,
            'SB_success%':self.sb/max(1,self.steal_attempts),
            'SB_per_600':self.sb/pa*600,'CS_per_600':self.cs/pa*600,
            'SB_attempts_per_600':self.steal_attempts/pa*600,
            'steal_opportunities_per_600':self.steal_opportunities/pa*600,
            'avg_attempt_probability':self.steal_attempt_probability_sum/max(1,self.steal_opportunities),
            'avg_success_probability_on_attempts':self.steal_success_probability_sum/max(1,self.steal_attempts),
            'batting_value':self.batting_value,'baserunning_value':self.baserunning_value,
            'total_offensive_value':self.total_offensive_value,
        })
        return m
