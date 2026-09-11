#!/usr/bin/env python3
"""05 Balance Lab validation-only harness for Physical Batted-Ball Phase 2A.

No production tuning is performed here. The script locks the pre-Phase2 offense
baseline and probes a future Phase2A BattedBallState without assuming a specific
production resolver change.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import time
from pathlib import Path

import tools.offense_pitch_diagnostic as opd
from src.hitting import model as hitting_model


def pct(n, d):
    return n / d if d else 0.0


def percentile(values, q):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * q)))
    return float(ordered[idx])


def dist(values):
    if not values:
        return {}
    return {
        "mean": statistics.mean(values),
        "sd": statistics.pstdev(values),
        "p1": percentile(values, .01),
        "p5": percentile(values, .05),
        "p25": percentile(values, .25),
        "p50": percentile(values, .50),
        "p75": percentile(values, .75),
        "p95": percentile(values, .95),
        "p99": percentile(values, .99),
        "min": min(values),
        "max": max(values),
    }


def run_games_with_p5(seed, games):
    original = opd._dist
    opd._dist = dist
    try:
        result = opd.run_full_games(seed, games)
    finally:
        opd._dist = original
    totals = result["totals"]
    rates = result["rates"]
    babip_den = totals["AB"] - totals["SO"] - totals["HR"] + totals["SF"]
    rates["BABIP"] = pct(totals["H"] - totals["HR"], babip_den)
    rates["ROE_per_PA"] = pct(totals.get("ROE", 0), totals["PA"])
    rates["SF_per_PA"] = pct(totals.get("SF", 0), totals["PA"])
    rates["GDP_per_PA"] = pct(totals.get("GDP", 0), totals["PA"])
    rates["XBT_per_PA"] = pct(totals.get("XBT", 0), totals["PA"])
    return result


def phase1_snapshot(seed, pa_samples, games):
    neutral = opd.run_pitch_population(seed + 1_000_000, pa_samples, False)
    generated = opd.run_pitch_population(seed + 2_000_000, pa_samples, True)
    full_games = run_games_with_p5(seed, games)
    return {
        "seed": seed,
        "neutral_pa": pa_samples,
        "generated_pa": pa_samples,
        "games": games,
        "pitch_neutral": neutral,
        "pitch_generated": generated,
        "full_games": full_games,
    }


def seed_variance(base_seed, games_per_seed):
    rows = []
    for seed in (base_seed, base_seed + 1, base_seed + 2):
        fg = run_games_with_p5(seed, games_per_seed)
        rows.append({
            "seed": seed,
            "games": games_per_seed,
            "runs_per_game": fg["game_distributions"]["runs"]["mean"],
            "hits_per_game": fg["game_distributions"]["hits"]["mean"],
            "hr_per_game": fg["game_distributions"]["HR"]["mean"],
            "bb_per_game": fg["game_distributions"]["BB"]["mean"],
            "k_per_game": fg["game_distributions"]["K"]["mean"],
            "bb_per_pa": fg["rates"]["BB_per_PA"],
            "k_per_pa": fg["rates"]["K_per_PA"],
            "hr_per_pa": fg["rates"]["HR_per_PA"],
        })
    return rows


def performance_snapshot(seed, pa_samples, games):
    t0 = time.perf_counter()
    opd.run_pitch_population(seed + 3_000_000, pa_samples, False)
    pa_seconds = time.perf_counter() - t0
    t1 = time.perf_counter()
    run_games_with_p5(seed + 4_000_000, games)
    game_seconds = time.perf_counter() - t1
    return {
        "pa_samples": pa_samples,
        "pa_wall_seconds": pa_seconds,
        "microseconds_per_pa": pa_seconds * 1_000_000 / pa_samples,
        "games": games,
        "games_wall_seconds": game_seconds,
        "milliseconds_per_game": game_seconds * 1000 / games,
        "season_representative_144_game_estimate_seconds": game_seconds * 144 / games,
    }


def determinism_snapshot(seed):
    a_pitch = opd.run_pitch_population(seed + 5_000_000, 20_000, False)
    b_pitch = opd.run_pitch_population(seed + 5_000_000, 20_000, False)
    a_games = run_games_with_p5(seed + 6_000_000, 250)
    b_games = run_games_with_p5(seed + 6_000_000, 250)
    return {
        "pitch_20k_exact_equal": a_pitch == b_pitch,
        "full_games_250_exact_equal": a_games == b_games,
    }


def _field_names(cls):
    if dataclasses.is_dataclass(cls):
        return [f.name for f in dataclasses.fields(cls)]
    return []


def phase2a_probe():
    cls = getattr(hitting_model, "BattedBallState", None)
    if cls is None:
        return {
            "status": "OPEN_NOT_IMPLEMENTED",
            "batted_ball_state_present": False,
            "required_distribution_contract": {
                "exit_velocity": ["mean", "sd", "p1", "p5", "p25", "p50", "p75", "p95", "p99", "min", "max"],
                "launch_angle": ["mean", "sd", "percentiles", "GB_like", "LD_like", "FB_like", "popup_like", "one_bin_collapse"],
                "timing": ["mean", "sd", "early", "on_time", "late", "boundary_pileup"],
                "spray": ["mean", "sd", "left", "center", "right", "pull", "opposite", "boundary_pileup", "handedness_mirror"],
                "fair_foul": ["fair_pct", "foul_pct", "handedness_split", "count_split"],
            },
            "required_sensitivity_contract": [
                "power_vs_upper_EV_tail",
                "contact_power_sign_sanity",
                "early_timing_pull_tendency",
                "late_timing_opposite_tendency",
                "inside_outside_directional_tendency",
                "left_right_handedness_mirror",
            ],
        }
    return {
        "status": "READY_FOR_STATE_DISTRIBUTION_ADAPTER",
        "batted_ball_state_present": True,
        "class": f"{cls.__module__}.{cls.__name__}",
        "fields": _field_names(cls),
        "note": "01 should expose the generated BattedBallState on the PA outcome or a validation-safe engine hook; 05 will sample the real production path without changing coefficients.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=20260911)
    p.add_argument("--pa", type=int, default=200000)
    p.add_argument("--games", type=int, default=10000)
    p.add_argument("--variance-games", type=int, default=1000)
    p.add_argument("--perf-pa", type=int, default=50000)
    p.add_argument("--perf-games", type=int, default=500)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    result = {
        "schema": "phase2a-validation-v1",
        "pre_phase2": phase1_snapshot(args.seed, args.pa, args.games),
        "seed_variance": seed_variance(args.seed, args.variance_games),
        "determinism": determinism_snapshot(args.seed),
        "performance": performance_snapshot(args.seed, args.perf_pa, args.perf_games),
        "phase2a": phase2a_probe(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
