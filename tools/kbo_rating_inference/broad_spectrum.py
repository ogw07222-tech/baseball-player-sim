from __future__ import annotations

"""Broad 2025 KBO player-spectrum calibration/report layer.

This module never changes production gameplay. It stratifies real player-seasons,
adds low/middle/high coverage labels, applies documented small-sample shrinkage,
and compares inferred ratings against generated first-team populations using
usage weights. Primary unit is player-season.
"""

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from tools.kbo_rating_inference.core import weighted_summary

HITTER_BINS=((0,.10,"P00_10_low"),(.10,.25,"P10_25_below"),(.25,.50,"P25_50_lower_mid"),(.50,.75,"P50_75_upper_mid"),(.75,.90,"P75_90_above"),(.90,1.01,"P90_100_star_elite"))
PITCHER_BINS=((0,.20,"P00_20_low"),(.20,.40,"P20_40_below"),(.40,.60,"P40_60_average"),(.60,.80,"P60_80_above"),(.80,1.01,"P80_100_top"))
HITTER_MIN_PA=100
HITTER_ROBUST_PA=300
PITCHER_MIN_BF=100
PITCHER_ROBUST_BF=300
HITTER_PRIOR_PA=250.0
PITCHER_PRIOR_BF=220.0


def read_csv(path:str|Path)->list[dict[str,str]]:
    p=Path(path)
    if not p.exists() or p.stat().st_size==0:return []
    with p.open(encoding="utf-8") as f:return list(csv.DictReader(f))

def write_csv(path:str|Path,rows:list[dict[str,object]])->None:
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if not rows:p.write_text("");return
    fields=[]
    for row in rows:
        for k in row:
            if k not in fields:fields.append(k)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)

def f(row,key,default=0.0):
    try:
        x=float(row.get(key,""));return x if math.isfinite(x) else default
    except (TypeError,ValueError):return default

def qrank(values:list[float])->list[float]:
    order=sorted(range(len(values)),key=values.__getitem__);out=[0.0]*len(values);n=max(1,len(values)-1)
    for rank,i in enumerate(order):out[i]=rank/n
    return out

def bucket_for(q:float,bins)->str:
    for lo,hi,name in bins:
        if lo<=q<hi:return name
    return bins[-1][2]

def shrink_rate(observed:float,usage:float,league:float,prior:float)->float:
    u=max(0.0,float(usage));return (observed*u+league*prior)/(u+prior)

def hitter_score(row:dict[str,str],league:dict[str,float])->float:
    # Multi-metric run-value proxy; no single OPS cut drives the bucket.
    avg=f(row,"AVG");obp=f(row,"OBP");slg=f(row,"SLG");pa=f(row,"PA");bb=f(row,"BB_pct",f(row,"BB")/max(1,pa));k=f(row,"K_pct",f(row,"SO")/max(1,pa));hr=f(row,"HR_pct",f(row,"HR")/max(1,pa));babip=f(row,"BABIP",league["BABIP"])
    def z(x,key,scale):return (x-league[key])/scale
    return .16*z(avg,"AVG",.035)+.21*z(obp,"OBP",.045)+.24*z(slg,"SLG",.070)+.10*z(bb,"BB_pct",.035)-.10*z(k,"K_pct",.060)+.13*z(hr,"HR_pct",.018)+.06*z(babip,"BABIP",.045)

def pitcher_score(row:dict[str,str],league:dict[str,float])->float:
    # Higher is better. ERA/FIP intentionally excluded from primary score.
    bf=max(1.0,f(row,"BF"));k=f(row,"K_pct",f(row,"SO")/bf);bb=f(row,"BB_pct",f(row,"BB")/bf);hr=f(row,"HR_pct",f(row,"HR")/bf);avg=f(row,"OPP_AVG",f(row,"H")/max(1,bf-f(row,"BB")));slg=f(row,"OPP_SLG",league["OPP_SLG"]);babip=f(row,"BABIP",league["BABIP"])
    return .30*(k-league["K_pct"])/.060-.22*(bb-league["BB_pct"])/.035-.14*(hr-league["HR_pct"])/.015-.18*(avg-league["OPP_AVG"])/.035-.12*(slg-league["OPP_SLG"])/.065-.04*(babip-league["BABIP"])/.045

def hitter_usage_bucket(pa:float)->str:
    if pa<100:return "small_sample_under_100"
    if pa<300:return "role_100_299"
    if pa<450:return "regular_300_449"
    if pa<550:return "regular_450_549"
    return "everyday_550_plus"

def pitcher_role(row:dict[str,str])->str:
    g=max(1.0,f(row,"G"));gs=f(row,"GS")
    if gs>=10 and gs/g>=.50:return "starter"
    if gs>=3:return "swingman"
    return "reliever"

def pitcher_usage_bucket(row:dict[str,str],role:str)->str:
    bf=f(row,"BF");g=f(row,"G");sv=f(row,"SV")
    if bf<100:return "small_sample_under_100"
    if role=="starter":return "starter_workhorse" if bf>=600 else "starter_regular" if bf>=400 else "starter_low_usage"
    if role=="swingman":return "swingman"
    if sv>=15:return "closer"
    if g>=50:return "setup_middle_high_usage"
    return "low_middle_relief"

def league_hitter_context(rows):
    w=[max(1,f(r,"PA")) for r in rows]
    def wm(key,calc=None):
        vals=[calc(r) if calc else f(r,key) for r in rows];return sum(a*b for a,b in zip(vals,w))/sum(w)
    return {"AVG":wm("AVG"),"OBP":wm("OBP"),"SLG":wm("SLG"),"BB_pct":wm("BB_pct",lambda r:f(r,"BB")/max(1,f(r,"PA"))),"K_pct":wm("K_pct",lambda r:f(r,"SO")/max(1,f(r,"PA"))),"HR_pct":wm("HR_pct",lambda r:f(r,"HR")/max(1,f(r,"PA"))),"BABIP":wm("BABIP",lambda r:(f(r,"H")-f(r,"HR"))/max(1,f(r,"AB")-f(r,"SO")-f(r,"HR")))}

def league_pitcher_context(rows):
    w=[max(1,f(r,"BF")) for r in rows]
    def wm(calc):return sum(calc(r)*ww for r,ww in zip(rows,w))/sum(w)
    return {"K_pct":wm(lambda r:f(r,"SO")/max(1,f(r,"BF"))),"BB_pct":wm(lambda r:f(r,"BB")/max(1,f(r,"BF"))),"HR_pct":wm(lambda r:f(r,"HR")/max(1,f(r,"BF"))),"OPP_AVG":wm(lambda r:f(r,"H")/max(1,f(r,"BF")-f(r,"BB"))),"OPP_SLG":.400,"BABIP":wm(lambda r:(f(r,"H")-f(r,"HR"))/max(1,f(r,"BF")-f(r,"BB")-f(r,"SO")-f(r,"HR")))}

def stratify_hitters(source:list[dict[str,str]])->list[dict[str,object]]:
    eligible=[r for r in source if f(r,"PA")>=HITTER_MIN_PA];league=league_hitter_context(eligible);scores=[hitter_score(r,league) for r in eligible];ranks=qrank(scores);out=[]
    for r,q,s in zip(eligible,ranks,scores):
        pa=f(r,"PA");row=dict(r);row.update({"performance_score":s,"performance_quantile":q,"performance_bucket":bucket_for(q,HITTER_BINS),"usage_bucket":hitter_usage_bucket(pa),"role":"hitter","sample_set":"robust_300plus" if pa>=HITTER_ROBUST_PA else "primary_100plus","shrinkage_weight":pa/(pa+HITTER_PRIOR_PA)})
        # Preserve originals and expose fixed-prior shrinkage targets for inference diagnostics.
        for key in ("AVG","OBP","SLG"):
            row["shrunk_"+key]=shrink_rate(f(r,key),pa,league[key],HITTER_PRIOR_PA)
        bb=f(r,"BB_pct",f(r,"BB")/max(1,pa));k=f(r,"K_pct",f(r,"SO")/max(1,pa));hr=f(r,"HR_pct",f(r,"HR")/max(1,pa))
        row["shrunk_BB_pct"]=shrink_rate(bb,pa,league["BB_pct"],HITTER_PRIOR_PA);row["shrunk_K_pct"]=shrink_rate(k,pa,league["K_pct"],HITTER_PRIOR_PA);row["shrunk_HR_pct"]=shrink_rate(hr,pa,league["HR_pct"],HITTER_PRIOR_PA);out.append(row)
    return out

def stratify_pitchers(source:list[dict[str,str]])->list[dict[str,object]]:
    eligible=[r for r in source if f(r,"BF")>=PITCHER_MIN_BF];league=league_pitcher_context(eligible);groups=defaultdict(list)
    for r in eligible:groups[pitcher_role(r)].append(r)
    out=[]
    for role,rows in groups.items():
        scores=[pitcher_score(r,league) for r in rows];ranks=qrank(scores)
        for r,q,s in zip(rows,ranks,scores):
            bf=f(r,"BF");row=dict(r);row.update({"role":role,"performance_score":s,"performance_quantile":q,"performance_bucket":bucket_for(q,PITCHER_BINS),"usage_bucket":pitcher_usage_bucket(r,role),"sample_set":"robust_300plus" if bf>=PITCHER_ROBUST_BF else "primary_100plus","shrinkage_weight":bf/(bf+PITCHER_PRIOR_BF)})
            for key,lv in (("K_pct",league["K_pct"]),("BB_pct",league["BB_pct"]),("HR_pct",league["HR_pct"]),("OPP_AVG",league["OPP_AVG"]),("BABIP",league["BABIP"])):
                obs=f(r,key)
                if key in ("K_pct","BB_pct","HR_pct") and not obs:
                    count={"K_pct":"SO","BB_pct":"BB","HR_pct":"HR"}[key];obs=f(r,count)/max(1,bf)
                row["shrunk_"+key]=shrink_rate(obs,bf,lv,PITCHER_PRIOR_BF)
            out.append(row)
    return out

def _join_labels(inferred,labels,key="player"):
    idx={str(r.get(key,"")):r for r in labels};out=[]
    for row in inferred:
        label=idx.get(str(row.get(key,"")),{});x=dict(row)
        for k in ("performance_bucket","usage_bucket","role","performance_quantile","sample_set","shrinkage_weight"):x[k]=label.get(k,x.get(k,""))
        out.append(x)
    return out

def _bucket_rating(rows,weight_key,rating_keys):
    groups=defaultdict(list)
    for r in rows:groups[(r.get("role",""),r.get("performance_bucket",""))].append(r)
    out=[]
    for (role,bucket),rs in sorted(groups.items()):
        w=[max(0.0,f(r,weight_key)) for r in rs]
        if not sum(w):continue
        row={"role":role,"performance_bucket":bucket,"players":len(rs),"usage_weight":sum(w)}
        for key in rating_keys:
            vals=[f(r,key) for r in rs];s=weighted_summary(vals,w);row[key+"_mean"]=s["mean"];row[key+"_sd"]=s["sd"];row[key+"_p50"]=s["p50"]
        out.append(row)
    return out

def _coverage(rows,bins,role=None):
    rr=[r for r in rows if role is None or r.get("role")==role];counts=defaultdict(int)
    for r in rr:counts[r.get("performance_bucket","")]+=1
    return dict(counts)

def main():
    hitter_source=read_csv("data/kbo_2025_hitter_stats_source.csv") or read_csv("data/kbo_2025_hitter_stats_seed.csv")
    pitcher_source=read_csv("data/kbo_2025_pitcher_stats_source.csv") or read_csv("data/kbo_2025_pitcher_stats_seed.csv")
    hitters=stratify_hitters(hitter_source);pitchers=stratify_pitchers(pitcher_source)
    write_csv("reports/kbo_hitter_spectrum_source.csv",hitters);write_csv("reports/kbo_pitcher_spectrum_source.csv",pitchers)
    hi=_join_labels(read_csv("data/kbo_real_hitter_ratings_inferred.csv"),hitters);pi=_join_labels(read_csv("data/kbo_real_pitcher_ratings_inferred.csv"),pitchers)
    if hi:write_csv("data/kbo_real_hitter_ratings_inferred.csv",hi)
    if pi:write_csv("data/kbo_real_pitcher_ratings_inferred.csv",pi)
    hbucket=_bucket_rating(hi,"PA",("raw_contact","raw_power","raw_discipline","raw_speed")) if hi else []
    pbucket=_bucket_rating(pi,"BF",("raw_velocity","raw_stuff","raw_control","raw_breaking")) if pi else []
    write_csv("reports/kbo_hitter_rating_by_bucket.csv",hbucket);write_csv("reports/kbo_pitcher_rating_by_bucket.csv",pbucket)
    hcoverage=_coverage(hitters,HITTER_BINS);starter=_coverage(pitchers,PITCHER_BINS,"starter");reliever=_coverage(pitchers,PITCHER_BINS,"reliever")
    # Broad gate is about source coverage, not fit success.
    h_ok=len(hitters)>=50 and all(hcoverage.get(b[2],0)>0 for b in HITTER_BINS)
    role_counts={r:sum(1 for x in pitchers if x.get("role")==r) for r in ("starter","reliever","swingman")}
    p_ok=len(pitchers)>=50 and role_counts["starter"]>=10 and role_counts["reliever"]>=10 and all(starter.get(b[2],0)>0 for b in PITCHER_BINS) and all(reliever.get(b[2],0)>0 for b in PITCHER_BINS)
    gate=h_ok and p_ok
    result={"gate":"KBO_BROAD_PLAYER_SPECTRUM_READY" if gate else "KBO_BROAD_PLAYER_SPECTRUM_NOT_READY","primary_year":2025,"hitter":{"eligible_100pa":len(hitters),"robust_300pa":sum(f(r,"PA")>=300 for r in hitters),"bucket_counts":hcoverage},"pitcher":{"eligible_100bf":len(pitchers),"robust_300bf":sum(f(r,"BF")>=300 for r in pitchers),"role_counts":role_counts,"starter_buckets":starter,"reliever_buckets":reliever},"weighting":{"hitter":"PA","pitcher":"BF"},"shrinkage":{"hitter_prior_pa":HITTER_PRIOR_PA,"pitcher_prior_bf":PITCHER_PRIOR_BF},"rules":["bottom buckets are retained","performance score is multi-metric","starter and reliever quantiles are separate","measured Velocity remains authoritative"]}
    Path("reports/kbo_broad_spectrum_contract.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    Path("reports/kbo_hitter_spectrum_summary.md").write_text("# KBO Hitter Spectrum\n\nGate: `%s`\n\nEligible >=100 PA: %d\nRobust >=300 PA: %d\n\nBuckets: `%s`\n\nLeague weighting: **PA-weighted**. 100-299 PA rows retain observed data and expose fixed pseudo-count shrinkage targets.\n"%(result["gate"],len(hitters),result["hitter"]["robust_300pa"],hcoverage),encoding="utf-8")
    Path("reports/kbo_pitcher_spectrum_summary.md").write_text("# KBO Pitcher Spectrum\n\nGate: `%s`\n\nEligible >=100 BF: %d\nRobust >=300 BF: %d\nRoles: `%s`\n\nStarter and reliever quantiles are computed separately, then league summaries use **BF weighting**.\n"%(result["gate"],len(pitchers),result["pitcher"]["robust_300bf"],role_counts),encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
