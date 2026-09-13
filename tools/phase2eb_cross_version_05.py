#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, time
from collections import Counter
from datetime import date,timedelta
from pathlib import Path

from src.game_provider import GameFixture,ProductionGameProvider
from src.hitting.model import HitterSnapshot,HittingEngine,PitcherSnapshot
from src.rng import RNG

def h(x):return hashlib.sha256(repr(x).encode()).hexdigest()

def run_pa(seed,n):
    rng=RNG(seed); hitter=HitterSnapshot(100,100,100,100); pitcher=PitcherSnapshot(100,100,100); c=Counter(); seq=hashlib.sha256()
    t=time.perf_counter()
    for _ in range(n):
        o=HittingEngine(hitter,pitcher,100.0,rng).simulate_plate_appearance();c[o.result]+=1;seq.update(str(o.result).encode())
    elapsed=time.perf_counter()-t
    return {"n":n,"elapsed_s":elapsed,"us_per_pa":elapsed*1e6/n,"counts":dict(c),"sequence_hash":seq.hexdigest(),"rng_hash":h(rng.get_state())}

def game_signature(r):
    return repr(r)

def run_games(seed,n):
    rng=RNG(seed); provider=ProductionGameProvider(notable_event_limit=8); seq=hashlib.sha256(); totals=Counter()
    t=time.perf_counter()
    for i in range(n):
        r=provider.run_game(GameFixture(date(2026,4,1)+timedelta(days=i),"A","H"),rng)
        seq.update(game_signature(r).encode())
        # repr is the strongest exact-sequence contract; totals are supplementary.
        if hasattr(r,"away_score"): totals["away_score"]+=int(r.away_score)
        if hasattr(r,"home_score"): totals["home_score"]+=int(r.home_score)
    elapsed=time.perf_counter()-t
    return {"n":n,"elapsed_s":elapsed,"ms_per_game":elapsed*1e3/n,"sequence_hash":seq.hexdigest(),"rng_hash":h(rng.get_state()),"totals":dict(totals)}

def main():
    p=argparse.ArgumentParser();p.add_argument("--pa",type=int,default=200000);p.add_argument("--games",type=int,default=1000);p.add_argument("--seed",type=int,default=20260913);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    out={"pa":run_pa(a.seed,a.pa),"games":run_games(a.seed+1,a.games)}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__":main()
