#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json

from src.hitting.model import HitterSnapshot, PitcherSnapshot
from src.rng import RNG
from tools.count_swing_diagnostic import CountTracedHittingEngine


class DetailedCountEngine(CountTracedHittingEngine):
    def _finish_current(self):
        cur = self.current
        if cur and not cur.get("finalized"):
            count = cur.get("count")
            if count is not None and cur["pitch"].is_strike:
                balls, strikes = count
                self.c[f"count_{balls}_{strikes}_called_strikes"] += 1
        return super()._finish_current()

    def _contact_resolution(self, pitch, strikes, protective_swing=False):
        count = None if self.current is None else self.current.get("count")
        result = super()._contact_resolution(pitch, strikes, protective_swing=protective_swing)
        if count is not None and result[0] != "miss":
            balls, count_strikes = count
            self.c[f"count_{balls}_{count_strikes}_contacts"] += 1
        return result


def pct(n, d):
    return n / d if d else 0.0


def main():
    counters = Counter()
    rng = RNG(20260911)
    hitter = HitterSnapshot(100, 100, 100, 100)
    for _ in range(200_000):
        DetailedCountEngine(
            hitter,
            PitcherSnapshot(100, 100, 100),
            100.0,
            rng,
            counters=counters,
        ).simulate_plate_appearance()

    out = {}
    for balls, strikes in ((3, 0), (3, 1), (3, 2)):
        prefix = f"count_{balls}_{strikes}"
        opp = counters[f"{prefix}_opportunities"]
        swings = counters[f"{prefix}_swings"]
        out[f"{balls}-{strikes}"] = {
            "opportunities": opp,
            "reach_pct": pct(counters[f"{prefix}_reached"], counters["PA"]),
            "swing_pct": pct(swings, opp),
            "z_swing_pct": pct(counters[f"{prefix}_zone_swings"], counters[f"{prefix}_zone_opportunities"]),
            "chase_pct": pct(counters[f"{prefix}_chases"], counters[f"{prefix}_ball_opportunities"]),
            "contact_pct": pct(counters[f"{prefix}_contacts"], swings),
            "called_strike_per_pitch": pct(counters[f"{prefix}_called_strikes"], opp),
        }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
