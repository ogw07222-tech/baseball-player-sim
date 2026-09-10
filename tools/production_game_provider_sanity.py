#!/usr/bin/env python3
"""Monte Carlo sanity/benchmark for the production full-game provider.

Validation only. No gameplay or calibration tuning occurs here. The runner
records structural invariants, deterministic replay, KBO regular-season
termination semantics, and distribution tails.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
import json
import math
from pathlib import Path
import statistics
import time

from src.game_provider import GameFixture, GameSafetyLimitError, ProductionGameProvider
from src.inning import KBO_REGULAR_SEASON_MAX_INNING
from src.rng import RNG


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return float(ordered[index])


def _distribution(values: list[float]) -> dict[str, float]:
    if not values:
        return {key: 0.0 for key in ("mean", "median", "sd", "min", "max", "p10", "p50", "p90", "p95", "p99")}
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "sd": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
        "p10": _percentile(values, 0.10),
        "p50": _percentile(values, 0.50),
        "p90": _percentile(values, 0.90),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
    }


def _result_fingerprint(result) -> tuple[object, ...]:
    hitters = tuple(
        (
            line.player_id,
            line.team,
            line.lineup_slot,
            tuple(sorted(line.stats.as_dict().items())),
        )
        for line in result.player_lines
    )
    pitchers = tuple(
        (
            line.pitcher_id,
            line.team,
            line.role,
            tuple(sorted(line.stats.as_dict().items())),
        )
        for line in result.pitcher_lines
    )
    return (
        result.away_team,
        result.home_team,
        result.away_score,
        result.home_score,
        result.innings_played,
        result.event_count,
        hitters,
        pitchers,
        tuple(result.notable_events),
    )


def _check_result_invariants(result, fixture) -> Counter:
    violations = Counter()
    if not isinstance(result.away_score, int) or not isinstance(result.home_score, int):
        violations["non_integer_score"] += 1
    if result.away_score < 0 or result.home_score < 0:
        violations["negative_score"] += 1
    if result.innings_played < 9:
        violations["innings_below_nine"] += 1
    if result.innings_played > KBO_REGULAR_SEASON_MAX_INNING:
        violations["innings_above_kbo_limit"] += 1
    if result.event_count <= 0:
        violations["nonpositive_event_count"] += 1
    if result.safety_cap_hit:
        violations["result_safety_cap_hit"] += 1

    is_draw = result.away_score == result.home_score
    if is_draw:
        if result.innings_played != KBO_REGULAR_SEASON_MAX_INNING:
            violations["draw_not_after_completed_11th"] += 1
        if result.winner is not None or result.loser is not None:
            violations["draw_has_winner_or_loser"] += 1
        if result.team_result_for(fixture.away_team) != "T" or result.team_result_for(fixture.home_team) != "T":
            violations["draw_team_result_semantics"] += 1

    away_lines = [line for line in result.player_lines if line.team == fixture.away_team]
    home_lines = [line for line in result.player_lines if line.team == fixture.home_team]
    if len(result.player_lines) != 18:
        violations["player_line_count"] += 1
    if len(away_lines) != 9 or len(home_lines) != 9:
        violations["team_lineup_count"] += 1

    for line in result.player_lines:
        stats = line.stats.as_dict()
        if any(not math.isfinite(float(value)) for value in stats.values()):
            violations["nonfinite_hitter_stat"] += 1
        if any(float(value) < 0 for value in stats.values()):
            violations["negative_hitter_stat"] += 1

    for line in result.pitcher_lines:
        stats = line.stats.as_dict()
        numeric = [value for value in stats.values() if value is not None]
        if any(not math.isfinite(float(value)) for value in numeric):
            violations["nonfinite_pitcher_stat"] += 1
        if any(float(value) < 0 for value in numeric):
            violations["negative_pitcher_stat"] += 1

    away_pa = sum(line.stats.PA for line in away_lines)
    home_pa = sum(line.stats.PA for line in home_lines)
    away_runs = sum(line.stats.R for line in away_lines)
    home_runs = sum(line.stats.R for line in home_lines)
    if away_runs != result.away_score or home_runs != result.home_score:
        violations["hitter_runs_score_mismatch"] += 1

    away_pitcher_bf = sum(line.stats.BF for line in result.pitcher_lines if line.team == fixture.away_team)
    home_pitcher_bf = sum(line.stats.BF for line in result.pitcher_lines if line.team == fixture.home_team)
    if away_pitcher_bf != home_pa or home_pitcher_bf != away_pa:
        violations["pitcher_bf_pa_mismatch"] += 1
    return violations


def _deterministic_replay(seed: int) -> dict[str, object]:
    fixture = GameFixture(date(2030, 4, 1), "Replay Away", "Replay Home")
    a = ProductionGameProvider(notable_event_limit=32).run_game(fixture, RNG(seed))
    b = ProductionGameProvider(notable_event_limit=32).run_game(fixture, RNG(seed))
    return {
        "seed": seed,
        "pass": _result_fingerprint(a) == _result_fingerprint(b),
        "away_score": a.away_score,
        "home_score": a.home_score,
        "innings": a.innings_played,
        "draw": a.away_score == a.home_score,
        "events": a.event_count,
    }


def run_games(games: int, seed: int) -> dict[str, object]:
    provider = ProductionGameProvider(notable_event_limit=8)
    rng = RNG(seed)
    totals = Counter()
    pa_hist = Counter()
    elapsed_start = time.perf_counter()
    cap_hits = 0
    violations = Counter()

    runs_game: list[float] = []
    team_runs: list[float] = []
    innings_game: list[float] = []
    pa_game: list[float] = []
    events_game: list[float] = []

    for index in range(games):
        fixture = GameFixture(
            date(2026, 4, 1) + timedelta(days=index),
            "Neutral Away",
            "Neutral Home",
        )
        try:
            result = provider.run_game(fixture, rng)
        except GameSafetyLimitError:
            cap_hits += 1
            continue

        violations.update(_check_result_invariants(result, fixture))
        away_lines = [line for line in result.player_lines if line.team == fixture.away_team]
        home_lines = [line for line in result.player_lines if line.team == fixture.home_team]
        game_pa = 0
        for line in away_lines + home_lines:
            stats = line.stats
            totals["PA"] += stats.PA
            totals["H"] += stats.H
            totals["HR"] += stats.HR
            totals["BB"] += stats.BB
            totals["SO"] += stats.SO
            pa_hist[stats.PA] += 1
            game_pa += stats.PA

        total_runs = result.away_score + result.home_score
        totals["runs"] += total_runs
        totals["extra_innings"] += int(result.innings_played > 9)
        totals["inning_9"] += int(result.innings_played == 9)
        totals["inning_10"] += int(result.innings_played == 10)
        totals["inning_11"] += int(result.innings_played == 11)
        totals["inning_12plus"] += int(result.innings_played >= 12)
        totals["draws"] += int(result.away_score == result.home_score)
        totals["walkoffs"] += int("WALKOFF" in result.notable_events)
        totals["events"] += result.event_count

        runs_game.append(float(total_runs))
        team_runs.extend((float(result.away_score), float(result.home_score)))
        innings_game.append(float(result.innings_played))
        pa_game.append(float(game_pa))
        events_game.append(float(result.event_count))

    elapsed = time.perf_counter() - elapsed_start
    completed = games - cap_hits
    team_games = max(1, completed * 2)
    all_values = [
        totals["runs"], totals["H"], totals["HR"], totals["BB"], totals["SO"], elapsed,
        *runs_game, *innings_game, *pa_game,
    ]
    if not all(math.isfinite(float(value)) for value in all_values):
        raise RuntimeError("non-finite Monte Carlo summary")

    deterministic = _deterministic_replay(seed + 50_000_000)
    invariant_count = sum(violations.values())
    run_dist = _distribution(runs_game)
    inning_dist = _distribution(innings_game)
    pa_dist = _distribution(pa_game)
    team_run_dist = _distribution(team_runs)
    event_dist = _distribution(events_game)
    collapse = run_dist["sd"] == 0 or pa_dist["sd"] == 0

    return {
        "games_requested": games,
        "games_completed": completed,
        "completion_rate": completed / max(1, games),
        "seed": seed,
        "kbo_regular_season_max_inning": KBO_REGULAR_SEASON_MAX_INNING,
        "regulation_9_inning_pct": totals["inning_9"] / max(1, completed),
        "ten_inning_pct": totals["inning_10"] / max(1, completed),
        "eleven_inning_pct": totals["inning_11"] / max(1, completed),
        "games_12plus_innings": totals["inning_12plus"],
        "draw_count": totals["draws"],
        "draw_pct": totals["draws"] / max(1, completed),
        "runs_per_team_game": totals["runs"] / team_games,
        "hits_per_team_game": totals["H"] / team_games,
        "hr_per_game": totals["HR"] / max(1, completed),
        "bb_per_game": totals["BB"] / max(1, completed),
        "k_per_game": totals["SO"] / max(1, completed),
        "extra_innings_pct": totals["extra_innings"] / max(1, completed),
        "walkoff_pct": totals["walkoffs"] / max(1, completed),
        "average_innings": statistics.mean(innings_game) if innings_game else 0.0,
        "average_pa_per_team_game": totals["PA"] / team_games,
        "average_events_per_game": totals["events"] / max(1, completed),
        "cap_hit_count": cap_hits,
        "cap_hit_pct": cap_hits / max(1, games),
        "invariant_violation_count": invariant_count,
        "invariant_violations": dict(sorted(violations.items())),
        "deterministic_replay": deterministic,
        "obvious_distribution_collapse": collapse,
        "runs_per_game_distribution": run_dist,
        "runs_per_team_game_distribution": team_run_dist,
        "innings_per_game_distribution": inning_dist,
        "pa_per_game_distribution_summary": pa_dist,
        "events_per_game_distribution": event_dist,
        "extreme_tails": {
            "games_12plus_innings": totals["inning_12plus"],
            "games_20plus_total_runs": sum(value >= 20 for value in runs_game),
            "team_games_15plus_runs": sum(value >= 15 for value in team_runs),
            "games_100plus_pa": sum(value >= 100 for value in pa_game),
            "games_150plus_events": sum(value >= 150 for value in events_game),
        },
        "runtime_seconds": elapsed,
        "games_per_second": completed / max(elapsed, 1e-9),
        "pa_per_player_game_distribution": dict(sorted(pa_hist.items())),
    }


def benchmark(seed: int) -> dict[str, object]:
    out: dict[str, object] = {}
    for label, games in (("one_game", 1), ("one_week_6_games", 6), ("one_month_26_games", 26), ("full_season_144_games", 144)):
        result = run_games(games, seed + games)
        out[label] = {
            "games": games,
            "runtime_seconds": result["runtime_seconds"],
            "games_per_second": result["games_per_second"],
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260906)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.games <= 0:
        raise SystemExit("--games must be positive")

    summary = run_games(args.games, args.seed)
    summary["benchmark"] = benchmark(args.seed + 10_000_000)
    encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    print(encoded)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")

    structural_failure = (
        summary["completion_rate"] != 1.0
        or summary["cap_hit_count"] != 0
        or summary["invariant_violation_count"] != 0
        or summary["games_12plus_innings"] != 0
        or summary["innings_per_game_distribution"]["max"] > KBO_REGULAR_SEASON_MAX_INNING
        or not summary["deterministic_replay"]["pass"]
        or summary["obvious_distribution_collapse"]
    )
    return 1 if structural_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
