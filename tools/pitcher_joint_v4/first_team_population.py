from __future__ import annotations

"""Build a production-faithful hitter population weighted by actual first-team PA.

This diagnostic intentionally drives the real CareerEngine roster flow instead
of assigning equal KBO weight to randomly sampled developing prospects.  The
raw player state remains canonical; gameplay values are derived only through
src.hitting.normalization.
"""

import argparse
import bisect
import json
import random
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.normalization import normalize_hitter
from src.player import Player
from src.rng import RNG


@dataclass(frozen=True)
class WeightedSeason:
    age: int
    pa: int
    contact: float
    power: float
    discipline: float
    speed: float
    bats_throws: str

    def gameplay(self):
        return normalize_hitter(self.contact, self.power, self.discipline, self.speed)


def build_first_team_seasons(n: int, seed: int, max_seasons: int) -> list[WeightedSeason]:
    seasons: list[WeightedSeason] = []
    positions = tuple(config.POSITIONS)
    for i in range(n):
        rng = RNG(seed + i * 1009)
        player = Player.random(f"FT{i}", rng, position=positions[i % len(positions)])
        career = CareerEngine(player, rng)
        career.evaluate_draft()
        for _ in range(max_seasons):
            if career.phase != "PRO":
                break
            before = WeightedSeason(
                age=player.age,
                pa=0,
                contact=float(player.stats.contact),
                power=float(player.stats.power),
                discipline=float(player.stats.discipline),
                speed=float(player.stats.speed),
                bats_throws=player.bats_throws,
            )
            record, _growth = career.finish_pro_season()
            first_pa = int(record.first_team.PA)
            if first_pa > 0:
                seasons.append(WeightedSeason(**{**before.__dict__, "pa": first_pa}))
            if career.should_retire():
                career.retire()
    return seasons


def weighted_mean(rows: list[WeightedSeason], attr: str) -> float:
    total = sum(r.pa for r in rows)
    return sum(getattr(r, attr) * r.pa for r in rows) / total


def weighted_gameplay_mean(rows: list[WeightedSeason], index: int) -> float:
    total = sum(r.pa for r in rows)
    return sum(tuple(r.gameplay().__dict__.values())[index] * r.pa for r in rows) / total


def pa_sampler(rows: list[WeightedSeason], seed: int):
    cumulative=[]; running=0
    for row in rows:
        running += row.pa
        cumulative.append(running)
    rng=random.Random(seed)
    while True:
        x=rng.randrange(running)
        yield rows[bisect.bisect_right(cumulative,x)]


def snapshot(row: WeightedSeason) -> HitterSnapshot:
    g=row.gameplay()
    return HitterSnapshot(g.contact,g.power,g.discipline,g.speed,
                          "L" if row.bats_throws.startswith("L") else "R","balanced")


def offense(rows: list[WeightedSeason], pa: int, seed: int) -> dict[str,float]:
    choose=pa_sampler(rows,seed); rng=random.Random(seed ^ 0xC0DE); c=Counter()
    for _ in range(pa):
        row=next(choose)
        out=HittingEngine(snapshot(row),PitcherSnapshot(),100.0,rng).simulate_plate_appearance()
        c[out.result]+=1
    bb=c['walk']; so=c['strikeout']; hr=c['home_run']; one=c['single']; two=c['double']; three=c['triple']
    hits=one+two+three+hr; ab=max(1,pa-bb); bip=max(1,ab-so-hr); obp=(hits+bb)/pa
    slg=(one+2*two+3*three+4*hr)/ab
    return {'AVG':hits/ab,'OBP':obp,'SLG':slg,'OPS':obp+slg,'BB%':bb/pa,'K%':so/pa,
            'HR%':hr/pa,'1B%':one/pa,'2B%':two/pa,'3B%':three/pa,'BABIP':(hits-hr)/bip}


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--players',type=int,default=600)
    ap.add_argument('--max-seasons',type=int,default=18); ap.add_argument('--pa',type=int,default=500000)
    ap.add_argument('--seed',type=int,default=261206); args=ap.parse_args()
    rows=build_first_team_seasons(args.players,args.seed,args.max_seasons)
    if not rows: raise RuntimeError('no first-team PA seasons produced')
    total_pa=sum(r.pa for r in rows)
    gp_names=('contact','power','discipline','speed')
    raw={s:weighted_mean(rows,s) for s in gp_names}
    gp={s:weighted_gameplay_mean(rows,i) for i,s in enumerate(gp_names)}
    ages=[]
    for r in rows: ages.extend([r.age]*r.pa)
    result={
        'contract':'production CareerEngine first-team PA-weighted hitter seasons',
        'players':args.players,'season_snapshots':len(rows),'total_first_team_pa':total_pa,
        'pa_weighted_age_mean':statistics.fmean(ages),
        'raw_pa_weighted_mean':raw,'gameplay_pa_weighted_mean':gp,
        'neutral_pitcher_offense':offense(rows,args.pa,args.seed+1),
        'note':'Calibration diagnostic only; production roster/growth/H3 formulas are unchanged.'
    }
    Path('reports').mkdir(exist_ok=True)
    Path('reports/pitcher_joint_v4_first_team_population.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
