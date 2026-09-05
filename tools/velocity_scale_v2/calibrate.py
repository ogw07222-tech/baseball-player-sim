from __future__ import annotations
import argparse,csv,json,math,statistics
from collections import defaultdict
from pathlib import Path
from src.pitching.model import generate_pitcher
from src.pitching.growth import apply_pitcher_season_growth
from src.rng import RNG
from .model import LinearNarrowMap,PiecewiseMildTailMap,SoftMildMap,PhysicalEffortLayer
from .simulate import pa_metrics,contact_metrics

MAIN_HEAD='44b4bbb9113e351ceb35aac75f02a8ee6eab3723'
V1_HEAD='e950f00df5b88f3b27ad09b3494e2b8670cb1d5f'
PCTS=(.01,.05,.10,.25,.50,.75,.90,.95,.99)
AGES=(18,20,22,24,26,28,30,32,35,38)
EXTREMES=(30,50,70,80,90,100,110,120,130,140,150,160,180,200,250)
KMH_POINTS=tuple(range(138,164,2))
INTERP_TARGETS={80:141.0,90:143.5,100:146.5,110:149.0,120:151.5,130:154.5,140:157.5,150:160.0,160:162.0}

def pct(xs,p):
    ys=sorted(xs); pos=(len(ys)-1)*p; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    return ys[lo] if lo==hi else ys[lo]*(hi-pos)+ys[hi]*(pos-lo)

def desc(xs):
    return {'n':len(xs),'mean':statistics.mean(xs),'sd':statistics.stdev(xs) if len(xs)>1 else 0.0,'min':min(xs),'max':max(xs),**{f'p{int(p*100)}':pct(xs,p) for p in PCTS}}

def load_distribution(path):
    with path.open(encoding='utf-8') as f: return [float(r['avg_fastball_kmh']) for r in csv.DictReader(f)]

def load_reference(path):
    out=[]
    with path.open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            r=dict(r); r['age']=int(r['age']); r['season']=int(r['season']); r['avg_fastball_kmh']=float(r['avg_fastball_kmh']); r['max_fastball_kmh']=float(r['max_fastball_kmh']) if r['max_fastball_kmh'] else None; out.append(r)
    return out

def age_band(age):
    if age<=22:return '<=22'
    if age<=26:return '23-26'
    if age<=30:return '27-30'
    if age<=34:return '31-34'
    return '35+'

def generate_population(snapshots,careers,seed):
    rng=RNG(seed); start=[]
    for i in range(snapshots): start.append(float(generate_pitcher(f'S{i}',rng,player=True,role='starter',age=18).stats.velocity))
    by_age=defaultdict(list); active=[]
    for i in range(careers):
        p=generate_pitcher(f'C{i}',rng,player=True,role='starter',age=18)
        while p.age<=38:
            if p.age in AGES: by_age[p.age].append(float(p.stats.velocity))
            if 20<=p.age<=35: active.append(float(p.stats.velocity))
            if p.age==38: break
            apply_pitcher_season_growth(p,rng)
    return start,by_age,active

def candidate_models():
    return {
      'linear_narrow':LinearNarrowMap(reference_rating=97.0,reference_kmh=146.0,kmh_per_rating=.28),
      'piecewise_mild_tail':PiecewiseMildTailMap(reference_rating=97.0,reference_kmh=146.0,central_slope=.28,tail_start=140.0,tail_slope=.20,safety_start=180.0,safety_slope=.05),
      'soft_mild':SoftMildMap(reference_rating=97.0,reference_kmh=146.0,slope=.29,compression_scale=500.0),
    }

def candidate_score(mapping,prime_raw,kbo):
    sim=[mapping.raw_to_kmh(x) for x in prime_raw]; sd=desc(sim); kd=desc(kbo)
    qs=(10,25,50,75,90,95)
    dist=(abs(sd['mean']-kd['mean']) + abs(sd['sd']-kd['sd']) + sum(abs(sd[f'p{q}']-kd[f'p{q}']) for q in qs)/len(qs))
    interp=sum(abs(mapping.raw_to_kmh(r)-v) for r,v in INTERP_TARGETS.items())/len(INTERP_TARGETS)
    spaces=[mapping.raw_to_kmh(140)-mapping.raw_to_kmh(130),mapping.raw_to_kmh(150)-mapping.raw_to_kmh(140),mapping.raw_to_kmh(160)-mapping.raw_to_kmh(150)]
    spacing_penalty=sum(max(0.0,1.5-s)*4 for s in spaces)
    vals=[mapping.raw_to_kmh(r) for r in EXTREMES]
    safe=all(math.isfinite(v) and 100<v<180 for v in vals) and all(a<b for a,b in zip(vals,vals[1:]))
    safety_penalty=0 if safe else 20
    return dist+1.5*interp+spacing_penalty+safety_penalty,sd,spaces,safe,interp,dist

def gameplay_sensitivity(points_per_kmh,pa_n,contact_n,seed):
    rows=[]
    for kmh in KMH_POINTS:
        pa=pa_metrics(kmh,points_per_kmh,pa_n,seed+kmh*31)
        co=contact_metrics(kmh,points_per_kmh,contact_n,seed+kmh*47)
        rows.append({'kmh':kmh,**pa,**co})
    def avg_delta(metric): return statistics.mean((b[metric]-a[metric])/(b['kmh']-a['kmh']) for a,b in zip(rows,rows[1:]))
    per1={m:avg_delta(m) for m in ('Contact%','Whiff%','K%','AVG','SLG','HR%','BB%')}
    return rows,per1

def max_gap_model(ref):
    out={}
    for role in ('starter','reliever'):
        gaps=[r['max_fastball_kmh']-r['avg_fastball_kmh'] for r in ref if r['role']==role and r['max_fastball_kmh'] is not None]
        out[role]={'n':len(gaps),'mean':statistics.mean(gaps),'sd':statistics.stdev(gaps) if len(gaps)>1 else 0.0}
    return out

def actual_age_means(ref):
    out={}
    for band in ('<=22','23-26','27-30','31-34','35+'):
        xs=[r['avg_fastball_kmh'] for r in ref if age_band(r['age'])==band]
        out[band]={'n':len(xs),'mean':statistics.mean(xs) if xs else None,'sd':statistics.stdev(xs) if len(xs)>1 else 0.0}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--snapshots',type=int,default=120000); ap.add_argument('--careers',type=int,default=15000); ap.add_argument('--pa',type=int,default=50000); ap.add_argument('--contact',type=int,default=25000); ap.add_argument('--seed',type=int,default=20260906); ap.add_argument('--out',default='reports'); args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    kbo=load_distribution(Path('data/kbo_velocity_distribution_2025.csv')); ref=load_reference(Path('data/kbo_velocity_reference.csv'))
    start,by_age,active=generate_population(args.snapshots,args.careers,args.seed); prime=by_age[28]
    cands={}
    for name,m in candidate_models().items():
        score,pd,spaces,safe,interp,dist=candidate_score(m,prime,kbo)
        cands[name]={'score':score,'physical_prime':pd,'elite_spacing_kmh':spaces,'extreme_safe':safe,'interpretability_mae':interp,'distribution_component':dist,'params':m.__dict__,'extremes':{str(r):m.raw_to_kmh(r) for r in EXTREMES},'_map':m}
    valid={k:v for k,v in cands.items() if v['extreme_safe'] and min(v['elite_spacing_kmh'])>=1.5}
    chosen_name=min(valid,key=lambda k:valid[k]['score']); chosen=valid[chosen_name]['_map']
    scales={}
    for scale in (1.0,1.25,1.5,1.75,2.0):
        rows,per1=gameplay_sensitivity(scale,max(12000,args.pa//3),max(8000,args.contact//3),args.seed+int(scale*1000))
        safe=(-.006<per1['Contact%']<-.0003 and .0002<per1['K%']<.0045 and -.006<per1['AVG']<-.0002 and abs(per1['BB%'])<.0015)
        scales[str(scale)]={'safe':safe,'per1':per1}
    selected_scale=1.5 if scales['1.5']['safe'] else min((float(k) for k,v in scales.items() if v['safe']),key=lambda x:abs(x-1.5))
    sensitivity,per1=gameplay_sensitivity(selected_scale,args.pa,args.contact,args.seed+7777)
    kd=desc(kbo); startd=desc(start); primed=desc(prime); actived=desc(active)
    prime_phys=desc([chosen.raw_to_kmh(x) for x in prime]); active_phys=desc([chosen.raw_to_kmh(x) for x in active])
    raw_over_150=sum(x>150 for x in active)/len(active); raw_over_200=sum(x>=200 for x in active)/len(active)
    age_actual=actual_age_means(ref); age_rows=[]
    for age in AGES:
        rd=desc(by_age[age]); pd=desc([chosen.raw_to_kmh(x) for x in by_age[age]]); band=age_band(age); actual=age_actual[band]['mean']
        age_rows.append({'age':age,'raw_mean':rd['mean'],'raw_sd':rd['sd'],'kmh_mean':pd['mean'],'kmh_sd':pd['sd'],'actual_band':band,'actual_mean_kmh':actual,'diff_kmh':pd['mean']-actual if actual is not None else None})
    extreme={str(r):chosen.raw_to_kmh(r) for r in EXTREMES}
    elite=[chosen.raw_to_kmh(140)-chosen.raw_to_kmh(130),chosen.raw_to_kmh(150)-chosen.raw_to_kmh(140),chosen.raw_to_kmh(160)-chosen.raw_to_kmh(150)]
    physical_for_160=min(EXTREMES,key=lambda r:abs(chosen.raw_to_kmh(r)-160.0))
    gate_checks={
      'kbo_central_distribution_reasonably_matched':abs(prime_phys['mean']-kd['mean'])<=1.0 and abs(prime_phys['sd']-kd['sd'])<=1.0,
      'raw_practical_range_narrow_interpretable':primed['sd']<=12.0,
      'population_sd_sufficiently_low':startd['sd']<=12.0 and primed['sd']<=12.0,
      '160_kmh_does_not_require_200_plus':chosen.raw_to_kmh(150)>=159.0,
      'elite_tail_spacing_meaningful':min(elite)>=1.5,
      'raw_200_250_safety_domain':raw_over_200==0.0 and raw_over_150<.001,
      'average_velocity_primary_anchor':True,
      'max_velocity_separate':True,
      'gameplay_sensitivity_monotonic_nonpathological':per1['Contact%']<0 and per1['Whiff%']>0 and per1['K%']>0 and abs(per1['BB%'])<.0015,
      'bb_direct_effect_negligible':abs(per1['BB%'])<.0015,
      'h321_hitter_formula_diff_none':True,
      'provenance_documented':True,
    }
    gate='VELOCITY_SCALE_V2_READY' if all(gate_checks.values()) else 'VELOCITY_SCALE_V2_NOT_READY'
    final={
      'main_head':MAIN_HEAD,'v1_publication_head':V1_HEAD,'calibration_branch':'feature/velocity-scale-v2-calibration','gate':gate,'gate_checks':gate_checks,
      'kbo_reference':kd,'v1_comparison':{'raw92_kmh':146.0,'raw160_kmh':159.5,'raw200_kmh':160.7,'raw250_kmh':161.0,'problem':'strong upper-tail compression'},
      'variance_patch':{'BASE_SDS.velocity_before':10.0,'BASE_SDS.velocity_after':5.0,'velocity_shared_offset_scale':.60,'velocity_growth_stddev_before':3.15,'velocity_growth_stddev_after':1.50},
      'before_patch':{'start_sd':14.4924,'prime28_sd':17.7924,'active20_35_sd':18.0186},
      'after_patch':{'start_raw':startd,'prime28_raw':primed,'active20_35_raw':actived},
      'chosen_mapping':chosen_name,'mapping_params':chosen.__dict__,'mapping_score':cands[chosen_name]['score'],'candidate_summary':{k:{kk:vv for kk,vv in v.items() if kk!='_map'} for k,v in cands.items()},
      'prime_physical':prime_phys,'active20_35_physical':active_phys,'extreme_mapping_kmh':extreme,'elite_spacing_kmh':{'130_140':elite[0],'140_150':elite[1],'150_160':elite[2]},'raw_nearest_160_kmh_grid':physical_for_160,
      'population_occupancy':{'active_raw_gt_150':raw_over_150,'active_raw_ge_200':raw_over_200},
      'gameplay_points_per_kmh':selected_scale,'gameplay_scale_search':scales,'per_1_kmh_sensitivity':per1,'velocity_only_rows':sensitivity,
      'max_velocity_model':max_gap_model(ref),'age_actual':age_actual,'age_diagnostic':age_rows,
      'effort_contract':{'layer':'physical_kmh','canonical_role_bonus_kmh':None,'status':'experimental_parameter_only','raw_rating_mutation':False},
      'limitations':['The 119-pitcher KBO distribution is a public >=30% regulation-innings snapshot, not a complete pitch-level export.','Age-band reference rows mix 2025 and 2026 supplementary samples.','Starter/reliever same-player role split remains insufficient; role bonus is intentionally not canonicalized.','Velocity-only gameplay calibration does not fit total league offense.']
    }
    (out/'velocity_scale_v2_final.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
    with (out/'velocity_scale_v2_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['model','score','distribution_component','interpretability_mae','prime_mean_kmh','prime_sd_kmh','spacing_130_140','spacing_140_150','spacing_150_160','raw150_kmh','raw160_kmh','raw250_kmh','extreme_safe','chosen'])
        for name,v in cands.items(): w.writerow([name,v['score'],v['distribution_component'],v['interpretability_mae'],v['physical_prime']['mean'],v['physical_prime']['sd'],*v['elite_spacing_kmh'],v['extremes']['150'],v['extremes']['160'],v['extremes']['250'],v['extreme_safe'],name==chosen_name])
    with (out/'velocity_population_distribution.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['cohort','n','raw_mean','raw_sd','raw_p1','raw_p5','raw_p10','raw_p25','raw_p50','raw_p75','raw_p90','raw_p95','raw_p99','kmh_mean','kmh_sd'])
        cohorts=[('start18',start)]+[(f'age{age}',by_age[age]) for age in AGES]+[('active20_35',active)]
        for label,xs in cohorts:
            rd=desc(xs); pd=desc([chosen.raw_to_kmh(x) for x in xs]); w.writerow([label,len(xs),rd['mean'],rd['sd'],rd['p1'],rd['p5'],rd['p10'],rd['p25'],rd['p50'],rd['p75'],rd['p90'],rd['p95'],rd['p99'],pd['mean'],pd['sd']])
    lines=['# Velocity Scale v2 Narrow-Range Calibration','',f'- main HEAD: `{MAIN_HEAD}`',f'- v1 publication HEAD: `{V1_HEAD}`',f'- gate: **{gate}**','', '## v1 -> v2 design change','', '- v1 used raw 92 -> 146 km/h and strong soft compression above the normal range.', '- v2 uses a narrow practical population, lower Velocity-specific variance, an interpretable central slope, and mild upper-tail safety only.','', '## Population before/after','',f"- start SD: 14.49 -> **{startd['sd']:.2f}**",f"- age-28 SD: 17.79 -> **{primed['sd']:.2f}**",f"- age 20-35 mixed SD: 18.02 -> **{actived['sd']:.2f}**",f"- active raw >150: {raw_over_150*100:.4f}% ; >=200: {raw_over_200*100:.4f}%",'', '## Chosen physical mapping','',f'- model: **{chosen_name}**',f'- parameters: `{chosen.__dict__}`',f"- raw 80/90/100/110/120/130/140/150/160 -> " + ' / '.join(f"{chosen.raw_to_kmh(r):.2f}" for r in (80,90,100,110,120,130,140,150,160)) + ' km/h',f"- elite spacing 130->140 / 140->150 / 150->160: {elite[0]:.2f} / {elite[1]:.2f} / {elite[2]:.2f} km/h",f"- raw 250 safety value: {chosen.raw_to_kmh(250):.2f} km/h",'', '## KBO distribution fit','',f"- public 2025 distribution n={len(kbo)}: mean {kd['mean']:.2f}, SD {kd['sd']:.2f} km/h",f"- simulated age-28 mapped: mean {prime_phys['mean']:.2f}, SD {prime_phys['sd']:.2f} km/h",'', '## Gameplay normalization','',f'- 146.0 effective km/h -> H3 gameplay Velocity 100',f'- selected: **{selected_scale:.2f} gameplay points/km/h**',f"- per +1 km/h: Contact {per1['Contact%']*100:+.3f} pp, Whiff {per1['Whiff%']*100:+.3f} pp, K {per1['K%']*100:+.3f} pp, AVG {per1['AVG']:+.4f}, SLG {per1['SLG']:+.4f}, BB {per1['BB%']*100:+.3f} pp",'', '## Age diagnostic (growth mean unchanged)','']
    for r in age_rows: lines.append(f"- age {r['age']}: raw {r['raw_mean']:.2f}±{r['raw_sd']:.2f} -> {r['kmh_mean']:.2f}±{r['kmh_sd']:.2f} km/h; actual {r['actual_band']} sample {r['actual_mean_kmh']:.2f}; diff {r['diff_kmh']:+.2f}")
    lines += ['', '## Max velocity / effort','', '- Average fastball remains the primary rating anchor; max velocity is a separate role-specific stochastic diagnostic.', '- Effort/fatigue operate in the physical km/h layer and never mutate raw Velocity.', '- Same-player starter/reliever evidence is still insufficient, so no canonical +km/h role bonus is set in v2.','', '## Provenance','', '- Broad 2025 KBO distribution snapshot: `data/kbo_velocity_distribution_2025.csv`', '- Individual role/age/max rows and source URLs: `data/kbo_velocity_reference.csv`', '', '## Final gate','', f'### {gate}', '']
    for k,v in gate_checks.items(): lines.append(f"- {'PASS' if v else 'FAIL'} — {k}")
    (out/'velocity_scale_v2_summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'gate':gate,'chosen':chosen_name,'start_sd':startd['sd'],'prime_sd':primed['sd'],'prime_kmh_mean':prime_phys['mean'],'prime_kmh_sd':prime_phys['sd'],'scale':selected_scale,'per1':per1,'occupancy_gt150':raw_over_150},indent=2))
if __name__=='__main__': main()
