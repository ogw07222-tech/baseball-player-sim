"""Validation-only experiments for the frozen experimental production hitter engine.

This module imports the real `src.simulation` implementation. It intentionally
contains no copied probability formula and never patches production constants.
"""
from __future__ import annotations
import csv,json,math
from dataclasses import dataclass
from pathlib import Path
from src.player import Player
from src.records import BattingLine
from src.rng import RNG
from src.simulation import simulate_player_game
from src.stats import PlayerStats
from tools.balance_lab.metrics import HittingMetrics,hitting_metrics

ROOT=Path(__file__).resolve().parents[2]
REPRESENTATIVE_NAMES=('오스틴','김도영','홍창기','김지찬','박해민','힐리어드','양의지')

@dataclass(frozen=True)
class Profile:
    contact:int=100;power:int=100;discipline:int=100;speed:int=100

def make_player(profile:Profile)->Player:
    return Player('BalanceLab',24,PlayerStats(profile.contact,profile.power,profile.discipline,profile.speed,100,100,100,100,100,100),traits=[],position='DH',development_profile='normal')

def simulate_profile(profile:Profile,pa:int,seed:int)->HittingMetrics:
    p=make_player(profile);rng=RNG(seed);line=BattingLine();remaining=int(pa)
    while remaining>0:
        n=min(4,remaining);simulate_player_game(p,100.0,rng,line,pa_count=n);remaining-=n
    return hitting_metrics(line)

def simulate_seasons(profile:Profile,seasons:int,seed:int)->HittingMetrics:
    total=BattingLine()
    for i in range(seasons):
        p=make_player(profile);rng=RNG(seed+i);line=BattingLine()
        for _ in range(150):simulate_player_game(p,100.0,rng,line,pa_count=4)
        total.add(line)
    return hitting_metrics(total)

def metric_delta(a:HittingMetrics,b:HittingMetrics)->dict[str,float]:
    return {k:float(getattr(b,k)-getattr(a,k)) for k in ('AVG','OBP','SLG','OPS','HR_rate','BB_rate','K_rate','H_rate','XBH_rate','BIP_rate','offensive_value')}

def marginal(base:int=100,seasons:int=100,seed:int=31000000)->dict[str,object]:
    baseline=simulate_seasons(Profile(base,base,base),seasons,seed);out={'baseline':baseline.as_dict(),'stats':{}}
    for name in ('contact','power','discipline'):
        idx={'contact':0,'power':1,'discipline':2}[name];entry={}
        for inc in (1,5,10):
            vals=[base,base,base,100];vals[idx]+=inc;m=simulate_seasons(Profile(*vals),seasons,seed);entry[str(inc)]={'result':m.as_dict(),'delta':metric_delta(baseline,m)}
        out['stats'][name]=entry
    return out

def build_allocations(budget:int=30,step:int=5):
    for dc in range(0,budget+1,step):
        for dp in range(0,budget-dc+1,step):yield dc,dp,budget-dc-dp

def build_search(seasons:int=100,seed:int=34000000,budget:int=30,step:int=5)->list[dict[str,object]]:
    rows=[]
    for dc,dp,dd in build_allocations(budget,step):
        m=simulate_seasons(Profile(100+dc,100+dp,100+dd),seasons,seed);rows.append({'dc':dc,'dp':dp,'dd':dd,**m.as_dict()})
    return sorted(rows,key=lambda r:float(r['offensive_value']),reverse=True)

def load_representatives(path:Path|None=None)->list[dict[str,str]]:
    path=path or ROOT/'data/kbo_2026_real_hitter_ratings_v4_provisional.csv'
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    by={r['name']:r for r in rows};return [by[n] for n in REPRESENTATIVE_NAMES]

def validate_real_players(seasons:int=100,seed:int=37000000)->list[dict[str,object]]:
    rows=[]
    for i,r in enumerate(load_representatives()):
        p=Profile(int(r['contact']),int(r['power']),int(r['discipline']),int(r['speed']));m=simulate_seasons(p,seasons,seed+i*100000)
        rows.append({'name':r['name'],'contact':p.contact,'power':p.power,'discipline':p.discipline,'target_avg':float(r['target_avg']),'target_obp':float(r['target_obp']),'target_slg':float(r['target_slg']),'target_ops':float(r['target_ops']),'target_hr_rate':float(r['target_hr_rate']),'target_bb_rate':float(r['target_bb_rate']),'target_k_rate':float(r['target_k_rate']),**{f'sim_{k}':v for k,v in m.as_dict().items() if k!='PA'}})
    return rows

def finite_metrics(metrics:HittingMetrics)->bool:return all(math.isfinite(float(v)) for k,v in metrics.as_dict().items() if k!='PA')
def write_json(path:Path,data:object)->None:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
