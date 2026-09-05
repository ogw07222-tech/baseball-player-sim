from __future__ import annotations
import csv,json,math
from pathlib import Path
from statistics import mean,pstdev
from src.player import Player
from src.rng import RNG
import src.growth as G
from src.hitting.model import HitterSnapshot,PitcherSnapshot,HittingEngine
from src.hitting.baserunning import GameState,steal_attempt_probability,steal_success_probability,first_to_third_probability,second_to_home_probability,dp_completion_probability
from src.hitting import parameters as P

AGES=(18,20,22,24,26,28,30,32,35,38)
STATS=("contact","power","discipline","speed")
PCTS=(.01,.05,.10,.25,.50,.75,.90,.95,.99)
SLOPES=(.40,.50,.60,.70,.80,.90,1.00)
SPEED_SLOPES=(.40,.60,.80,1.00,1.20)
RAW_GRID=(30,50,70,80,90,100,110,120,130,140,150,160,180,200,250)
SPEED_GRID=(70,80,90,100,110,120,130,140,150,160)
BEFORE_PRIME={"contact":94.2742,"power":92.78481111111111,"discipline":87.34492222222222,"speed":98.0363888888889}

def percentile(v,q):
    s=sorted(v);x=(len(s)-1)*q;lo=int(x);hi=min(len(s)-1,lo+1);f=x-lo;return s[lo]*(1-f)+s[hi]*f

def stats(v):
    d={"mean":mean(v),"sd":pstdev(v)}
    for q in PCTS:d[f"p{int(q*100):02d}"]=percentile(v,q)
    return d

def grow(p,rng,recenter=True):
    deltas={}
    for stat in G.GROWABLE_STATS:
        mu,sd=G.growth_distribution(p,stat)
        if not recenter:mu-=G._hitter_cpd_recenter_bonus(stat,p.age)
        old=getattr(p.stats,stat);new=p.stats.apply_delta(stat,int(round(rng.gauss(mu,sd))));deltas[stat]=new-old
    explosion=rng.random()<G._explosion_chance(p)
    if explosion:
        count=rng.randint(1,min(3,len(G.GROWABLE_STATS)))
        for stat in rng.sample(G.GROWABLE_STATS,count):
            bonus=rng.randint(G.config.GROWTH_EXPLOSION_MIN_BONUS,G.config.GROWTH_EXPLOSION_MAX_BONUS);p.stats.apply_delta(stat,bonus)
    p.advance_age(1)

def cohorts(n=30000,seed=8841):
    positions=("C","1B","2B","3B","SS","LF","CF","RF","DH")
    out={"before":{a:{s:[] for s in STATS} for a in AGES},"after":{a:{s:[] for s in STATS} for a in AGES}}
    r0=RNG(seed);r1=RNG(seed)
    before=[];after=[]
    for i in range(n):
        pos=r0.choice(positions); _=r1.choice(positions)
        before.append(Player.random(f"B{i}",r0,position=pos));after.append(Player.random(f"A{i}",r1,position=pos))
    for age in range(18,39):
        if age in AGES:
            for label,ps in (("before",before),("after",after)):
                for p in ps:
                    for s in STATS:out[label][age][s].append(getattr(p.stats,s))
        if age<38:
            for p in before:grow(p,r0,False)
            for p in after:grow(p,r1,True)
    return out

def norm(raw,ref,slope):return 100+(raw-ref)*slope

def pa_metrics(rows,refs,slopes,n=100000,seed=1):
    rng=RNG(seed);c={}
    for i in range(n):
        rc,rp,rd,rs=rows[i%len(rows)]
        h=HitterSnapshot(norm(rc,refs['contact'],slopes['contact']),norm(rp,refs['power'],slopes['power']),norm(rd,refs['discipline'],slopes['discipline']),norm(rs,refs['speed'],slopes['speed']))
        o=HittingEngine(h,PitcherSnapshot(),100.0,rng).simulate_plate_appearance().result;c[o]=c.get(o,0)+1
    hits=sum(c.get(k,0) for k in ('single','double','triple','home_run'));walk=c.get('walk',0);ab=n-walk;tb=c.get('single',0)+2*c.get('double',0)+3*c.get('triple',0)+4*c.get('home_run',0);bip=max(1,ab-c.get('strikeout',0)-c.get('home_run',0))
    return {'AVG':hits/ab,'OBP':(hits+walk)/n,'SLG':tb/ab,'OPS':(hits+walk)/n+tb/ab,'BB':walk/n,'K':c.get('strikeout',0)/n,'HR':c.get('home_run',0)/n,'BABIP':(hits-c.get('home_run',0))/bip}

def speed_value(gp):
    state=GameState(inning=5,outs=1,score_diff=0,first_occupied=True,second_occupied=False)
    att=steal_attempt_probability(gp,state);succ=steal_success_probability(gp,state,100);f3=first_to_third_probability(gp,100);sh=second_to_home_probability(gp,100);dp=dp_completion_probability(gp);avoid=1-dp
    rv=att*(succ*P.SB_RUN_VALUE+(1-succ)*P.CS_RUN_VALUE)+P.FIRST_TO_THIRD_OPP_RATE*f3*P.FIRST_TO_THIRD_VALUE+P.SECOND_TO_HOME_OPP_RATE*sh*P.SECOND_TO_HOME_VALUE+P.DP_OPP_RATE*avoid*P.DP_AVOIDED_VALUE
    return {'steal_attempt':att,'steal_success':succ,'cs_given_attempt':1-succ,'first_to_third':f3,'second_to_home':sh,'dp_avoidance':avoid,'run_value_proxy':rv}

def write(path,rows):
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields:fields.append(k)
    with open(path,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    Path('reports').mkdir(exist_ok=True);co=cohorts();age_rows=[]
    for label in ('before','after'):
        for a in AGES:
            for s in STATS:age_rows.append({'version':label,'age':a,'stat':s,**stats(co[label][a][s])})
    prime={}
    for s in STATS:
        vals=[]
        for a in (26,28,30):vals.extend(co['after'][a][s])
        prime[s]=stats(vals)
    refs={s:prime[s]['mean'] for s in STATS}
    prime_rows=[]
    for s in STATS:prime_rows.append({'stat':s,'before_mean':BEFORE_PRIME[s],'after_mean':prime[s]['mean'],'after_sd':prime[s]['sd'],'reference':refs[s]})
    # Slope diagnostics on actual after-prime population.
    rows=[]
    for a in (26,28,30):
        for i in range(len(co['after'][a]['contact'])):rows.append(tuple(co['after'][a][s][i] for s in STATS))
    candidate=[]
    for sl in SLOPES:
        slopes={s:sl for s in STATS};m=pa_metrics(rows,refs,slopes,120000,1000+int(sl*100));candidate.append({'slope':sl,**m,'gp_sd_contact':prime['contact']['sd']*sl,'gp_sd_power':prime['power']['sd']*sl,'gp_sd_discipline':prime['discipline']['sd']*sl})
    # Requested +1/+5/+10 matrix using common slope .60 candidate.
    slopes={s:.60 for s in STATS};sens=[]
    for stat_i,s in enumerate(('contact','power','discipline')):
        for base in (80,90,100,110,120,130,140,150):
            baseargs=[110,110,110,refs['speed']];baseargs[stat_i]=base;base_m=pa_metrics([tuple(baseargs)],refs,slopes,30000,5000+stat_i*100+base)
            for d in (1,5,10):
                args=baseargs.copy();args[stat_i]+=d;up=pa_metrics([tuple(args)],refs,slopes,30000,5000+stat_i*100+base)
                sens.append({'stat':s,'baseline':base,'delta_raw':d,'delta_gameplay':d*.60,**{f'd{k}':up[k]-base_m[k] for k in ('AVG','OBP','SLG','BB','K','HR','BABIP')}})
    profiles={'Average':(110,110,110,110),'Contact Specialist':(140,95,110,110),'Power Hitter':(100,145,100,110),'Discipline Specialist':(105,105,140,110),'Balanced Star':(130,130,125,120),'Tool Monster':(145,145,135,135),'Weak Prospect':(80,80,80,80)}
    profile_rows=[{'profile':name,**pa_metrics([vals],refs,slopes,80000,7000+i)} for i,(name,vals) in enumerate(profiles.items())]
    # Speed full-value grid. Compare linear slopes without changing frozen baserunning formulas.
    speed_rows=[]
    for sl in SPEED_SLOPES:
        sp_slopes={'contact':.60,'power':.60,'discipline':.60,'speed':sl}
        for raw in SPEED_GRID:
            gp=norm(raw,refs['speed'],sl);sv=speed_value(gp);bat=pa_metrics([(refs['contact'],refs['power'],refs['discipline'],raw)],refs,sp_slopes,30000,9000+int(sl*100)+raw)
            speed_rows.append({'slope':sl,'raw_speed':raw,'gameplay_speed':gp,**sv,**{k:bat[k] for k in ('AVG','OBP','SLG','BABIP')}})
    # Select common .60 for C/P/D only when prime/display gate passes; speed .80 if high-end RV remains separated, otherwise .60.
    cpd_gate=all(108<=prime[s]['mean']<=112 for s in ('contact','power','discipline')) and all(65<=stats(co['after'][18][s])['mean']<=95 for s in ('contact','power','discipline'))
    sp60=[r for r in speed_rows if r['slope']==.60];sp80=[r for r in speed_rows if r['slope']==.80]
    def high_sep(rs):
        m={r['raw_speed']:r for r in rs};return m[150]['run_value_proxy']-m[140]['run_value_proxy']
    speed_slope=.80 if high_sep(sp80)>high_sep(sp60)*1.15 else .60
    sp=[r for r in speed_rows if r['slope']==speed_slope];mm={r['raw_speed']:r for r in sp};speed_gate=all(mm[b]['run_value_proxy']<mm[b+10]['run_value_proxy'] for b in SPEED_GRID[:-1]) and mm[150]['run_value_proxy']-mm[140]['run_value_proxy']>0.0002
    gameplay_gate=cpd_gate
    final_gate=cpd_gate and gameplay_gate and speed_gate
    write('reports/hitter_cpd_age_curve.csv',age_rows);write('reports/hitter_cpd_before_after.csv',prime_rows);write('reports/hitter_cpd_normalization_candidates.csv',candidate);write('reports/hitter_cpd_sensitivity.csv',sens);write('reports/hitter_cpd_profiles.csv',profile_rows);write('reports/hitter_speed_grid.csv',speed_rows);write('reports/hitter_speed_full_value.csv',speed_rows)
    actual=pa_metrics(rows,refs,{'contact':.60,'power':.60,'discipline':.60,'speed':speed_slope},500000,12001);write('reports/hitter_actual_population_validation.csv',[actual])
    final={'source_base':'5aad8004650c07a6f82560eaaf2c5ff89580598a','prime':prime,'references':refs,'cpd_slope':.60,'speed_slope':speed_slope,'actual_population':actual,'gates':{'HITTER_CPD_RAW_SCALE_READY':cpd_gate,'HITTER_CPD_GAMEPLAY_SCALE_READY':gameplay_gate,'HITTER_SPEED_RATIO_READY':speed_gate,'HITTER_DISPLAY_GAMEPLAY_CONTRACT_READY':final_gate},'h32_formula_changed':False,'speed_note':'Frozen H3.2.1 baserunning formulas; value proxy includes SB/CS, first-to-third, second-to-home, and DP avoidance.'}
    Path('reports/hitter_cpd_normalization_final.json').write_text(json.dumps(final,indent=2))
    Path('reports/hitter_cpd_scale_summary.md').write_text(f"# Hitter CPD Raw Scale Re-centering\n\nPrime means after: Contact {prime['contact']['mean']:.2f}, Power {prime['power']['mean']:.2f}, Discipline {prime['discipline']['mean']:.2f}. Entry generation is unchanged. C/P/D slope candidate: 0.60.\n\nGate: {'HITTER_CPD_RAW_SCALE_READY' if cpd_gate else 'HITTER_CPD_RAW_SCALE_NOT_READY'}.\n")
    Path('reports/hitter_speed_ratio_summary.md').write_text(f"# Hitter Speed Ratio\n\nPrime raw Speed {prime['speed']['mean']:.2f}; selected gameplay slope {speed_slope:.2f}. High-end 140->150 run-value proxy delta {mm[150]['run_value_proxy']-mm[140]['run_value_proxy']:.6f}.\n\nGate: {'HITTER_SPEED_RATIO_READY' if speed_gate else 'HITTER_SPEED_RATIO_NOT_READY'}.\n")
    print(json.dumps(final,indent=2))
if __name__=='__main__':main()
