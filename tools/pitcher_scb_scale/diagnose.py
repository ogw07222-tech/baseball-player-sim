from __future__ import annotations
import argparse,csv,json,math,statistics
from pathlib import Path
from src.pitching.model import generate_pitcher
from src.pitching.growth import apply_pitcher_season_growth
from src.pitching.physical_velocity import base_avg_kmh
from src.rng import RNG

AGES=(18,20,22,24,26,28,30,32,35)
STATS=('velocity','stuff','control','breaking')
PCTS=(10,25,50,75,90,95,99)

def pct(xs,p):
 s=sorted(xs);x=(len(s)-1)*p/100;lo=int(math.floor(x));hi=int(math.ceil(x));return s[lo] if lo==hi else s[lo]*(hi-x)+s[hi]*(x-lo)

def summarize(xs):
 return {'mean':statistics.fmean(xs),'sd':statistics.pstdev(xs),**{f'p{p}':pct(xs,p) for p in PCTS}}

def run(n,seed):
 r=RNG(seed); buckets={a:{s:[] for s in STATS} for a in AGES}
 for i in range(n):
  p=generate_pitcher(str(i),r,player=True,age=18)
  if 18 in buckets:
   for s in STATS:buckets[18][s].append(getattr(p.stats,s))
  while p.age<max(AGES):
   apply_pitcher_season_growth(p,r)
   if p.age in buckets:
    for s in STATS:buckets[p.age][s].append(getattr(p.stats,s))
 out={str(a):{s:summarize(buckets[a][s]) for s in STATS} for a in AGES}
 for a in AGES:
  out[str(a)]['physical_velocity_kmh']=summarize([base_avg_kmh(x) for x in buckets[a]['velocity']])
 prime={s:summarize([v for a in (26,28,30) for v in buckets[a][s]]) for s in STATS}
 prime['physical_velocity_kmh']=summarize([base_avg_kmh(v) for a in (26,28,30) for v in buckets[a]['velocity']])
 return {'n_per_age':n,'ages':out,'prime_26_30':prime}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=30000);ap.add_argument('--seed',type=int,default=260906);ap.add_argument('--json',default='reports/pitcher_scb_before.json');ap.add_argument('--csv',default='reports/pitcher_scb_before.csv');a=ap.parse_args();res=run(a.n,a.seed);Path(a.json).parent.mkdir(parents=True,exist_ok=True)
 with open(a.json,'w') as f:json.dump(res,f,indent=2)
 with open(a.csv,'w',newline='') as f:
  w=csv.writer(f);w.writerow(['age','stat','mean','sd','p10','p25','p50','p75','p90','p95','p99'])
  for age,data in res['ages'].items():
   for stat,x in data.items():w.writerow([age,stat,x['mean'],x['sd'],x['p10'],x['p25'],x['p50'],x['p75'],x['p90'],x['p95'],x['p99']])
 print(json.dumps({'prime_26_30':res['prime_26_30']},indent=2))
if __name__=='__main__':main()
