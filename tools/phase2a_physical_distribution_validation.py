#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical import generate_batted_ball_state
from src.rng import RNG


def pct(n, d):
    return n / d if d else 0.0


def percentile(values, q):
    if not values:
        return 0.0
    xs = sorted(values)
    return float(xs[min(len(xs)-1, max(0, round((len(xs)-1)*q)))])


def dist(values):
    return {
        "n": len(values),
        "mean": statistics.mean(values) if values else 0.0,
        "sd": statistics.pstdev(values) if values else 0.0,
        "p1": percentile(values, .01), "p5": percentile(values, .05),
        "p25": percentile(values, .25), "p50": percentile(values, .50),
        "p75": percentile(values, .75), "p95": percentile(values, .95),
        "p99": percentile(values, .99),
        "min": min(values) if values else 0.0,
        "max": max(values) if values else 0.0,
    }


def production_states(seed: int, pas: int, side: str = "R"):
    rng = RNG(seed)
    states = []
    results = Counter()
    hitter = HitterSnapshot(100, 100, 100, 100, handedness=side)
    pitcher = PitcherSnapshot(100, 100, 100)
    for _ in range(pas):
        out = HittingEngine(hitter, pitcher, 100.0, rng).simulate_plate_appearance()
        results[out.result] += 1
        if out.batted_ball is not None and out.batted_ball.physical_state is not None:
            states.append(out.batted_ball.physical_state)
    return states, results


def summarize(states):
    ev = [s.exit_velocity for s in states]
    la = [s.launch_angle for s in states]
    timing = [s.timing for s in states]
    spray = [s.spray_angle for s in states]
    n = len(states)
    la_regions = {
        "ground_ball_like_lt_10": pct(sum(x < 10 for x in la), n),
        "line_drive_like_10_25": pct(sum(10 <= x < 25 for x in la), n),
        "fly_ball_like_25_50": pct(sum(25 <= x < 50 for x in la), n),
        "popup_like_ge_50": pct(sum(x >= 50 for x in la), n),
    }
    timing_comp = {
        "late_lt_minus_0_20": pct(sum(x < -0.20 for x in timing), n),
        "on_time_minus_0_20_to_0_20": pct(sum(-0.20 <= x <= 0.20 for x in timing), n),
        "early_gt_0_20": pct(sum(x > 0.20 for x in timing), n),
        "lower_bound_pileup": pct(sum(x <= -0.999999 for x in timing), n),
        "upper_bound_pileup": pct(sum(x >= 0.999999 for x in timing), n),
    }
    spray_comp = {
        "left_lt_minus_15": pct(sum(x < -15 for x in spray), n),
        "center_minus_15_to_15": pct(sum(-15 <= x <= 15 for x in spray), n),
        "right_gt_15": pct(sum(x > 15 for x in spray), n),
        "left_bound_pileup": pct(sum(x <= -74.999999 for x in spray), n),
        "right_bound_pileup": pct(sum(x >= 74.999999 for x in spray), n),
        "fair_pct": pct(sum(s.is_fair for s in states), n),
        "foul_pct": pct(sum(not s.is_fair for s in states), n),
    }
    early = [s.spray_angle for s in states if s.timing > .30]
    late = [s.spray_angle for s in states if s.timing < -.30]
    return {
        "count": n,
        "exit_velocity_mph": dist(ev),
        "launch_angle_deg": dist(la),
        "launch_angle_regions": la_regions,
        "timing": dist(timing),
        "timing_composition": timing_comp,
        "spray_angle_deg": dist(spray),
        "spray_composition": spray_comp,
        "conditional_spray": {
            "early_n": len(early), "early_mean": statistics.mean(early) if early else 0.0,
            "late_n": len(late), "late_mean": statistics.mean(late) if late else 0.0,
        },
        "unique_launch_angle_0_01deg": len({round(x, 2) for x in la}),
        "unique_ev_0_01mph": len({round(x, 2) for x in ev}),
    }


def direct_population(seed, n, *, contact=100.0, power=100.0, side="R", zone="middle"):
    states = []
    for i in range(n):
        states.append(generate_batted_ball_state(
            hitter_contact=contact, hitter_power=power, batter_side=side,
            approach="balanced", pitch_zone=zone, pitch_velocity_quality=0.0,
            pitch_movement_quality=0.0, pitch_location_quality=0.0,
            pitch_hittable_quality=0.35, parent_rng=RNG(seed + i),
        ))
    return states


def sensitivity(seed, n):
    low_power = direct_population(seed, n, power=70)
    high_power = direct_population(seed, n, power=140)
    low_contact = direct_population(seed + 100000, n, contact=70)
    high_contact = direct_population(seed + 100000, n, contact=140)
    inside_r = direct_population(seed + 200000, n, side="R", zone="inside")
    outside_r = direct_population(seed + 200000, n, side="R", zone="outside")
    mirror_r = direct_population(seed + 300000, n, side="R")
    mirror_l = direct_population(seed + 300000, n, side="L")
    lp = [s.exit_velocity for s in low_power]
    hp = [s.exit_velocity for s in high_power]
    lc_t = [s.timing for s in low_contact]
    hc_t = [s.timing for s in high_contact]
    mir_err = [abs(r.spray_angle + l.spray_angle) for r, l in zip(mirror_r, mirror_l)]
    return {
        "power_ev": {
            "low_mean": statistics.mean(lp), "high_mean": statistics.mean(hp),
            "low_p95": percentile(lp, .95), "high_p95": percentile(hp, .95),
            "mean_delta_high_minus_low": statistics.mean(hp)-statistics.mean(lp),
            "p95_delta_high_minus_low": percentile(hp,.95)-percentile(lp,.95),
        },
        "contact_timing_sd": {
            "low_contact_sd": statistics.pstdev(lc_t),
            "high_contact_sd": statistics.pstdev(hc_t),
        },
        "inside_outside_R": {
            "inside_mean_spray": statistics.mean([s.spray_angle for s in inside_r]),
            "outside_mean_spray": statistics.mean([s.spray_angle for s in outside_r]),
        },
        "handedness_mirror": {
            "max_abs_sum_spray": max(mir_err),
            "mean_abs_sum_spray": statistics.mean(mir_err),
            "right_fair": pct(sum(s.is_fair for s in mirror_r), n),
            "left_fair": pct(sum(s.is_fair for s in mirror_l), n),
        },
    }


def deterministic_sequence(seed, pas):
    def one():
        states, results = production_states(seed, pas)
        seq = [(s.exit_velocity, s.launch_angle, s.timing, s.spray_angle, s.is_fair,
                s.contact_quality, s.pitch_location_x, s.pitch_location_y, s.batter_side)
               for s in states]
        return seq, dict(results)
    a, ar = one(); b, br = one()
    return {"state_sequence_exact_equal": a == b, "result_counts_exact_equal": ar == br,
            "states": len(a)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=20260911)
    p.add_argument("--pa", type=int, default=200000)
    p.add_argument("--sensitivity-n", type=int, default=20000)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    right, result_counts = production_states(a.seed + 7000000, a.pa, "R")
    left, _ = production_states(a.seed + 8000000, a.pa // 4, "L")
    result = {
        "seed": a.seed, "production_pa": a.pa,
        "production_R": summarize(right),
        "production_R_result_counts": dict(result_counts),
        "production_L_quarter_sample": summarize(left),
        "sensitivity": sensitivity(a.seed + 9000000, a.sensitivity_n),
        "determinism": deterministic_sequence(a.seed + 10000000, 20000),
        "notes": {
            "launch_regions": "Descriptive validation bins only: <10 GB-like, 10-25 LD-like, 25-50 FB-like, >=50 popup-like; not calibration targets.",
            "phase2a_scope": "Physical state is shadow-only; legacy final resolver remains authoritative.",
        },
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
