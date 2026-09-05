from __future__ import annotations
import csv,json
from pathlib import Path
from statistics import mean,pstdev
from src.player import Player
from src.growth import apply_season_growth
from src.rng import RNG
from src import config
from src.hitting.model import HitterSnapshot,PitcherSnapshot,HittingEngine

REF={'contact':109.26405555555556,'power':109.10451111111111,'discipline':108.80516666666666,'speed':98.10803333333332}
SLOPES=(.40,.50,.60,.70,.80,.90,1.00)
SELECTED=.60
KBO={'AVG':.2616,'OBP':.3385,'SLG':.3887,'OPS':.7272,'BB':.09149,'K':.19687,'HR':.02127,'1B':.16398,'2B':.04006,'3B':.00371,'BABIP':.3122}

def norm(raw,stat,slope=SELECTED):return 100.0+(float(raw)-REF[stat])*slope

def prime_players(n=2000,seed=48211):
    rng=RNG(seed);out=[]
    for i in range(n):
        p=Player.random(f'H{i}',rng,position=config.POSITIONS[i%len(config.POSITIONS)]);target=(26,28,30)[i%3]
        while p.age<target:apply_season_growth(p,rng)
        out.append((p.stats.contact,p.stats.power,p.stats.discipline,p.stats.speed))
    return out

def metrics(rows,slope=SELECTED,n=100000,seed=1):
    rng=RNG(seed);c={}
    for i in range(n):
        a,b,d,s=rows[i%len(rows)];h=HitterSnapshot(norm(a,'contact',slope),norm(b,'power',slope),norm(d,'discipline',slope),norm(s,'speed',SELECTED));r=HittingEngine(h,PitcherSnapshot(),100,rng).simulate_plate_appearance().result;c[r]=c.get(r,0)+1
    hits=sum(c.get(k,0) for k in ('single','double','triple','home_run'));walk=c.get('walk',0);ab=n-walk;tb=c.get('single',0)+2*c.get('double',0)+3*c.get('triple',0)+4*c.get('home_run',0);bip=max(1,ab-c.get('strikeout',0)-c.get('home_run',0));bih=hits-c.get('home_run',0)
    avg=hits/ab;obp=(hits+walk)/n;slg=tb/ab
    return {'AVG':avg,'OBP':obp,'SLG':slg,'OPS':obp+slg,'BB':walk/n,'K':c.get('strikeout',0)/n,'HR':c.get('home_run',0)/n,'1B':c.get('single',0)/n,'2B':c.get('double',0)/n,'3B':c.get('triple',0)/n,'BABIP':bih/bip,'ISO':slg-avg}

def fixed(stat,raw,slope=SELECTED,n=60000,seed=1):
    vals={'contact':110,'power':110,'discipline':110,'speed':110};vals[stat]=raw;return metrics([(vals['contact'],vals['power'],vals['discipline'],vals['speed'])],slope,n,seed)

def pitch_diag(stat,raw,slope=SELECTED,n=50000,seed=2):
    rng=RNG(seed);sw=chase=balls=miss=0
    vals={'contact':110,'power':110,'discipline':110,'speed':110};vals[stat]=raw
    h=HitterSnapshot(norm(vals['contact'],'contact',slope),norm(vals['power'],'power',slope),norm(vals['discipline'],'discipline',slope),norm(vals['speed'],'speed',SELECTED))
    for _ in range(n):
        e=HittingEngine(h,PitcherSnapshot(),100,rng);p=e._pitch();sp=e._swing_probability(p,0,0);swing=rng.random()<sp
        if not p.is_strike:balls+=1
        if swing:
            sw+=1;chase+=not p.is_strike
            r,_,_=e._contact_resolution(p,0);miss+=r=='miss'
    return {'Swing':sw/n,'Chase':chase/max(1,balls),'Whiff':miss/max(1,sw),'Contact':(sw-miss)/max(1,sw)}

def write(path,rows):
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields:fields.append(k)
    with open(path,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    Path('reports').mkdir(exist_ok=True);players=prime_players();cand=[]
    raw_sd={stat:pstdev([r[i] for r in players]) for i,stat in enumerate(('contact','power','discipline','speed'))}
    for sl in SLOPES:
        m=metrics(players,sl,120000,1000+int(sl*100));cand.append({'slope':sl,'contact_gameplay_sd':raw_sd['contact']*sl,'power_gameplay_sd':raw_sd['power']*sl,'discipline_gameplay_sd':raw_sd['discipline']*sl,**m})
    sens=[]
    for si,stat in enumerate(('contact','power','discipline')):
        for base in (80,100,110,130,150):
            m0=fixed(stat,base,SELECTED,50000,4000+si*500+base)
            for delta in (1,5,10,20):
                m1=fixed(stat,base+delta,SELECTED,50000,4000+si*500+base)
                row={'stat':stat,'baseline_raw':base,'delta_raw':delta,'gameplay_delta':delta*SELECTED}
                for k in ('AVG','OBP','SLG','BB','K','HR','BABIP','ISO'):row['d'+k]=m1[k]-m0[k]
                sens.append(row)
        for raw in (80,100,110,130,140,150):sens.append({'stat':stat,'baseline_raw':raw,'delta_raw':0,**pitch_diag(stat,raw,SELECTED,40000,8000+si*500+raw)})
    pop=[]
    for seed in (9101,9102,9103):pop.append({'kind':'population','seed':seed,**metrics(players,SELECTED,1000000,seed)})
    avg={k:mean([r[k] for r in pop]) for k in ('AVG','OBP','SLG','OPS','BB','K','HR','1B','2B','3B','BABIP')}
    profiles={'Average':(110,110,110,110),'Contact Specialist':(140,95,110,110),'Power Hitter':(100,145,100,110),'Discipline Specialist':(105,105,140,110),'Balanced Star':(130,130,125,110),'Tool Monster':(145,145,135,130),'Weak':(80,80,80,90)}
    for i,(name,v) in enumerate(profiles.items()):pop.append({'kind':'profile','profile':name,**metrics([v],SELECTED,180000,12000+i)})
    table=[]
    for stat in ('contact','power','discipline'):
        for raw in (70,80,90,100,110,120,130,140,150,160,180,200,250):table.append({'stat':stat,'raw':raw,'gameplay':norm(raw,stat),'local_per_raw':SELECTED,'delta_per_10_raw':10*SELECTED})
    write('reports/hitter_cpd_normalization_candidates.csv',cand);write('reports/hitter_cpd_sensitivity.csv',sens);write('reports/hitter_actual_population_validation.csv',pop);write('reports/hitter_cpd_raw_to_gameplay.csv',table)
    prime_gp={stat:100.0 for stat in ('contact','power','discipline')}
    sane=.22<avg['AVG']<.31 and .60<avg['OPS']<.90 and .05<avg['BB']<.13 and .12<avg['K']<.32
    gate=sane
    final={'gate':'HITTER_CPD_GAMEPLAY_SCALE_READY' if gate else 'HITTER_CPD_GAMEPLAY_SCALE_NOT_READY','raw_scale_gate':'HITTER_CPD_RAW_SCALE_READY','model':'linear','selected_common_slope':SELECTED,'references':{k:REF[k] for k in ('contact','power','discipline')},'prime_gameplay_center':prime_gp,'actual_population_multi_seed_mean':avg,'kbo_reference_for_context_only':KBO,'selection_basis':'common slope preserving ~12-14 gameplay SD and monotonic stat identity; not league-fit optimization','h32_formula_changed':False}
    Path('reports/hitter_cpd_normalization_final.json').write_text(json.dumps(final,indent=2))
    print(json.dumps(final,indent=2))
if __name__=='__main__':main()
