#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,time
from datetime import date,timedelta
from src.hitting.model import HitterSnapshot,HittingEngine,PitcherSnapshot
from src.game_provider import GameFixture,ProductionGameProvider
from src.rng import RNG

def main():
    p=argparse.ArgumentParser(); p.add_argument('--pa',type=int,default=50000); p.add_argument('--games',type=int,default=500); p.add_argument('--seed',type=int,default=20260912); a=p.parse_args()
    rng=RNG(a.seed); h=HitterSnapshot(100,100,100,100); pit=PitcherSnapshot(100,100,100)
    t=time.perf_counter()
    for _ in range(a.pa): HittingEngine(h,pit,100.0,rng).simulate_plate_appearance()
    pa_s=time.perf_counter()-t
    rng=RNG(a.seed+1); provider=ProductionGameProvider(notable_event_limit=8); t=time.perf_counter()
    for i in range(a.games): provider.run_game(GameFixture(date(2026,4,1)+timedelta(days=i),'A','H'),rng)
    game_s=time.perf_counter()-t
    print(json.dumps({'pa':a.pa,'games':a.games,'pa_seconds':pa_s,'us_per_pa':pa_s/a.pa*1e6,'game_seconds':game_s,'ms_per_game':game_s/a.games*1e3},sort_keys=True))
if __name__=='__main__': main()
