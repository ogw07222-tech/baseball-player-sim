from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from statistics import mean,pstdev
from src.player import Player
from src.rng import RNG
from src.growth import apply_season_growth

AGES=(18,20,22,24,26,28,30,32,35)
STATS=("contact","power","discipline","speed")
QS=(.01,.05,.10,.25,.50,.75,.90,.95,.99)

def pct(xs,q):
    s=sorted(xs); i=(len(s)-1)*q; lo=int(math.floor(i)); hi=int(math.ceil(i))
    return s[lo] if lo==hi else s[lo]*(hi-i)+s[hi]*(i-lo)

def run(n:int,seed:int=92026):
    rng=RNG(seed); by_age={a:{s:[] for s in STATS} for a in AGES}
    for i in range(n):
        p=Player.random(f"H{i}",rng,position=rng.choice(("C","1B","2B","3B","SS","LF","CF","RF","DH")))
        target=35
        while True:
            if p.age in by_age:
                for s in STATS: by_age[p.age][s].append(getattr(p.stats,s))
            if p.age>=target: break
            apply_season_growth(p,rng)
    rows=[]
    for a in AGES:
        for s in STATS:
            xs=by_age[a][s]; row={"age":a,"stat":s,"n":len(xs),"mean":mean(xs),"sd":pstdev(xs)}
            for q in QS: row[f"p{int(q*100):02d}"]=pct(xs,q)
            rows.append(row)
    prime={}
    for s in STATS:
        xs=[]
        for a in (26,28,30): xs.extend(by_age[a][s])
        prime[s]={"mean":mean(xs),"sd":pstdev(xs),**{f"p{int(q*100):02d}":pct(xs,q) for q in QS}}
    return rows,prime

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--n',type=int,default=30000);ap.add_argument('--csv',required=True);ap.add_argument('--json',required=True);args=ap.parse_args()
    rows,prime=run(args.n); Path(args.csv).parent.mkdir(parents=True,exist_ok=True)
    with open(args.csv,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    Path(args.json).write_text(json.dumps({"n":args.n,"ages":AGES,"prime_26_30_mixed":prime},indent=2))
    print(json.dumps(prime,indent=2))
if __name__=='__main__':main()
