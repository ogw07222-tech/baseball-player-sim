"""Reproducible H3.1 Balance-Lab validation CLI. Production src/ is not imported or changed."""
from __future__ import annotations
import argparse,csv,json,time
from dataclasses import replace
from pathlib import Path
from . import parameters as P
from .model import H31Model, simulate_profile
from .profiles import H3DefenseProfile,H3HitterProfile

REPORT_DIR=Path(__file__).with_name('reports');REPORT_DIR.mkdir(parents=True,exist_ok=True)
SEED=20260905

def write_csv(name,rows):
    if not rows:return
    with (REPORT_DIR/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def baseline(pa=500_000):
    t=time.perf_counter();line=simulate_profile(H3HitterProfile(),pa,SEED,defense=100);dt=time.perf_counter()-t;m=line.as_metrics()
    row={'seed':SEED,'runtime_s':dt,'pa_per_second':pa/dt,**m};write_csv('h31_baseline.csv',[row]);return row,line

def marginal(pa=100_000):
    base=simulate_profile(H3HitterProfile(),pa,SEED,defense=100).as_metrics();rows=[]
    for stat in ('contact','power','discipline','speed','defense'):
        for delta in (1,5,10):
            m=simulate_profile(H3HitterProfile(),pa,SEED,defense=100+delta).as_metrics() if stat=='defense' else simulate_profile(replace(H3HitterProfile(),**{stat:100+delta}),pa,SEED,defense=100).as_metrics()
            row={'stat':stat,'delta':delta}
            for k in ('AVG','OBP','SLG','OPS','HR%','BB%','K%','1B%','2B%','3B%','offensive_value'):
                row[f'base_{k}']=base[k];row[f'new_{k}']=m[k];row[f'delta_{k}']=m[k]-base[k]
            row['defensive_value_gain']=-(m['offensive_value']-base['offensive_value']) if stat=='defense' else 0.0;rows.append(row)
    write_csv('h31_marginal_value.csv',rows);return rows

def speed(pa=100_000):
    rows=[]
    for s in (40,50,60,70,80,90,100,110,120,130,140,150,160,170):
        line=simulate_profile(H3HitterProfile(speed=s),pa,SEED,defense=100);m=line.as_metrics();rows.append({'speed':s,**{k:m[k] for k in ('offensive_value','1B%','2B%','3B%','2B_to_1B_downgrade%','3B_conversion%','3B_share_2B3B','1B_to_2B_upgrade%','BB%','K%','HR%')}})
    write_csv('h31_speed_curve.csv',rows);return rows

def defense(pa=100_000):
    rows=[]
    for d in (50,70,85,100,115,130,145,160):
        line=simulate_profile(H3HitterProfile(),pa,SEED,defense=d);m=line.as_metrics();rows.append({'defense':d,**{k:m[k] for k in ('AVG','OBP','SLG','OPS','BABIP','1B%','2B%','3B%','HR%','OUT%','ERROR%','ROE%','offensive_value')}})
    write_csv('h31_defense_curve.csv',rows);return rows

def builds(pa=40_000):
    rows=[]
    for dc in range(0,31,5):
        for dp in range(0,31-dc,5):
            dd=30-dc-dp;m=simulate_profile(H3HitterProfile(100+dc,100+dp,100+dd,100),pa,SEED,defense=100).as_metrics();rows.append({'search':'CPD30','dC':dc,'dP':dp,'dD':dd,'dS':0,'C':100+dc,'P':100+dp,'D':100+dd,'S':100,'offensive_value':m['offensive_value'],'AVG':m['AVG'],'OBP':m['OBP'],'SLG':m['SLG'],'OPS':m['OPS']})
    for dc in range(0,21,5):
        for dp in range(0,21-dc,5):
            for dd in range(0,21-dc-dp,5):
                ds=20-dc-dp-dd;m=simulate_profile(H3HitterProfile(100+dc,100+dp,100+dd,100+ds),pa,SEED+1,defense=100).as_metrics();rows.append({'search':'CPDS20','dC':dc,'dP':dp,'dD':dd,'dS':ds,'C':100+dc,'P':100+dp,'D':100+dd,'S':100+ds,'offensive_value':m['offensive_value'],'AVG':m['AVG'],'OBP':m['OBP'],'SLG':m['SLG'],'OPS':m['OPS']})
    write_csv('h31_build_search.csv',rows);return rows

def difficulty_table():
    rows=[]
    for tier in ('ROUTINE','EASY','AVERAGE','HARD','VERY_HARD','EXCEPTIONAL'):
        row={'difficulty':tier,'base_catch':P.DIFFICULTY_BASE_CATCH[tier]}
        for d in (70,100,130,160):row[f'DEF{d}']=H31Model(H3HitterProfile(),defense=H3DefenseProfile(d),seed=1)._catch_probability(tier)
        rows.append(row)
    write_csv('h31_difficulty_table.csv',rows);return rows

def summary():
    def read(name):
        with (REPORT_DIR/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))
    b=read('h31_baseline.csv')[0];m=read('h31_marginal_value.csv');s=read('h31_speed_curve.csv');d=read('h31_defense_curve.csv');bu=read('h31_build_search.csv')
    p10={r['stat']:float(r['delta_offensive_value']) for r in m if r['delta']=='10'};cpd=sorted([r for r in bu if r['search']=='CPD30'],key=lambda x:float(x['offensive_value']),reverse=True);cpds=sorted([r for r in bu if r['search']=='CPDS20'],key=lambda x:float(x['offensive_value']),reverse=True);bal=next(r for r in cpd if r['dC']==r['dP']==r['dD']=='10');sm={int(r['speed']):float(r['offensive_value']) for r in s};dm={int(r['defense']):r for r in d}
    low={f'{a}->{z}':sm[z]-sm[a] for a,z in ((50,60),(60,70),(70,80),(80,90),(90,100))};first_speed=next(i for i,r in enumerate(cpds,1) if int(r['dS'])>0)
    statuses={'baseline':'PASS' if .250<=float(b['AVG'])<=.270 and .315<=float(b['OBP'])<=.335 and .390<=float(b['SLG'])<=.420 else 'WARN','low_speed':'PASS' if min(low.values())>.00025 else 'WARN','defense':'PASS' if float(dm[70]['BABIP'])>float(dm[100]['BABIP'])>float(dm[130]['BABIP'])>float(dm[160]['BABIP']) and float(dm[160]['AVG'])>.18 else 'FAIL','cpd_balance':'PASS' if max(p10[x] for x in ('contact','power','discipline'))/min(p10[x] for x in ('contact','power','discipline'))<=1.5 else 'WARN','build_diversity':'WARN' if first_speed>10 else 'PASS'}
    out={'model':'H3.1 Balance-Lab only','main_sha':'b9fda177973c00a220d83242a3bfc8de42143b0d','branch':'experiment/h3-batted-ball-validation','baseline':b,'plus10':p10,'low_speed_gains':low,'cpd_best':cpd[0],'cpd_balanced_rank':cpd.index(bal)+1,'cpds_first_speed_allocation_rank':first_speed,'statuses':statuses,'promotion_gate':'READY_FOR_H3_PRODUCTION_PORT' if all(v=='PASS' for v in statuses.values()) else 'NOT_READY'}
    (REPORT_DIR/'h31_validation_summary_compact.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');return out

def main():
    p=argparse.ArgumentParser();p.add_argument('section',choices=('baseline','marginal','speed','defense','builds','difficulty','summary','all'));p.add_argument('--quick',action='store_true');a=p.parse_args();scale=.25 if a.quick else 1
    if a.section in ('baseline','all'):baseline(int(500000*scale))
    if a.section in ('marginal','all'):marginal(int(100000*scale))
    if a.section in ('speed','all'):speed(int(100000*scale))
    if a.section in ('defense','all'):defense(int(100000*scale))
    if a.section in ('builds','all'):builds(int(40000*scale))
    if a.section in ('difficulty','all'):difficulty_table()
    if a.section in ('summary','all'):print(json.dumps(summary(),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
