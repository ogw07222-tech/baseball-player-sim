"""Player base-stat model and random generation helpers."""
from __future__ import annotations
from dataclasses import dataclass, fields
from . import config
from .rng import RNG

def _truncated_gauss_int(rng:RNG,mean:float,stddev:float,minimum:int=0)->int:
    for _ in range(64):
        value=int(round(rng.gauss(mean,stddev)))
        if value>=minimum:return value
    return max(minimum,int(round(mean)))
def _generate_talent(rng:RNG)->int:
    component=rng.weighted_choice([(e,e[0]) for e in config.TALENT_MIXTURE]); _,mean,stddev,minimum=component
    return _truncated_gauss_int(rng,mean,stddev,minimum)
@dataclass
class PlayerStats:
    contact:int; power:int; discipline:int; speed:int; defense:int; throwing:int; stamina:int; durability:int; mentality:int; talent:int
    def __post_init__(self)->None:
        for f in fields(self):
            v=getattr(self,f.name)
            if not isinstance(v,int): raise TypeError(f'{f.name} must be int')
            if v<config.STAT_MIN: raise ValueError(f'{f.name} must be >= {config.STAT_MIN}')
    def as_dict(self)->dict[str,int]: return {f.name:getattr(self,f.name) for f in fields(self)}
    @classmethod
    def from_dict(cls,data:dict[str,int])->'PlayerStats': return cls(**{n:int(data[n]) for n in config.STAT_NAMES})
    def apply_delta(self,stat_name:str,delta:int)->int:
        if stat_name not in config.STAT_NAMES: raise KeyError(f'unknown stat: {stat_name}')
        new=max(config.STAT_MIN,getattr(self,stat_name)+int(delta)); setattr(self,stat_name,new); return new
    def current_ability(self)->float:
        w={'contact':1.2,'power':1.1,'discipline':1.0,'speed':.55,'defense':.75,'throwing':.35,'stamina':.30,'durability':.30,'mentality':.45}
        return sum(getattr(self,n)*x for n,x in w.items())/sum(w.values())
def generate_random_stats(rng:RNG,position:str='SS')->PlayerStats:
    if position not in config.POSITIONS: raise ValueError(f'unsupported position: {position}')
    adj=config.POSITION_ADJUSTMENTS.get(position,{}); vals={}
    for n,(m,s) in config.INITIAL_STAT_DISTRIBUTIONS.items(): vals[n]=max(config.STAT_MIN,_truncated_gauss_int(rng,m,s,config.STAT_MIN)+adj.get(n,0))
    vals['talent']=_generate_talent(rng); return PlayerStats(**vals)
