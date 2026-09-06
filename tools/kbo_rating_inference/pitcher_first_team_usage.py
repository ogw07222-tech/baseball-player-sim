from __future__ import annotations

"""Calibration-only role-aware pitcher first-team usage provider.

The repository does not yet have a production pitcher CareerEngine. This provider
therefore uses generated production ratings plus empirical 2025 KBO role/usage
shapes. It never mutates production formulas or raw ratings and it labels every
weight as a proxy rather than claiming simulated BF are real career-engine BF.
"""

import argparse
import csv
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path

from src.pitching.physical_velocity import base_avg_kmh,gameplay_velocity
from tools.pitcher_joint_v3 import calibrate as v3

@dataclass(frozen=True)
class PitcherFirstTeamUsageSnapshot:
    age:int
    role:str
    raw_velocity:float
    raw_stuff:float
    raw_control:float
    raw_breaking:float
    gp_velocity:float
    avg_fastball_kmh:float
    BF:int
    IP:float
    G:int
    GS:int
    usage_weight:float
    weight_source:str="role_aware_2025_kbo_empirical_proxy"


def f(row,key,default=0.0):
    try:return float(row.get(key,default))
    except (TypeError,ValueError):return default

def read(path):
    p=Path(path)
    if not p.exists():return []
    with p.open(encoding='utf-8') as h:return list(csv.DictReader(h))
def role(row):
    g=max(1,f(row,'G'));gs=f(row,'GS')
    if gs>=10 and gs/g>=.5:return 'starter'
    if gs>=3:return 'swingman'
    return 'reliever'
def empirical_usage(rows):
    out={}
    for rname in ('starter','reliever','swingman'):
        q=[r for r in rows if role(r)==rname and f(r,'BF')>=100]
        if not q:continue
        out[rname]={k:[f(r,k) for r in q] for k in ('BF','IP','G','GS')}
    return out
def assign_roles(pitchers):
    # Starter selection prioritizes stamina and balanced command; relievers are
    # not penalized in raw ability, preserving role vs base-skill separation.
    ranked=sorted(pitchers,key=lambda p:(p.stats.stamina+.20*p.stats.control+.10*p.stats.breaking),reverse=True)
    n=len(ranked);out={}
    for i,p in enumerate(ranked):
        frac=i/max(1,n-1);out[id(p)]='starter' if frac<.36 else 'swingman' if frac<.46 else 'reliever'
    return out
def draw_usage(emp,role_name,rng):
    source=emp.get(role_name) or emp.get('reliever') or emp.get('starter')
    if not source:return (450,100.0,35,15) if role_name=='starter' else (180,45.0,45,0)
    i=rng.randrange(len(source['BF']));return int(source['BF'][i]),float(source['IP'][i]),int(source['G'][i]),int(source['GS'][i])
def build(n,seed,source_path='data/kbo_2025_pitcher_stats_source.csv'):
    source=read(source_path) or read('data/kbo_2025_pitcher_stats_seed.csv');emp=empirical_usage(source);pitchers=v3.build_pitchers(n,seed);roles=assign_roles(pitchers);rng=random.Random(seed^0xA551);out=[]
    for p in pitchers:
        r=roles[id(p)];bf,ip,g,gs=draw_usage(emp,r,rng);kmh=base_avg_kmh(p.stats.velocity)
        out.append(PitcherFirstTeamUsageSnapshot(p.age,r,p.stats.velocity,p.stats.stuff,p.stats.control,p.stats.breaking,gameplay_velocity(kmh),kmh,bf,ip,g,gs,float(bf)))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pitchers',type=int,default=5000);ap.add_argument('--seed',type=int,default=262006);ap.add_argument('--out',default='reports/kbo_generated_first_team_pitcher_population.csv');a=ap.parse_args();rows=build(a.pitchers,a.seed);Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with Path(a.out).open('w',newline='',encoding='utf-8') as fobj:
        fields=list(rows[0].__dict__);w=csv.DictWriter(fobj,fieldnames=fields);w.writeheader();w.writerows([x.__dict__ for x in rows])
    result={'n':len(rows),'roles':{r:sum(x.role==r for x in rows) for r in ('starter','reliever','swingman')},'total_BF_proxy':sum(x.BF for x in rows),'mean_BF':statistics.fmean(x.BF for x in rows),'weighting':'BF proxy drawn from empirical 2025 role-specific usage; raw ratings unchanged'}
    Path('reports/kbo_pitcher_usage_provider.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
