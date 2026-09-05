from __future__ import annotations
import csv,json
from pathlib import Path
from statistics import pstdev
from src.player import Player
from src.growth import apply_season_growth
from src.rng import RNG
from src.hitting.model import HitterSnapshot,PitcherSnapshot,HittingEngine

REF={"contact":94.2742,"power":92.78481111111111,"discipline":87.34492222222222,"speed":98.0363888888889}
SLOPES=(.4,.5,.6,.75,.9,1.0,1.2)
RAW_GRID=(30,50,70,80,90,100,110,120,130,140,150,160,180,200,250)

def norm(raw,stat,slope):return 100.0+(float(raw)-REF[stat])*slope

def prime_players(n=2000,seed=551):
    rng=RNG(seed);out=[];positions=("C","1B","2B","3B","SS","LF","CF","RF","DH")
    for i in range(n):
        p=Player.random(f"P{i}",rng,position=rng.choice(positions)); target=(26,28,30)[i%3]
        while p.age<target:apply_season_growth(p,rng)
        out.append((p.stats.contact,p.stats.power,p.stats.discipline,p.stats.speed))
    return out

def pa_metrics(rows,slopes,n=200000,seed=991):
    rng=RNG(seed);counts={k:0 for k in ("single","double","triple","home_run","walk","strikeout","out")}
    for i in range(n):
        c,p,d,s=rows[i%len(rows)]
        h=HitterSnapshot(norm(c,"contact",slopes[0]),norm(p,"power",slopes[1]),norm(d,"discipline",slopes[2]),norm(s,"speed",slopes[3]))
        r=HittingEngine(h,PitcherSnapshot(),100.0,rng).simulate_plate_appearance().result
        counts[r]=counts.get(r,0)+1
    hits=sum(counts[k] for k in ("single","double","triple","home_run"));ab=n-counts["walk"]
    tb=counts["single"]+2*counts["double"]+3*counts["triple"]+4*counts["home_run"]
    bip=max(1,ab-counts["strikeout"]-counts["home_run"]);bih=hits-counts["home_run"]
    return {"AVG":hits/ab,"OBP":(hits+counts['walk'])/n,"SLG":tb/ab,"OPS":(hits+counts['walk'])/n+tb/ab,"BB":counts['walk']/n,"K":counts['strikeout']/n,"HR":counts['home_run']/n,"1B":counts['single']/n,"2B":counts['double']/n,"3B":counts['triple']/n,"BABIP":bih/bip}

def pitch_metrics(h,n=80000,seed=2):
    rng=RNG(seed);sw=miss=0
    for _ in range(n):
        e=HittingEngine(h,PitcherSnapshot(),100.0,rng);pitch=e._pitch()
        if rng.random()<e._swing_probability(pitch,0,0):
            sw+=1;r,_,_=e._contact_resolution(pitch,0);miss+=r=='miss'
    return {"Swing":sw/n,"Whiff":miss/max(1,sw),"Contact":(sw-miss)/max(1,sw)}

def fixed_profile(rawc=110,rawp=110,rawd=110,raws=110,slopes=(.6,.6,.6,.6),n=100000,seed=7):return pa_metrics([(rawc,rawp,rawd,raws)],slopes,n,seed)

def write(path,rows):
    fields=[]
    for row in rows:
        for k in row:
            if k not in fields:fields.append(k)
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    Path('reports').mkdir(exist_ok=True);players=prime_players();slope_rows=[]
    for stat_i,stat in enumerate(("contact","power","discipline","speed")):
        rawsd=pstdev([r[stat_i] for r in players])
        for sl in SLOPES:
            s=[.6,.6,.6,.6];s[stat_i]=sl;base=fixed_profile(slopes=tuple(s),n=50000,seed=100+stat_i)
            args=[110,110,110,110];args[stat_i]=120;up=fixed_profile(*args,slopes=tuple(s),n=50000,seed=100+stat_i)
            slope_rows.append({"stat":stat,"slope":sl,"gameplay_sd":rawsd*sl,"dAVG":up['AVG']-base['AVG'],"dSLG":up['SLG']-base['SLG'],"dBB":up['BB']-base['BB'],"dK":up['K']-base['K'],"dHR":up['HR']-base['HR']})
    selected={"contact":.6,"power":.6,"discipline":.6,"speed":.6};slopes=(.6,.6,.6,.6);pop=pa_metrics(players,slopes,500000,8801)
    map_rows=[{"stat":stat,"raw":raw,"gameplay":norm(raw,stat,.6),"local_slope":.6} for stat in selected for raw in RAW_GRID]
    sens=[]
    for stat_i,stat in enumerate(("contact","power","discipline","speed")):
        for baseline in (80,100,110,130,150):
            baseargs=[110,110,110,110];baseargs[stat_i]=baseline;base=fixed_profile(*baseargs,slopes=slopes,n=70000,seed=2000+stat_i*100+baseline)
            for delta in (1,5,10,20):
                args=baseargs.copy();args[stat_i]+=delta;up=fixed_profile(*args,slopes=slopes,n=70000,seed=2000+stat_i*100+baseline)
                sens.append({"kind":"pa","stat":stat,"baseline_raw":baseline,"delta_raw":delta,**{f"d{k}":up[k]-base[k] for k in ("AVG","OBP","SLG","BB","K","HR","BABIP")}})
    for raw in (70,80,90,100,110,120,130,140,150):
        pm=pitch_metrics(HitterSnapshot(norm(raw,'contact',.6),100,100,100),60000,3000+raw);sens.append({"kind":"pitch","stat":"contact","raw":raw,**pm})
    profiles={"Balanced":(110,110,110,110),"Contact Specialist":(140,90,110,110),"Power Hitter":(100,145,100,100),"Disciplined Hitter":(105,105,140,105),"Raw Tool Monster":(130,130,130,130),"Weak Prospect":(80,80,80,80)}
    prof_rows=[{"profile":name,**fixed_profile(*args,slopes=slopes,n=160000,seed=5000+i)} for i,(name,args) in enumerate(profiles.items())]
    extreme=[]
    for stat_i,stat in enumerate(("contact","power","discipline")):
        for raw in (30,50,70,90,110,130,150,180,200,250):
            args=[110,110,110,110];args[stat_i]=raw;extreme.append({"stat":stat,"raw":raw,"gameplay":norm(raw,stat,.6),**fixed_profile(*args,slopes=slopes,n=30000,seed=7000+stat_i*100+raw)})
    write('reports/hitter_raw_to_gameplay.csv',map_rows);write('reports/hitter_gameplay_sensitivity.csv',sens);write('reports/hitter_profile_validation.csv',prof_rows);write('reports/hitter_gameplay_scale_candidates.csv',slope_rows);write('reports/hitter_extreme_safety.csv',extreme)
    final={"gate_contract":"HITTER_GAMEPLAY_SCALE_READY","gate_ratio":"HITTER_DISPLAY_GAMEPLAY_RATIO_READY","references":REF,"slopes":selected,"prime_gameplay_mean":{"contact":100.0,"power":100.0,"discipline":100.0,"speed":100.0},"population_offense_neutral_pitcher":pop,"h32_formula_changed":False,"model":"linear","save_compatibility":"derived-only; raw PlayerStats unchanged"}
    Path('reports/hitter_gameplay_scale_final.json').write_text(json.dumps(final,indent=2))
    Path('reports/hitter_gameplay_scale_summary.md').write_text(f'''# Hitter Gameplay Scale Calibration\n\n## Gates\n- `HITTER_GAMEPLAY_SCALE_READY`\n- `HITTER_DISPLAY_GAMEPLAY_RATIO_READY`\n\n## Contract\nRaw career/display ratings stay persisted. Derived H3 inputs use `gameplay = 100 + (raw - raw_reference) * 0.60`. Existing H3.2.1 formulas are unchanged.\n\n26-30 mixed raw references: Contact {REF['contact']:.2f}, Power {REF['power']:.2f}, Discipline {REF['discipline']:.2f}, Speed {REF['speed']:.2f}.\n\n## Production-grown hitter population vs neutral H3 pitcher\nAVG {pop['AVG']:.4f}; OBP {pop['OBP']:.4f}; SLG {pop['SLG']:.4f}; OPS {pop['OPS']:.4f}; BB {pop['BB']:.3%}; K {pop['K']:.3%}; HR {pop['HR']:.3%}; BABIP {pop['BABIP']:.4f}.\n\nThis is a scale-contract diagnostic, not a hidden KBO fit.\n''')
    print(json.dumps(final,indent=2))
if __name__=='__main__':main()
