#!/usr/bin/env python3
"""Validation-only offensive and pitch-structure decomposition.

This tool does not modify or duplicate production probability constants. Pitch-level
measurement subclasses HittingEngine only to observe calls made by the production
PA implementation. Full-game measurement uses ProductionGameProvider directly.
"""
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


def _pct(n: float, d: float) -> float:
    return n / d if d else 0.0


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    return float(xs[min(len(xs)-1, max(0, int(round((len(xs)-1)*q))))])


def _dist(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    return {
        "mean": statistics.mean(values),
        "p10": _percentile(values,.10), "p25": _percentile(values,.25),
        "p50": _percentile(values,.50), "p75": _percentile(values,.75),
        "p90": _percentile(values,.90), "p95": _percentile(values,.95),
        "p99": _percentile(values,.99), "min": min(values), "max": max(values),
    }


class TracedHittingEngine(HittingEngine):
    """Observe the real HittingEngine control flow without changing probabilities."""
    def __init__(self, *args, counters: Counter, **kwargs):
        super().__init__(*args, **kwargs)
        self.c = counters
        self.current = None
        self.count_seen: set[tuple[int,int]] = set()

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
        self.c["pitches"] += 1
        self.c["in_zone"] += int(pitch.is_strike)
        self.c["out_zone"] += int(not pitch.is_strike)
        self.current = {"pitch": pitch, "swing": False, "finalized": False, "contact_result": None}
        return pitch

    def _swing_probability(self, pitch, balls, strikes):
        if self.current is not None:
            self.current["balls"] = balls
            self.current["strikes"] = strikes
        count = (balls, strikes)
        if count not in self.count_seen:
            self.count_seen.add(count)
            if count == (0,2): self.c["count_0_2_reached"] += 1
            if count == (3,0): self.c["count_3_0_reached"] += 1
            if count == (3,2): self.c["count_3_2_reached"] += 1
        return super()._swing_probability(pitch, balls, strikes)

    def _contact_resolution(self, pitch, strikes):
        result = super()._contact_resolution(pitch, strikes)
        if self.current is not None:
            self.current["swing"] = True
            self.current["finalized"] = True
            self.current["contact_result"] = result[0]
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
            if result[0] == "foul": self.c["fouls"] += 1
            elif result[0] == "bip": self.c["bip"] += 1
        return result

    def _is_home_run(self, ball):
        eligible = ball.ball_type != "ground_ball" and ball.depth == "deep"
        self.c["hr_eligible_batted_balls"] += int(eligible)
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
        result = super().simulate_plate_appearance()
        self._finish_current()
        self.c["PA"] += 1
        self.c[f"pa_{result.result}"] += 1
        if result.raw_candidate:
            self.c[f"outcome_raw_{result.raw_candidate}"] += 1
        if result.resolved_candidate:
            self.c[f"outcome_resolved_{result.resolved_candidate}"] += 1
        if result.result == "strikeout":
            if self.current and self.current.get("swing") and self.current.get("contact_result") == "miss":
                self.c["K_swinging"] += 1
            else:
                self.c["K_looking"] += 1
        elif result.result == "walk":
            self.c["walks"] += 1
        elif result.result == "hit_by_pitch":
            self.c["HBP"] += 1
        return result


def _pitch_summary(c: Counter) -> dict[str, object]:
    p, swings = c["pitches"], c["swings"]
    inz, outz = c["in_zone"], c["out_zone"]
    return {
        "counts": dict(sorted(c.items())),
        "rates": {
            "zone_pct": _pct(inz,p), "strike_pct_observed": _pct(c["called_strikes"]+c["swinging_strikes"]+c["fouls"]+c["bip"],p),
            "called_strike_pct": _pct(c["called_strikes"],p), "swinging_strike_pct": _pct(c["swinging_strikes"],p),
            "foul_pct": _pct(c["fouls"],p), "bip_pitch_pct": _pct(c["bip"],p),
            "swing_pct": _pct(swings,p), "take_pct": _pct(c["takes"],p),
            "in_zone_swing_pct": _pct(c["in_zone_swings"],inz), "out_zone_swing_pct": _pct(c["out_zone_swings"],outz),
            "contact_pct": _pct(c["contacts"],swings), "whiff_pct": _pct(c["whiffs"],swings),
            "in_zone_contact_pct": _pct(c["in_zone_contacts"],c["in_zone_swings"]),
            "out_zone_contact_pct": _pct(c["out_zone_contacts"],c["out_zone_swings"]),
            "BB_pct": _pct(c["pa_walk"],c["PA"]), "K_pct": _pct(c["pa_strikeout"],c["PA"]),
            "HR_pct": _pct(c["pa_home_run"],c["PA"]),
            "H_per_PA": _pct(sum(c[f"pa_{x}"] for x in ("single","double","triple","home_run")),c["PA"]),
            "2B_per_PA": _pct(c["pa_double"],c["PA"]), "3B_per_PA": _pct(c["pa_triple"],c["PA"]),
            "K_swinging_share": _pct(c["K_swinging"],c["pa_strikeout"]),
            "K_looking_share": _pct(c["K_looking"],c["pa_strikeout"]),
            "first_pitch_strike_proxy": None,
        }
    }


def run_pitch_population(seed: int, pas: int, generated: bool) -> dict[str, object]:
    rng = RNG(seed)
    c = Counter()
    positions = tuple(config.POSITIONS)
    for i in range(pas):
        if generated:
            pl = Player.random(f"D{i}", rng, position=positions[i % len(positions)])
            h = HitterSnapshot(float(pl.stats.contact), float(pl.stats.power), float(pl.stats.discipline), float(pl.stats.speed))
        else:
            h = HitterSnapshot(100,100,100,100)
        engine = TracedHittingEngine(h, PitcherSnapshot(100,100,100), 100.0, rng, counters=c)
        engine.simulate_plate_appearance()
    return _pitch_summary(c)


def run_full_games(seed: int, games: int) -> dict[str, object]:
    rng = RNG(seed)
    provider = ProductionGameProvider(notable_event_limit=8)
    league = Counter()
    gruns=[]; ghits=[]; ghr=[]; gbb=[]; gk=[]; gpa=[]
    for i in range(games):
        result = provider.run_game(GameFixture(date(2026,4,1)+timedelta(days=i),"Neutral Away","Neutral Home"), rng)
        game = Counter()
        for line in result.player_lines:
            s=line.stats
            vals={"PA":s.PA,"AB":s.AB,"H":s.H,"1B":s.singles,"2B":s.doubles,"3B":s.triples,"HR":s.HR,"BB":s.BB,"SO":s.SO,"HBP":s.HBP,"R":s.R,"RBI":s.RBI,"GDP":s.GDP,"SF":s.SF,"E":s.ROE,"XBT":s.XBT,"XBT_attempts":s.XBT_attempts,"first_to_third":s.first_to_third,"second_to_home":s.second_to_home}
            for k,v in vals.items(): league[k]+=v; game[k]+=v
        gruns.append(float(result.away_score+result.home_score)); ghits.append(float(game["H"])); ghr.append(float(game["HR"])); gbb.append(float(game["BB"])); gk.append(float(game["SO"])); gpa.append(float(game["PA"]))
    H=league["H"]; xbh=league["2B"]+league["3B"]+league["HR"]
    tb=league["1B"]+2*league["2B"]+3*league["3B"]+4*league["HR"]
    rates={
        "1B_per_PA":_pct(league["1B"],league["PA"]),"2B_per_PA":_pct(league["2B"],league["PA"]),"3B_per_PA":_pct(league["3B"],league["PA"]),"HR_per_PA":_pct(league["HR"],league["PA"]),"XBH_per_PA":_pct(xbh,league["PA"]),"XBH_per_H":_pct(xbh,H),"TB_per_H":_pct(tb,H),"AVG":_pct(H,league["AB"]),"SLG":_pct(tb,league["AB"]),"ISO":_pct(tb,league["AB"])-_pct(H,league["AB"]),"R_per_H":_pct(league["R"],H),"R_per_PA":_pct(league["R"],league["PA"]),"R_per_XBH":_pct(league["R"],xbh),"TB_per_R":_pct(tb,league["R"]),"XBT_success_rate":_pct(league["XBT"],league["XBT_attempts"]),
    }
    return {"games":games,"seed":seed,"totals":dict(league)|{"XBH":xbh,"TB":tb},"rates":rates,"identity_H_equals_hit_types":H==league["1B"]+league["2B"]+league["3B"]+league["HR"],"game_distributions":{"runs":_dist(gruns),"hits":_dist(ghits),"HR":_dist(ghr),"BB":_dist(gbb),"K":_dist(gk),"PA":_dist(gpa)}}


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--games",type=int,default=10000); ap.add_argument("--pa-samples",type=int,default=200000); ap.add_argument("--seed",type=int,default=20260906); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    out={"full_games_neutral":run_full_games(a.seed,a.games),"pitch_neutral":run_pitch_population(a.seed+1000000,a.pa_samples,False),"pitch_generated_hitter_population":run_pitch_population(a.seed+2000000,a.pa_samples,True),"notes":{"generated_population":"Player.random age-18/prospect hitter ratings vs neutral pitcher 100; this isolates hitter-rating distribution from engine baseline and is not a claim about a complete KBO roster population.","unavailable_exact":"LOB and base-state-specific runner denominators are not persisted by ProductionGameResult; XBT/GDP/SF/ROE and first_to_third/second_to_home counters are reported instead."}}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
