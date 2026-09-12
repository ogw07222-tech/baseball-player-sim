#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical_defense import build_defensive_opportunity, resolve_defensive_shadow
from src.hitting.stadium import WallInteraction
from src.hitting.trajectory import BattedBallTrajectory
from src.rng import RNG


def pct(n,d): return n/d if d else 0.0

def q(xs,p):
    if not xs: return 0.0
    ys=sorted(xs); return float(ys[min(len(ys)-1,max(0,round((len(ys)-1)*p)))])

def dist(xs, probs=(.10,.25,.50,.75,.90,.95,.99)):
    if not xs: return {"n":0}
    out={"n":len(xs),"mean":statistics.mean(xs),"median":q(xs,.5),"min":min(xs),"max":max(xs)}
    for p in probs: out[f"p{int(p*100)}"]=q(xs,p)
    return out

def probdist(xs):
    d=dist(xs,(.01,.05,.10,.25,.50,.75,.90,.95,.99))
    d["sat_zero_rate"]=pct(sum(x<=1e-12 for x in xs),len(xs)); d["sat_one_rate"]=pct(sum(x>=1-1e-12 for x in xs),len(xs))
    return d

def bucket(v,cuts,labels):
    for c,l in zip(cuts,labels):
        if v<c:return l
    return labels[-1]

def traj(x,y,time=4.0,cls="fly_ball",valid=True):
    r=math.hypot(x,y)
    return BattedBallTrajectory(horizontal_distance_ft=r,hang_time_s=time,apex_height_ft=100.0,landing_x_ft=x,landing_y_ft=y,trajectory_class=cls,apex_distance_fraction=.5,valid=valid)

def wall(radius=500.0,height=10.0,reaches=False,clears=False,hr=False,contact=False):
    bh=20.0 if reaches else 0.0
    return WallInteraction(stadium_id="v05",wall_radius_ft=radius,wall_height_ft=height,reaches_wall=reaches,ball_height_at_wall_ft=bh,clearance_ft=(bh-height if reaches else -height),clears_wall=clears,wall_contact=contact,physical_hr_shadow=hr)

def controlled_op(x,y,*,time=4.0,rating=100.0,cls="fly_ball",radius=500.0,is_fair=True):
    return build_defensive_opportunity(trajectory=traj(x,y,time,cls),wall_interaction=wall(radius),defender_rating=rating,is_fair_shadow=is_fair)

def summarize_ops(rows):
    valid=[r for r in rows if r["op"].valid]
    reasons=Counter(r["op"].opportunity_type for r in rows if not r["op"].valid)
    cls=defaultdict(lambda:Counter(n=0,valid=0))
    for r in rows:
        c=r["state"].trajectory.trajectory_class if r["state"].trajectory else "missing"
        cls[c]["n"]+=1; cls[c]["valid"]+=int(r["op"].valid)
    return {"total":len(rows),"valid":len(valid),"valid_rate":pct(len(valid),len(rows)),"invalid_rate":1-pct(len(valid),len(rows)),"invalid_reasons":dict(reasons),"trajectory_class_valid_rate":{k:{"n":v["n"],"valid":v["valid"],"rate":pct(v["valid"],v["n"])} for k,v in cls.items()}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pa',type=int,default=200000); ap.add_argument('--seed',type=int,default=20260912); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    rng=RNG(a.seed); hitter=HitterSnapshot(100,100,100,100); pitcher=PitcherSnapshot(100,100,100)
    rows=[]; outcomes=Counter()
    for _ in range(a.pa):
        out=HittingEngine(hitter,pitcher,100.0,rng).simulate_plate_appearance(); outcomes[out.result]+=1
        if out.batted_ball and out.batted_ball.physical_state:
            s=out.batted_ball.physical_state; op=s.defensive_opportunity; res=s.defensive_resolution
            rows.append({"state":s,"op":op,"res":res,"legacy":out.result})
    valid=[r for r in rows if r["op"] and r["op"].valid]

    # ownership + controlled boundaries
    owners=Counter(r["op"].defender_position for r in valid)
    spray_owners=defaultdict(Counter)
    for r in valid:
        sp=r["state"].spray_angle
        b=bucket(sp,[-30,-15,-5,5,15,30],["<-30","-30:-15","-15:-5","-5:5","5:15","15:30",">=30"])
        spray_owners[b][r["op"].defender_position]+=1
    boundary={}
    for ang in (-15.001,-15.0,-14.999,14.999,15.0,15.001):
        rr=300; x=rr*math.sin(math.radians(ang)); y=rr*math.cos(math.radians(ang)); op=controlled_op(x,y)
        boundary[str(ang)]={"owner":op.defender_position,"distance":op.required_distance_ft,"direction":op.direction_class,"p":op.adjusted_catch_probability}

    # distributions
    req=[r["op"].required_distance_ft for r in valid]; tm=[r["op"].opportunity_time_s for r in valid]
    basep=[r["op"].baseline_catch_probability for r in valid]; adjp=[r["op"].adjusted_catch_probability for r in valid]
    posstats={}; nearstats={}
    for pos in ("LF","CF","RF"):
        z=[r for r in valid if r["op"].defender_position==pos]
        posstats[pos]={"n":len(z),"required_distance_ft":dist([r["op"].required_distance_ft for r in z]),"opportunity_time_s":dist([r["op"].opportunity_time_s for r in z]),"baseline_p":probdist([r["op"].baseline_catch_probability for r in z]),"adjusted_p":probdist([r["op"].adjusted_catch_probability for r in z])}
    for nw in (False,True):
        z=[r for r in valid if r["op"].near_wall==nw]
        nearstats[str(nw)]={"n":len(z),"rate":pct(len(z),len(valid)),"required_distance_ft":dist([r["op"].required_distance_ft for r in z]),"opportunity_time_s":dist([r["op"].opportunity_time_s for r in z]),"adjusted_p":probdist([r["op"].adjusted_catch_probability for r in z])}
    dirs=Counter(r["op"].direction_class for r in valid)

    by_class={}; by_dir={}; by_dist={}; by_time={}
    for cls in ("line_drive","fly_ball","popup"):
        z=[r["op"].adjusted_catch_probability for r in valid if r["state"].trajectory.trajectory_class==cls]; by_class[cls]=probdist(z)
    for d in ("in","lateral","back"):
        z=[r["op"].adjusted_catch_probability for r in valid if r["op"].direction_class==d]; by_dir[d]=probdist(z)
    for label,lo,hi in [("0-25",0,25),("25-50",25,50),("50-75",50,75),("75-100",75,100),("100-150",100,150),("150+",150,1e9)]:
        z=[r["op"].adjusted_catch_probability for r in valid if lo<=r["op"].required_distance_ft<hi]; by_dist[label]={"n":len(z),"mean_p":statistics.mean(z) if z else 0.0,"median_p":q(z,.5)}
    for label,lo,hi in [("0-1",0,1),("1-2",1,2),("2-3",2,3),("3-4",3,4),("4-5",4,5),("5-6",5,6),("6+",6,1e9)]:
        z=[r["op"].adjusted_catch_probability for r in valid if lo<=r["op"].opportunity_time_s<hi]; by_time[label]={"n":len(z),"mean_p":statistics.mean(z) if z else 0.0,"median_p":q(z,.5)}

    # mirror
    mirrors=[]
    for rr in (220,260,300,340):
        for ang in (18,25,35,42):
            x=rr*math.sin(math.radians(ang)); y=rr*math.cos(math.radians(ang))
            l=controlled_op(-x,y,time=4.0); r=controlled_op(x,y,time=4.0)
            mirrors.append({"radius":rr,"angle":ang,"owners":[l.defender_position,r.defender_position],"distance_delta":abs(l.required_distance_ft-r.required_distance_ft),"direction_equal":l.direction_class==r.direction_class,"baseline_delta":abs(l.baseline_catch_probability-r.baseline_catch_probability),"adjusted_delta":abs(l.adjusted_catch_probability-r.adjusted_catch_probability)})
    mirror_pass=all(x["owners"]==["LF","RF"] and x["distance_delta"]<1e-9 and x["direction_equal"] and x["baseline_delta"]<1e-12 and x["adjusted_delta"]<1e-12 for x in mirrors)

    # monotonicity grids
    p_dist=[controlled_op(0,315+d,time=4).adjusted_catch_probability for d in range(15,151,5)]
    p_time=[controlled_op(0,365,time=t).adjusted_catch_probability for t in [0.5,1,1.5,2,3,4,5,6,7]]
    p_rating=[controlled_op(0,365,time=4,rating=r).adjusted_catch_probability for r in range(40,181,5)]
    op_in=controlled_op(0,265,time=3.5); op_lat=controlled_op(50,315,time=3.5); op_back=controlled_op(0,365,time=3.5)
    tr=traj(0,340,time=4); far=build_defensive_opportunity(trajectory=tr,wall_interaction=wall(500),defender_rating=100,is_fair_shadow=True); near=build_defensive_opportunity(trajectory=tr,wall_interaction=wall(350),defender_rating=100,is_fair_shadow=True)
    mono={"distance_nonincreasing":all(b<=a+1e-15 for a,b in zip(p_dist,p_dist[1:])),"time_nondecreasing":all(b+1e-15>=a for a,b in zip(p_time,p_time[1:])),"rating_nondecreasing":all(b+1e-15>=a for a,b in zip(p_rating,p_rating[1:])),"direction_order":op_back.adjusted_catch_probability<=op_lat.adjusted_catch_probability<=op_in.adjusted_catch_probability,"near_wall_not_easier":near.adjusted_catch_probability<=far.adjusted_catch_probability,"direction_p":{"back":op_back.adjusted_catch_probability,"lateral":op_lat.adjusted_catch_probability,"in":op_in.adjusted_catch_probability},"near_wall_p":near.adjusted_catch_probability,"nonwall_p":far.adjusted_catch_probability}

    # rating sensitivity on frozen valid opportunities and frozen roll
    ratings={}
    for rating in (60,80,100,120,140):
        ps=[]; outs=0; diff=Counter(); conv=Counter()
        for rr in valid:
            s=rr["state"]; old=rr["op"]; roll=rr["res"].roll
            op=build_defensive_opportunity(trajectory=s.trajectory,wall_interaction=s.wall_interaction,defender_rating=float(rating),is_fair_shadow=s.is_fair)
            if not op.valid: continue
            ps.append(op.adjusted_catch_probability); out=resolve_defensive_shadow(op,roll=roll).physical_out_shadow; outs+=int(out)
            cat="routine" if old.baseline_catch_probability>=.8 else ("borderline" if old.baseline_catch_probability>=.2 else "extreme")
            diff[cat]+=1; conv[cat]+=int(out)
        ratings[str(rating)]={"mean_p":statistics.mean(ps),"median_p":q(ps,.5),"out_rate":pct(outs,len(ps)),"routine_conversion":pct(conv["routine"],diff["routine"]),"borderline_conversion":pct(conv["borderline"],diff["borderline"]),"extreme_conversion":pct(conv["extreme"],diff["extreme"]),"counts":dict(diff)}

    # impossible/invalid pack
    cases={}
    def check(name,op):
        res=resolve_defensive_shadow(op,roll=0.0); cases[name]={"op_valid":op.valid,"type":op.opportunity_type,"res_valid":res.valid,"roll":res.roll,"out":res.physical_out_shadow,"p":res.catch_probability}
    check("trajectory_none",build_defensive_opportunity(trajectory=None,wall_interaction=wall(),defender_rating=100,is_fair_shadow=True))
    check("trajectory_invalid",build_defensive_opportunity(trajectory=traj(0,300,valid=False),wall_interaction=wall(),defender_rating=100,is_fair_shadow=True))
    check("ground_like",build_defensive_opportunity(trajectory=traj(0,120,cls="ground_like"),wall_interaction=wall(),defender_rating=100,is_fair_shadow=True))
    check("shadow_foul",build_defensive_opportunity(trajectory=traj(0,300),wall_interaction=wall(),defender_rating=100,is_fair_shadow=False))
    check("missing_wall",build_defensive_opportunity(trajectory=traj(0,300),wall_interaction=None,defender_rating=100,is_fair_shadow=True))
    check("over_wall",build_defensive_opportunity(trajectory=traj(0,380),wall_interaction=wall(350,reaches=True,clears=True,hr=True),defender_rating=100,is_fair_shadow=True))
    check("wall_intersection",build_defensive_opportunity(trajectory=traj(0,350),wall_interaction=wall(350,reaches=True,contact=True),defender_rating=100,is_fair_shadow=True))
    check("nonfinite_rating",build_defensive_opportunity(trajectory=traj(0,300),wall_interaction=wall(),defender_rating=float('nan'),is_fair_shadow=True))
    invalid_pass=all((not v["op_valid"]) and (not v["res_valid"]) and v["roll"] is None and (not v["out"]) for v in cases.values())

    # shadow vs legacy disagreement on valid airborne opportunities
    cm=Counter(); detail_class=defaultdict(Counter); detail_dir=defaultdict(Counter); detail_pos=defaultdict(Counter); detail_wall=defaultdict(Counter); detail_dist=defaultdict(Counter); detail_time=defaultdict(Counter)
    for rr in valid:
        legacy=rr["legacy"]=="out"; phys=rr["res"].physical_out_shadow
        key=("LO" if legacy else "LS")+("_PO" if phys else "_PS"); cm[key]+=1
        disagree=legacy!=phys
        c=rr["state"].trajectory.trajectory_class; d=rr["op"].direction_class; p=rr["op"].defender_position; nw=str(rr["op"].near_wall)
        db=bucket(rr["op"].required_distance_ft,[25,50,75,100,150],["<25","25-50","50-75","75-100","100-150","150+"])
        tb=bucket(rr["op"].opportunity_time_s,[1,2,3,4,5,6],["<1","1-2","2-3","3-4","4-5","5-6","6+"])
        for m,k in ((detail_class,c),(detail_dir,d),(detail_pos,p),(detail_wall,nw),(detail_dist,db),(detail_time,tb)):
            m[k]["n"]+=1; m[k]["disagree"]+=int(disagree)
    fmt=lambda m:{k:{"n":v["n"],"disagree_rate":pct(v["disagree"],v["n"])} for k,v in m.items()}

    result={"seed":a.seed,"pa":a.pa,"bip_states":len(rows),"outcomes":dict(outcomes),"opportunity_population":summarize_ops(rows),"ownership":{"shares":{k:pct(v,len(valid)) for k,v in owners.items()},"counts":dict(owners),"spray_buckets":{k:dict(v) for k,v in spray_owners.items()},"boundary_probe":boundary},"mirror":{"pass":mirror_pass,"cases":mirrors},"physical_distributions":{"required_distance_ft":dist(req),"opportunity_time_s":dist(tm),"direction_shares":{k:pct(v,len(valid)) for k,v in dirs.items()},"near_wall":nearstats,"by_position":posstats},"catch_probability":{"baseline":probdist(basep),"adjusted":probdist(adjp),"by_trajectory_class":by_class,"by_direction":by_dir,"by_distance_bucket":by_dist,"by_time_bucket":by_time},"monotonicity":mono,"rating_sensitivity":ratings,"impossible_out":{"pass":invalid_pass,"cases":cases},"determinism":{"parent_rng_state":rng.get_state()},"shadow_disagreement":{"matrix":dict(cm),"overall_disagreement_rate":pct(cm["LO_PS"]+cm["LS_PO"],sum(cm.values())),"by_class":fmt(detail_class),"by_direction":fmt(detail_dir),"by_position":fmt(detail_pos),"by_near_wall":fmt(detail_wall),"by_distance":fmt(detail_dist),"by_time":fmt(detail_time)}}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__': main()
