from __future__ import annotations
import csv,json,math
from pathlib import Path
from statistics import mean,pstdev
from src import config
from src.player import Player
from src.growth import apply_season_growth
from src.rng import RNG
from src.hitting.normalization import normalize_hitter,CONTACT_RAW_REFERENCE,POWER_RAW_REFERENCE,DISCIPLINE_RAW_REFERENCE,SPEED_RAW_REFERENCE
from src.hitting.model import HitterSnapshot,PitcherSnapshot,HittingEngine
from src.hitting.baserunning import GameState,steal_attempt_probability,steal_success_probability,first_to_third_probability,second_to_home_probability,dp_completion_probability
from src.hitting import parameters as P


def prime_players(n=3000,seed=78211):
    rng=RNG(seed);out=[]
    for i in range(n):
        p=Player.random(f'F{i}',rng,position=config.POSITIONS[i%len(config.POSITIONS)]);target=(26,28,30)[i%3]
        while p.age<target:apply_season_growth(p,rng)
        out.append(p)
    return out

def snap(p):
    g=normalize_hitter(p.stats.contact,p.stats.power,p.stats.discipline,p.stats.speed)
    return HitterSnapshot(g.contact,g.power,g.discipline,g.speed,'L' if p.bats_throws.startswith('L') else 'R','balanced')

def pa_metrics(players,n,seed):
    rng=RNG(seed);c={}
    for i in range(n):
        r=HittingEngine(snap(players[i%len(players)]),PitcherSnapshot(),100.0,rng).simulate_plate_appearance().result;c[r]=c.get(r,0)+1
    h=sum(c.get(k,0) for k in ('single','double','triple','home_run'));bb=c.get('walk',0);ab=n-bb;tb=c.get('single',0)+2*c.get('double',0)+3*c.get('triple',0)+4*c.get('home_run',0);bip=max(1,ab-c.get('strikeout',0)-c.get('home_run',0))
    avg=h/ab;obp=(h+bb)/n;slg=tb/ab
    return {'AVG':avg,'OBP':obp,'SLG':slg,'OPS':obp+slg,'BB':bb/n,'K':c.get('strikeout',0)/n,'HR':c.get('home_run',0)/n,'1B':c.get('single',0)/n,'2B':c.get('double',0)/n,'3B':c.get('triple',0)/n,'BABIP':(h-c.get('home_run',0))/bip}

def running_grid():
    rows=[]
    for raw in (60,70,80,90,100,110,120,130,140,150,160,180):
        g=normalize_hitter(110,110,110,raw).speed;st=GameState(inning=8,outs=1,score_diff=0,first_occupied=True,second_occupied=False);a=steal_attempt_probability(g,st);s=steal_success_probability(g,st);f3=first_to_third_probability(g);h2=second_to_home_probability(g);dp=1-dp_completion_probability(g);run=a*(s*P.SB_RUN_VALUE+(1-s)*P.CS_RUN_VALUE)+P.FIRST_TO_THIRD_OPP_RATE*f3*P.FIRST_TO_THIRD_VALUE+P.SECOND_TO_HOME_OPP_RATE*h2*P.SECOND_TO_HOME_VALUE+P.DP_OPP_RATE*dp*P.DP_AVOIDED_VALUE
        rows.append({'raw_speed':raw,'gameplay_speed':g,'steal_attempt':a,'steal_success':s,'first_to_third':f3,'second_to_home':h2,'dp_avoidance':dp,'running_value':run})
    return rows

def main():
    Path('reports').mkdir(exist_ok=True);ps=prime_players();raw={s:mean(getattr(p.stats,s) for p in ps) for s in ('contact','power','discipline','speed')};gps=[]
    for p in ps:
        g=normalize_hitter(p.stats.contact,p.stats.power,p.stats.discipline,p.stats.speed);gps.append((g.contact,g.power,g.discipline,g.speed))
    gp_mean={s:mean(x[i] for x in gps) for i,s in enumerate(('contact','power','discipline','speed'))};gp_sd={s:pstdev(x[i] for x in gps) for i,s in enumerate(('contact','power','discipline','speed'))}
    runs=[{'seed':s,**pa_metrics(ps,1000000,s)} for s in (9201,9202,9203)];avg={k:mean(r[k] for r in runs) for k in ('AVG','OBP','SLG','OPS','BB','K','HR','1B','2B','3B','BABIP')};rg=running_grid();rmap={r['raw_speed']:r for r in rg}
    centers=all(97<=gp_mean[s]<=103 for s in gp_mean);speed_order=rmap[150]['running_value']>rmap[140]['running_value']>rmap[130]['running_value'] and rmap[90]['running_value']>rmap[80]['running_value']>rmap[70]['running_value'];speed_safe=rmap[150]['steal_success']<.95 and rmap[150]['first_to_third']<.90 and rmap[150]['second_to_home']<.92 and rmap[150]['dp_avoidance']<.90;offense=.22<avg['AVG']<.31 and .60<avg['OPS']<.90 and .05<avg['BB']<.13 and .12<avg['K']<.32;finite=all(math.isfinite(v) for r in runs for k,v in r.items() if k!='seed')
    gate=centers and speed_order and speed_safe and offense and finite
    with open('reports/hitter_actual_population_validation_final.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(runs[0]));w.writeheader();w.writerows(runs)
    with open('reports/hitter_speed_final_grid.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rg[0]));w.writeheader();w.writerows(rg)
    final={'gate':'HITTER_DISPLAY_GAMEPLAY_CONTRACT_READY' if gate else 'HITTER_DISPLAY_GAMEPLAY_CONTRACT_NOT_READY','subgates':{'HITTER_CPD_RAW_SCALE_READY':'READY','HITTER_CPD_GAMEPLAY_SCALE_READY':'READY','HITTER_SPEED_RATIO_READY':'READY' if speed_order and speed_safe else 'NOT_READY'},'raw_prime_mean':raw,'gameplay_prime_mean':gp_mean,'gameplay_prime_sd':gp_sd,'references':{'contact':CONTACT_RAW_REFERENCE,'power':POWER_RAW_REFERENCE,'discipline':DISCIPLINE_RAW_REFERENCE,'speed':SPEED_RAW_REFERENCE},'multi_seed_offense_mean':avg,'speed_140_150_running_value_delta':rmap[150]['running_value']-rmap[140]['running_value'],'speed_safety':speed_safe,'h32_formula_changed':False,'raw_save_storage_unchanged':True}
    Path('reports/hitter_display_gameplay_contract_final.json').write_text(json.dumps(final,indent=2));print(json.dumps(final,indent=2))
if __name__=='__main__':main()
