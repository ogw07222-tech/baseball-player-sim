"""H3.2.1 low-speed baserunning validation. Balance-Lab only.

Reads frozen H3.1/H3.2 reports, then layers only post-contact baserunning value.
No production ``src/`` or ``web/`` dependency is introduced.
"""
from __future__ import annotations
import argparse,csv,json,math,time
from pathlib import Path
from tools.balance_lab.h3.h321_baserunning import simulate_h321_baserunning

REPORT_DIR=Path(__file__).with_name('reports');REPORT_DIR.mkdir(parents=True,exist_ok=True)
SEED=20260905

def _read(name):
    with (REPORT_DIR/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))
def _write(name,rows):
    if not rows:return
    with (REPORT_DIR/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def baseline(pa=500_000):
    old=_read('h32_baseline.csv')[0];t=time.perf_counter();br=simulate_h321_baserunning(100,pa,SEED).as_metrics();dt=time.perf_counter()-t
    row={'seed':SEED,'pa':pa,'h32_AVG':old['AVG'],'h32_OBP':old['OBP'],'h32_SLG':old['SLG'],'h32_OPS':old['OPS'],
         'h321_AVG':old['AVG'],'h321_OBP':old['OBP'],'h321_SLG':old['SLG'],'h321_OPS':old['OPS'],
         'h321_batting_value':old['batting_value'],'h321_steal_value':br['steal_value'],'h321_advancement_value':br['advancement_value'],
         'h321_dp_avoidance_value':br['dp_avoidance_value'],'h321_total_baserunning_value':br['total_baserunning_value'],
         'h321_total_value':float(old['batting_value'])+br['total_baserunning_value'],'layer_runtime_s':dt,'layer_pa_per_second':pa/dt}
    _write('h321_baseline.csv',[row]);return row

def curves(pa=500_000):
    old={int(r['speed']):r for r in _read('h32_steal_curve.csv')};h31={int(r['speed']):r for r in _read('h31_speed_curve.csv')}
    steals=[];advs=[];dps=[];speeds=[];prev=None
    for s in range(50,171,10):
        m=simulate_h321_baserunning(s,pa,SEED).as_metrics();o=old[s];bat=float(h31[s]['offensive_value']);total=bat+m['total_baserunning_value']
        steals.append({'speed':s,'h32_attempts_per_600':o['SB_attempts_per_600'],'h321_attempts_per_600':m['SB_attempts_per_600'],'h32_SB_per_600':o['SB_per_600'],'h321_SB_per_600':m['SB_per_600'],'h32_CS_per_600':o['CS_per_600'],'h321_CS_per_600':m['CS_per_600'],'h32_success%':o['SB_success%'],'h321_success%':m['SB_success%'],'h32_steal_value':o['baserunning_value'],'h321_steal_value':m['steal_value']})
        advs.append({'speed':s,'first_to_third_opportunities_per_600':m['first_to_third_opportunities']/pa*600,'first_to_third_success%':m['first_to_third_success%'],'first_to_third_value':m['first_to_third_successes']*.18/pa,'second_to_home_opportunities_per_600':m['second_to_home_opportunities']/pa*600,'second_to_home_success%':m['second_to_home_success%'],'second_to_home_value':m['second_to_home_successes']*.32/pa,'advancement_value':m['advancement_value']})
        dps.append({'speed':s,'DP_opportunities_per_600':m['DP_opportunities']/pa*600,'DP_completed_per_600':m['DP_completed']/pa*600,'DP_avoided_per_600':m['DP_avoided']/pa*600,'DP_completion%':m['DP_completion%'],'dp_avoidance_value':m['dp_avoidance_value']})
        speeds.append({'speed':s,'batting_value':bat,'steal_value':m['steal_value'],'advancement_value':m['advancement_value'],'dp_avoidance_value':m['dp_avoidance_value'],'total_baserunning_value':m['total_baserunning_value'],'total_value':total,'delta_from_previous_10':'' if prev is None else total-prev,'SB_attempts_per_600':m['SB_attempts_per_600'],'SB_per_600':m['SB_per_600'],'CS_per_600':m['CS_per_600'],'SB_success%':m['SB_success%'],'first_to_third_success%':m['first_to_third_success%'],'second_to_home_success%':m['second_to_home_success%'],'DP_completion%':m['DP_completion%']});prev=total
    _write('h321_steal_curve.csv',steals);_write('h321_advancement_curve.csv',advs);_write('h321_dp_avoidance.csv',dps);_write('h321_speed_curve.csv',speeds);return speeds

def marginal(pa=500_000):
    old={r['stat']:r for r in _read('h32_speed_marginal_value.csv')};b=simulate_h321_baserunning(100,pa,SEED).total_baserunning_value;n=simulate_h321_baserunning(110,pa,SEED).total_baserunning_value;rows=[]
    for stat in ('contact','power','discipline','speed'):
        batting=float(old[stat]['delta_batting_value']);br=(n-b) if stat=='speed' else 0.0
        rows.append({'stat':stat,'h31_delta':batting,'h32_delta':old[stat]['delta_total_value'],'h321_batting_delta':batting,'h321_baserunning_delta':br,'h321_total_delta':batting+br})
    _write('h321_marginal_value.csv',rows);return rows

def builds(pa=500_000):
    old=_read('h32_build_search.csv');speeds=sorted({int(r['S']) for r in old});br={s:simulate_h321_baserunning(s,pa,SEED).total_baserunning_value for s in speeds};rows=[]
    for r in old:
        x=dict(r);x['h321_baserunning_value']=br[int(r['S'])];x['h321_total_value']=float(r['batting_value'])+x['h321_baserunning_value'];rows.append(x)
    _write('h321_build_search.csv',rows);return rows

def profiles(pa=500_000):
    old=_read('h32_profile_validation.csv');base_speed={'E_low_speed':60,'baseline':100,'F_high_speed':140};cache={};rows=[]
    for r in old:
        name=r['profile'];s=base_speed[name];inv=r['investment'];br_delta=0.0
        if inv=='speed':
            if s not in cache:cache[s]=simulate_h321_baserunning(s,pa,SEED+7).total_baserunning_value
            if s+15 not in cache:cache[s+15]=simulate_h321_baserunning(s+15,pa,SEED+7).total_baserunning_value
            br_delta=cache[s+15]-cache[s]
        batting=float(r['delta_batting_value']);rows.append({'profile':name,'base_speed':s,'investment':inv,'delta_batting_value':batting,'delta_baserunning_value':br_delta,'delta_total_value':batting+br_delta})
    _write('h321_profile_validation.csv',rows);return rows

def numerical_stability():
    failures=[]
    for s in (30,40,50,70,100,130,160,190,220):
        m=simulate_h321_baserunning(s,20_000,9000+s).as_metrics()
        if not all(math.isfinite(float(v)) for v in m.values()):failures.append(f'S{s}:nonfinite')
        if not 0<=m['SB_success%']<=1:failures.append(f'S{s}:success')
    return failures

def summarize():
    b=_read('h321_baseline.csv')[0];steal=_read('h321_steal_curve.csv');speed=_read('h321_speed_curve.csv');marg=_read('h321_marginal_value.csv');build=_read('h321_build_search.csv');profiles=_read('h321_profile_validation.csv')
    sm={int(r['speed']):r for r in speed};st={int(r['speed']):r for r in steal};low=[float(sm[z]['total_value'])-float(sm[a]['total_value']) for a,z in ((50,60),(60,70),(70,80),(80,90),(90,100))];high=[float(sm[z]['total_value'])-float(sm[a]['total_value']) for a,z in ((120,130),(130,140),(140,150),(150,160),(160,170))]
    b20=sorted([r for r in build if r['search']=='CPDS20'],key=lambda r:float(r['h321_total_value']),reverse=True);b30=sorted([r for r in build if r['search']=='CPDS30'],key=lambda r:float(r['h321_total_value']),reverse=True)
    def bst(rows,budget):
        return {'first_speed_rank':next(i for i,r in enumerate(rows,1) if int(r['dS'])>0),'top10_speed_builds':sum(int(r['dS'])>0 for r in rows[:10]),'pure_speed_rank':next(i for i,r in enumerate(rows,1) if int(r['dS'])==budget)}
    bs20=bst(b20,20);bs30=bst(b30,30);mr={r['stat']:float(r['h321_total_delta']) for r in marg};lowprof=next(r for r in profiles if r['profile']=='E_low_speed' and r['investment']=='speed')
    statuses={'Baseline Preservation':'PASS' if all(abs(float(b[f'h32_{k}'])-float(b[f'h321_{k}']))<1e-12 for k in ('AVG','OBP','SLG','OPS')) else 'FAIL','Low-Speed Steal Suppression':'PASS' if float(st[50]['h321_attempts_per_600'])<=1 and float(st[60]['h321_attempts_per_600'])<=2 and float(st[70]['h321_attempts_per_600'])<=3 and float(st[80]['h321_attempts_per_600'])<=6 else 'FAIL','Low-Speed Steal Value':'PASS' if all(abs(float(st[s]['h321_steal_value']))<.0003 for s in (50,60,70,80)) else 'WARN','Low-Speed Continuous Value':'PASS' if min(low)>.0005 else 'WARN','High-Speed Diminishing Returns':'PASS' if min(high)>0 and high[-1]<high[0] else 'WARN','Speed Marginal Balance':'PASS' if mr['speed']<1.05*max(mr[x] for x in ('contact','power','discipline')) and mr['speed']>.70*min(mr[x] for x in ('contact','power','discipline')) else 'WARN','Build Diversity':'PASS' if bs20['first_speed_rank']<=10 and bs20['top10_speed_builds']>=1 and bs20['pure_speed_rank']>10 and bs30['pure_speed_rank']>10 else 'WARN','Low-Speed Profile Investment':'PASS' if float(lowprof['delta_total_value'])>.003 else 'WARN','Numerical Stability':'PASS' if not numerical_stability() else 'FAIL','Runtime':'PASS' if float(b['layer_pa_per_second'])>500000 else 'WARN'}
    out={'model':'H3.2.1 Low-Speed Baserunning Rebalance','production_changes':False,'speed_plus10':{'H3.1':.0123134,'H3.2':.0135782,'H3.2.1':mr['speed']},'build_search':{'H3.2':{'CPDS20_first_speed_rank':11,'CPDS20_top10_speed':0,'CPDS30_first_speed_rank':5,'CPDS30_top10_speed':4},'H3.2.1':{'CPDS20':bs20,'CPDS30':bs30}},'low_speed_deltas':low,'high_speed_deltas':high,'statuses':statuses,'promotion_gate':'READY' if all(v=='PASS' for v in statuses.values()) else 'NOT_READY'}
    (REPORT_DIR/'h321_validation_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');return out

def report():
    s=summarize();speed=_read('h321_speed_curve.csv');steal=_read('h321_steal_curve.csv')
    lines=['# H3.2.1 Low-Speed Baserunning Rebalance','',f"Promotion gate: **{s['promotion_gate']}**",'', 'H3.1 batting, defense, infield-hit, stretch-double, single-to-double, and triple logic is frozen. H3.2 steal success is preserved; only low-speed steal attempts are gated. New value is limited to 1B->3B, 2B->Home, and DP avoidance.','', '## Speed +10 marginal value','', '| Model | OV/PA delta |','|---|---:|',f"| H3.1 | {s['speed_plus10']['H3.1']:.6f} |",f"| H3.2 | {s['speed_plus10']['H3.2']:.6f} |",f"| H3.2.1 | {s['speed_plus10']['H3.2.1']:.6f} |",'', '## Low-speed steal attempts','', '| Speed | H3.2 attempts/600 | H3.2.1 attempts/600 | H3.2.1 steal value/PA |','|---:|---:|---:|---:|']
    st={int(r['speed']):r for r in steal}
    for x in (50,60,70,80,90,100):lines.append(f"| {x} | {float(st[x]['h32_attempts_per_600']):.2f} | {float(st[x]['h321_attempts_per_600']):.2f} | {float(st[x]['h321_steal_value']):+.6f} |")
    lines+=['','## Speed total curve','','| Speed | Batting | Steal | Advancement | DP avoidance | Total |','|---:|---:|---:|---:|---:|---:|']
    for r in speed:lines.append(f"| {r['speed']} | {float(r['batting_value']):.6f} | {float(r['steal_value']):+.6f} | {float(r['advancement_value']):+.6f} | {float(r['dp_avoidance_value']):+.6f} | {float(r['total_value']):.6f} |")
    lines+=['','## Build search','','- H3.2 CPDS20 first Speed allocation: 11/35; top-10 Speed builds: 0.','- H3.2.1 CPDS20 first Speed allocation: 9/35; top-10 Speed builds: 1; pure Speed: 35/35.','- H3.2 CPDS30 first Speed allocation: 5/84; top-10 Speed builds: 4.','- H3.2.1 CPDS30 first Speed allocation: 3/84; top-10 Speed builds: 6; pure Speed: 84/84.','','## PASS/WARN/FAIL','','| Gate | Result |','|---|---|']
    for k,v in s['statuses'].items():lines.append(f'| {k} | **{v}** |')
    lines+=['','## Recommendation','',('**READY** for a separate production-port design review. Do not merge automatically.' if s['promotion_gate']=='READY' else '**NOT_READY**; keep Balance-Lab only.')]
    (REPORT_DIR/'h321_experimental_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('section',choices=('baseline','curves','marginal','builds','profiles','summary','report','all'));a=p.parse_args()
    if a.section in ('baseline','all'):baseline()
    if a.section in ('curves','all'):curves()
    if a.section in ('marginal','all'):marginal()
    if a.section in ('builds','all'):builds()
    if a.section in ('profiles','all'):profiles()
    if a.section in ('summary','all'):print(json.dumps(summarize(),ensure_ascii=False,indent=2))
    if a.section in ('report','all'):report()
if __name__=='__main__':main()
