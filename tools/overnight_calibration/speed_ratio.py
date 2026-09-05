from __future__ import annotations
import csv,json
from pathlib import Path
from statistics import mean
from src.rng import RNG
from src.hitting.model import HitterSnapshot,PitcherSnapshot,HittingEngine
from src.hitting.baserunning import GameState,steal_attempt_probability,steal_success_probability,first_to_third_probability,second_to_home_probability,dp_completion_probability
from src.hitting import parameters as P

REF_A=98.10803333333332
REF_B=110.0
SLOPES=(.4,.6,.8,1.0,1.2)
RAW_GRID=(60,70,80,90,100,110,120,130,140,150,160,180)

def gp(raw,ref,slope):return 100+(raw-ref)*slope

def pa(speed_gp,n=60000,seed=1):
    rng=RNG(seed);c={}
    for _ in range(n):
        r=HittingEngine(HitterSnapshot(100,100,100,speed_gp),PitcherSnapshot(),100,rng).simulate_plate_appearance().result;c[r]=c.get(r,0)+1
    h=sum(c.get(k,0) for k in ('single','double','triple','home_run'));bb=c.get('walk',0);ab=n-bb;tb=c.get('single',0)+2*c.get('double',0)+3*c.get('triple',0)+4*c.get('home_run',0);bip=max(1,ab-c.get('strikeout',0)-c.get('home_run',0));
    return {'AVG':h/ab,'OBP':(h+bb)/n,'SLG':tb/ab,'BB':bb/n,'K':c.get('strikeout',0)/n,'HR':c.get('home_run',0)/n,'1B':c.get('single',0)/n,'2B':c.get('double',0)/n,'3B':c.get('triple',0)/n,'BABIP':(h-c.get('home_run',0))/bip,'OUT':(c.get('out',0)+c.get('strikeout',0))/n}

def running(speed_gp,obp):
    contexts=[GameState(inning=i,outs=o,score_diff=d,first_occupied=True,second_occupied=False) for i in (3,8) for o in (0,1,2) for d in (-4,0,4)]
    attempts=[steal_attempt_probability(speed_gp,s) for s in contexts];weighted_success=sum(a*steal_success_probability(speed_gp,s) for a,s in zip(attempts,contexts))/max(1e-12,sum(attempts));attempt=mean(attempts)
    f3=first_to_third_probability(speed_gp);s2h=second_to_home_probability(speed_gp);dp_avoid=1-dp_completion_probability(speed_gp)
    eligible_obp=obp*(1-P.STEAL_SECOND_BASE_OCCUPIED_RATE);att_pa=eligible_obp*attempt;sb_pa=att_pa*weighted_success;cs_pa=att_pa*(1-weighted_success)
    run=sb_pa*P.SB_RUN_VALUE+cs_pa*P.CS_RUN_VALUE+P.FIRST_TO_THIRD_OPP_RATE*f3*P.FIRST_TO_THIRD_VALUE+P.SECOND_TO_HOME_OPP_RATE*s2h*P.SECOND_TO_HOME_VALUE+P.DP_OPP_RATE*dp_avoid*P.DP_AVOIDED_VALUE
    return {'SB_attempt_rate_per_onbase':attempt,'SB_success':weighted_success,'SB_attempts_per_600PA':att_pa*600,'SB_per_600PA':sb_pa*600,'CS_per_600PA':cs_pa*600,'first_to_third':f3,'second_to_home':s2h,'DP_avoidance':dp_avoid,'running_runs_per_PA':run}

def total(row):
    bat=.47*row['1B']+.78*row['2B']+1.09*row['3B']+1.40*row['HR']+.33*row['BB']-.27*row['OUT']
    return bat+row['running_runs_per_PA']

def evaluate(model,ref,slope,n=50000):
    rows=[]
    for raw in RAW_GRID:
        g=gp(raw,ref,slope);m=pa(g,n,10000+int(ref*10)+int(slope*100)+raw);r=running(g,m['OBP']);row={'model':model,'reference_raw':ref,'slope':slope,'raw_speed':raw,'gameplay_speed':g,**m,**r};row['total_runs_proxy_per_PA']=total(row);rows.append(row)
    return rows

def main():
    Path('reports').mkdir(exist_ok=True);allrows=[];candidates=[]
    for model,ref in (('A_keep_raw_scale',REF_A),('B_prime_110_recenter',REF_B)):
        for slope in SLOPES:
            rows=evaluate(model,ref,slope);allrows+=rows;d={r['raw_speed']:r for r in rows};high=d[150]['total_runs_proxy_per_PA']-d[140]['total_runs_proxy_per_PA'];mid=d[120]['total_runs_proxy_per_PA']-d[110]['total_runs_proxy_per_PA'];weak=d[80]['total_runs_proxy_per_PA']-d[70]['total_runs_proxy_per_PA'];over=d[150]['SB_success']>.95 or d[150]['first_to_third']>.90 or d[150]['second_to_home']>.92 or d[150]['DP_avoidance']>.90
            candidates.append({'model':model,'reference_raw':ref,'slope':slope,'d_total_140_150':high,'d_total_110_120':mid,'d_total_70_80':weak,'speed150_sb_success':d[150]['SB_success'],'speed150_sb_attempts_600PA':d[150]['SB_attempts_per_600PA'],'speed150_f2t':d[150]['first_to_third'],'speed150_s2h':d[150]['second_to_home'],'speed150_dp_avoid':d[150]['DP_avoidance'],'overpowered':over})
    # Prefer UI-consistent model B; slope .8 is the first stronger candidate after .6 and is accepted only if all safety/ordering gates hold.
    viable=[r for r in candidates if r['model']=='B_prime_110_recenter' and not r['overpowered'] and r['d_total_140_150']>0 and r['d_total_110_120']>0 and r['d_total_70_80']>0]
    selected=min(viable,key=lambda r:(abs(r['slope']-.8),r['slope'])) if viable else None
    gate=selected is not None and selected['d_total_140_150']>=0.001
    with open('reports/hitter_speed_grid.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    with open('reports/hitter_speed_full_value.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(candidates[0]));w.writeheader();w.writerows(candidates)
    final={'gate':'HITTER_SPEED_RATIO_READY' if gate else 'HITTER_SPEED_RATIO_NOT_READY','persistent_inning_engine':'ABSENT; used frozen production baserunning probability/state-adapter paths without inventing teammate state','selected':selected,'model_preference':'B_prime_110_recenter' if gate else None,'run_proxy':'validated H3.2.1 SB/CS/XBT/DP run values plus fixed batting event values; comparative diagnostic only'}
    Path('reports/hitter_speed_ratio_final.json').write_text(json.dumps(final,indent=2));Path('reports/hitter_speed_ratio_summary.md').write_text('# Hitter Speed Full Gameplay Ratio\n\n'+f"Gate: `{final['gate']}`\n\nPersistent team inning engine is not present, so this calibration uses the frozen production SB/XBT/DP probability paths and their validated run-value constants plus H3 PA outcomes. No baserunning formula was retuned.\n\nSelected candidate: {json.dumps(selected,ensure_ascii=False)}\n")
    print(json.dumps(final,indent=2))
if __name__=='__main__':main()
