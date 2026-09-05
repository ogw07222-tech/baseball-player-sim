from __future__ import annotations
import csv,json
from pathlib import Path
from statistics import mean
from src import config
from src.player import Player
from src.rng import RNG
from src.growth import growth_distribution,_explosion_chance,GROWABLE_STATS

CANDIDATES=((1.10,.65),(1.20,.70),(1.30,.80),(1.35,.825),(1.40,.90),(1.50,1.00))
AGES=(18,20,22,24,26,28,30,32,35,38)

def apply_one(p,rng,early,late):
    for stat in GROWABLE_STATS:
        m,sd=growth_distribution(p,stat)
        if stat=='speed':m+=(early if p.age<=25 else late if p.age<=27 else 0.0)
        p.stats.apply_delta(stat,int(round(rng.gauss(m,sd))))
    if rng.random()<_explosion_chance(p):
        count=rng.randint(1,min(3,len(GROWABLE_STATS)))
        for stat in rng.sample(GROWABLE_STATS,count):p.stats.apply_delta(stat,rng.randint(config.GROWTH_EXPLOSION_MIN_BONUS,config.GROWTH_EXPLOSION_MAX_BONUS))
    p.advance_age(1)

def run(early,late,n=12000,seed=61001):
    rng=RNG(seed);ps=[Player.random(f'S{i}',rng,position=config.POSITIONS[i%len(config.POSITIONS)]) for i in range(n)];rows=[]
    for age in AGES:
        while ps[0].age<age:
            for p in ps:apply_one(p,rng,early,late)
        vals=[p.stats.speed for p in ps];rows.append({'age':age,'mean':mean(vals),'p01':sorted(vals)[int(.01*(n-1))],'p50':sorted(vals)[int(.50*(n-1))],'p99':sorted(vals)[int(.99*(n-1))],'max':max(vals)})
    return rows

def main():
    Path('reports').mkdir(exist_ok=True);summary=[];detail=[]
    for early,late in CANDIDATES:
        rows=run(early,late);detail += [{'early':early,'late':late,**r} for r in rows];by={r['age']:r for r in rows};prime=mean(by[a]['mean'] for a in (26,28,30));summary.append({'early_bonus_18_25':early,'late_bonus_26_27':late,'prime_mean':prime,'age18_mean':by[18]['mean'],'age28_p99':by[28]['p99'],'age38_mean':by[38]['mean'],'distance_to_110':abs(prime-110)})
    summary.sort(key=lambda r:r['distance_to_110']);sel=summary[0]
    for path,rows in [('reports/hitter_speed_recenter_candidates.csv',summary),('reports/hitter_speed_recenter_age_curve.csv',detail)]:
        with open(path,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={'selected':sel,'target':'prime 26/28/30 mean 108-112; entry unchanged','production_patch_applied':False}
    Path('reports/hitter_speed_recenter_search.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
