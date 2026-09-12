#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical import BattedBallState
from src.hitting.stadium import (
    DAEJEON_ASYMMETRIC_2026,
    GENERIC_ENGINEERING_BASELINE,
    GOCHEOK_LIKE_2026,
    JAMSIL_LIKE_2026,
    QUALITY_APPROXIMATED,
    StadiumGeometry,
    resolve_wall_interaction,
)
from src.hitting.trajectory import BattedBallTrajectory, generate_batted_ball_trajectory
from src.rng import RNG


def pct(n, d): return n / d if d else 0.0

def percentile(values, q):
    xs=sorted(values)
    if not xs: return 0.0
    return float(xs[min(len(xs)-1,max(0,round((len(xs)-1)*q)))])

def dist(values):
    if not values: return {}
    return {"n":len(values),"mean":statistics.mean(values),"sd":statistics.pstdev(values),
            "p1":percentile(values,.01),"p5":percentile(values,.05),"p25":percentile(values,.25),
            "p50":percentile(values,.50),"p75":percentile(values,.75),"p95":percentile(values,.95),
            "p99":percentile(values,.99),"min":min(values),"max":max(values)}

def corpus(seed, pa):
    rng=RNG(seed); states=[]; outcomes=Counter()
    hitter=HitterSnapshot(100,100,100,100); pitcher=PitcherSnapshot(100,100,100)
    for _ in range(pa):
        out=HittingEngine(hitter,pitcher,100.0,rng).simulate_plate_appearance()
        outcomes[out.result]+=1
        if out.batted_ball is not None and out.batted_ball.physical_state is not None:
            states.append(out.batted_ball.physical_state)
    return states, outcomes

def sector(angle):
    if angle < -27: return "LF"
    if angle < -9: return "LC"
    if angle <= 9: return "CF"
    if angle <= 27: return "RC"
    return "RF"

def stadium_summary(states, stadium):
    counts=Counter(); sec=defaultdict(Counter); clearances=[]; radii=[]; heights=[]
    for s in states:
        if s.trajectory is None: continue
        w=resolve_wall_interaction(trajectory=s.trajectory,spray_angle_deg=s.spray_angle,is_fair_shadow=s.is_fair,stadium=stadium)
        counts["n"]+=1; counts["fair"]+=int(s.is_fair); counts["reached"]+=int(w.reaches_wall)
        counts["cleared"]+=int(w.clears_wall); counts["hr"]+=int(w.physical_hr_shadow)
        counts["contact"]+=int(w.wall_contact); counts["below_or_contact"]+=int(w.reaches_wall and not w.clears_wall)
        counts["near_wall_10ft"]+=int(abs(s.trajectory.horizontal_distance_ft-w.wall_radius_ft)<=10.0)
        if w.reaches_wall: clearances.append(w.clearance_ft)
        radii.append(w.wall_radius_ft); heights.append(w.wall_height_ft)
        c=sec[sector(s.spray_angle)]; c["n"]+=1; c["reached"]+=int(w.reaches_wall); c["hr"]+=int(w.physical_hr_shadow); c["fair"]+=int(s.is_fair)
    return {"stadium_id":stadium.stadium_id,"source_quality":stadium.source_quality,"is_real":stadium.is_real_stadium,
            "n":counts["n"],"wall_reached_pct":pct(counts["reached"],counts["n"]),"clears_wall_pct":pct(counts["cleared"],counts["n"]),
            "below_or_contact_pct":pct(counts["below_or_contact"],counts["n"]),"wall_contact_pct":pct(counts["contact"],counts["n"]),
            "near_wall_10ft_pct":pct(counts["near_wall_10ft"],counts["n"]),"physical_hr_shadow_pct":pct(counts["hr"],counts["n"]),
            "physical_hr_shadow_per_fair":pct(counts["hr"],counts["fair"]),"clearance_ft_reached":dist(clearances),
            "wall_radius_ft":dist(radii),"wall_height_ft":dist(heights),
            "sectors":{k:{"n":v["n"],"wall_reached_pct":pct(v["reached"],v["n"]),"hr_shadow_pct":pct(v["hr"],v["n"]),"hr_shadow_per_fair":pct(v["hr"],v["fair"])} for k,v in sorted(sec.items())}}

def uniform_stadium(name,radius,height):
    return StadiumGeometry(stadium_id=name,season=None,is_real_stadium=False,source_quality=QUALITY_APPROXIMATED,
        wall_radius_ft=(radius,)*5,wall_height_ft=(height,)*5)

def sensitivity(states):
    base=uniform_stadium("base",350.0,8.0); tall=uniform_stadium("tall",350.0,16.0); far=uniform_stadium("far",375.0,8.0)
    def hrs(st):
        return sum(resolve_wall_interaction(trajectory=s.trajectory,spray_angle_deg=s.spray_angle,is_fair_shadow=s.is_fair,stadium=st).physical_hr_shadow for s in states if s.trajectory)
    a,b,c=hrs(base),hrs(tall),hrs(far)
    return {"base_hr":a,"higher_wall_hr":b,"farther_wall_hr":c,"height_nonincreasing":b<=a,"radius_nonincreasing":c<=a}

def impossible_checks():
    deep=BattedBallTrajectory(horizontal_distance_ft=430,hang_time_s=5,apex_height_ft=110,landing_x_ft=0,landing_y_ft=430,trajectory_class="fly_ball",apex_distance_fraction=.5,valid=True)
    invalid=BattedBallTrajectory(horizontal_distance_ft=430,hang_time_s=5,apex_height_ft=110,landing_x_ft=0,landing_y_ft=430,trajectory_class="fly_ball",apex_distance_fraction=.5,valid=False)
    short=BattedBallTrajectory(horizontal_distance_ft=250,hang_time_s=3,apex_height_ft=80,landing_x_ft=0,landing_y_ft=250,trajectory_class="fly_ball",apex_distance_fraction=.5,valid=True)
    st=uniform_stadium("test",350,8)
    short_w=resolve_wall_interaction(trajectory=short,spray_angle_deg=0,is_fair_shadow=True,stadium=st)
    invalid_w=resolve_wall_interaction(trajectory=invalid,spray_angle_deg=0,is_fair_shadow=True,stadium=st)
    low=uniform_stadium("high",350,100); low_w=resolve_wall_interaction(trajectory=deep,spray_angle_deg=0,is_fair_shadow=True,stadium=low)
    neg_rejected=False; nonfinite_rejected=False
    try: uniform_stadium("neg",-1,8)
    except ValueError: neg_rejected=True
    try: uniform_stadium("nan",math.nan,8)
    except ValueError: nonfinite_rejected=True
    return {"hr_without_wall_reach":bool(short_w.physical_hr_shadow),"hr_below_wall":bool(low_w.physical_hr_shadow),
            "invalid_trajectory_hr":bool(invalid_w.physical_hr_shadow),"negative_radius_rejected":neg_rejected,"nonfinite_geometry_rejected":nonfinite_rejected}

def mirror_check():
    def state(spray):
        return BattedBallState(exit_velocity=100,launch_angle=29,timing=0,spray_angle=spray,is_fair=True,contact_quality=.7,pitch_location_x=0,pitch_location_y=0,batter_side="R")
    a=generate_batted_ball_trajectory(state(-30)); b=generate_batted_ball_trajectory(state(30))
    wa=resolve_wall_interaction(trajectory=a,spray_angle_deg=-30,is_fair_shadow=True,stadium=GENERIC_ENGINEERING_BASELINE)
    wb=resolve_wall_interaction(trajectory=b,spray_angle_deg=30,is_fair_shadow=True,stadium=GENERIC_ENGINEERING_BASELINE)
    return {"radius_equal":wa.wall_radius_ft==wb.wall_radius_ft,"height_equal":wa.wall_height_ft==wb.wall_height_ft,
            "ball_height_equal":abs(wa.ball_height_at_wall_ft-wb.ball_height_at_wall_ft)<1e-12,"hr_equal":wa.physical_hr_shadow==wb.physical_hr_shadow}

def height_profile_smoke():
    s=BattedBallState(exit_velocity=100,launch_angle=29,timing=0,spray_angle=0,is_fair=True,contact_quality=.7,pitch_location_x=0,pitch_location_y=0,batter_side="R")
    t=generate_batted_ball_trajectory(s); peak=t.horizontal_distance_ft*t.apex_distance_fraction
    vals={"launch":t.height_at_horizontal_distance(0),"apex":t.height_at_horizontal_distance(peak),"stored_apex":t.apex_height_ft,
          "impact":t.height_at_horizontal_distance(t.horizontal_distance_ft),"beyond":t.height_at_horizontal_distance(t.horizontal_distance_ft+10)}
    vals["finite"]=all(math.isfinite(x) for x in vals.values() if isinstance(x,(int,float)))
    return vals

def main():
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=20260911); p.add_argument("--pa",type=int,default=200000); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    states,outcomes=corpus(a.seed+7000000,a.pa)
    parks=[GENERIC_ENGINEERING_BASELINE,JAMSIL_LIKE_2026,GOCHEOK_LIKE_2026,DAEJEON_ASYMMETRIC_2026]
    result={"seed":a.seed,"pa":a.pa,"bip_states":len(states),"legacy_outcomes":dict(outcomes),
            "parks":{p.stadium_id:stadium_summary(states,p) for p in parks},"sensitivity":sensitivity(states),
            "impossible":impossible_checks(),"mirror":mirror_check(),"height_profile":height_profile_smoke(),
            "production_attachment":{"all_have_trajectory":all(s.trajectory is not None for s in states),"all_have_wall":all(s.wall_interaction is not None for s in states),
                "generic_only":all(s.wall_interaction and s.wall_interaction.stadium_id=="generic_neutral_v1" for s in states)},
            "determinism":{"same_wall_exact":resolve_wall_interaction(trajectory=states[0].trajectory,spray_angle_deg=states[0].spray_angle,is_fair_shadow=states[0].is_fair,stadium=GENERIC_ENGINEERING_BASELINE)==resolve_wall_interaction(trajectory=states[0].trajectory,spray_angle_deg=states[0].spray_angle,is_fair_shadow=states[0].is_fair,stadium=GENERIC_ENGINEERING_BASELINE)}}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
