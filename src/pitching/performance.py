"""League-relative pitcher performance scoring foundation."""
from __future__ import annotations
from dataclasses import dataclass
import math
from . import parameters as P
from .model import PitchingLine

@dataclass(frozen=True)
class PitcherPerformanceScore:
    score:float; index:float; reliability:float; percentile:float; role:str; metric_z:dict[str,float]

def _pct(z:float)->float:return 100*.5*(1+math.erf(z/math.sqrt(2)))

def score_pitcher_performance(line:PitchingLine,role:str="starter")->PitcherPerformanceScore:
    if role not in P.PERFORMANCE_WEIGHTS: raise ValueError(f"unknown pitcher role: {role}")
    reliability=line.BF/(line.BF+P.PERFORMANCE_RELIABILITY_BF) if line.BF else 0.0
    observed={"k_rate":line.K_pct,"bb_rate":line.BB_pct,"hr_rate":line.HR_pct,"fip":line.FIP}
    z={}
    for name,(mean,sd,direction) in P.PERFORMANCE_BASELINES.items():
        adjusted=mean+reliability*(observed[name]-mean); z[name]=direction*(adjusted-mean)/sd if sd else 0.0
    work=line.BF/max(1,line.G); z["workload"]=reliability*(work-P.WORKLOAD_BASELINE[role])/P.WORKLOAD_SD[role]
    weights=P.PERFORMANCE_WEIGHTS[role]; idx=sum(z[k]*w for k,w in weights.items())/sum(weights.values())
    return PitcherPerformanceScore(100+15*idx,idx,reliability,_pct(idx),role,z)
