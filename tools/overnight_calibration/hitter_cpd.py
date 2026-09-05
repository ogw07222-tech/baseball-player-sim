from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from statistics import mean,pstdev
from src.player import Player
from src.rng import RNG
from src.growth import growth_distribution,_explosion_chance,_hitter_cpd_recenter_bonus,GROWABLE_STATS
from src import config

AGES=(18,20,22,24,26,28,30,32,35,38)
STATS=('contact','power','discipline','speed')
QS=(.01,.05,.10,.25,.50,.75,.90,.95,.99)

def q(v,p):
    a=sorted(v);x=(len(a)-1)*p;lo=int(x);hi=min(len(a)-1,lo+1);f=x-lo
    return a[lo]*(1-f)+a[hi]*f

def summarize(v):
    return {'mean':mean(v),'sd':pstdev(v),**{f'p{int(p*100):02d}':q(v,p) for p in QS},'max':max(v)}

def apply_one(player,rng,include_recenter):
    for stat in GROWABLE_STATS:
        m,sd=growth_distribution(player,stat)
        if not include_recenter:m-=_hitter_cpd_recenter_bonus(stat,player.age)
        delta=int(round(rng.gauss(m,sd)));player.stats.apply_delta(stat,delta)
    if rng.random()<_explosion_chance(player):
        count=rng.randint(1,min(3,len(GROWABLE_STATS)))
        for stat in rng.sample(GROWABLE_STATS,count):player.stats.apply_delta(stat,rng.randint(config.GROWTH_EXPLOSION_MIN_BONUS,config.GROWTH_EXPLOSION_MAX_BONUS))
    player.advance_age(1)

def cohort(n,seed,include_recenter):
    rng=RNG(seed);positions=config.POSITIONS;players=[Player.random(f'P{i}',rng,position=positions[i%len(positions)]) for i in range(n)]
    rows=[]
    for age in AGES:
        while players[0].age<age:
            for p in players:apply_one(p,rng,include_recenter)
        for stat in STATS:
            s=summarize([getattr(p.stats,stat) for p in players]);rows.append({'mode':'after' if include_recenter else 'before','age':age,'stat':stat,**s})
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=30000);ap.add_argument('--seed',type=int,default=91901);a=ap.parse_args()
    Path('reports').mkdir(exist_ok=True);before=cohort(a.n,a.seed,False);after=cohort(a.n,a.seed,True);rows=before+after
    fields=list(rows[0]);
    with open('reports/hitter_cpd_age_curve.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    lookup={(r['mode'],r['age'],r['stat']):r for r in rows}
    ba=[]
    for age in AGES:
        for stat in STATS:
            b=lookup['before',age,stat];c=lookup['after',age,stat];ba.append({'age':age,'stat':stat,'before_mean':b['mean'],'after_mean':c['mean'],'delta_mean':c['mean']-b['mean'],'before_sd':b['sd'],'after_sd':c['sd'],'before_p99':b['p99'],'after_p99':c['p99']})
    with open('reports/hitter_cpd_before_after.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(ba[0]));w.writeheader();w.writerows(ba)
    prime={}
    for stat in STATS:
        vals=[lookup['after',age,stat]['mean'] for age in (26,28,30)];prime[stat]=sum(vals)/len(vals)
    gate=all(108<=prime[s]<=112 for s in ('contact','power','discipline'))
    entry_ok=all(abs(lookup['after',18,s]['mean']-lookup['before',18,s]['mean'])<1e-9 for s in STATS)
    tail_ok=all(lookup['after',28,s]['p99']<180 for s in ('contact','power','discipline'))
    result={'gate':'HITTER_CPD_RAW_SCALE_READY' if gate and entry_ok and tail_ok else 'HITTER_CPD_RAW_SCALE_NOT_READY','n':a.n,'seed':a.seed,'prime_26_28_30_mean':prime,'entry_unchanged':entry_ok,'tail_sane':tail_ok,'bonus_contract':{'contact':{'18_25':1.70,'26_27':1.00},'power':{'18_25':1.85,'26_27':1.10},'discipline':{'18_25':2.45,'26_27':1.50},'speed':'exempt'}}
    Path('reports/hitter_cpd_scale_final.json').write_text(json.dumps(result,indent=2))
    Path('reports/hitter_cpd_scale_summary.md').write_text('# Hitter C/P/D Raw Scale Re-centering\n\n'+f"Gate: `{result['gate']}`\n\n30k cohort, entry unchanged. Prime mixed means (ages 26/28/30): Contact {prime['contact']:.2f}, Power {prime['power']:.2f}, Discipline {prime['discipline']:.2f}, Speed {prime['speed']:.2f}. Speed is not recentered in Stage A. Full before/after age curves and tails are in the CSV reports.\n")
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
