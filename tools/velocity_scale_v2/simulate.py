from __future__ import annotations
from collections import Counter
import random
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from .model import GameplayVelocityMap

NEUTRAL_HITTER = HitterSnapshot(100.0,100.0,100.0,100.0)
NEUTRAL_PITCHER = PitcherSnapshot(stuff=100.0,control=100.0,movement=100.0)

def make_engine(kmh:float, points_per_kmh:float, seed:int)->HittingEngine:
    gp=GameplayVelocityMap(points_per_kmh).kmh_to_gameplay(kmh)
    delta=100.0-gp
    def velocity_only_modifier(_pitch,_strikes):
        return delta,0.0
    return HittingEngine(NEUTRAL_HITTER,NEUTRAL_PITCHER,100.0,random.Random(seed),pitch_stat_modifier=velocity_only_modifier)

def pa_metrics(kmh:float, points_per_kmh:float, n:int, seed:int)->dict[str,float]:
    e=make_engine(kmh,points_per_kmh,seed); c:Counter[str]=Counter()
    for _ in range(n): c[e.simulate_plate_appearance().result]+=1
    bb=c['walk']; so=c['strikeout']; hr=c['home_run']; one=c['single']; two=c['double']; three=c['triple']
    hits=one+two+three+hr; ab=max(1,n-bb)
    return {'AVG':hits/ab,'SLG':(one+2*two+3*three+4*hr)/ab,'K%':so/n,'BB%':bb/n,'HR%':hr/n}

def contact_metrics(kmh:float, points_per_kmh:float, n:int, seed:int)->dict[str,float]:
    e=make_engine(kmh,points_per_kmh,seed); swings=touches=whiffs=0
    for _ in range(n):
        pitch=e._pitch()
        if e.rng.random()>=e._swing_probability(pitch,0,0): continue
        swings+=1; result,_,_=e._contact_resolution(pitch,0)
        if result=='miss': whiffs+=1
        else: touches+=1
    return {'Contact%':touches/max(1,swings),'Whiff%':whiffs/max(1,swings)}
