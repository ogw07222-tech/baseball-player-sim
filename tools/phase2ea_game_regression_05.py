#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
from src.game_provider import GameFixture,ProductionGameProvider
from src.rng import RNG

def run(seed,games,disabled):
    rng=RNG(seed); provider=ProductionGameProvider(notable_event_limit=8); h=hashlib.sha256(); samples=[]
    ctx=patch('src.hitting.ground_travel.generate_ground_travel_state',return_value=None) if disabled else None
    if ctx: ctx.start()
    try:
        for i in range(games):
            result=provider.run_game(GameFixture(date(2026,4,1)+timedelta(days=i),'A','H'),rng)
            r=repr(result); h.update(r.encode())
            if i<3: samples.append(r)
    finally:
        if ctx: ctx.stop()
    return {'sequence_hash':h.hexdigest(),'rng_hash':hashlib.sha256(repr(rng.get_state()).encode()).hexdigest(),'samples':samples}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--games',type=int,default=1000); p.add_argument('--seed',type=int,default=20260913); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    enabled=run(a.seed,a.games,False); disabled=run(a.seed,a.games,True)
    out={'games':a.games,'seed':a.seed,'enabled':enabled,'disabled':disabled,'sequence_equal':enabled['sequence_hash']==disabled['sequence_hash'],'rng_equal':enabled['rng_hash']==disabled['rng_hash']}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
if __name__=='__main__': main()
