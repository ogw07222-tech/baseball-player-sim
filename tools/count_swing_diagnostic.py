#!/usr/bin/env python3
"""Count-specific Phase-1 swing diagnostic.

Measures actual pitch opportunities/swings by count while reusing the canonical
Phase-1 traced engine for global pitch/PA metrics. Validation only; no runtime
production dependency.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json

from src.hitting.model import HitterSnapshot, PitcherSnapshot
from src.rng import RNG
from tools.offense_pitch_diagnostic import TracedHittingEngine, _pitch_summary

ALL_COUNTS = tuple(
    (balls, strikes)
    for balls in range(4)
    for strikes in range(3)
)


def _pct(n: int, d: int) -> float:
    return n / d if d else 0.0


class CountTracedHittingEngine(TracedHittingEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._count_reached_seen: set[tuple[int, int]] = set()

    def _swing_probability(self, pitch, balls, strikes):
        count = (balls, strikes)
        if count not in self._count_reached_seen:
            self._count_reached_seen.add(count)
            self.c[f"count_{balls}_{strikes}_reached"] += 1
        self.c[f"count_{balls}_{strikes}_opportunities"] += 1
        if pitch.is_strike:
            self.c[f"count_{balls}_{strikes}_zone_opportunities"] += 1
        else:
            self.c[f"count_{balls}_{strikes}_ball_opportunities"] += 1
        if self.current is not None:
            self.current["count"] = count
        return super()._swing_probability(pitch, balls, strikes)

    def _contact_resolution(self, pitch, strikes):
        count = None if self.current is None else self.current.get("count")
        result = super()._contact_resolution(pitch, strikes)
        if count is not None:
            balls, count_strikes = count
            self.c[f"count_{balls}_{count_strikes}_swings"] += 1
            if pitch.is_strike:
                self.c[f"count_{balls}_{count_strikes}_zone_swings"] += 1
            else:
                self.c[f"count_{balls}_{count_strikes}_chases"] += 1
        return result

    def simulate_plate_appearance(self):
        self._count_reached_seen = set()
        return super().simulate_plate_appearance()


def count_summary(counters: Counter) -> dict[str, dict[str, float | int]]:
    pa = counters["PA"]
    out: dict[str, dict[str, float | int]] = {}
    for balls, strikes in ALL_COUNTS:
        key = f"{balls}-{strikes}"
        opp = counters[f"count_{balls}_{strikes}_opportunities"]
        zone = counters[f"count_{balls}_{strikes}_zone_opportunities"]
        balls_seen = counters[f"count_{balls}_{strikes}_ball_opportunities"]
        swings = counters[f"count_{balls}_{strikes}_swings"]
        zone_swings = counters[f"count_{balls}_{strikes}_zone_swings"]
        chases = counters[f"count_{balls}_{strikes}_chases"]
        out[key] = {
            "reached_pct": _pct(counters[f"count_{balls}_{strikes}_reached"], pa),
            "opportunities": opp,
            "swing_pct": _pct(swings, opp),
            "z_swing_pct": _pct(zone_swings, zone),
            "chase_pct": _pct(chases, balls_seen),
        }
    return out


def run_neutral(seed: int = 20260911, pas: int = 100_000) -> dict:
    counters = Counter()
    rng = RNG(seed)
    hitter = HitterSnapshot(100, 100, 100, 100)
    for _ in range(pas):
        CountTracedHittingEngine(
            hitter,
            PitcherSnapshot(100, 100, 100),
            100.0,
            rng,
            counters=counters,
        ).simulate_plate_appearance()
    return {
        "seed": seed,
        "PA": pas,
        "global": _pitch_summary(counters)["rates"],
        "by_count": count_summary(counters),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260911)
    parser.add_argument("--pa", type=int, default=100_000)
    args = parser.parse_args()
    print(json.dumps(run_neutral(args.seed, args.pa), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())