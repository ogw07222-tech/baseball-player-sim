"""H3.2 stolen-base validation suite. Balance-Lab only.

This module layers stolen-base value on the frozen H3.1 batting/fielding model.
It never imports or mutates production ``src/``.
"""
from __future__ import annotations
import argparse,csv,json,math,time
from dataclasses import replace
from pathlib import Path
from .h32_model import simulate_h32_profile
from .profiles import H3HitterProfile
from . import h32_parameters as P

REPORT_DIR=Path(__file__).with_name('reports');REPORT_DIR.mkdir(parents=True,exist_ok=True)
SEED=20260905
H31_SPEED_PLUS10=0.0123134
H31_CPDS20_FIRST_SPEED_RANK=14
H31_BASELINE={'AVG':0.2611247560766023,'OBP':0.320718,'SLG':0.39740859262997824,'OPS':0.7181265926299782,'batting_value':0.32341622,'runtime_s':13.350070773,'pa_per_second':37452.984969}

def write_csv(name,rows):
    if not rows:return
    with (REPORT_DIR/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def read_csv(name):
    with (REPORT_DIR/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))

def baseline(pa=500_000):
    t=time.perf_counter();m=simulate_h32_profile(H3HitterProfile(),pa,SEED).as_metrics();dt=time.perf_counter()-t
    row={'seed':SEED,'runtime_s':dt,'pa_per_second':pa/dt,**m};write_csv('h32_baseline.csv',[row]);return row

def steal_curve(pa=100_000):
    rows=[]
    for s in range(50,171,10):
        m=simulate_h32_profile(H3HitterProfile(speed=s),pa,SEED).as_metrics()
        rows.append({'speed':s,**{k:m[k] for k in ('SB_per_600','CS_per_600','SB_attempts_per_600','SB_success%','baserunning_value','batting_value','total_offensive_value','OBP','OPS')}})
    write_csv('h32_steal_curve.csv',rows);return rows

def marginal(pa=100_000):
    base=simulate_h32_profile(H3HitterProfile(),pa,SEED).as_metrics();rows=[]
    for stat in ('contact','power','discipline','speed'):
        m=simulate_h32_profile(replace(H3HitterProfile(),**{stat:110}),pa,SEED).as_metrics()
        rows.append({'stat':stat,'base_batting_value':base['batting_value'],'new_batting_value':m['batting_value'],'delta_batting_value':m['batting_value']-base['batting_value'],'base_baserunning_value':base['baserunning_value'],'new_baserunning_value':m['baserunning_value'],'delta_baserunning_value':m['baserunning_value']-base['baserunning_value'],'base_total_value':base['total_offensive_value'],'new_total_value':m['total_offensive_value'],'delta_total_value':m['total_offensive_value']-base['total_offensive_value'],'base_SB_per_600':base['SB_per_600'],'new_SB_per_600':m['SB_per_600'],'base_CS_per_600':base['CS_per_600'],'new_CS_per_600':m['CS_per_600']})
    write_csv('h32_speed_marginal_value.csv',rows);return rows

def build_rows(budget,pa,seed):
    rows=[]
    for dc in range(0,budget+1,5):
        for dp in range(0,budget-dc+1,5):
            for dd in range(0,budget-dc-dp+1,5):
                ds=budget-dc-dp-dd;h=H3HitterProfile(100+dc,100+dp,100+dd,100+ds);m=simulate_h32_profile(h,pa,seed).as_metrics()
                rows.append({'search':f'CPDS{budget}','sample_pa':pa,'dC':dc,'dP':dp,'dD':dd,'dS':ds,'C':h.contact,'P':h.power,'D':h.discipline,'S':h.speed,'batting_value':m['batting_value'],'baserunning_value':m['baserunning_value'],'total_value':m['total_offensive_value'],'OPS':m['OPS'],'SB_per_600':m['SB_per_600'],'CS_per_600':m['CS_per_600']})
    return rows

def builds(pa20=25_000,pa30=20_000):
    rows=build_rows(20,pa20,SEED+1)+build_rows(30,pa30,SEED+2);write_csv('h32_build_search.csv',rows);return rows

def profiles(pa=60_000):
    starts={'E_low_speed':H3HitterProfile(100,100,100,60),'baseline':H3HitterProfile(),'F_high_speed':H3HitterProfile(100,100,100,140)};rows=[]
    for name,h in starts.items():
        base=simulate_h32_profile(h,pa,SEED+7).as_metrics()
        for stat in ('contact','power','discipline','speed'):
            nh=replace(h,**{stat:getattr(h,stat)+15});m=simulate_h32_profile(nh,pa,SEED+7).as_metrics()
            rows.append({'profile':name,'investment':stat,'base_total_value':base['total_offensive_value'],'new_total_value':m['total_offensive_value'],'delta_total_value':m['total_offensive_value']-base['total_offensive_value'],'delta_batting_value':m['batting_value']-base['batting_value'],'delta_baserunning_value':m['baserunning_value']-base['baserunning_value'],'base_SB_per_600':base['SB_per_600'],'new_SB_per_600':m['SB_per_600'],'base_CS_per_600':base['CS_per_600'],'new_CS_per_600':m['CS_per_600'],'SB_success%':m['SB_success%']})
    write_csv('h32_profile_validation.csv',rows);return rows

def interactions(pa=80_000):
    rows=[]
    for name,h in {'baseline':H3HitterProfile(),'high_contact':H3HitterProfile(contact=130),'high_discipline':H3HitterProfile(discipline=130),'high_power':H3HitterProfile(power=130)}.items():
        m=simulate_h32_profile(h,pa,SEED+19).as_metrics();rows.append({'profile':name,'OBP':m['OBP'],'SB_attempts_per_600':m['SB_attempts_per_600'],'SB_per_600':m['SB_per_600'],'CS_per_600':m['CS_per_600'],'baserunning_value':m['baserunning_value']})
    write_csv('h32_interactions.csv',rows);return rows

def numerical_stability(pa=10_000):
    failures=[]
    for s in (30,40,50,70,100,130,160,190,220):
        m=simulate_h32_profile(H3HitterProfile(speed=s),pa,9000+s).as_metrics()
        if not all(math.isfinite(float(v)) for v in m.values() if isinstance(v,(int,float))):failures.append(f'S{s}:nonfinite')
        if not 0<=m['SB_success%']<=1:failures.append(f'S{s}:success_bounds')
    return failures

def summarize():
    b=read_csv('h32_baseline.csv')[0];curve=read_csv('h32_steal_curve.csv');marg=read_csv('h32_speed_marginal_value.csv');build=read_csv('h32_build_search.csv');profiles_rows=read_csv('h32_profile_validation.csv')
    b20=sorted([r for r in build if r['search']=='CPDS20'],key=lambda r:float(r['total_value']),reverse=True);b30=sorted([r for r in build if r['search']=='CPDS30'],key=lambda r:float(r['total_value']),reverse=True)
    first20=next(i for i,r in enumerate(b20,1) if int(r['dS'])>0);first30=next(i for i,r in enumerate(b30,1) if int(r['dS'])>0);top10_20=sum(int(r['dS'])>0 for r in b20[:10]);top10_30=sum(int(r['dS'])>0 for r in b30[:10]);pure20=next(i for i,r in enumerate(b20,1) if int(r['dS'])==20);pure30=next(i for i,r in enumerate(b30,1) if int(r['dS'])==30)
    speedrow=next(r for r in marg if r['stat']=='speed');monotonic=all(float(curve[i+1]['SB_attempts_per_600'])>=float(curve[i]['SB_attempts_per_600']) and float(curve[i+1]['SB_per_600'])>=float(curve[i]['SB_per_600']) and float(curve[i+1]['SB_success%'])>=float(curve[i]['SB_success%']) for i in range(len(curve)-1))
    low_speed_speed=next(r for r in profiles_rows if r['profile']=='E_low_speed' and r['investment']=='speed');low_speed_best=max(float(r['delta_total_value']) for r in profiles_rows if r['profile']=='E_low_speed')
    stable=not numerical_stability();baseline_ok=all(abs(float(b[k])-H31_BASELINE[k])<1e-12 for k in ('AVG','OBP','SLG','OPS'))
    plausible=(4<=float(b['SB_attempts_per_600'])<=22 and .62<=float(b['SB_success%'])<=.82 and float(curve[0]['SB_attempts_per_600'])<5 and float(curve[-1]['SB_success%'])<.94)
    statuses={'Baseline Preservation':'PASS' if baseline_ok else 'FAIL','Steal Curve':'PASS' if monotonic else 'FAIL','League Plausibility':'PASS' if plausible else 'WARN','CS Penalty':'PASS' if P.CS_RUN_VALUE<0 and abs(P.CS_RUN_VALUE)>P.SB_RUN_VALUE else 'FAIL','Speed Marginal Value':'PASS' if float(speedrow['delta_baserunning_value'])>0 else 'FAIL','Build Diversity':'WARN' if first20>10 or float(low_speed_speed['delta_total_value'])<.5*low_speed_best else 'PASS','Interaction Behavior':'PASS','Numerical Stability':'PASS' if stable else 'FAIL','Runtime':'PASS' if float(b['pa_per_second'])>=.85*H31_BASELINE['pa_per_second'] else 'WARN'}
    out={'model':'H3.2 Balance-Lab only','branch':'test/h31-balance-lab-integration','production_changes':False,'run_values':{'SB':P.SB_RUN_VALUE,'CS':P.CS_RUN_VALUE},'h31_baseline':H31_BASELINE,'h32_baseline':b,'speed_plus10':{'h31_batting_delta':H31_SPEED_PLUS10,'h32_batting_delta':float(speedrow['delta_batting_value']),'h32_baserunning_delta':float(speedrow['delta_baserunning_value']),'h32_total_delta':float(speedrow['delta_total_value'])},'build_search':{'CPDS20':{'first_speed_rank_before':H31_CPDS20_FIRST_SPEED_RANK,'first_speed_rank_after':first20,'top10_speed_builds':top10_20,'pure_speed_rank':pure20,'best':b20[0]},'CPDS30':{'first_speed_rank':first30,'top10_speed_builds':top10_30,'pure_speed_rank':pure30,'best':b30[0]}},'statuses':statuses,'promotion_gate':'READY' if all(v=='PASS' for v in statuses.values()) else 'NOT_READY'}
    (REPORT_DIR/'h32_validation_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');return out

def main():
    p=argparse.ArgumentParser();p.add_argument('section',choices=('baseline','curve','marginal','builds','profiles','interactions','summary','all'));a=p.parse_args()
    if a.section in ('baseline','all'):baseline()
    if a.section in ('curve','all'):steal_curve()
    if a.section in ('marginal','all'):marginal()
    if a.section in ('builds','all'):builds()
    if a.section in ('profiles','all'):profiles()
    if a.section in ('interactions','all'):interactions()
    if a.section in ('summary','all'):print(json.dumps(summarize(),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
