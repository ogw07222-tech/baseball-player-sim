"""Independent experimental pitcher FastSim used before production promotion."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import math, random
from . import parameters as P

def clamp(x,a,b): return max(a,min(b,x))
def sigmoid(x): x=clamp(x,-60,60); return 1/(1+math.exp(-x))
def logit(p): return math.log(p/(1-p))

def ability(stats): return sum(float(stats[k])*P.ABILITY_WEIGHTS[k] for k in P.PITCHER_STATS)

@dataclass(frozen=True)
class PitcherProfile:
    velocity:float=100; stuff:float=100; control:float=100; breaking:float=100; stamina:float=100; resilience:float=100

@dataclass(frozen=True)
class HitterProfile:
    contact:float=100; power:float=100; discipline:float=100

def probabilities(p:PitcherProfile,h:HitterProfile=HitterProfile(),role:str="starter",pitches:float=0):
    drain=P.RELIEVER_DRAIN if role=="reliever" else P.STARTER_DRAIN
    vb=P.RELIEVER_VELOCITY_BONUS if role=="reliever" else 0; sb=P.RELIEVER_STUFF_BONUS if role=="reliever" else 0
    ratio=pitches*drain/max(30.,60+.45*p.stamina); x=max(0.,ratio-.55); penalty=x**1.35*10
    v=p.velocity+vb-penalty; s=p.stuff+sb-penalty; c=p.control-.38*penalty; b=p.breaking-.18*penalty
    bb=sigmoid(logit(P.NEUTRAL_BB)-.010*(c-100)+.006*(h.discipline-100))
    k0=P.NEUTRAL_K/(1-P.NEUTRAL_BB)
    so=sigmoid(logit(k0)+.008*(v-100)+.012*(s-100)+.009*(b-100)-.010*(h.contact-100)-.003*(h.discipline-100))
    hr0=P.NEUTRAL_HR/(1-P.NEUTRAL_BB-P.NEUTRAL_K)
    hr=sigmoid(logit(hr0)+.012*(h.power-100)-.006*(s-100)-.009*(b-100)-.002*(c-100)-.0015*(v-100))
    hit0=(P.NEUTRAL_AVG*(1-P.NEUTRAL_BB)-P.NEUTRAL_HR)/(1-P.NEUTRAL_BB-P.NEUTRAL_K-P.NEUTRAL_HR)
    hit=sigmoid(logit(hit0)+.006*(h.contact-100)-.003*(s-100)-.0035*(b-100)+.0008*(h.power-100))
    double=sigmoid(logit(.185)+.006*(h.power-100)-.0025*(b-100)-.001*(s-100))
    return {"bb":clamp(bb,.005,.35),"so":clamp(so,.04,.55),"hr":clamp(hr,.003,.18),"hit":clamp(hit,.12,.55),"double":clamp(double,.05,.42),"triple":.018,"effective_velocity":v,"effective_stuff":s,"fatigue_ratio":ratio}

def simulate_pa(p:PitcherProfile,n:int=100000,seed:int=1,role:str="starter"):
    rng=random.Random(seed); c=Counter(); effv=effs=0.
    for _ in range(n):
        q=probabilities(p,role=role); effv+=q["effective_velocity"]; effs+=q["effective_stuff"]
        if rng.random()<q["bb"]: c["BB"]+=1; continue
        if rng.random()<q["so"]: c["SO"]+=1; continue
        if rng.random()<q["hr"]: c["HR"]+=1; continue
        if rng.random()<q["hit"]:
            r=rng.random(); c["3B" if r<q["triple"] else "2B" if r<q["triple"]+q["double"] else "1B"]+=1
        else:c["OUT"]+=1
    ab=n-c["BB"]; hits=c["1B"]+c["2B"]+c["3B"]+c["HR"]
    avg=hits/ab; obp=(hits+c["BB"])/n; slg=(c["1B"]+2*c["2B"]+3*c["3B"]+4*c["HR"])/ab
    return {"PA":n,"AVG":avg,"OBP":obp,"SLG":slg,"OPS":obp+slg,"K%":c["SO"]/n,"BB%":c["BB"]/n,"HR%":c["HR"]/n,"BABIP":(hits-c["HR"])/max(1,ab-c["SO"]-c["HR"]),"effective_velocity":effv/n,"effective_stuff":effs/n}
