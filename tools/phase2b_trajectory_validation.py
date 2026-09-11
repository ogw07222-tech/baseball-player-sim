#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import math
import statistics
from dataclasses import asdict
from pathlib import Path

from src.hitting.physical import BattedBallState


def percentile(values, q):
    if not values:
        return 0.0
    xs = sorted(values)
    i = min(len(xs)-1, max(0, round((len(xs)-1)*q)))
    return float(xs[i])


def dist(values):
    if not values:
        return {}
    return {
        "n": len(values), "mean": statistics.mean(values), "sd": statistics.pstdev(values),
        "p1": percentile(values,.01), "p5": percentile(values,.05),
        "p25": percentile(values,.25), "p50": percentile(values,.50),
        "p75": percentile(values,.75), "p95": percentile(values,.95),
        "p99": percentile(values,.99), "min": min(values), "max": max(values),
    }


def _num(obj, names):
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if isinstance(v, (int, float)):
                return float(v), n
    return None, None


def _normalize_output(obj):
    carry, carry_name = _num(obj, ["carry_distance_ft","carry_ft","distance_ft","carry_distance_m","carry_m","distance_m","radial_distance_ft","radial_distance_m"])
    hang, hang_name = _num(obj, ["hang_time_s","ground_flight_time_s","flight_time_s","hang_time","flight_time"])
    apex, apex_name = _num(obj, ["apex_height_ft","apex_ft","max_height_ft","apex_height_m","apex_m","max_height_m"])
    x, x_name = _num(obj, ["landing_x_ft","x_ft","landing_x_m","x_m","landing_x"])
    y, y_name = _num(obj, ["landing_y_ft","y_ft","landing_y_m","y_m","landing_y","landing_depth_ft","landing_depth_m"])

    def to_ft(v, name):
        if v is None:
            return None
        return v * 3.280839895 if name and name.endswith("_m") else v

    carry_ft = to_ft(carry, carry_name)
    apex_ft = to_ft(apex, apex_name)
    x_ft = to_ft(x, x_name)
    y_ft = to_ft(y, y_name)
    if carry_ft is None and x_ft is not None and y_ft is not None:
        carry_ft = math.hypot(x_ft, y_ft)
    return {
        "carry_ft": carry_ft,
        "hang_s": hang,
        "apex_ft": apex_ft,
        "x_ft": x_ft,
        "y_ft": y_ft,
        "raw_type": f"{type(obj).__module__}.{type(obj).__name__}",
    }


def resolve_adapter():
    try:
        module = importlib.import_module("src.hitting.trajectory")
    except ModuleNotFoundError:
        return None, "src.hitting.trajectory not implemented"
    for name in ("generate_trajectory", "generate_trajectory_state", "solve_trajectory", "trajectory_from_batted_ball"):
        fn = getattr(module, name, None)
        if callable(fn):
            return fn, name
    return None, "no supported trajectory function found"


def make_state(ev, la, spray=0.0, side="R"):
    return BattedBallState(
        exit_velocity=float(ev), launch_angle=float(la), timing=0.0,
        spray_angle=float(spray), is_fair=abs(float(spray)) <= 45.0,
        contact_quality=0.70, pitch_location_x=0.0, pitch_location_y=0.0,
        batter_side=side,
    )


def call_trajectory(fn, state):
    sig = inspect.signature(fn)
    kwargs = {}
    params = sig.parameters
    if "state" in params:
        kwargs["state"] = state
    elif "batted_ball_state" in params:
        kwargs["batted_ball_state"] = state
    elif "physical_state" in params:
        kwargs["physical_state"] = state
    else:
        mapping = {
            "exit_velocity": state.exit_velocity,
            "exit_velocity_mph": state.exit_velocity,
            "ev_mph": state.exit_velocity,
            "launch_angle": state.launch_angle,
            "launch_angle_deg": state.launch_angle,
            "la_deg": state.launch_angle,
            "spray_angle": state.spray_angle,
            "spray_angle_deg": state.spray_angle,
            "batter_side": state.batter_side,
        }
        for k, v in mapping.items():
            if k in params:
                kwargs[k] = v
    for k, v in (("launch_height_ft",3.0),("launch_height_m",0.9144),("air_density_kg_m3",1.225)):
        if k in params and k not in kwargs:
            kwargs[k] = v
    return fn(**kwargs)


def controlled_grid(fn):
    evs = [80,90,100,110]
    las = [-10,0,10,20,30,40,50]
    rows = []
    for ev in evs:
        for la in las:
            out = _normalize_output(call_trajectory(fn, make_state(ev,la)))
            rows.append({"ev_mph":ev,"la_deg":la,**out})
    return rows


def low_la(fn):
    rows=[]
    for ev in [80,90,100,110]:
        for la in [-15,-10,-5,0]:
            rows.append({"ev_mph":ev,"la_deg":la,**_normalize_output(call_trajectory(fn,make_state(ev,la)))})
    return rows


def high_la(fn):
    rows=[]
    for ev in [80,90,100,110]:
        for la in [40,50,60]:
            rows.append({"ev_mph":ev,"la_deg":la,**_normalize_output(call_trajectory(fn,make_state(ev,la)))})
    return rows


def coordinates(fn):
    rows=[]
    for spray in [-30,-15,0,15,30]:
        rows.append({"spray_deg":spray,**_normalize_output(call_trajectory(fn,make_state(100,30,spray)))})
    return rows


def deterministic(fn):
    state=make_state(100,29,15)
    a=call_trajectory(fn,state); b=call_trajectory(fn,state)
    try:
        return asdict(a)==asdict(b)
    except Exception:
        return repr(a)==repr(b)


def sanity(rows):
    numeric = []
    for r in rows:
        for k in ("carry_ft","hang_s","apex_ft","x_ft","y_ft"):
            v=r.get(k)
            if v is not None:
                numeric.append(v)
                if not math.isfinite(v):
                    return False
    carries=[r["carry_ft"] for r in rows if r.get("carry_ft") is not None]
    hangs=[r["hang_s"] for r in rows if r.get("hang_s") is not None]
    apex=[r["apex_ft"] for r in rows if r.get("apex_ft") is not None]
    return all(v>=0 for v in carries+hangs+apex)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    fn, adapter = resolve_adapter()
    if fn is None:
        result={"status":"OPEN_NOT_IMPLEMENTED","adapter":adapter,
                "contract":{"grid_ev_mph":[80,90,100,110],"grid_la_deg":[-10,0,10,20,30,40,50],
                            "low_la_deg":[-15,-10,-5,0],"high_la_deg":[40,50,60],
                            "spray_deg":[-30,-15,0,15,30],
                            "reference_100mph_29deg_aero_ft":397.0,"reference_100mph_29deg_vacuum_ft":571.0}}
    else:
        grid=controlled_grid(fn); low=low_la(fn); high=high_la(fn); coords=coordinates(fn)
        result={"status":"IMPLEMENTED","adapter":adapter,"grid":grid,"low_la":low,"high_la":high,
                "coordinates":coords,"deterministic_same_state":deterministic(fn),
                "finite_nonnegative_sanity":sanity(grid+low+high+coords)}
        for metric in ("carry_ft","hang_s","apex_ft"):
            vals=[r[metric] for r in grid if r.get(metric) is not None]
            result[f"grid_{metric}_distribution"]=dist(vals)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
