#!/usr/bin/env python3
"""Validation-only offensive and Phase-1 pitch-structure decomposition."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
import json
from pathlib import Path
import statistics

from src import config
from src.game_provider import GameFixture, ProductionGameProvider
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.player import Player
from src.rng import RNG


def _pct(n, d):
    return n / d if d else 0.0


def _percentile(values, q):
    if not values:
        return 0.0
    ordered = sorted(values)
    return float(ordered[min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))])


def _dist(values):
    if not values:
        return {}
    return {
        "mean": statistics.mean(values),
        "p10": _percentile(values, .10),
        "p25": _percentile(values, .25),
        "p50": _percentile(values, .50),
        "p75": _percentile(values, .75),
        "p90": _percentile(values, .90),
        "p95": _percentile(values, .95),
        "p99": _percentile(values, .99),
        "min": min(values),
        "max": max(values),
    }


class TracedHittingEngine(HittingEngine):
    def __init__(self, *args, counters: Counter, **kwargs):
        super().__init__(*args, **kwargs)
        self.c = counters
        self.current = None
        self.count_seen = set()
        self.pitch_index = 0

    def _finish_current(self):
        cur = self.current
        if not cur or cur.get("finalized"):
            return
        cur["finalized"] = True
        self.c["takes"] += 1
        if cur["pitch"].is_strike:
            self.c["called_strikes"] += 1
            self.c["called_strike_in_zone_take"] += 1
        else:
            self.c["balls"] += 1
            self.c["ball_out_zone_take"] += 1

    def _pitch(self):
        self._finish_current()
        pitch = super()._pitch()
        self.pitch_index += 1
        self.c["pitches"] += 1
        self.c["in_zone"] += int(pitch.is_strike)
        self.c["out_zone"] += int(not pitch.is_strike)
        if self.pitch_index == 1:
            self.c["first_pitch_in_zone"] += int(pitch.is_strike)
        self.current = {
            "pitch": pitch,
            "swing": False,
            "finalized": False,
            "contact_result": None,
        }
        return pitch

    def _is_hit_by_pitch(self, pitch):
        result = super()._is_hit_by_pitch(pitch)
        if result:
            self.c["hbp_pitches"] += 1
            if self.current:
                self.current["finalized"] = True
        return result

    def _swing_probability(self, pitch, balls, strikes):
        count = (balls, strikes)
        if count not in self.count_seen:
            self.count_seen.add(count)
            if count == (0, 2):
                self.c["count_0_2_reached"] += 1
            elif count == (3, 0):
                self.c["count_3_0_reached"] += 1
            elif count == (3, 1):
                self.c["count_3_1_reached"] += 1
            elif count == (3, 2):
                self.c["count_3_2_reached"] += 1
        return super()._swing_probability(pitch, balls, strikes)

    def _contact_resolution(self, pitch, strikes):
        result = super()._contact_resolution(pitch, strikes)
        if self.current:
            self.current.update(swing=True, finalized=True, contact_result=result[0])
        self.c["swings"] += 1
        self.c["in_zone_swings"] += int(pitch.is_strike)
        self.c["out_zone_swings"] += int(not pitch.is_strike)
        if result[0] == "miss":
            self.c["swinging_strikes"] += 1
            self.c["whiffs"] += 1
            self.c["in_zone_whiffs"] += int(pitch.is_strike)
            self.c["out_zone_whiffs"] += int(not pitch.is_strike)
        else:
            self.c["contacts"] += 1
            self.c["in_zone_contacts"] += int(pitch.is_strike)
            self.c["out_zone_contacts"] += int(not pitch.is_strike)
            if result[0] == "foul":
                self.c["fouls"] += 1
                if strikes == 2:
                    self.c["two_strike_fouls"] += 1
            elif result[0] == "bip":
                self.c["bip"] += 1
        return result

    def _is_home_run(self, ball):
        self.c["hr_eligible_batted_balls"] += int(
            ball.ball_type != "ground_ball" and ball.depth == "deep"
        )
        result = super()._is_home_run(ball)
        self.c["hr_from_batted_ball"] += int(result)
        return result

    def _raw_hit_candidate(self, ball):
        result = super()._raw_hit_candidate(ball)
        self.c[f"raw_{result}"] += 1
        return result

    def _speed_resolve(self, candidate, ball):
        result = super()._speed_resolve(candidate, ball)
        self.c[f"speed_resolved_{result}"] += 1
        return result

    def simulate_plate_appearance(self):
        self.count_seen = set()
        self.current = None
        self.pitch_index = 0
        result = super().simulate_plate_appearance()
        self._finish_current()
        self.c["PA"] += 1
        self.c[f"pa_{result.result}"] += 1
        if result.raw_candidate:
            self.c[f"outcome_raw_{result.raw_candidate}"] += 1
        if result.resolved_candidate:
            self.c[f"outcome_resolved_{result.resolved_candidate}"] += 1
        if result.result == "strikeout":
            if (
                self.current
                and self.current.get("swing")
                and self.current.get("contact_result") == "miss"
            ):
                self.c["K_swinging"] += 1
            else:
                self.c["K_looking"] += 1
        return result


def _pitch_summary(c):
    pitches = c["pitches"]
    swings = c["swings"]
    in_zone = c["in_zone"]
    out_zone = c["out_zone"]
    pa = c["PA"]
    return {
        "counts": dict(sorted(c.items())),
        "rates": {
            "zone_pct": _pct(in_zone, pitches),
            "called_strike_pct": _pct(c["called_strikes"], pitches),
            "swinging_strike_pct": _pct(c["swinging_strikes"], pitches),
            "foul_pct": _pct(c["fouls"], pitches),
            "two_strike_foul_per_PA": _pct(c["two_strike_fouls"], pa),
            "BIP_pct": _pct(c["bip"], pitches),
            "swing_pct": _pct(swings, pitches),
            "take_pct": _pct(c["takes"], pitches),
            "in_zone_swing_pct": _pct(c["in_zone_swings"], in_zone),
            "out_zone_swing_pct": _pct(c["out_zone_swings"], out_zone),
            "contact_pct": _pct(c["contacts"], swings),
            "whiff_pct": _pct(c["whiffs"], swings),
            "in_zone_contact_pct": _pct(c["in_zone_contacts"], c["in_zone_swings"]),
            "out_zone_contact_pct": _pct(c["out_zone_contacts"], c["out_zone_swings"]),
            "pitches_per_PA": _pct(pitches, pa),
            "first_pitch_strike_pct": _pct(c["first_pitch_in_zone"], pa),
            "count_0_2_reached_pct": _pct(c["count_0_2_reached"], pa),
            "count_3_0_reached_pct": _pct(c["count_3_0_reached"], pa),
            "count_3_1_reached_pct": _pct(c["count_3_1_reached"], pa),
            "count_3_2_reached_pct": _pct(c["count_3_2_reached"], pa),
            "BB_pct": _pct(c["pa_walk"], pa),
            "HBP_pct": _pct(c["pa_hit_by_pitch"], pa),
            "K_pct": _pct(c["pa_strikeout"], pa),
            "HR_pct": _pct(c["pa_home_run"], pa),
            "H_per_PA": _pct(
                sum(c[f"pa_{x}"] for x in ("single", "double", "triple", "home_run")),
                pa,
            ),
            "2B_per_PA": _pct(c["pa_double"], pa),
            "3B_per_PA": _pct(c["pa_triple"], pa),
            "K_swinging_share": _pct(c["K_swinging"], c["pa_strikeout"]),
            "K_looking_share": _pct(c["K_looking"], c["pa_strikeout"]),
            "HR_per_BIP": _pct(c["pa_home_run"], c["bip"]),
            "HR_per_eligible_deep_air_ball": _pct(
                c["hr_from_batted_ball"], c["hr_eligible_batted_balls"]
            ),
        },
    }


def run_pitch_population(seed, pas, generated):
    rng = RNG(seed)
    counters = Counter()
    positions = tuple(config.POSITIONS)
    for i in range(pas):
        if generated:
            player = Player.random(f"D{i}", rng, position=positions[i % len(positions)])
            hitter = HitterSnapshot(
                float(player.stats.contact),
                float(player.stats.power),
                float(player.stats.discipline),
                float(player.stats.speed),
            )
        else:
            hitter = HitterSnapshot(100, 100, 100, 100)
        TracedHittingEngine(
            hitter,
            PitcherSnapshot(100, 100, 100),
            100.0,
            rng,
            counters=counters,
        ).simulate_plate_appearance()
    return _pitch_summary(counters)


def run_full_games(seed, games):
    rng = RNG(seed)
    provider = ProductionGameProvider(notable_event_limit=8)
    league = Counter()
    gruns, ghits, ghr, gbb, gk, gpa, ghbp = ([] for _ in range(7))
    for i in range(games):
        result = provider.run_game(
            GameFixture(date(2026, 4, 1) + timedelta(days=i), "Neutral Away", "Neutral Home"),
            rng,
        )
        game = Counter()
        for player_line in result.player_lines:
            line = player_line.batting_line
            vals = {
                "PA": line.PA,
                "AB": line.AB,
                "H": line.H,
                "1B": line.singles,
                "2B": line.doubles,
                "3B": line.triples,
                "HR": line.HR,
                "BB": line.BB,
                "SO": line.SO,
                "HBP": line.HBP,
                "R": line.R,
                "RBI": line.RBI,
                "ROE": line.ROE,
                "GDP": line.GDP,
                "SF": line.SF,
                "XBT": line.XBT,
                "XBT_attempts": line.XBT_attempts,
                "first_to_third": line.first_to_third,
                "second_to_home": line.second_to_home,
            }
            for key, value in vals.items():
                league[key] += value
                game[key] += value
        gruns.append(float(result.away_score + result.home_score))
        ghits.append(float(game["H"]))
        ghr.append(float(game["HR"]))
        gbb.append(float(game["BB"]))
        gk.append(float(game["SO"]))
        gpa.append(float(game["PA"]))
        ghbp.append(float(game["HBP"]))
    hits = league["H"]
    xbh = league["2B"] + league["3B"] + league["HR"]
    tb = league["1B"] + 2 * league["2B"] + 3 * league["3B"] + 4 * league["HR"]
    rates = {
        "1B_per_PA": _pct(league["1B"], league["PA"]),
        "2B_per_PA": _pct(league["2B"], league["PA"]),
        "3B_per_PA": _pct(league["3B"], league["PA"]),
        "HR_per_PA": _pct(league["HR"], league["PA"]),
        "BB_per_PA": _pct(league["BB"], league["PA"]),
        "K_per_PA": _pct(league["SO"], league["PA"]),
        "HBP_per_PA": _pct(league["HBP"], league["PA"]),
        "H_per_PA": _pct(hits, league["PA"]),
        "XBH_per_PA": _pct(xbh, league["PA"]),
        "XBH_per_H": _pct(xbh, hits),
        "TB_per_H": _pct(tb, hits),
        "AVG": _pct(hits, league["AB"]),
        "SLG": _pct(tb, league["AB"]),
        "ISO": _pct(tb, league["AB"]) - _pct(hits, league["AB"]),
        "R_per_H": _pct(league["R"], hits),
        "R_per_PA": _pct(league["R"], league["PA"]),
        "R_per_XBH": _pct(league["R"], xbh),
        "TB_per_R": _pct(tb, league["R"]),
        "XBT_success_rate": _pct(league["XBT"], league["XBT_attempts"]),
    }
    return {
        "games": games,
        "seed": seed,
        "totals": dict(league) | {"XBH": xbh, "TB": tb},
        "rates": rates,
        "identity_H_equals_hit_types": hits == league["1B"] + league["2B"] + league["3B"] + league["HR"],
        "game_distributions": {
            "runs": _dist(gruns),
            "hits": _dist(ghits),
            "HR": _dist(ghr),
            "BB": _dist(gbb),
            "K": _dist(gk),
            "HBP": _dist(ghbp),
            "PA": _dist(gpa),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10000)
    parser.add_argument("--pa-samples", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=20260906)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = {
        "full_games_neutral": run_full_games(args.seed, args.games),
        "pitch_neutral": run_pitch_population(args.seed + 1000000, args.pa_samples, False),
        "pitch_generated_hitter_population": run_pitch_population(
            args.seed + 2000000, args.pa_samples, True
        ),
        "notes": {
            "generated_population": "Player.random age-18/prospect hitter ratings versus neutral pitcher 100; isolation diagnostic, not mature KBO roster population.",
            "runner_observability": "Full BattingLine is used for ROE/XBT/first-to-third/second-to-home. LOB/base-state transition matrices still require separate RNG-free instrumentation if needed.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
