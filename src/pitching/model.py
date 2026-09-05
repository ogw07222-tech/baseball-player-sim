"""Production pitcher stats, generation and FastSim outcome model."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, fields
import math
from .. import config
from ..rng import RNG
from . import parameters as P
from .fatigue import effective_stats, outing_pitch_cap
from .roles import PITCHER_ROLES

def clamp(x,a,b): return max(a,min(b,x))
def sigmoid(x): x=clamp(x,-60,60); return 1/(1+math.exp(-x))
def logit(p): return math.log(p/(1-p))

@dataclass
class PitcherStats:
    velocity:int; stuff:int; control:int; breaking:int; stamina:int; resilience:int; talent:int
    def __post_init__(self):
        for f in fields(self):
            v=getattr(self,f.name)
            if not isinstance(v,int): raise TypeError(f"{f.name} must be int")
            if v<config.STAT_MIN: raise ValueError(f"{f.name} must be >= {config.STAT_MIN}")
    def as_dict(self): return {f.name:getattr(self,f.name) for f in fields(self)}
    @classmethod
    def from_dict(cls,d): return cls(**{f.name:int(d[f.name]) for f in fields(cls)})
    def apply_delta(self,name:str,delta:int)->int:
        if name not in P.PITCHER_STATS: raise KeyError(f"unknown pitcher stat: {name}")
        nv=max(config.STAT_MIN,getattr(self,name)+int(delta)); setattr(self,name,nv); return nv
    def current_ability(self)->float: return sum(getattr(self,n)*P.ABILITY_WEIGHTS[n] for n in P.PITCHER_STATS)

@dataclass
class Pitcher:
    name:str; age:int; stats:PitcherStats; usage_role:str="starter"; archetype:str="balanced"; recovery_fatigue:float=0.0
    def __post_init__(self):
        if self.usage_role not in PITCHER_ROLES: raise ValueError(f"unknown pitcher role: {self.usage_role}")
    def set_usage_role(self,role:str)->None:
        if role not in PITCHER_ROLES: raise ValueError(f"unknown pitcher role: {role}")
        self.usage_role=role
    def as_dict(self): return {"name":self.name,"age":self.age,"stats":self.stats.as_dict(),"usage_role":self.usage_role,"archetype":self.archetype,"recovery_fatigue":self.recovery_fatigue}
    @classmethod
    def from_dict(cls,d): return cls(str(d["name"]),int(d["age"]),PitcherStats.from_dict(dict(d["stats"])),str(d.get("usage_role","starter")),str(d.get("archetype","balanced")),float(d.get("recovery_fatigue",0.0)))

@dataclass(frozen=True)
class HitterMatchupProfile:
    contact:float=100.; power:float=100.; discipline:float=100.

@dataclass(frozen=True)
class CatcherExtension:
    framing:float=0.; blocking:float=0.; game_calling:float=0.; arm:float=0.
    # Foundation only: no catcher modifier is applied in this PR.

@dataclass
class PitchingLine:
    G:int=0; BF:int=0; outs:int=0; H:int=0; doubles:int=0; triples:int=0; HR:int=0; BB:int=0; SO:int=0; ER:int=0; pitches:int=0
    @property
    def IP(self): return self.outs/3.0
    @property
    def ERA(self): return self.ER*9/self.IP if self.IP else 0.0
    @property
    def WHIP(self): return (self.H+self.BB)/self.IP if self.IP else 0.0
    @property
    def K_pct(self): return self.SO/self.BF if self.BF else 0.0
    @property
    def BB_pct(self): return self.BB/self.BF if self.BF else 0.0
    @property
    def HR_pct(self): return self.HR/self.BF if self.BF else 0.0
    @property
    def K_minus_BB(self): return self.K_pct-self.BB_pct
    @property
    def FIP(self): return (13*self.HR+3*self.BB-2*self.SO)/self.IP+3.2 if self.IP else 0.0
    def as_dict(self): return {"G":self.G,"BF":self.BF,"outs":self.outs,"H":self.H,"2B":self.doubles,"3B":self.triples,"HR":self.HR,"BB":self.BB,"SO":self.SO,"ER":self.ER,"pitches":self.pitches}
    @classmethod
    def from_dict(cls,d): return cls(G=int(d.get("G",0)),BF=int(d.get("BF",0)),outs=int(d.get("outs",0)),H=int(d.get("H",0)),doubles=int(d.get("2B",0)),triples=int(d.get("3B",0)),HR=int(d.get("HR",0)),BB=int(d.get("BB",0)),SO=int(d.get("SO",0)),ER=int(d.get("ER",0)),pitches=int(d.get("pitches",0)))
    def add(self,o):
        for n in ("G","BF","outs","H","doubles","triples","HR","BB","SO","ER","pitches"): setattr(self,n,getattr(self,n)+getattr(o,n))

def _talent(rng:RNG)->int:
    comp=rng.weighted_choice([(entry,entry[0]) for entry in config.TALENT_MIXTURE]);_,mean,sd,floor=comp
    for _ in range(64):
        v=int(round(rng.gauss(mean,sd)))
        if v>=floor:return v
    return int(floor)

def generate_pitcher_stats(rng:RNG,player:bool=True)->tuple[PitcherStats,str]:
    archetype=rng.weighted_choice(P.ARCHETYPE_WEIGHTS); bonus=P.PLAYER_BONUS if player else 0.; shared=rng.gauss(0,P.PLAYER_SHARED_SD if player else P.NPC_SHARED_SD); adj=P.ARCHETYPE_ADJUSTMENTS[archetype]
    vals={n:max(config.STAT_MIN,int(round(rng.gauss(P.BASE_MEANS[n]+bonus+shared+adj.get(n,0),P.BASE_SDS[n])))) for n in P.PITCHER_STATS}
    return PitcherStats(**vals,talent=_talent(rng)),archetype

def generate_pitcher(name:str,rng:RNG,player:bool=True,role:str="starter",age:int=config.START_AGE)->Pitcher:
    stats,arch=generate_pitcher_stats(rng,player); return Pitcher(name,age,stats,role,arch)

def outcome_probabilities(stats:PitcherStats,hitter:HitterMatchupProfile=HitterMatchupProfile(),role:str="starter",pitches:float=0.0)->dict[str,float]:
    e=effective_stats(stats,role,pitches)
    bb=sigmoid(logit(P.NEUTRAL_BB)-.010*(e.control-100)+.006*(hitter.discipline-100))
    k0=P.NEUTRAL_K/(1-P.NEUTRAL_BB); so=sigmoid(logit(k0)+.008*(e.velocity-100)+.012*(e.stuff-100)+.009*(e.breaking-100)-.010*(hitter.contact-100)-.003*(hitter.discipline-100))
    hr0=P.NEUTRAL_HR/(1-P.NEUTRAL_BB-P.NEUTRAL_K); hr=sigmoid(logit(hr0)+.012*(hitter.power-100)-.006*(e.stuff-100)-.009*(e.breaking-100)-.002*(e.control-100)-.0015*(e.velocity-100))
    hit0=(P.NEUTRAL_AVG*(1-P.NEUTRAL_BB)-P.NEUTRAL_HR)/(1-P.NEUTRAL_BB-P.NEUTRAL_K-P.NEUTRAL_HR); hit=sigmoid(logit(hit0)+.006*(hitter.contact-100)-.003*(e.stuff-100)-.0035*(e.breaking-100)+.0008*(hitter.power-100))
    two=sigmoid(logit(.185)+.006*(hitter.power-100)-.0025*(e.breaking-100)-.001*(e.stuff-100))
    return {"bb":clamp(bb,.005,.35),"so":clamp(so,.04,.55),"hr":clamp(hr,.003,.18),"hit":clamp(hit,.12,.55),"double":clamp(two,.05,.42),"triple":.018,"effective_velocity":e.velocity,"effective_stuff":e.stuff,"fatigue_ratio":e.fatigue_ratio}

def _pitch_count(rng:RNG,result:str)->int:
    if result=="BB": return 4+int(rng.random()<.55)+int(rng.random()<.18)
    if result=="SO": return 3+int(rng.random()<.65)+int(rng.random()<.20)
    return 3+int(rng.random()<.45)+int(rng.random()<.15)

def _earned_runs(rng:RNG,result:str)->int:
    if result=="HR": return 1+int(rng.random()<.23)+int(rng.random()<.08)
    if result=="3B": return int(rng.random()<.55)
    if result=="2B": return int(rng.random()<.38)
    if result=="1B": return int(rng.random()<.24)
    if result=="BB": return int(rng.random()<.06)
    return 0

def simulate_batter_faced(stats:PitcherStats,rng:RNG,hitter:HitterMatchupProfile=HitterMatchupProfile(),role:str="starter",pitches:float=0.0)->tuple[str,int,dict[str,float]]:
    q=outcome_probabilities(stats,hitter,role,pitches)
    if rng.random()<q["bb"]: result="BB"
    elif rng.random()<q["so"]: result="SO"
    elif rng.random()<q["hr"]: result="HR"
    elif rng.random()<q["hit"]:
        r=rng.random(); result="3B" if r<q["triple"] else "2B" if r<q["triple"]+q["double"] else "1B"
    else: result="OUT"
    return result,_pitch_count(rng,result),q

def simulate_outing(pitcher:Pitcher,rng:RNG,hitter:HitterMatchupProfile=HitterMatchupProfile())->PitchingLine:
    line=PitchingLine(G=1); cap=outing_pitch_cap(pitcher.stats.stamina,pitcher.usage_role); target_outs=21 if pitcher.usage_role=="starter" else 3
    while line.pitches<cap and line.outs<target_outs and line.BF<80:
        result,count,_=simulate_batter_faced(pitcher.stats,rng,hitter,pitcher.usage_role,line.pitches); line.BF+=1;line.pitches+=count;line.ER+=_earned_runs(rng,result)
        if result in {"SO","OUT"}: line.outs+=1
        if result=="SO": line.SO+=1
        elif result=="BB": line.BB+=1
        elif result in {"1B","2B","3B","HR"}:
            line.H+=1
            if result=="2B":line.doubles+=1
            elif result=="3B":line.triples+=1
            elif result=="HR":line.HR+=1
    return line
