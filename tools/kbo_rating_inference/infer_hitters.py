from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path

from src.hitting.baserunning import GameState, steal_attempt_probability, steal_success_probability
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.normalization import normalize_hitter
from src.pitching.model import PitcherStats
from tools.kbo_rating_inference.core import HITTER_OBJECTIVE_WEIGHTS, HITTER_TOLERANCES, confidence_from_alternatives, robust_loss
from tools.pitcher_joint_v3.adapter import JointWeights, PitcherJointV3Adapter

STEAL_ELIGIBLE_OPPORTUNITIES_PER_PA = 0.30
LEAGUE_PRIOR = (109.26405555555556,109.10451111111111,108.80516666666666,109.91386666666666)


def _read(path: Path):
    with path.open(encoding="utf-8") as f:return list(csv.DictReader(f))

def _f(row,key,default=0.0):
    try:
        x=float(row.get(key,""));return x if math.isfinite(x) else default
    except (TypeError,ValueError):return default

def actual_metrics(row:dict[str,str])->dict[str,float]:
    pa=_f(row,"PA");ab=_f(row,"AB");h=_f(row,"H");bb=_f(row,"BB");hbp=_f(row,"HBP");so=_f(row,"SO");hr=_f(row,"HR");sb=_f(row,"SB");cs=_f(row,"CS")
    one=_f(row,"1B",max(0,h-_f(row,"2B")-_f(row,"3B")-hr));two=_f(row,"2B");three=_f(row,"3B")
    model_pa=max(1.0,pa-hbp);model_ab=max(1.0,model_pa-bb);bip=max(1.0,model_ab-so-hr)
    obs_avg=_f(row,"AVG",h/max(1,ab));obs_obp=_f(row,"OBP",(h+bb+hbp)/max(1,pa));obs_slg=_f(row,"SLG",(one+2*two+3*three+4*hr)/max(1,ab))
    target={"AVG":h/model_ab,"OBP":(h+bb)/model_pa,"SLG":(one+2*two+3*three+4*hr)/model_ab,"BB_pct":bb/model_pa,"K_pct":so/model_pa,"HR_pct":hr/model_pa,"BABIP":(h-hr)/bip}
    if sb+cs>0:
        target["SB_attempt_pct"]=(sb+cs)/max(1,pa)
        target["SB_success"]=sb/(sb+cs)
    target["observed_AVG"]=obs_avg;target["observed_OBP"]=obs_obp;target["observed_SLG"]=obs_slg
    return target

def _metrics(c:Counter,pa:int)->dict[str,float]:
    bb=c['walk'];so=c['strikeout'];hr=c['home_run'];one=c['single'];two=c['double'];three=c['triple'];h=one+two+three+hr;ab=max(1,pa-bb);bip=max(1,ab-so-hr);obp=(h+bb)/pa;slg=(one+2*two+3*three+4*hr)/ab
    return {"AVG":h/ab,"OBP":obp,"SLG":slg,"BB_pct":bb/pa,"K_pct":so/pa,"HR_pct":hr/pa,"BABIP":(h-hr)/bip}

def _speed_metrics(gp_speed:float)->dict[str,float]:
    state=GameState(inning=5,outs=1,score_diff=0,first_occupied=True,second_occupied=False)
    attempt=steal_attempt_probability(gp_speed,state)
    return {"SB_attempt_pct":attempt*STEAL_ELIGIBLE_OPPORTUNITIES_PER_PA,"SB_success":steal_success_probability(gp_speed,state,100.0)}

def _pitcher_sampler(population_path:Path,weights:JointWeights|None):
    if weights is None:return None
    rows=_read(population_path);cum=[];total=0.0
    for r in rows:total+=max(0.0,_f(r,"weight",1.0));cum.append(total)
    return rows,cum,total,weights

def _pick_pitcher(sampler,rng):
    if sampler is None:return None
    rows,cum,total,w=sampler;r=rows[bisect.bisect_right(cum,rng.random()*total)]
    stats=PitcherStats(int(round(_f(r,'raw_velocity'))),int(round(_f(r,'raw_stuff'))),int(round(_f(r,'raw_control'))),int(round(_f(r,'raw_breaking'))),100,100,100)
    return stats,w

def simulate_candidate(ratings:tuple[int,int,int,int],pa:int,seed:int,pitcher_sampler=None)->dict[str,float]:
    gp=normalize_hitter(*ratings);h=HitterSnapshot(gp.contact,gp.power,gp.discipline,gp.speed,'R','balanced');choose=random.Random(seed^0x7711);rng=random.Random(seed^0xC0DE);c=Counter()
    for _ in range(pa):
        picked=_pick_pitcher(pitcher_sampler,choose)
        if picked is None:o=HittingEngine(h,PitcherSnapshot(),100.0,rng).simulate_plate_appearance()
        else:
            stats,w=picked;o=PitcherJointV3Adapter(stats,w).make_engine(h,100.0,rng).simulate_plate_appearance()
        c[o.result]+=1
    out=_metrics(c,pa);out.update(_speed_metrics(gp.speed));return out

def candidate_profiles(n:int,seed:int):
    r=random.Random(seed);profiles=[]
    for _ in range(n):
        profiles.append((r.randint(60,170),r.randint(60,180),r.randint(60,170),r.randint(50,170)))
    # deterministic anchors improve identity/regression diagnostics.
    for c in range(70,161,15):profiles.append((c,109,109,110))
    for p in range(70,171,15):profiles.append((109,p,109,110))
    for d in range(70,161,15):profiles.append((109,109,d,110))
    for s in range(60,171,15):profiles.append((109,109,109,s))
    return list(dict.fromkeys(profiles))
def build_library(n:int,pa:int,seed:int,pitcher_sampler):
    rows=[]
    for i,ratings in enumerate(candidate_profiles(n,seed)):
        m=simulate_candidate(ratings,pa,seed+i*7919,pitcher_sampler);gp=normalize_hitter(*ratings)
        rows.append({"raw_contact":ratings[0],"raw_power":ratings[1],"raw_discipline":ratings[2],"raw_speed":ratings[3],"gp_contact":gp.contact,"gp_power":gp.power,"gp_discipline":gp.discipline,"gp_speed":gp.speed,**m})
    return rows

def prior_penalty(ratings,actual,pa):
    # Population-aware weak regularization. Low-PA and weak speed evidence receive stronger prior.
    scale=min(1.0,300.0/max(100.0,pa));pen=sum(((x-m)/45.0)**2 for x,m in zip(ratings,LEAGUE_PRIOR))*.05*scale
    if "SB_attempt_pct" not in actual:pen+=((ratings[3]-LEAGUE_PRIOR[3])/25.0)**2*.35
    return pen

def infer_one(row,library,refine_pa,seed,pitcher_sampler):
    actual=actual_metrics(row);pa=_f(row,"PA")
    scored=[]
    for cand in library:
        ratings=(int(cand['raw_contact']),int(cand['raw_power']),int(cand['raw_discipline']),int(cand['raw_speed']))
        sim={k:float(cand[k]) for k in HITTER_OBJECTIVE_WEIGHTS if k in cand}
        scored.append((robust_loss(actual,sim,HITTER_TOLERANCES,HITTER_OBJECTIVE_WEIGHTS)+prior_penalty(ratings,actual,pa),ratings,sim))
    scored.sort(key=lambda x:x[0]);seeds=scored[:12]
    local=set()
    for _,base,_ in seeds:
        for dc in (-8,-4,0,4,8):
            for dp in (-8,-4,0,4,8):
                for dd in (-8,-4,0,4,8):
                    for ds in (-8,0,8):
                        q=(max(60,min(170,base[0]+dc)),max(60,min(180,base[1]+dp)),max(60,min(170,base[2]+dd)),max(50,min(170,base[3]+ds)));local.add(q)
    refined=[]
    for i,ratings in enumerate(local):
        sim=simulate_candidate(ratings,refine_pa,seed+i*3571,pitcher_sampler);loss=robust_loss(actual,sim,HITTER_TOLERANCES,HITTER_OBJECTIVE_WEIGHTS)+prior_penalty(ratings,actual,pa);refined.append((loss,ratings,sim))
    refined.sort(key=lambda x:x[0]);best=refined[0];alts=refined[1:6]
    return actual,best,alts

def write_csv(path,rows):
    if not rows:return
    with Path(path).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',default='data/kbo_2025_hitter_stats_source.csv');ap.add_argument('--population-dir',default='reports');ap.add_argument('--candidates',type=int,default=3000);ap.add_argument('--library-pa',type=int,default=2500);ap.add_argument('--refine-pa',type=int,default=12000);ap.add_argument('--seed',type=int,default=261506);a=ap.parse_args();d=Path(a.population_dir)
    provenance=json.loads(Path('reports/kbo_real_data_provenance.json').read_text()) if Path('reports/kbo_real_data_provenance.json').exists() else {}
    joint_path=d/'pitcher_joint_v4_first_team_final.json';joint=json.loads(joint_path.read_text()) if joint_path.exists() else {"gate":"NOT_RUN"}
    weights=JointWeights(**joint['best']['weights']) if joint.get('gate')=='PITCHER_JOINT_CALIBRATION_V4_READY' else None
    sampler=_pitcher_sampler(d/'kbo_generated_first_team_pitcher_population.csv',weights) if weights else None
    source_rows=_read(Path(a.data));library=build_library(a.candidates,a.library_pa,a.seed,sampler)
    write_csv(d/'hitter_inverse_candidate_library.csv',library)
    outputs=[];examples=[];losses=[]
    for idx,row in enumerate(source_rows):
        actual,best,alts=infer_one(row,library,a.refine_pa,a.seed+idx*100003,sampler);loss,ratings,sim=best;gp=normalize_hitter(*ratings);losses.append(loss)
        alt_text=';'.join(f"C{x[1][0]} P{x[1][1]} D{x[1][2]} S{x[1][3]} loss={x[0]:.3f}" for x in alts[:3]);conf=confidence_from_alternatives(loss,[x[0] for x in alts])
        out={"season":row.get('season',2025),"player":row.get('player',''),"team":row.get('team',''),"PA":int(_f(row,'PA')),"AVG":actual['observed_AVG'],"OBP":actual['observed_OBP'],"SLG":actual['observed_SLG'],"BB_pct":actual['BB_pct'],"K_pct":actual['K_pct'],"HR_pct":actual['HR_pct'],"BABIP":actual['BABIP'],"SB":int(_f(row,'SB')),"CS":int(_f(row,'CS')),"raw_contact":ratings[0],"raw_power":ratings[1],"raw_discipline":ratings[2],"raw_speed":ratings[3],"gp_contact":gp.contact,"gp_power":gp.power,"gp_discipline":gp.discipline,"gp_speed":gp.speed,"fit_loss":loss,"fit_confidence":conf,"top_alternatives":alt_text,"fit_pitcher_context":'first_team_v4' if weights else 'neutral_provisional',"source":row.get('source','')};outputs.append(out)
        examples.append({"kind":"hitter","player":out['player'],"usage":out['PA'],"actual_AVG":out['AVG'],"sim_AVG":sim['AVG'],"actual_OBP":out['OBP'],"sim_OBP":sim['OBP'],"actual_SLG":out['SLG'],"sim_SLG":sim['SLG'],"actual_BB_pct":out['BB_pct'],"sim_BB_pct":sim['BB_pct'],"actual_K_pct":out['K_pct'],"sim_K_pct":sim['K_pct'],"actual_HR_pct":out['HR_pct'],"sim_HR_pct":sim['HR_pct'],"ratings":f"C{ratings[0]} P{ratings[1]} D{ratings[2]} S{ratings[3]}","loss":loss})
    write_csv('data/kbo_real_hitter_ratings_inferred.csv',outputs);write_csv(d/'kbo_hitter_fit_examples.csv',examples)
    # 3-fold player split is used for distribution/report validation, not to refit tolerances.
    folds=[losses[i::3] for i in range(3)];fold_means=[statistics.fmean(x) for x in folds if x]
    full_source=provenance.get('hitter_mode')=='live_full_table';joint_ready=weights is not None;reasonable=statistics.median(losses)<4.0 if losses else False
    gate=full_source and joint_ready and reasonable and len(outputs)>=30
    summary={"gate":"KBO_REAL_HITTER_RATING_INFERENCE_READY" if gate else "KBO_REAL_HITTER_RATING_INFERENCE_NOT_READY","players":len(outputs),"source_mode":provenance.get('hitter_mode','unknown'),"pitcher_context":'first_team_v4' if joint_ready else 'neutral_provisional','candidate_library':len(library),"library_pa_per_candidate":a.library_pa,"refine_pa_per_candidate":a.refine_pa,"median_fit_loss":statistics.median(losses) if losses else None,"fold_mean_losses":fold_means,"speed_contract":f"SB attempt proxy uses frozen steal curve × fixed eligible-opportunity factor {STEAL_ELIGIBLE_OPPORTUNITIES_PER_PA}; no running evidence => strong prior/low confidence"}
    (d/'kbo_real_hitter_inference_summary.json').write_text(json.dumps(summary,indent=2));(d/'kbo_real_hitter_inference_summary.md').write_text('# KBO Real Hitter Rating Inference\n\n'+f"Gate: `{summary['gate']}`\n\nPlayers: {len(outputs)}\nSource mode: {summary['source_mode']}\nPitcher context: {summary['pitcher_context']}\nMedian fit loss: {summary['median_fit_loss']}\n")
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
