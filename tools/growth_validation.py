"""Current generation x current production growth validation.

Validation only: imports production generation/growth/career code without mutating
configuration or production mechanics. Produces chart-ready JSON/CSV summaries.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Iterable

from src import config
from src.career import CareerEngine
from src.growth import apply_season_growth
from src.player import Player
from src.rng import RNG
from src.stats import generate_high_school_npc_stats
from src.traits import generate_random_traits

SOURCE_BRANCH = "feature/h32-production-integration"
SOURCE_SHA = "c3ebae8763337bfec5b0ec8e1eee0ec03d078cf9"
DEFAULT_MASTER_SEED = 20260905
AGES = (18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,35,37,40)
COMPARE_AGES = (18,20,22,24,26,28,30,32,35)
STAT_AGES = (18,22,25,28,31,35)
TRACKED_STATS = ("contact","power","discipline","speed","defense")


def pct(values:list[float], q:float)->float:
    if not values:return float("nan")
    a=sorted(values);x=(len(a)-1)*q;lo=int(x);hi=min(len(a)-1,lo+1);f=x-lo
    return a[lo]*(1-f)+a[hi]*f


def r3(v:float)->float|None:
    return None if not math.isfinite(v) else round(v,3)


def describe(values:Iterable[float], qs=(.10,.25,.50,.75,.90,.95,.99))->dict[str,object]:
    v=list(values)
    if not v:return {"n":0}
    out={"n":len(v),"mean":r3(statistics.mean(v)),"sd":r3(statistics.pstdev(v)),"min":r3(min(v)),"max":r3(max(v))}
    for q in qs:out[f"p{int(q*100)}"]=r3(pct(v,q))
    return out


def corr(xs:list[float],ys:list[float])->float|None:
    if len(xs)<2:return None
    mx=statistics.mean(xs);my=statistics.mean(ys)
    dx=[x-mx for x in xs];dy=[y-my for y in ys]
    den=math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
    return None if den==0 else round(sum(x*y for x,y in zip(dx,dy))/den,4)


def rate(rows:list[dict], pred)->float:
    return round(100*sum(1 for row in rows if pred(row))/len(rows),3) if rows else 0.0


def make_npc(name:str,rng:RNG,position:str)->Player:
    # Mirror Player.random non-stat generation; only the stats source differs.
    profile=rng.weighted_choice(config.DEVELOPMENT_PROFILE_WEIGHTS)
    stats=generate_high_school_npc_stats(rng,position)
    traits=generate_random_traits(rng,None)
    p=Player(name=name,age=config.START_AGE,stats=stats,traits=traits,position=position,development_profile=profile)
    p.breakthrough_affinity=float(rng.weighted_choice(config.BREAKTHROUGH_AFFINITY_WEIGHTS))
    return p


def make_player(cohort:str,idx:int,seed:int)->tuple[Player,RNG]:
    rng=RNG(seed);pos=config.POSITIONS[idx%len(config.POSITIONS)]
    if cohort=="player":return Player.random(f"P{idx}",rng,position=pos),rng
    return make_npc(f"N{idx}",rng,pos),rng


def snap(p:Player)->dict[str,object]:
    return {"ability":p.stats.current_ability(),**{s:getattr(p.stats,s) for s in TRACKED_STATS}}


def run_pure_one(args:tuple[str,int,int])->dict[str,object]:
    cohort,idx,seed=args;p,rng=make_player(cohort,idx,seed)
    # PURE mode explicitly removes growth-trait effects; all other production
    # growth mechanics (Talent/profile/age/damping/explosion/aging) remain.
    p.traits=[]
    start=snap(p);snaps={18:start.copy()};peak_ability=float(start["ability"]);peak_age=18
    stat_peak={s:float(start[s]) for s in TRACKED_STATS}
    while p.age<config.RETIREMENT_HARD_AGE:
        g=apply_season_growth(p,rng,coach=None,experience=None,modifiers=None)
        # ability_before captures any pre-growth state; in PURE it equals the
        # previous snapshot. ability_after is the new age snapshot.
        for ability,age in ((g.ability_before,g.age_before),(g.ability_after,g.age_after)):
            if ability>peak_ability:peak_ability=float(ability);peak_age=age
        s=snap(p);snaps[p.age]=s
        for k in TRACKED_STATS:stat_peak[k]=max(stat_peak[k],float(s[k]))
    return {"cohort":cohort,"mode":"pure","start":float(start["ability"]),"talent":p.initial_talent,"profile":p.development_profile,
            "peak":peak_ability,"peak_age":peak_age,"growth":peak_ability-float(start["ability"]),"retirement_age":None,
            "snaps":snaps,"stat_peak":stat_peak,"draft_round":None}


def run_full_one(args:tuple[str,int,int])->dict[str,object]:
    cohort,idx,seed=args;p,rng=make_player(cohort,idx,seed)
    start=snap(p);snaps={18:start.copy()};stat_peak={s:float(start[s]) for s in TRACKED_STATS}
    engine=CareerEngine(p,rng);draft=engine.evaluate_draft();seasons=0
    peak_ability=float(start["ability"]);peak_age=18
    while engine.phase=="PRO" and seasons<30:
        _,g=engine.finish_pro_season();seasons+=1
        for ability,age in ((g.ability_before,g.age_before),(g.ability_after,g.age_after)):
            if ability>peak_ability:peak_ability=float(ability);peak_age=age
        s=snap(p);snaps[p.age]=s
        for k in TRACKED_STATS:stat_peak[k]=max(stat_peak[k],float(s[k]))
        if engine.should_retire():engine.retire()
    if engine.phase=="PRO":engine.retire()
    return {"cohort":cohort,"mode":"full","start":float(start["ability"]),"talent":p.initial_talent,"profile":p.development_profile,
            "peak":peak_ability,"peak_age":peak_age,"growth":peak_ability-float(start["ability"]),"retirement_age":p.retirement_age,
            "snaps":snaps,"stat_peak":stat_peak,"draft_round":draft.round}


def run_many(kind:str,cohort:str,n:int,master:int,offset:int,workers:int)->list[dict[str,object]]:
    fn=run_pure_one if kind=="pure" else run_full_one
    items=[(cohort,i,master+offset+i) for i in range(n)]
    if workers<=1:return [fn(x) for x in items]
    with ProcessPoolExecutor(max_workers=workers) as ex:return list(ex.map(fn,items,chunksize=16))


def bucket(rows:list[dict], selector, specs:list[tuple[str,object]])->list[dict[str,object]]:
    out=[]
    for name,pred in specs:
        sub=[r for r in rows if pred(selector(r))]
        if not sub:out.append({"group":name,"count":0});continue
        out.append({"group":name,"count":len(sub),"mean_start":r3(statistics.mean(r["start"] for r in sub)),"mean_peak":r3(statistics.mean(r["peak"] for r in sub)),
                    "mean_growth":r3(statistics.mean(r["growth"] for r in sub)),"mean_peak_age":r3(statistics.mean(r["peak_age"] for r in sub)),"p90_peak":r3(pct([r["peak"] for r in sub],.90)),
                    "ge100_pct":rate(sub,lambda r:r["peak"]>=100),"ge110_pct":rate(sub,lambda r:r["peak"]>=110),"ge120_pct":rate(sub,lambda r:r["peak"]>=120)})
    return out


def age_curve(rows:list[dict])->dict[str,object]:
    out={}
    for age in AGES:
        vals=[r["snaps"][age]["ability"] for r in rows if age in r["snaps"]]
        d=describe(vals);d.update({f"ge{t}_pct":round(100*sum(v>=t for v in vals)/len(vals),3) if vals else 0.0 for t in (90,100,110,120)})
        out[str(age)]=d
    return out


def stat_curves(rows:list[dict])->dict[str,object]:
    out={}
    for s in TRACKED_STATS:
        d={}
        for age in STAT_AGES:
            v=[r["snaps"][age][s] for r in rows if age in r["snaps"]];d[str(age)]=r3(statistics.mean(v)) if v else None
        d["peak_mean"]=r3(statistics.mean(r["stat_peak"][s] for r in rows));out[s]=d
    return out


def profile_analysis(rows:list[dict])->list[dict[str,object]]:
    out=[]
    for name,_ in config.DEVELOPMENT_PROFILE_WEIGHTS:
        sub=[r for r in rows if r["profile"]==name]
        row={"profile":name,"count":len(sub)}
        for age in (18,22,25,28,31):
            v=[r["snaps"][age]["ability"] for r in sub if age in r["snaps"]];row[f"age{age}_mean"]=r3(statistics.mean(v)) if v else None
        if sub:
            row.update({"peak_mean":r3(statistics.mean(r["peak"] for r in sub)),"peak_age_mean":r3(statistics.mean(r["peak_age"] for r in sub)),"growth_mean":r3(statistics.mean(r["growth"] for r in sub))})
        out.append(row)
    return out


def special_subset(rows:list[dict],name:str,pred)->dict[str,object]:
    sub=[r for r in rows if pred(r)]
    if not sub:return {"name":name,"count":0}
    out={"name":name,"count":len(sub),"share_pct":round(100*len(sub)/len(rows),3),"mean_start":r3(statistics.mean(r["start"] for r in sub)),
         "mean_peak":r3(statistics.mean(r["peak"] for r in sub)),"p90_peak":r3(pct([r["peak"] for r in sub],.9)),"mean_peak_age":r3(statistics.mean(r["peak_age"] for r in sub)),
         "mean_growth":r3(statistics.mean(r["growth"] for r in sub))}
    for t in (90,100,110,120):out[f"ge{t}_pct"]=rate(sub,lambda r,t=t:r["peak"]>=t)
    for age in (18,22,25):
        v=[r["snaps"][age]["ability"] for r in sub if age in r["snaps"]];out[f"age{age}_mean"]=r3(statistics.mean(v)) if v else None
    return out


def summarize(rows:list[dict])->dict[str,object]:
    starts=[r["start"] for r in rows];peaks=[r["peak"] for r in rows];ages=[r["peak_age"] for r in rows];growth=[r["growth"] for r in rows]
    start_desc=describe(starts,qs=(.01,.05,.10,.25,.50,.75,.90,.95,.99))
    start_desc["bands_pct"]={
        "<60":rate(rows,lambda r:r["start"]<60),"60-69":rate(rows,lambda r:60<=r["start"]<70),"70-79":rate(rows,lambda r:70<=r["start"]<80),
        "80-89":rate(rows,lambda r:80<=r["start"]<90),"90-99":rate(rows,lambda r:90<=r["start"]<100),"100-109":rate(rows,lambda r:100<=r["start"]<110),"110+":rate(rows,lambda r:r["start"]>=110)}
    peak_desc=describe(peaks);peak_desc["bands_pct"]={
        "<90":rate(rows,lambda r:r["peak"]<90),"90-99":rate(rows,lambda r:90<=r["peak"]<100),"100-109":rate(rows,lambda r:100<=r["peak"]<110),
        "110-119":rate(rows,lambda r:110<=r["peak"]<120),"120-129":rate(rows,lambda r:120<=r["peak"]<130),"130-139":rate(rows,lambda r:130<=r["peak"]<140),
        "140-149":rate(rows,lambda r:140<=r["peak"]<150),"150+":rate(rows,lambda r:r["peak"]>=150)}
    peak_age=describe(ages,qs=(.10,.50,.90));peak_age["bands_pct"]={"<=22":rate(rows,lambda r:r["peak_age"]<=22),"23-24":rate(rows,lambda r:23<=r["peak_age"]<=24),"25-26":rate(rows,lambda r:25<=r["peak_age"]<=26),"27-28":rate(rows,lambda r:27<=r["peak_age"]<=28),"29-30":rate(rows,lambda r:29<=r["peak_age"]<=30),"31-32":rate(rows,lambda r:31<=r["peak_age"]<=32),"33+":rate(rows,lambda r:r["peak_age"]>=33)}
    growth_desc=describe(growth,qs=(.10,.50,.90,.95,.99));growth_desc["bands_pct"]={"<0":rate(rows,lambda r:r["growth"]<0),"0-9":rate(rows,lambda r:0<=r["growth"]<10),"10-19":rate(rows,lambda r:10<=r["growth"]<20),"20-29":rate(rows,lambda r:20<=r["growth"]<30),"30-39":rate(rows,lambda r:30<=r["growth"]<40),"40+":rate(rows,lambda r:r["growth"]>=40)}
    start_specs=[("<65",lambda x:x<65),("65-69",lambda x:65<=x<70),("70-74",lambda x:70<=x<75),("75-79",lambda x:75<=x<80),("80-84",lambda x:80<=x<85),("85-89",lambda x:85<=x<90),("90-94",lambda x:90<=x<95),("95-99",lambda x:95<=x<100),("100+",lambda x:x>=100)]
    talent_specs=[("<70",lambda x:x<70),("70-89",lambda x:70<=x<90),("90-109",lambda x:90<=x<110),("110-129",lambda x:110<=x<130),("130-149",lambda x:130<=x<150),("150-179",lambda x:150<=x<180),("180+",lambda x:x>=180)]
    return {"starting":start_desc,"age_curve":age_curve(rows),"peak":peak_desc,"peak_age":peak_age,"growth":growth_desc,
            "starting_buckets":bucket(rows,lambda r:r["start"],start_specs),"talent_buckets":bucket(rows,lambda r:r["talent"],talent_specs),
            "talent_peak_corr":corr([r["talent"] for r in rows],peaks),"talent_growth_corr":corr([r["talent"] for r in rows],growth),"profiles":profile_analysis(rows),
            "instant_90":special_subset(rows,"start>=90",lambda r:r["start"]>=90),"instant_100":special_subset(rows,"start>=100",lambda r:r["start"]>=100),
            "low_start_high_talent":special_subset(rows,"start<75 & talent>=130",lambda r:r["start"]<75 and r["talent"]>=130),
            "high_start_low_talent":special_subset(rows,"start>=90 & talent<90",lambda r:r["start"]>=90 and r["talent"]<90),
            "stat_curves":stat_curves(rows),
            "extreme_peak_pct":{str(t):rate(rows,lambda r,t=t:r["peak"]>=t) for t in (120,130,140,150,170,200)},
            "extreme_stat_pct":{str(t):round(100*sum(1 for r in rows for s in TRACKED_STATS if r["stat_peak"][s]>=t)/(len(rows)*len(TRACKED_STATS)),4) for t in (150,180,200,250)},
            "retirement_age":describe([r["retirement_age"] for r in rows if r["retirement_age"] is not None],qs=(.10,.50,.90))}


def top_subset(rows:list[dict],field:str,q:float,name:str)->dict[str,object]:
    threshold=pct([r[field] for r in rows],q);return special_subset(rows,name,lambda r:r[field]>=threshold)


def npc_extra(rows:list[dict])->dict[str,object]:
    talent_specs=[("<70",lambda x:x<70),("70-89",lambda x:70<=x<90),("90-109",lambda x:90<=x<110),("110-129",lambda x:110<=x<130),("130-149",lambda x:130<=x<150),("150+",lambda x:x>=150)]
    drafted=[r for r in rows if r.get("draft_round") is not None]
    return {"start_top10":top_subset(rows,"start",.90,"start top 10%"),"start_top5":top_subset(rows,"start",.95,"start top 5%"),"start_top1":top_subset(rows,"start",.99,"start top 1%"),
            "talent_top10":top_subset(rows,"talent",.90,"talent top 10%"),"talent_top5":top_subset(rows,"talent",.95,"talent top 5%"),
            "drafted_subset":special_subset(rows,"actual production draft round assigned",lambda r:r.get("draft_round") is not None),
            "talent_buckets_npc":bucket(rows,lambda r:r["talent"],talent_specs),
            "low_start_high_talent_npc":special_subset(rows,"start<70 & talent>=130",lambda r:r["start"]<70 and r["talent"]>=130),
            "high_start80":special_subset(rows,"start>=80",lambda r:r["start"]>=80),"high_start85":special_subset(rows,"start>=85",lambda r:r["start"]>=85),"high_start90":special_subset(rows,"start>=90",lambda r:r["start"]>=90),
            "population_funnel":{"observed_n":len(rows),"age18":{"ge80_count":sum(r["start"]>=80 for r in rows),"ge90_count":sum(r["start"]>=90 for r in rows)},
                                 "peak":{f"ge{t}_count":sum(r["peak"]>=t for r in rows) for t in (90,100,110,120)},
                                 "per_10000":{f"peak_ge{t}":round(10000*sum(r["peak"]>=t for r in rows)/len(rows)) for t in (90,100,110,120)}}}


def odds_ratio(a_hits:int,a_n:int,b_hits:int,b_n:int)->float|None:
    # Haldane-Anscombe correction handles zero cells deterministically.
    ao=a_hits+.5;an=(a_n-a_hits)+.5;bo=b_hits+.5;bn=(b_n-b_hits)+.5
    return round((ao/an)/(bo/bn),4)


def cohort_compare(player:list[dict],npc:list[dict])->dict[str,object]:
    age={}
    for a in COMPARE_AGES:
        pv=[r["snaps"][a]["ability"] for r in player if a in r["snaps"]];nv=[r["snaps"][a]["ability"] for r in npc if a in r["snaps"]]
        age[str(a)]={"player_n":len(pv),"npc_n":len(nv),"player_mean":r3(statistics.mean(pv)) if pv else None,"npc_mean":r3(statistics.mean(nv)) if nv else None,
                     "mean_difference":r3(statistics.mean(pv)-statistics.mean(nv)) if pv and nv else None,"player_p50":r3(pct(pv,.5)),"npc_p50":r3(pct(nv,.5)),
                     "player_p90":r3(pct(pv,.9)),"npc_p90":r3(pct(nv,.9)),"npc_p95":r3(pct(nv,.95)),"npc_p99":r3(pct(nv,.99))}
    gaps={"start_mean_gap":r3(statistics.mean(r["start"] for r in player)-statistics.mean(r["start"] for r in npc)),"peak_mean_gap":r3(statistics.mean(r["peak"] for r in player)-statistics.mean(r["peak"] for r in npc)),
          "p90_peak_gap":r3(pct([r["peak"] for r in player],.9)-pct([r["peak"] for r in npc],.9))}
    sg=float(gaps["start_mean_gap"]);pg=float(gaps["peak_mean_gap"])
    gaps["classification"]="growth compression" if pg<sg*.8 else "growth amplification" if pg>sg*1.2 else "gap preserved"
    probs={}
    for t in (100,110,120):
        ph=sum(r["peak"]>=t for r in player);nh=sum(r["peak"]>=t for r in npc)
        probs[str(t)]={"player_pct":round(100*ph/len(player),3),"npc_pct":round(100*nh/len(npc),3),"odds_ratio":odds_ratio(ph,len(player),nh,len(npc))}
    return {"age_curves":age,"gaps":gaps,"peak_probabilities":probs}


def chart_samples(groups:dict[str,list[dict]],limit:int=5000)->list[dict[str,object]]:
    out=[]
    for key,rows in groups.items():
        step=max(1,len(rows)//limit)
        for r in rows[::step][:limit]:out.append({"group":key,"start":round(r["start"],4),"talent":r["talent"],"profile":r["profile"],"peak":round(r["peak"],4),"peak_age":r["peak_age"],"growth":round(r["growth"],4)})
    return out


def write_csv(path:Path,rows:list[dict[str,object]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=("group","start","talent","profile","peak","peak_age","growth"));w.writeheader();w.writerows(rows)


def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument("--pure",type=int,default=20000);ap.add_argument("--full",type=int,default=5000);ap.add_argument("--npc-pure",type=int,default=20000);ap.add_argument("--npc-full",type=int,default=5000);ap.add_argument("--seed",type=int,default=DEFAULT_MASTER_SEED);ap.add_argument("--workers",type=int,default=max(1,min(2,os.cpu_count() or 1)));ap.add_argument("--json",default="reports/current_generation_growth_validation.json");ap.add_argument("--csv",default="reports/current_generation_growth_validation_samples.csv");a=ap.parse_args()
    pp=run_many("pure","player",a.pure,a.seed,0,a.workers);np=run_many("pure","npc",a.npc_pure,a.seed,100000,a.workers)
    pf=run_many("full","player",a.full,a.seed,200000,a.workers);nf=run_many("full","npc",a.npc_full,a.seed,300000,a.workers)
    groups={"player_pure":pp,"npc_pure":np,"player_full":pf,"npc_full":nf}
    summaries={k:summarize(v) for k,v in groups.items()}
    report={"source":{"branch":SOURCE_BRANCH,"sha":SOURCE_SHA},"seed":a.seed,"sample_size":{k:len(v) for k,v in groups.items()},"positions":"cycled uniformly across config.POSITIONS, matching tools/draft_calibration.py",
            "mode_notes":{"pure":"production generation + development profile + Talent + production apply_season_growth; traits cleared; coach/experience/event/injury absent; fixed through age 45",
                          "full_player":"production Player.random + production CareerEngine, including high school/draft, coaches, playing time, experience, traits, events, injuries, breakthroughs, aging and retirement",
                          "full_npc":"generate_high_school_npc_stats with the same profile/traits/breakthrough-affinity generation as Player.random, then the same production CareerEngine; no hidden NPC-only growth assumptions"},
            "summaries":summaries,"npc_full_extra":npc_extra(nf),"compare_pure":cohort_compare(pp,np),"compare_full":cohort_compare(pf,nf),
            "old_v04":{"starting_mean":70.207,"peak_mean":102.086,"peak_p90":116.729,"peak_p95":123.328,"peak_p99":133.273,"mean_peak_age":31.277,"talent_peak_corr":0.511,"sample_careers":300,"source":"docs/balance-v0.4.md"}}
    jp=Path(a.json);jp.parent.mkdir(parents=True,exist_ok=True);jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_csv(Path(a.csv),chart_samples(groups))
    print(json.dumps({"source":report["source"],"sample_size":report["sample_size"],"player_full_peak":summaries["player_full"]["peak"],"npc_full_peak":summaries["npc_full"]["peak"],"compare_full":report["compare_full"]},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
