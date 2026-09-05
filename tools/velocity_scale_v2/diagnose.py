from __future__ import annotations
import argparse,csv,json,math,statistics
from collections import defaultdict
from pathlib import Path
from src import config
from src.pitching.model import generate_pitcher
from src.pitching.growth import apply_pitcher_season_growth
from src.rng import RNG
from .model import LinearNarrowMap,PiecewiseMildTailMap,SoftMildMap

PCTS=(.01,.05,.10,.25,.50,.75,.90,.95,.99)
AGES=(18,20,22,24,26,28,30,32,35,38)

def pct(xs,p):
    ys=sorted(xs); pos=(len(ys)-1)*p; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    return ys[lo] if lo==hi else ys[lo]*(hi-pos)+ys[hi]*(pos-lo)

def desc(xs):
    return {'n':len(xs),'mean':statistics.mean(xs),'sd':statistics.stdev(xs),'min':min(xs),'max':max(xs),**{f'p{int(p*100)}':pct(xs,p) for p in PCTS}}

def load_kbo(path):
    with path.open(encoding='utf-8') as f: return [float(r['avg_fastball_kmh']) for r in csv.DictReader(f)]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshots',type=int,default=120000); ap.add_argument('--careers',type=int,default=12000); ap.add_argument('--seed',type=int,default=20260906); ap.add_argument('--output',default='reports/velocity_v2_baseline.json'); args=ap.parse_args()
    rng=RNG(args.seed)
    start=[]
    for i in range(args.snapshots): start.append(float(generate_pitcher(f'S{i}',rng,player=True,role='starter',age=18).stats.velocity))
    by_age=defaultdict(list); active=[]
    for i in range(args.careers):
        p=generate_pitcher(f'C{i}',rng,player=True,role='starter',age=18)
        while p.age<=38:
            if p.age in AGES: by_age[p.age].append(float(p.stats.velocity))
            if 20<=p.age<=35: active.append(float(p.stats.velocity))
            if p.age==38: break
            apply_pitcher_season_growth(p,rng)
    kbo=load_kbo(Path('data/kbo_velocity_distribution_2025.csv')); kd=desc(kbo)
    prime=by_age[28]
    raw_reference=statistics.mean(active)
    candidates={
      'linear':LinearNarrowMap(reference_rating=raw_reference,reference_kmh=146.0,kmh_per_rating=.28),
      'piecewise':PiecewiseMildTailMap(reference_rating=raw_reference,reference_kmh=146.0,central_slope=.28,tail_start=140,tail_slope=.20,safety_start=180,safety_slope=.05),
      'soft_mild':SoftMildMap(reference_rating=raw_reference,reference_kmh=146.0,slope=.30,compression_scale=300),
    }
    out={'start_raw':desc(start),'prime_age28_raw':desc(prime),'active_20_35_raw':desc(active),'raw_reference_active_mean':raw_reference,'kbo':kd,'ages':{},'candidates':{}}
    for age,xs in by_age.items(): out['ages'][str(age)]={'raw':desc(xs)}
    for name,m in candidates.items():
        phys=[m.raw_to_kmh(x) for x in active]; pd=desc(phys)
        qerr=sum(abs(pd[f'p{q}']-kd[f'p{q}']) for q in (5,10,25,50,75,90,95))/7
        meanerr=abs(pd['mean']-146.0); sderr=abs(pd['sd']-kd['sd'])
        out['candidates'][name]={'params':m.__dict__,'active_physical':pd,'fit_score':meanerr+sderr+qerr,'extremes':{str(r):m.raw_to_kmh(r) for r in (30,50,70,80,90,100,110,120,130,140,150,160,180,200,250)}}
        for age,xs in by_age.items(): out['ages'][str(age)].setdefault('physical',{})[name]=desc([m.raw_to_kmh(x) for x in xs])
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({'start':out['start_raw'],'prime':out['prime_age28_raw'],'active':out['active_20_35_raw'],'kbo':kd,'scores':{k:v['fit_score'] for k,v in out['candidates'].items()}},indent=2))
if __name__=='__main__': main()
