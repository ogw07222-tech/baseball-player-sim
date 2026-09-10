#!/usr/bin/env python3
"""Deterministic catcher-foundation generation sanity for consolidation."""
from __future__ import annotations

from collections import Counter
import argparse
import json
import math
import statistics

from src.player import Player
from src.rng import RNG


def _summary(values: list[int]) -> dict[str, float | int]:
    ordered = sorted(values)
    n = len(ordered)
    def pct(q: float) -> int:
        return ordered[min(n - 1, max(0, int(round((n - 1) * q))))]
    return {
        "mean": statistics.mean(ordered),
        "sd": statistics.pstdev(ordered),
        "p10": pct(.10),
        "p50": pct(.50),
        "p90": pct(.90),
        "p95": pct(.95),
        "p99": pct(.99),
        "min": ordered[0],
        "max": ordered[-1],
        "ge150": sum(v >= 150 for v in ordered),
        "ge170": sum(v >= 170 for v in ordered),
        "ge200": sum(v >= 200 for v in ordered),
    }


def run(samples: int = 200_000, seed: int = 20260906) -> dict[str, object]:
    if samples <= 0:
        raise ValueError("samples must be positive")
    rng = RNG(seed)
    defense: list[int] = []
    throwing: list[int] = []
    calling: list[int] = []
    archetypes: Counter[str] = Counter()
    for index in range(samples):
        player = Player.random(f"C{index}", rng, position="C")
        defense.append(player.stats.defense)
        throwing.append(player.stats.throwing)
        calling.append(player.stats.game_calling)
        archetypes[str(player.catcher_archetype)] += 1

    noncatcher_rng = RNG(seed)
    noncatcher_nonzero = 0
    for index in range(min(samples, 100_000)):
        player = Player.random(f"N{index}", noncatcher_rng, position="SS")
        noncatcher_nonzero += int(player.stats.game_calling != 0 or player.catcher_archetype is not None)

    result = {
        "samples": samples,
        "seed": seed,
        "defense": _summary(defense),
        "throwing": _summary(throwing),
        "game_calling": _summary(calling),
        "archetypes": dict(sorted(archetypes.items())),
        "noncatcher_checked": min(samples, 100_000),
        "noncatcher_catcher_semantic_violations": noncatcher_nonzero,
    }
    numeric = [
        result["defense"]["mean"],
        result["throwing"]["mean"],
        result["game_calling"]["mean"],
    ]
    if not all(math.isfinite(float(value)) for value in numeric):
        raise RuntimeError("non-finite catcher generation summary")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=200_000)
    parser.add_argument("--seed", type=int, default=20260906)
    args = parser.parse_args()
    print(json.dumps(run(args.samples, args.seed), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
