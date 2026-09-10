#!/usr/bin/env python3
"""Monte Carlo sanity/benchmark for the production full-game provider.

No tuning occurs here. The runner reports integration distributions and fails
only on structural safety violations (non-finite values or safety-cap hits).
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
import json
import math
from pathlib import Path
import time

from src.game_provider import GameFixture, GameSafetyLimitError, ProductionGameProvider
from src.rng import RNG


def run_games(games: int, seed: int) -> dict[str, object]:
    provider = ProductionGameProvider(notable_event_limit=8)
    rng = RNG(seed)
    totals = Counter()
    pa_hist = Counter()
    innings_sum = 0
    elapsed_start = time.perf_counter()
    cap_hits = 0

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

        away_lines = [line for line in result.player_lines if line.team == fixture.away_team]
        home_lines = [line for line in result.player_lines if line.team == fixture.home_team]
        for line in away_lines + home_lines:
            stats = line.stats
            totals["PA"] += stats.PA
            totals["H"] += stats.H
            totals["HR"] += stats.HR
            totals["BB"] += stats.BB
            totals["SO"] += stats.SO
            pa_hist[stats.PA] += 1

        totals["runs"] += result.away_score + result.home_score
        totals["extra_innings"] += int(result.innings_played > 9)
        totals["walkoffs"] += int("WALKOFF" in result.notable_events)
        totals["events"] += result.event_count
        innings_sum += result.innings_played

    elapsed = time.perf_counter() - elapsed_start
    completed = games - cap_hits
    team_games = max(1, completed * 2)
    all_values = [
        totals["runs"], totals["H"], totals["HR"], totals["BB"], totals["SO"],
        innings_sum, elapsed,
    ]
    if not all(math.isfinite(float(value)) for value in all_values):
        raise RuntimeError("non-finite Monte Carlo summary")

    return {
        "games_requested": games,
        "games_completed": completed,
        "seed": seed,
        "runs_per_team_game": totals["runs"] / team_games,
        "hits_per_team_game": totals["H"] / team_games,
        "hr_per_game": totals["HR"] / max(1, completed),
        "bb_per_game": totals["BB"] / max(1, completed),
        "k_per_game": totals["SO"] / max(1, completed),
        "extra_innings_pct": totals["extra_innings"] / max(1, completed),
        "walkoff_pct": totals["walkoffs"] / max(1, completed),
        "average_innings": innings_sum / max(1, completed),
        "average_pa_per_team_game": totals["PA"] / team_games,
        "average_events_per_game": totals["events"] / max(1, completed),
        "cap_hit_count": cap_hits,
        "cap_hit_pct": cap_hits / max(1, games),
        "runtime_seconds": elapsed,
        "games_per_second": completed / max(elapsed, 1e-9),
        "pa_per_game_distribution": dict(sorted(pa_hist.items())),
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
    return 1 if summary["cap_hit_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
