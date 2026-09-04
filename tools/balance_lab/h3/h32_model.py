"""H3.2 steals layered on the frozen H3.1 batting/fielding model."""
from __future__ import annotations
import random
from .model import H31Model
from .h32_metrics import H32Line
from .profiles import H3HitterProfile,H3PitcherProfile,H3DefenseProfile
from .steal import H32StealModel,H3RunningDefenseProfile
class H32Model(H31Model):
    def __init__(self,hitter:H3HitterProfile,pitcher:H3PitcherProfile|None=None,defense:H3DefenseProfile|None=None,seed:int=1,running_defense:H3RunningDefenseProfile|None=None):
        super().__init__(hitter,pitcher,defense,seed);self.steal_rng=random.Random(seed ^ 0x5EED32A1);self.steal_model=H32StealModel(running_defense)
    def _maybe_steal(self,line:H32Line):
        line.steal_opportunities+=1;outcome,ap,sp,eligible=self.steal_model.resolve(self.hitter.speed,self.steal_rng)
        if not eligible:line.steal_blocked+=1;return
        line.steal_attempt_probability_sum+=ap
        if outcome in {'SB','CS'}:
            line.steal_attempts+=1;line.steal_success_probability_sum+=sp
            if outcome=='SB':line.sb+=1
            else:line.cs+=1
    def plate_appearance(self,line:H32Line):
        bb0,s10,opp0=line.bb,line.singles,line.steal_opportunities
        super().plate_appearance(line)
        # The frozen H3.1 parent has no steal hook. The opp guard also keeps this
        # wrapper safe in local compatibility runs against a temporarily instrumented parent.
        if line.steal_opportunities==opp0 and (line.bb>bb0 or line.singles>s10):self._maybe_steal(line)
    def simulate(self,pa:int)->H32Line:
        line=H32Line()
        for _ in range(pa):self.plate_appearance(line)
        return line
def simulate_h32_profile(hitter:H3HitterProfile,pa:int,seed:int=1,pitcher:H3PitcherProfile|None=None,defense:float=100.0,running_defense:float=100.0)->H32Line:
    return H32Model(hitter,pitcher,H3DefenseProfile(defense),seed,H3RunningDefenseProfile(running_defense)).simulate(pa)
