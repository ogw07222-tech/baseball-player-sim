from __future__ import annotations
import csv,json
from pathlib import Path
from src import config
from src.career import CareerEngine
from src.player import Player
from src.rng import RNG

RANGES={'1R':(8,15),'2-3R':(12,20),'4-7R':(25,35),'8-11R':(20,30),'undrafted':(10,25)}

def bucket(score,t):
    if score>=t['round1']:return '1R'
    if score>=t['round2_3']:return '2-3R'
    if score>=t['round4_7']:return '4-7R'
    if score>=t['round8_11']:return '8-11R'
    return 'undrafted'

def main(n=10000,seed=20260905):
    scores=[]
    for i in range(n):
        r=RNG(seed+200000+i);p=Player.random('DRAFT',r,position=config.POSITIONS[i%len(config.POSITIONS)])
        d=CareerEngine(p,r).evaluate_draft();scores.append(d.scouting_score)
    base=dict(config.DRAFT_THRESHOLDS);rows=[];best=None
    for step in range(0,61):
        delta=step/10;t={k:v+delta for k,v in base.items()};counts={k:0 for k in RANGES}
        for s in scores:counts[bucket(s,t)]+=1
        pct={k:100*counts[k]/n for k in counts};passed=all(lo<=pct[k]<=hi for k,(lo,hi) in RANGES.items())
        penalty=sum(max(0,lo-pct[k],pct[k]-hi)**2 for k,(lo,hi) in RANGES.items())
        row={'delta':delta,'passed':passed,'penalty':penalty,**pct};rows.append(row)
        if passed and best is None:best={'delta':delta,'thresholds':t,'draft_pct':pct}
    out=Path('reports');out.mkdir(exist_ok=True)
    with open(out/'draft_threshold_recalibration_candidates.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    final={'n':n,'seed':seed,'base_thresholds':base,'frozen_ranges':RANGES,'best_minimal_uniform_shift':best,'gate':'DRAFT_THRESHOLD_RECALIBRATION_READY' if best else 'DRAFT_THRESHOLD_RECALIBRATION_NOT_READY'}
    (out/'draft_threshold_recalibration_final.json').write_text(json.dumps(final,indent=2))
    print(json.dumps(final,indent=2))
if __name__=='__main__':main()
