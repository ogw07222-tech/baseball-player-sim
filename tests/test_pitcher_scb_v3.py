from __future__ import annotations
from functools import lru_cache
import random,statistics
from collections import Counter

from src.pitching.model import PitcherStats,generate_pitcher
from src.pitching.growth import apply_pitcher_season_growth
from src.pitching.physical_velocity import raw_to_uncapped_avg_kmh,GAMEPLAY_POINTS_PER_KMH
from src.rng import RNG
from src.hitting.model import HitterSnapshot
from tools.pitcher_joint_v3.adapter import (
    JointWeights,PitcherJointV3Adapter,normalize,
    STUFF_RAW_REFERENCE,CONTROL_RAW_REFERENCE,BREAKING_RAW_REFERENCE,
)


def stats(**kw):
    d=dict(velocity=97,stuff=109,control=109,breaking=109,stamina=100,resilience=100,talent=100);d.update(kw);return PitcherStats(**d)

@lru_cache(maxsize=1)
def age28_cohort():
    r=RNG(260907);out=[]
    for i in range(3000):
        p=generate_pitcher(str(i),r,player=True,age=18)
        while p.age<28:apply_pitcher_season_growth(p,r)
        out.append(p)
    return out

def test_velocity_distribution_unchanged():
    assert abs(raw_to_uncapped_avg_kmh(97)-146.0)<1e-12
    assert abs(raw_to_uncapped_avg_kmh(150)-159.8979)<0.02
    assert GAMEPLAY_POINTS_PER_KMH==1.50

def test_stuff_prime_mean_near_110(): assert 108<=statistics.fmean(p.stats.stuff for p in age28_cohort())<=112
def test_control_prime_mean_near_110(): assert 108<=statistics.fmean(p.stats.control for p in age28_cohort())<=112
def test_breaking_prime_mean_near_110(): assert 108<=statistics.fmean(p.stats.breaking for p in age28_cohort())<=112

def test_starting_pitchers_not_prime_scaled():
    r=RNG(7);ps=[generate_pitcher(str(i),r,player=True,age=18) for i in range(2000)]
    assert statistics.fmean(p.stats.stuff for p in ps)<90
    assert statistics.fmean(p.stats.control for p in ps)<90
    assert statistics.fmean(p.stats.breaking for p in ps)<90

def test_scb_extreme_generation_rare():
    ps=age28_cohort();assert sum(max(p.stats.stuff,p.stats.control,p.stats.breaking)>=180 for p in ps)/len(ps)<.001

def test_stuff_raw_reference_maps_to_gameplay_neutral(): assert normalize(STUFF_RAW_REFERENCE,STUFF_RAW_REFERENCE,.7)==100
def test_control_raw_reference_maps_to_gameplay_neutral(): assert normalize(CONTROL_RAW_REFERENCE,CONTROL_RAW_REFERENCE,.7)==100
def test_breaking_raw_reference_maps_to_gameplay_neutral(): assert normalize(BREAKING_RAW_REFERENCE,BREAKING_RAW_REFERENCE,.7)==100

def pa_metrics(s:PitcherStats,n=18000,seed=88):
    rng=random.Random(seed);h=HitterSnapshot(100,100,100,100);a=PitcherJointV3Adapter(s,JointWeights());c=Counter();hard=0;bip=0
    for _ in range(n):
        o=a.make_engine(h,100,rng).simulate_plate_appearance();c[o.result]+=1
        if o.batted_ball is not None:
            bip+=1;hard+=int(o.batted_ball.exit_quality>=.75)
    hits=c['single']+c['double']+c['triple']+c['home_run'];ab=max(1,n-c['walk'])
    return {'BB%':c['walk']/n,'AVG':hits/ab,'K%':c['strikeout']/n,'HardContact%':hard/max(1,bip)}

def whiff_rate(s:PitcherStats,n=20000,seed=99):
    rng=random.Random(seed);h=HitterSnapshot(100,100,100,100);e=PitcherJointV3Adapter(s,JointWeights()).make_engine(h,100,rng);sw=miss=0
    for _ in range(n):
        p=e._pitch()
        if e.rng.random()>=e._swing_probability(p,0,0):continue
        sw+=1;res,_,_=e._contact_resolution(p,0);miss+=res=='miss'
    return miss/max(1,sw)

def test_control_reduces_walks(): assert pa_metrics(stats(control=129))['BB%']<pa_metrics(stats())['BB%']
def test_control_does_not_raise_avg_pathologically(): assert pa_metrics(stats(control=129))['AVG']-pa_metrics(stats())['AVG']<.02
def test_stuff_reduces_hard_contact(): assert pa_metrics(stats(stuff=129))['HardContact%']<pa_metrics(stats())['HardContact%']
def test_stuff_not_universal():
    a=PitcherJointV3Adapter(stats(stuff=129),JointWeights());assert a.pitcher_snapshot().control==100

def test_breaking_increases_whiff(): assert whiff_rate(stats(breaking=129))>whiff_rate(stats())
def test_breaking_not_universal():
    a=PitcherJointV3Adapter(stats(breaking=129),JointWeights());assert a.pitcher_snapshot().control==100

def test_velocity_path_unchanged():
    a=PitcherJointV3Adapter(stats(velocity=97),JointWeights());assert abs(a.effective_kmh-146)<1e-12

def test_scb_extreme_rating_safety():
    w=JointWeights()
    for q in (30,50,70,90,100,110,120,130,150,180,200,250):
        a=PitcherJointV3Adapter(stats(stuff=q,control=q,breaking=q),w)
        x=a.modifier(None,0);assert all(abs(v)<1000 for v in x);assert -1000<a.pitcher_snapshot().control<1000
