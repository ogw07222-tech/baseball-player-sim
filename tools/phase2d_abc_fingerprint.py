#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter
from datetime import date,timedelta
from src.hitting.model import HitterSnapshot,HittingEngine,PitcherSnapshot
from src.game_provider import GameFixture,ProductionGameProvider
from src.rng import RNG


def stable(v):
    if hasattr(v,'__dict__'): return {k:stable(x) for k,x in sorted(v.__dict__.items()) if k not in ('defensive_opportunity','defensive_resolution')}
    if isinstance(v,(tuple,list)): return [stable(x) for x in v]
    if isinstance(v,dict): return {k:stable(x) for k,x in sorted(v.items())}
    return v

def main():
    p=argparse.ArgumentParser(); p.add_argument('--pa',type=int,default=200000); p.add_argument('--games',type=int,default=1000); p.add_argument('--seed',type=int,default=20260912); a=p.parse_args()
    rng=RNG(a.seed); h=HitterSnapshot(100,100,100,100); pit=PitcherSnapshot(100,100,100); c=Counter(); sha=hashlib.sha256(); bips=0
    for _ in range(a.pa):
        o=HittingEngine(h,pit,100.0,rng).simulate_plate_appearance(); c[o.result]+=1
        if o.batted_ball and o.batted_ball.physical_state:
            bips+=1; s=o.batted_ball.physical_state
            payload={'result':o.result,'state':stable(s)}
            sha.update((json.dumps(payload,sort_keys=True,separators=(',',':'))+'\n').encode())
    pa_rng=rng.get_state()
    grng=RNG(a.seed+1); provider=ProductionGameProvider(notable_event_limit=8); gc=Counter(); gsha=hashlib.sha256()
    for i in range(a.games):
        g=provider.run_game(GameFixture(date(2026,4,1)+timedelta(days=i),'A','H'),grng)
        gsha.update(f'{g.away_score},{g.home_score},{g.innings_played},{len(g.notable_events)}\n'.encode())
        for pl in g.player_lines:
            x=pl.batting_line
            for k,v in {'PA':x.PA,'AB':x.AB,'H':x.H,'1B':x.singles,'2B':x.doubles,'3B':x.triples,'HR':x.HR,'BB':x.BB,'SO':x.SO,'HBP':x.HBP,'R':x.R,'ROE':x.ROE,'GDP':x.GDP,'SF':x.SF,'XBT':x.XBT,'XBT_attempts':x.XBT_attempts,'first_to_third':x.first_to_third,'second_to_home':x.second_to_home}.items(): gc[k]+=v
    out={'pa':a.pa,'bips':bips,'pa_results':dict(c),'phase2abc_hash':sha.hexdigest(),'pa_rng_state':pa_rng,'games':a.games,'game_totals':dict(gc),'game_sequence_hash':gsha.hexdigest(),'game_rng_state':grng.get_state()}
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
