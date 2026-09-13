#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from src.game_provider import GameFixture, ProductionGameProvider
from src.hitting import ground_travel_parameters as GP
from src.hitting import retrieval_parameters as P
from src.hitting.ground_travel import GroundTravelState
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.retrieval import (
    build_retrieval_state,
    resolve_physical_hit_shadow,
)
from src.rng import RNG


def ground_at(x: float, y: float) -> GroundTravelState:
    return GroundTravelState(
        valid=True,
        surface_class=GP.SURFACE_CLASS_NEUTRAL,
        impact_horizontal_speed_fps=70.0,
        post_impact_horizontal_speed_fps=35.0,
        bounce_distance_ft=8.0,
        rollout_start_speed_fps=24.0,
        rollout_distance_ft=12.0,
        ground_travel_distance_ft=20.0,
        first_impact_x_ft=x,
        first_impact_y_ft=y,
        final_x_ft=x,
        final_y_ft=y,
        final_radial_distance_ft=math.hypot(x, y),
        wall_ground_contact=False,
        ground_model_version=GP.GROUND_MODEL_VERSION,
        invalid_reason=None,
    )


def finite_retrieval(state) -> bool:
    vals = (
        state.defender_start_x_ft, state.defender_start_y_ft, state.ball_x_ft, state.ball_y_ft,
        state.retrieval_distance_ft, state.reaction_time_s, state.effective_fielder_speed_fps,
        state.movement_time_s, state.pickup_transfer_time_s, state.total_retrieval_time_s,
        state.defender_rating,
    )
    return all(math.isfinite(v) for v in vals)


def edge_probe() -> dict:
    ball = ground_at(0.0, 360.0)
    out = {"fielder_speed": {}, "throw_speed": {}, "rating_denominator": {}, "mph_to_fps": {}}
    bads = [0.0, -1.0, float("nan"), float("inf"), float("-inf")]
    for bad in bads:
        key = repr(bad)
        try:
            with patch("src.hitting.retrieval._rating_adjusted_retrieval_terms", return_value=(0.5, bad, 0.3)):
                state = build_retrieval_state(ground_travel=ball, defender_rating=100.0)
                res = resolve_physical_hit_shadow(
                    ground_travel=ball, defensive_resolution=None,
                    defender_rating=100.0, runner_speed_rating=100.0,
                )
            out["fielder_speed"][key] = {
                "exception": None,
                "retrieval_valid": state.valid,
                "retrieval_reason": state.invalid_reason,
                "retrieval_finite": finite_retrieval(state),
                "resolution_valid": res.valid,
                "resolution_result": res.physical_result_shadow,
                "resolution_reason": res.invalid_reason,
            }
        except Exception as exc:
            out["fielder_speed"][key] = {"exception": repr(exc)}

    for bad in bads:
        key = repr(bad)
        try:
            with patch.dict(P.EFFECTIVE_THROW_SPEED_MPH, {"OF": bad}, clear=False):
                res = resolve_physical_hit_shadow(
                    ground_travel=ground_at(0.0, 300.0), defensive_resolution=None,
                    defender_rating=100.0, runner_speed_rating=100.0,
                )
            out["throw_speed"][key] = {
                "exception": None, "valid": res.valid,
                "result": res.physical_result_shadow, "reason": res.invalid_reason,
            }
        except Exception as exc:
            out["throw_speed"][key] = {"exception": repr(exc)}

    for bad in bads:
        key = repr(bad)
        try:
            with patch.object(P, "DEFENSE_RATING_FULL_EFFECT_POINTS", bad):
                state = build_retrieval_state(ground_travel=ball, defender_rating=100.0)
            out["rating_denominator"][key] = {
                "exception": None, "valid": state.valid,
                "reason": state.invalid_reason, "finite": finite_retrieval(state),
            }
        except Exception as exc:
            out["rating_denominator"][key] = {"exception": repr(exc)}

    for bad in bads:
        key = repr(bad)
        try:
            with patch.object(P, "MPH_TO_FPS", bad):
                res = resolve_physical_hit_shadow(
                    ground_travel=ground_at(0.0, 300.0), defensive_resolution=None,
                    defender_rating=100.0, runner_speed_rating=100.0,
                )
            out["mph_to_fps"][key] = {
                "exception": None, "valid": res.valid,
                "result": res.physical_result_shadow, "reason": res.invalid_reason,
            }
        except Exception as exc:
            out["mph_to_fps"][key] = {"exception": repr(exc)}

    return out


def disabled_shadow(*, ground_travel, defensive_resolution, defender_rating, runner_speed_rating):
    from src.hitting.retrieval import _invalid_resolution
    return _invalid_resolution("disabled_for_05_regression")


def pa_run(seed: int, n: int, disabled: bool) -> dict:
    rng = RNG(seed)
    hitter = HitterSnapshot(100.0, 100.0, 100.0, 112.0)
    pitcher = PitcherSnapshot(100.0, 100.0, 100.0)
    counts = Counter()
    seq = hashlib.sha256()
    upstream = hashlib.sha256()
    ctx = patch("src.hitting.retrieval.resolve_physical_hit_shadow", side_effect=disabled_shadow) if disabled else None
    if ctx: ctx.start()
    try:
        for _ in range(n):
            o = HittingEngine(hitter, pitcher, 107.0, rng).simulate_plate_appearance()
            counts[o.result] += 1
            seq.update(repr(o.result).encode())
            if o.batted_ball is not None and o.batted_ball.physical_state is not None:
                s = o.batted_ball.physical_state
                upstream.update(repr((
                    s.exit_velocity, s.launch_angle, s.timing, s.spray_angle, s.is_fair,
                    s.contact_quality, s.trajectory, s.wall_interaction,
                    s.defensive_opportunity, s.defensive_resolution, s.ground_travel,
                )).encode())
    finally:
        if ctx: ctx.stop()
    return {
        "counts": dict(counts), "sequence_hash": seq.hexdigest(),
        "upstream_hash": upstream.hexdigest(),
        "rng_hash": hashlib.sha256(repr(rng.get_state()).encode()).hexdigest(),
    }


def game_run(seed: int, games: int, disabled: bool) -> dict:
    rng = RNG(seed)
    provider = ProductionGameProvider(notable_event_limit=8)
    h = hashlib.sha256()
    ctx = patch("src.hitting.retrieval.resolve_physical_hit_shadow", side_effect=disabled_shadow) if disabled else None
    if ctx: ctx.start()
    try:
        for i in range(games):
            result = provider.run_game(
                GameFixture(date(2026, 4, 1) + timedelta(days=i), "A", "H"), rng
            )
            h.update(repr(result).encode())
    finally:
        if ctx: ctx.stop()
    return {
        "sequence_hash": h.hexdigest(),
        "rng_hash": hashlib.sha256(repr(rng.get_state()).encode()).hexdigest(),
    }


def perf() -> dict:
    ball = ground_at(180.0, 300.0)
    # Warmup then repeated direct resolution; this is a regression guard, not a cross-run attribution benchmark.
    for _ in range(2000):
        resolve_physical_hit_shadow(ground_travel=ball, defensive_resolution=None, defender_rating=100.0, runner_speed_rating=100.0)
    rounds = []
    for _ in range(3):
        t0 = time.perf_counter()
        for _ in range(50_000):
            resolve_physical_hit_shadow(ground_travel=ball, defensive_resolution=None, defender_rating=100.0, runner_speed_rating=100.0)
        rounds.append(time.perf_counter() - t0)
    return {"resolution_50k_seconds": rounds, "best_seconds": min(rounds)}


def main() -> None:
    out = {"edge_probe": edge_probe()}
    enabled = pa_run(20260913, 200_000, False)
    disabled = pa_run(20260913, 200_000, True)
    out["pa_regression"] = {
        "enabled": enabled, "disabled": disabled,
        "counts_equal": enabled["counts"] == disabled["counts"],
        "sequence_equal": enabled["sequence_hash"] == disabled["sequence_hash"],
        "upstream_equal": enabled["upstream_hash"] == disabled["upstream_hash"],
        "rng_equal": enabled["rng_hash"] == disabled["rng_hash"],
    }
    out["determinism"] = pa_run(20260914, 20_000, False) == pa_run(20260914, 20_000, False)
    ge = game_run(20260913, 1000, False)
    gd = game_run(20260913, 1000, True)
    out["game_regression"] = {
        "enabled": ge, "disabled": gd,
        "sequence_equal": ge["sequence_hash"] == gd["sequence_hash"],
        "rng_equal": ge["rng_hash"] == gd["rng_hash"],
    }
    out["performance"] = perf()
    Path("phase2eb-revalidation.json").write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=True), encoding="utf-8")

    assert out["pa_regression"]["counts_equal"]
    assert out["pa_regression"]["sequence_equal"]
    assert out["pa_regression"]["upstream_equal"]
    assert out["pa_regression"]["rng_equal"]
    assert out["determinism"]
    assert out["game_regression"]["sequence_equal"]
    assert out["game_regression"]["rng_equal"]
    for group in out["edge_probe"].values():
        for case in group.values():
            assert case.get("exception") is None, case
    for case in out["edge_probe"]["fielder_speed"].values():
        assert case["retrieval_valid"] is False
        assert case["retrieval_reason"] == "invalid_effective_fielder_speed"
        assert case["retrieval_finite"] is True
        assert case["resolution_valid"] is False
        assert case["resolution_result"] is None
        assert case["resolution_reason"] == "invalid_effective_fielder_speed"
    for group_name in ("throw_speed", "mph_to_fps"):
        for case in out["edge_probe"][group_name].values():
            assert case["valid"] is False
            assert case["result"] is None
            assert case["reason"] == "invalid_timing_derivation"
    for case in out["edge_probe"]["rating_denominator"].values():
        assert case["valid"] is False
        assert case["reason"] == "invalid_retrieval_derivation"
        assert case["finite"] is True


if __name__ == "__main__":
    main()
