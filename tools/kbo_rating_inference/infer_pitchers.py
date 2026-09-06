from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics
from collections import Counter
from pathlib import Path

from src.hitting.model import HitterSnapshot
from src.pitching.model import PitcherStats
from tools.kbo_rating_inference.core import PITCHER_OBJECTIVE_WEIGHTS, PITCHER_TOLERANCES, confidence_from_alternatives, robust_loss, velocity_contract
from tools.pitcher_joint_v3 import calibrate as v3
from tools.pitcher_joint_v3.adapter import JointWeights, PitcherJointV3Adapter

SCB_PRIOR=(109.0,109.0,109.0)
LIBRARY_FIELDS=("player","avg_fastball_kmh","raw_stuff","raw_control","raw_breaking","K_pct","BB_pct","HR_pct","OPP_AVG","OPP_SLG","BABIP","HardContact_pct","loss","stage","seed","simulated_PA")

def read_csv(path):
    with Path(path).open(encoding='utf-8') as f:return list(csv.DictReader(f))
def write_csv(path,rows,fieldnames=None):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    fields=list(fieldnames or (list(rows[0]) if rows else []))
    with p.open('w',newline='',encoding='utf-8') as f:
        if not fields:return
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def fnum(row,key,default=None):
    try:
        x=float(row.get(key,''));return x if math.isfinite(x) else default
    except (TypeError,ValueError):return default
def name_key(name):
    tokens=re.findall(r'[a-z0-9]+',str(name).lower())
    return '|'.join(sorted(tokens))
def velocity_index(path='data/kbo_velocity_reference.csv'):
    out={}
    for r in read_csv(path):
        if str(r.get('season'))!='2025':continue
        kmh=fnum(r,'avg_fastball_kmh')
        if kmh is not None:out[name_key(r.get('player',''))]=r
    return out
def actual_metrics(row):
    bf=max(1.0,fnum(row,'BF',0.0) or 0.0);h=fnum(row,'H',0.0) or 0.0;hr=fnum(row,'HR',0.0) or 0.0;bb=fnum(row,'BB',0.0) or 0.0;so=fnum(row,'SO',0.0) or 0.0
    opp_ab=max(1.0,bf-bb);bip=max(1.0,opp_ab-so-hr)
    out={'K_pct':fnum(row,'K_pct',so/bf),'BB_pct':fnum(row,'BB_pct',bb/bf),'HR_pct':fnum(row,'HR_pct',hr/bf),'OPP_AVG':fnum(row,'OPP_AVG',h/opp_ab),'BABIP':fnum(row,'BABIP',(h-hr)/bip)}
    slg=fnum(row,'OPP_SLG')
    if slg is not None:out['OPP_SLG']=slg
    return out
def simulate(scb,kmh,weights,pa,seed):
    stuff,control,breaking=scb;stats=PitcherStats(97,int(stuff),int(control),int(breaking),100,100,100);rng=random.Random(seed);counts=Counter();balls=Counter();hard=0;h=HitterSnapshot(100,100,100,100);ad=PitcherJointV3Adapter(stats,weights,physical_kmh_override=kmh)
    for _ in range(pa):
        o=ad.make_engine(h,100.0,rng).simulate_plate_appearance();counts[o.result]+=1
        if o.batted_ball is not None:balls[o.batted_ball.ball_type]+=1;hard+=int(o.batted_ball.exit_quality>=.75)
    m=v3.metrics(counts,balls,pa,hard)
    return {'K_pct':m['K%'],'BB_pct':m['BB%'],'HR_pct':m['HR%'],'OPP_AVG':m['AVG'],'OPP_SLG':m['SLG'],'BABIP':m['BABIP'],'HardContact_pct':m['HardContact%']}
def semantic_penalty(scb):
    return sum(((x-m)/45.0)**2 for x,m in zip(scb,SCB_PRIOR))*.05
def candidates(n,seed):
    r=random.Random(seed);out=[(r.randint(60,180),r.randint(60,180),r.randint(60,180)) for _ in range(n)];out.extend([(109,109,109),(140,100,100),(100,140,100),(100,100,140)]);return list(dict.fromkeys(out))
def infer_one(row,kmh,weights,n,coarse_pa,refine_pa,seed,player):
    actual=actual_metrics(row);coarse=[];library=[]
    for i,q in enumerate(candidates(n,seed)):
        run_seed=seed+i*7919;m=simulate(q,kmh,weights,coarse_pa,run_seed);loss=robust_loss(actual,m,PITCHER_TOLERANCES,PITCHER_OBJECTIVE_WEIGHTS)+semantic_penalty(q);coarse.append((loss,q,m));library.append({'player':player,'avg_fastball_kmh':kmh,'raw_stuff':q[0],'raw_control':q[1],'raw_breaking':q[2],**m,'loss':loss,'stage':'coarse','seed':run_seed,'simulated_PA':coarse_pa})
    coarse.sort(key=lambda x:x[0]);r=random.Random(seed^0x55AA);local=set()
    for _,base,_ in coarse[:6]:
        local.add(base)
        for _ in range(20):local.add((max(60,min(180,base[0]+r.randint(-12,12))),max(60,min(180,base[1]+r.randint(-12,12))),max(60,min(180,base[2]+r.randint(-12,12)))))
    refined=[]
    for i,q in enumerate(local):
        run_seed=seed+500000+i*3571;m=simulate(q,kmh,weights,refine_pa,run_seed);loss=robust_loss(actual,m,PITCHER_TOLERANCES,PITCHER_OBJECTIVE_WEIGHTS)+semantic_penalty(q);refined.append((loss,q,m));library.append({'player':player,'avg_fastball_kmh':kmh,'raw_stuff':q[0],'raw_control':q[1],'raw_breaking':q[2],**m,'loss':loss,'stage':'local','seed':run_seed,'simulated_PA':refine_pa})
    refined.sort(key=lambda x:x[0]);return actual,refined[0],refined[1:6],library
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',default='data/kbo_2025_pitcher_stats_source.csv');ap.add_argument('--population-dir',default='reports');ap.add_argument('--candidates',type=int,default=800);ap.add_argument('--coarse-pa',type=int,default=1500);ap.add_argument('--refine-pa',type=int,default=6000);ap.add_argument('--seed',type=int,default=261606);a=ap.parse_args();d=Path(a.population_dir)
    provenance=json.loads(Path('reports/kbo_real_data_provenance.json').read_text()) if Path('reports/kbo_real_data_provenance.json').exists() else {};joint_path=d/'pitcher_joint_v4_first_team_final.json';joint=json.loads(joint_path.read_text()) if joint_path.exists() else {'gate':'NOT_RUN'};joint_ready=joint.get('gate')=='PITCHER_JOINT_CALIBRATION_V4_READY';weights=JointWeights(**joint['best']['weights']) if joint_ready else None;vindex=velocity_index();source=read_csv(a.data);outputs=[];examples=[];losses=[];matched=0;library_rows=[]
    for idx,row in enumerate(source):
        player=row.get('player','');vr=vindex.get(name_key(player));kmh=fnum(vr or {},'avg_fastball_kmh');actual=actual_metrics(row)
        base={'season':row.get('season',2025),'player':player,'team':row.get('team',''),'BF':int(fnum(row,'BF',0) or 0),'IP':row.get('IP',''),'avg_fastball_kmh':kmh if kmh is not None else '', 'raw_velocity':'','raw_stuff':'','raw_control':'','raw_breaking':'','gp_velocity':'','gp_stuff':'','gp_control':'','gp_breaking':'','actual_K_pct':actual.get('K_pct',''),'actual_BB_pct':actual.get('BB_pct',''),'actual_HR_pct':actual.get('HR_pct',''),'actual_OPP_AVG':actual.get('OPP_AVG',''),'actual_OPP_SLG':actual.get('OPP_SLG',''),'actual_BABIP':actual.get('BABIP',''),'fit_loss':'','confidence':'missing_velocity' if kmh is None else 'provisional','velocity_source':(vr or {}).get('source_url',''),'stat_source':row.get('source','')}
        if kmh is not None:
            vc=velocity_contract(kmh);base['raw_velocity']=vc['raw_velocity'];base['gp_velocity']=vc['gp_velocity'];matched+=1
        if kmh is not None and joint_ready:
            actual,best,alts,lib=infer_one(row,kmh,weights,a.candidates,a.coarse_pa,a.refine_pa,a.seed+idx*100003,player);library_rows.extend(lib);loss,q,sim=best;losses.append(loss);base.update({'raw_stuff':q[0],'raw_control':q[1],'raw_breaking':q[2],'gp_stuff':100+(q[0]-109)*weights.w_stuff_quality,'gp_control':100+(q[1]-109)*weights.w_control_zone,'gp_breaking':100+(q[2]-109)*weights.w_breaking_quality,'fit_loss':loss,'confidence':confidence_from_alternatives(loss,[x[0] for x in alts])});examples.append({'kind':'pitcher','player':player,'usage':base['BF'],'velocity_kmh':kmh,'actual_K_pct':actual.get('K_pct',''),'sim_K_pct':sim.get('K_pct',''),'actual_BB_pct':actual.get('BB_pct',''),'sim_BB_pct':sim.get('BB_pct',''),'actual_HR_pct':actual.get('HR_pct',''),'sim_HR_pct':sim.get('HR_pct',''),'actual_OPP_AVG':actual.get('OPP_AVG',''),'sim_OPP_AVG':sim.get('OPP_AVG',''),'ratings':f"V{vc['raw_velocity']:.1f} S{q[0]} C{q[1]} B{q[2]}",'loss':loss})
        outputs.append(base)
    write_csv('data/kbo_real_pitcher_ratings_inferred.csv',outputs);write_csv(d/'kbo_pitcher_fit_examples.csv',examples);write_csv(d/'pitcher_inverse_candidate_library.csv',library_rows,LIBRARY_FIELDS)
    full_source=provenance.get('pitcher_mode')=='live_full_table';reasonable=statistics.median(losses)<4.0 if losses else False;gate=joint_ready and full_source and matched>=10 and len(losses)>=10 and reasonable
    fold_losses=[losses[i::3] for i in range(3)];summary={'gate':'KBO_REAL_PITCHER_RATING_INFERENCE_READY' if gate else 'KBO_REAL_PITCHER_RATING_INFERENCE_NOT_READY','source_players':len(source),'measured_velocity_matches':matched,'scb_fitted_players':len(losses),'source_mode':provenance.get('pitcher_mode','unknown'),'joint_v4_context':joint.get('gate'),'candidate_library_rows':len(library_rows),'median_fit_loss':statistics.median(losses) if losses else None,'fold_mean_losses':[statistics.fmean(x) for x in fold_losses if x],'velocity_rule':'Measured 2025 average fastball is authoritative; raw Velocity is frozen-v2 inverse and never optimized from performance.','missing_velocity_rule':'No exact velocity is fabricated; S/C/B inference is withheld without measured velocity.'}
    (d/'kbo_real_pitcher_inference_summary.json').write_text(json.dumps(summary,indent=2));(d/'kbo_real_pitcher_inference_summary.md').write_text('# KBO Real Pitcher Rating Inference\n\n'+f"Gate: `{summary['gate']}`\n\nMeasured-velocity matches: {matched}\nS/C/B fitted: {len(losses)}\nCandidate-library rows: {len(library_rows)}\nJoint v4 context: {joint.get('gate')}\n");print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
