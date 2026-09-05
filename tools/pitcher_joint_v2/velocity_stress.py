from __future__ import annotations
import argparse,csv,math
from pathlib import Path
from src.pitching.model import generate_pitcher
from src.pitching.growth import apply_pitcher_season_growth
from src.pitching.physical_velocity import base_avg_kmh,effective_avg_kmh,max_pitch_kmh,BASE_HARD_CAP,EFFECTIVE_HARD_CAP,MAX_PITCH_HARD_CAP
from src.rng import RNG

def pct(xs,p):
 s=sorted(xs); x=(len(s)-1)*p/100; lo=int(math.floor(x));hi=int(math.ceil(x));return s[lo] if lo==hi else s[lo]*(hi-x)+s[hi]*(x-lo)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--careers',type=int,default=100000);ap.add_argument('--seed',type=int,default=260906);ap.add_argument('--output',default='reports/velocity_cap_stress.csv');a=ap.parse_args();rng=RNG(a.seed)
 raw=[];base=[];eff=[];mx=[]
 for i in range(a.careers):
  # player=True is both the Velocity-v2 source cohort and the stricter high-end stress cohort.
  p=generate_pitcher(str(i),rng,player=True,age=18);rmax=p.stats.velocity;bmax=base_avg_kmh(rmax);emax=effective_avg_kmh(rmax,4.0,0.0);mmax=max_pitch_kmh(emax,max(0.0,rng.gauss(6.3,1.5)))
  while p.age<45:
   apply_pitcher_season_growth(p,rng);r=p.stats.velocity;b=base_avg_kmh(r);e=effective_avg_kmh(r,4.0,0.0);m=max_pitch_kmh(e,max(0.0,rng.gauss(6.3,1.5)))
   rmax=max(rmax,r);bmax=max(bmax,b);emax=max(emax,e);mmax=max(mmax,m)
  raw.append(rmax);base.append(bmax);eff.append(emax);mx.append(mmax)
 Path(a.output).parent.mkdir(parents=True,exist_ok=True)
 with open(a.output,'w',newline='') as f:
  w=csv.writer(f);w.writerow(['metric','p99','p99_9','p99_99','max','exact_cap_fraction'])
  for name,vals,cap in [('raw_velocity',raw,None),('base_avg_kmh',base,BASE_HARD_CAP),('effective_avg_kmh',eff,EFFECTIVE_HARD_CAP),('max_pitch_kmh',mx,MAX_PITCH_HARD_CAP)]:
   hit=0.0 if cap is None else sum(abs(v-cap)<1e-12 for v in vals)/len(vals);w.writerow([name,pct(vals,99),pct(vals,99.9),pct(vals,99.99),max(vals),hit])
 print('base max',max(base),'effective max',max(eff),'max pitch',max(mx))
if __name__=='__main__':main()
