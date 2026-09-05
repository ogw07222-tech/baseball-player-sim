from __future__ import annotations
import argparse,json,statistics
from src.pitching.model import generate_pitcher
from src.pitching.growth import apply_pitcher_season_growth
from src.rng import RNG

def main():
 p=argparse.ArgumentParser();p.add_argument('--n',type=int,default=30000);p.add_argument('--seed',type=int,default=260906);p.add_argument('--output',default='reports/pitcher_prime_raw_diagnostic.json');a=p.parse_args()
 rng=RNG(a.seed); cols={k:[] for k in ('velocity','stuff','control','breaking','stamina','resilience','ability')}
 for i in range(a.n):
  x=generate_pitcher(str(i),rng,player=False,age=18)
  while x.age<28: apply_pitcher_season_growth(x,rng)
  for k in cols:
   cols[k].append(x.stats.current_ability() if k=='ability' else getattr(x.stats,k))
 out={k:{'mean':statistics.fmean(v),'sd':statistics.pstdev(v)} for k,v in cols.items()}
 import pathlib;pathlib.Path(a.output).parent.mkdir(parents=True,exist_ok=True);open(a.output,'w').write(json.dumps(out,indent=2))
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
