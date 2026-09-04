"""Shared metric helpers for Balance Lab validation."""
from __future__ import annotations
from dataclasses import dataclass
from statistics import mean
from typing import Iterable
from src.records import BattingLine

@dataclass(frozen=True)
class MetricSummary:
    count:int;mean:float;minimum:float;maximum:float

def summarize(values:Iterable[float])->MetricSummary:
    materialized=[float(v) for v in values]
    if not materialized:raise ValueError('values must contain at least one observation')
    return MetricSummary(len(materialized),mean(materialized),min(materialized),max(materialized))

@dataclass(frozen=True)
class HittingMetrics:
    PA:int;AVG:float;OBP:float;SLG:float;OPS:float;HR_rate:float;BB_rate:float;K_rate:float;H_rate:float;XBH_rate:float;BIP_rate:float;offensive_value:float
    def as_dict(self)->dict[str,float|int]:return self.__dict__.copy()

LINEAR_WEIGHTS={'BB':.69,'HBP':.72,'1B':.89,'2B':1.27,'3B':1.62,'HR':2.10}

def hitting_metrics(line:BattingLine)->HittingMetrics:
    if line.PA<=0:raise ValueError('line must contain at least one PA')
    singles=line.H-line.doubles-line.triples-line.HR;xbh=line.doubles+line.triples+line.HR;bip=line.AB-line.SO-line.HR
    ov=(LINEAR_WEIGHTS['BB']*line.BB+LINEAR_WEIGHTS['HBP']*line.HBP+LINEAR_WEIGHTS['1B']*singles+LINEAR_WEIGHTS['2B']*line.doubles+LINEAR_WEIGHTS['3B']*line.triples+LINEAR_WEIGHTS['HR']*line.HR)/line.PA
    return HittingMetrics(line.PA,line.AVG,line.OBP,line.SLG,line.OPS,line.HR/line.PA,line.BB/line.PA,line.SO/line.PA,line.H/line.PA,xbh/line.PA,bip/line.PA,ov)
