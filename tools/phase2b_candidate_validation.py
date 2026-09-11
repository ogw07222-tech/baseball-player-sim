#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from src.hitting.physical import BattedBallState
from src.hitting.trajectory import generate_batted_ball_trajectory
from tools.phase2a_physical_distribution_validation import production_states


def percentile(values, q):
    xs = sorted(values)
    if not xs:
        return 0.0
    return float(xs[min(len(xs)-1, max(0, round((len(xs)-1)*q)))])


def dist(values):
    if not values:
        return {}
    return {"n":len(values),"mean":statistics.mean(values),"sd":statistics.pstdev(values),
            "p1":percentile(values,.01),"p5":percentile(values,.05),"p25":percentile(values,.25),
            "p50":percentile(values,.50),"p75":percentile(values,.75),"p95":percentile(values,.95),
            "p99":percentile(values,.99),"min":min(values),"max":max(values)}


def state(ev, la, spray=0.0, side="R"):
    return BattedBallState(exit_velocity=float(ev),launch_angle=float(la),timing=0.0,
        spray_angle=float(spray),is_fair=abs(float(spray))<=45.0,contact_quality=.70,
        pitch_location_x=0.0,pitch_location_y=0.0,batter_side=side)


def row(ev,la,spray=0.0):
    t=generate_batted_ball_trajectory(state(ev,la,spray))
    return {"ev_mph":ev,"la_deg":la,"spray_deg":spray,
        "carry_ft":t.horizontal_distance_ft,"hang_s":t.hang_time_s,"apex_ft":t.apex_height_ft,
        "x_ft":t.landing_x_ft,"y_ft":t.landing_y_ft,"class":t.trajectory_class}


def production_summary(seed,pa):
    states,_=production_states(seed,pa,"R")
    trajectories=[s.trajectory for s in states if s.trajectory is not None]
    carry=[t.horizontal_distance_ft for t in trajectories]
    hang=[t.hang_time_s for t in trajectories]
    apex=[t.apex_height_ft for t in trajectories]
    x=[t.landing_x_ft for t in trajectories]
    y=[t.landing_y_ft for t in trajectories]
    radial=[math.hypot(t.landing_x_ft,t.landing_y_ft) for t in trajectories]
    return {"states":len(states),"trajectories":len(trajectories),
        "carry_ft":dist(carry),"hang_s":dist(hang),"apex_ft":dist(apex),
        "landing_x_ft":dist(x),"landing_y_ft":dist(y),"radial_ft":dist(radial),
        "carry_ge_500_rate":sum(v>=500 for v in carry)/len(carry),
        "carry_ge_600_rate":sum(v>=600 for v in carry)/len(carry),
        "hang_ge_9_rate":sum(v>=9 for v in hang)/len(hang),
        "apex_at_max_guard_rate":sum(v>=259.999999 for v in apex)/len(apex)}


def grid():
    return [row(ev,la) for ev in [80,90,100,110] for la in [-10,0,10,20,30,40,50]]


def low_grid():
    return [row(ev,la) for ev in [80,90,100,110] for la in [-15,-10,-5,0]]


def high_grid():
    return [row(ev,la) for ev in [80,90,100,110] for la in [40,50,60]]


def coordinate_grid():
    return [row(100,30,s) for s in [-30,-15,0,15,30]]


def angle_sweep_100():
    return [row(100,la) for la in range(0,61)]


def main():
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=20260911); p.add_argument("--pa",type=int,default=200000); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    g=grid(); low=low_grid(); high=high_grid(); coords=coordinate_grid(); sweep=angle_sweep_100()
    anchor=row(100,29)
    best=max(sweep,key=lambda r:r["carry_ft"])
    same=generate_batted_ball_trajectory(state(100,29,15))==generate_batted_ball_trajectory(state(100,29,15))
    mirror_pos=row(100,30,30); mirror_neg=row(100,30,-30); center=row(100,30,0)
    result={"seed":a.seed,"production_pa":a.pa,"production":production_summary(a.seed+7000000,a.pa),
        "ev_la_grid":g,"ground_low_la":low,"high_la":high,"coordinates":coords,
        "anchor_100_29":anchor,"angle_sweep_100_best":{"la_deg":best["la_deg"],"carry_ft":best["carry_ft"]},
        "vacuum_artifact_checks":{"anchor_vs_397_ft_delta":anchor["carry_ft"]-397.0,"anchor_vs_571_ft_delta":anchor["carry_ft"]-571.0,"carry_45_ft":row(100,45)["carry_ft"],"best_angle_deg":best["la_deg"]},
        "coordinate_invariants":{"radial_pos":mirror_pos["carry_ft"],"radial_neg":mirror_neg["carry_ft"],"x_sum":mirror_pos["x_ft"]+mirror_neg["x_ft"],"y_delta":mirror_pos["y_ft"]-mirror_neg["y_ft"],"center_x":center["x_ft"]},
        "deterministic_same_state_exact":same}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__": main()
