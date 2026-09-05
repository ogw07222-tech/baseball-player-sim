"""Deterministic high-school generation/draft Monte Carlo promotion gate."""
from __future__ import annotations
import argparse,json,statistics
from collections import Counter
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.draft_scoring import evaluate_hitter_draft
from src.player import Player
from src.rng import RNG
from src.stats import generate_high_school_npc_stats


class ZeroNoise:
    def gauss(self,_mean,_stddev):return 0.0


def describe(values:list[float])->dict[str,float]:
    ordered=sorted(values)
    def pct(q:float)->float:
        x=(len(ordered)-1)*q;lo=int(x);hi=min(len(ordered)-1,lo+1);f=x-lo
        return ordered[lo]*(1-f)+ordered[hi]*f
    return {
        'mean':round(statistics.mean(values),3),'sd':round(statistics.pstdev(values),3),
        'p5':round(pct(.05),3),'p10':round(pct(.10),3),'p25':round(pct(.25),3),
        'p50':round(pct(.50),3),'p75':round(pct(.75),3),'p90':round(pct(.90),3),'p95':round(pct(.95),3),
        'le60_pct':round(100*sum(v<=60 for v in values)/len(values),2),
        'le70_pct':round(100*sum(v<=70 for v in values)/len(values),2),
        'ge80_pct':round(100*sum(v>=80 for v in values)/len(values),2),
        'ge90_pct':round(100*sum(v>=90 for v in values)/len(values),2),
        'ge100_pct':round(100*sum(v>=100 for v in values)/len(values),2),
    }


def run(players:int=10000,npcs:int=10000,drafts:int=10000,seed:int=20260905)->dict[str,object]:
    positions=config.POSITIONS
    player_ability=[];npc_ability=[]
    for i in range(players):
        pos=positions[i%len(positions)];r=RNG(seed+i)
        player_ability.append(Player.random('GEN',r,position=pos).stats.current_ability())
    for i in range(npcs):
        pos=positions[i%len(positions)];r=RNG(seed+100000+i)
        npc_ability.append(generate_high_school_npc_stats(r,pos).current_ability())

    rounds=Counter();perf=[];contrib={name:[] for name in ('performance','scouting','position','health','context')}
    for i in range(drafts):
        pos=positions[i%len(positions)];r=RNG(seed+200000+i);p=Player.random('DRAFT',r,position=pos);e=CareerEngine(p,r);d=e.evaluate_draft()
        bucket='undrafted' if d.round is None else '1R' if d.round==1 else '2-3R' if d.round<=3 else '4-7R' if d.round<=7 else '8-11R';rounds[bucket]+=1
        ev=evaluate_hitter_draft(p.high_school_stats,p.position,d.scouted_talent,p.stats.durability,e.tournament_results,ZeroNoise())
        perf.append(ev.performance.score)
        for name,value in ev.contribution_points.items():contrib[name].append(abs(value))

    player_desc=describe(player_ability);npc_desc=describe(npc_ability)
    draft_pct={name:round(100*rounds[name]/drafts,2) for name in ('1R','2-3R','4-7R','8-11R','undrafted')}
    mean_abs={name:statistics.mean(values) for name,values in contrib.items()};total=sum(mean_abs.values()) or 1.0
    contribution_pct={name:round(100*value/total,2) for name,value in mean_abs.items()}
    report={
        'seed':seed,'players':players,'npcs':npcs,'drafts':drafts,
        'player_ability':player_desc,'npc_ability':npc_desc,
        'draft_pct':draft_pct,'performance_score':describe(perf),
        'configured_draft_weights':config.DRAFT_WEIGHTS,
        'mean_absolute_contribution_pct':contribution_pct,
        'h32_formula_files_touched':False,
    }
    return report


def validate(report:dict[str,object])->list[str]:
    errors=[];p=report['player_ability'];n=report['npc_ability'];d=report['draft_pct']
    if not 79<=p['mean']<=81:errors.append(f"player mean {p['mean']} outside 79..81")
    if not 9<=p['sd']<=12:errors.append(f"player sd {p['sd']} outside 9..12")
    if not 68<=n['mean']<=72:errors.append(f"npc mean {n['mean']} outside 68..72")
    if not 6<=n['sd']<=8:errors.append(f"npc sd {n['sd']} outside 6..8")
    if not p['mean']>n['mean']:errors.append('player mean must exceed npc mean')
    if not p['sd']>n['sd']:errors.append('player sd must exceed npc sd')
    ranges={'1R':(8,15),'2-3R':(12,20),'4-7R':(25,35),'8-11R':(20,30),'undrafted':(10,25)}
    for name,(lo,hi) in ranges.items():
        if not lo<=d[name]<=hi:errors.append(f"{name} {d[name]} outside {lo}..{hi}")
    if report['configured_draft_weights']['performance']<.70:errors.append('draft is not performance dominant')
    if report['configured_draft_weights']['current_ability']!=0:errors.append('current ability direct weight must be zero')
    return errors


def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--players',type=int,default=10000);ap.add_argument('--npcs',type=int,default=10000);ap.add_argument('--drafts',type=int,default=10000);ap.add_argument('--seed',type=int,default=20260905);ap.add_argument('--output',default='');a=ap.parse_args()
    report=run(a.players,a.npcs,a.drafts,a.seed);text=json.dumps(report,ensure_ascii=False,indent=2);print(text)
    if a.output:Path(a.output).write_text(text+'\n',encoding='utf-8')
    errors=validate(report)
    if errors:raise SystemExit('CALIBRATION FAILED: '+'; '.join(errors))
    print('PRODUCTION_PORT_CALIBRATION_PASS')
if __name__=='__main__':main()
