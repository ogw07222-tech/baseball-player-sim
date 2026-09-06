from __future__ import annotations
import json,random,statistics
from collections import Counter
from pathlib import Path
from tools.pitcher_joint_v3 import calibrate as v3
from src.hitting.model import HitterSnapshot,HittingEngine,PitcherSnapshot
from src.hitting.normalization import normalize_hitter


def hs(p):
    g=normalize_hitter(float(p.stats.contact),float(p.stats.power),float(p.stats.discipline),float(p.stats.speed))
    return HitterSnapshot(g.contact,g.power,g.discipline,g.speed,'L' if p.bats_throws.startswith('L') else 'R','balanced')

def metrics(c,pa):
    bb=c['walk'];so=c['strikeout'];hr=c['home_run'];one=c['single'];two=c['double'];three=c['triple'];h=one+two+three+hr;ab=pa-bb;bip=max(1,ab-so-hr);obp=(h+bb)/pa;slg=(one+2*two+3*three+4*hr)/ab
    return {'AVG':h/ab,'OBP':obp,'SLG':slg,'OPS':obp+slg,'BB%':bb/pa,'K%':so/pa,'HR%':hr/pa,'1B%':one/pa,'2B%':two/pa,'3B%':three/pa,'BABIP':(h-hr)/bip}

def main(n=4000,pa=300000,seed=261106):
    hitters=v3.build_hitters(n,seed)
    gp=[];ages=[]
    for p in hitters:
        g=normalize_hitter(p.stats.contact,p.stats.power,p.stats.discipline,p.stats.speed);gp.append((g.contact,g.power,g.discipline,g.speed));ages.append(p.age)
    choose=random.Random(seed+1);rng=random.Random(seed+2);c=Counter()
    for _ in range(pa):
        p=hitters[choose.randrange(n)];o=HittingEngine(hs(p),PitcherSnapshot(),100.0,rng).simulate_plate_appearance();c[o.result]+=1
    names=('contact','power','discipline','speed')
    out={'n':n,'pa':pa,'age_mean':statistics.fmean(ages),'age_counts':{str(a):ages.count(a) for a in sorted(set(ages))},'gameplay_mean':{s:statistics.fmean(x[i] for x in gp) for i,s in enumerate(names)},'gameplay_sd':{s:statistics.pstdev(x[i] for x in gp) for i,s in enumerate(names)},'offense_vs_neutral_pitcher':metrics(c,pa)}
    Path('reports').mkdir(exist_ok=True);Path('reports/pitcher_joint_v4_population_mix.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
