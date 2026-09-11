#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, statistics
from collections import Counter, defaultdict
from pathlib import Path
from src import config
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.player import Player
from src.rng import RNG

COUNTS=[(b,s) for b in range(4) for s in range(3)]
KEY_COUNTS=[(3,0),(3,1),(3,2),(0,2),(1,2),(2,2)]

def pct(n,d): return n/d if d else 0.0

def qtile(xs,q):
    ys=sorted(xs); return ys[min(len(ys)-1,max(0,int(round((len(ys)-1)*q))))] if ys else 0

class Trace(HittingEngine):
    def __init__(self,*a,global_c:Counter,count_c:dict,**kw):
        super().__init__(*a,**kw); self.g=global_c; self.cc=count_c; self.cur=None; self.last_count=None
    def _finish_take(self):
        c=self.cur
        if not c or c.get('done'): return
        c['done']=True; key=c['count']; pitch=c['pitch']; d=self.cc[key]; self.g['takes']+=1; d['takes']+=1
        if pitch.is_strike:
            self.g['called_strikes']+=1; d['called_strikes']+=1
            if key[1]==2:
                self.g['looking_k']+=1; d['terminal_looking_k']+=1
        else:
            self.g['balls']+=1; d['balls']+=1
    def _pitch(self):
        self._finish_take(); p=super()._pitch(); self.g['pitches']+=1; self.g['in_zone']+=int(p.is_strike); self.g['out_zone']+=int(not p.is_strike)
        self.cur={'pitch':p,'done':False,'count':None}; return p
    def _is_hit_by_pitch(self,p):
        r=super()._is_hit_by_pitch(p)
        if r:
            self.g['hbp']+=1
            if self.cur: self.cur['done']=True
        return r
    def _swing_probability(self,p,b,s):
        key=(b,s); self.last_count=key; d=self.cc[key]; d['pitches']+=1; d['in_zone']+=int(p.is_strike); d['out_zone']+=int(not p.is_strike)
        if self.cur: self.cur['count']=key
        return super()._swing_probability(p,b,s)
    def _contact_resolution(self,p,strikes):
        key=self.last_count; d=self.cc[key]; r=super()._contact_resolution(p,strikes)
        if self.cur: self.cur['done']=True
        self.g['swings']+=1; d['swings']+=1; self.g['zswings']+=int(p.is_strike); d['zswings']+=int(p.is_strike); self.g['chases']+=int(not p.is_strike); d['chases']+=int(not p.is_strike)
        if r[0]=='miss':
            self.g['whiffs']+=1; d['whiffs']+=1
            if strikes==2: self.g['swinging_k']+=1; d['terminal_swinging_k']+=1
        else:
            self.g['contacts']+=1; d['contacts']+=1
            if p.is_strike: self.g['zcontacts']+=1; d['zcontacts']+=1
            else: self.g['ocontacts']+=1; d['ocontacts']+=1
            if r[0]=='foul':
                self.g['fouls']+=1; d['fouls']+=1
                if strikes==2: self.g['two_strike_fouls']+=1; d['two_strike_fouls']+=1
            elif r[0]=='bip': self.g['bip']+=1; d['bip']+=1
        return r
    def simulate_plate_appearance(self):
        self.cur=None; self.last_count=None; seen=set(); orig=self._swing_probability
        def wrapped(p,b,s):
            key=(b,s)
            if key not in seen: seen.add(key); self.cc[key]['reached']+=1
            return orig(p,b,s)
        self._swing_probability=wrapped
        try: out=super().simulate_plate_appearance()
        finally: self._swing_probability=orig
        self._finish_take(); self.g['PA']+=1; self.g['pa_'+out.result]+=1
        return out

def summarize(g,cc):
    p=g['pitches']; sw=g['swings']; inz=g['in_zone']; outz=g['out_zone']; pa=g['PA']; k=g['pa_strikeout']
    global_rates={
      'zone_pct':pct(inz,p),'swing_pct':pct(sw,p),'z_swing_pct':pct(g['zswings'],inz),'chase_pct':pct(g['chases'],outz),
      'contact_pct':pct(g['contacts'],sw),'z_contact_pct':pct(g['zcontacts'],g['zswings']),'o_contact_pct':pct(g['ocontacts'],g['chases']),
      'whiff_per_swing':pct(g['whiffs'],sw),'swinging_strike_per_pitch':pct(g['whiffs'],p),'called_strike_per_pitch':pct(g['called_strikes'],p),
      'foul_per_pitch':pct(g['fouls'],p),'two_strike_foul_per_pa':pct(g['two_strike_fouls'],pa),'pitches_per_pa':pct(p,pa),
      'BB_pct':pct(g['pa_walk'],pa),'K_pct':pct(k,pa),'swinging_K_share':pct(g['swinging_k'],k),'looking_K_share':pct(g['looking_k'],k),
      'HBP_pct':pct(g['pa_hit_by_pitch'],pa),'H_per_PA':pct(sum(g['pa_'+x] for x in ('single','double','triple','home_run')),pa),'HR_per_PA':pct(g['pa_home_run'],pa)
    }
    count_rates={}
    for key in COUNTS:
        d=cc[key]; pitches=d['pitches']; swings=d['swings']; iz=d['in_zone']; oz=d['out_zone']
        count_rates[f'{key[0]}-{key[1]}']={
          'reach_per_PA':pct(d['reached'],pa),'swing_pct':pct(swings,pitches),'z_swing_pct':pct(d['zswings'],iz),'chase_pct':pct(d['chases'],oz),
          'contact_pct':pct(d['contacts'],swings),'whiff_per_swing':pct(d['whiffs'],swings),'foul_per_swing':pct(d['fouls'],swings),
          'called_strike_rate':pct(d['called_strikes'],pitches),'terminal_looking_K_per_reach':pct(d['terminal_looking_k'],d['reached']),
          'terminal_swinging_K_per_reach':pct(d['terminal_swinging_k'],d['reached'])}
    return {'global':global_rates,'counts':count_rates,'raw':dict(g)}

def run_population(seed,pas,generated=False,buckets=False):
    gen_rng=RNG(seed); sim_rng=RNG(seed+1); positions=tuple(config.POSITIONS); players=[]
    if generated:
        for i in range(pas): players.append(Player.random(f'P{i}',gen_rng,position=positions[i%len(positions)]))
        ds=[p.stats.discipline for p in players]; lo=qtile(ds,.333); hi=qtile(ds,.667)
    else: lo=hi=100
    g=Counter(); cc=defaultdict(Counter); bucket=defaultdict(lambda:(Counter(),defaultdict(Counter)))
    for i in range(pas):
        if generated:
            pl=players[i]; h=HitterSnapshot(float(pl.stats.contact),float(pl.stats.power),float(pl.stats.discipline),float(pl.stats.speed)); name='low' if pl.stats.discipline<=lo else ('high' if pl.stats.discipline>=hi else 'mid')
        else:
            h=HitterSnapshot(100,100,100,100); name='neutral'
        Trace(h,PitcherSnapshot(100,100,100),100.0,sim_rng,global_c=g,count_c=cc).simulate_plate_appearance()
        if generated and buckets:
            # independent same-rating one-PA probe for bucket chase only, avoids post-hoc shared-counter ambiguity
            bg,bcc=bucket[name]; Trace(h,PitcherSnapshot(100,100,100),100.0,RNG(seed+3000000+i),global_c=bg,count_c=bcc).simulate_plate_appearance()
    out=summarize(g,cc)
    if generated and buckets:
        out['discipline_thresholds']={'low_max':lo,'high_min':hi}
        out['discipline_buckets']={k:{'n_pa':v[0]['PA'],'chase_pct':pct(v[0]['chases'],v[0]['out_zone']),'swing_pct':pct(v[0]['swings'],v[0]['pitches']),'K_pct':pct(v[0]['pa_strikeout'],v[0]['PA']),'BB_pct':pct(v[0]['pa_walk'],v[0]['PA'])} for k,v in bucket.items()}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pa-samples',type=int,default=200000); ap.add_argument('--seed',type=int,default=20260906); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    out={'seed':a.seed,'pa_samples_each':a.pa_samples,'neutral':run_population(a.seed+1000000,a.pa_samples),'generated_prospect':run_population(a.seed+2000000,a.pa_samples,True,True),'key_counts':[f'{b}-{s}' for b,s in KEY_COUNTS]}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
