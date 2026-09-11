#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json

from src import config
from src.hitting.model import HitterSnapshot, PitcherSnapshot
from src.player import Player
from src.rng import RNG
from tools.offense_pitch_diagnostic import TracedHittingEngine, _pitch_summary


def main() -> int:
    rng = RNG(20260911 + 3000000)
    groups = {"low": Counter(), "mid": Counter(), "high": Counter()}
    pa_counts = Counter()
    positions = tuple(config.POSITIONS)
    for i in range(200_000):
        p = Player.random(f"B{i}", rng, position=positions[i % len(positions)])
        d = p.stats.discipline
        group = "low" if d <= 66 else "high" if d >= 80 else "mid"
        hitter = HitterSnapshot(float(p.stats.contact), float(p.stats.power), float(d), float(p.stats.speed))
        TracedHittingEngine(hitter, PitcherSnapshot(100, 100, 100), 100.0, rng, counters=groups[group]).simulate_plate_appearance()
        pa_counts[group] += 1
    out = {}
    for group, c in groups.items():
        r = _pitch_summary(c)["rates"]
        out[group] = {
            "PA": pa_counts[group],
            "chase_pct": r["out_zone_swing_pct"],
            "swing_pct": r["swing_pct"],
            "BB_pct": r["BB_pct"],
            "K_pct": r["K_pct"],
            "HBP_pct": r["HBP_pct"],
            "looking_K_share": r["K_looking_share"],
        }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
