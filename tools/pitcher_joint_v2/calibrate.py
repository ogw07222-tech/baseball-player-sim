from __future__ import annotations
import argparse,csv,json,math,random,statistics
from collections import Counter
from pathlib import Path
from src import config
from src.growth import GrowthExperience,apply_season_growth
from src.hitting.model import HitterSnapshot
from src.player import Player
from src.pitching.growth import apply_pitcher_season_growth
from src.pitching.model import PitcherStats,generate_pitcher
from src.pitching.physical_velocity import base_avg_kmh,effective_avg_kmh,gameplay_velocity
from src.rng import RNG
from src.stats import generate_high_school_npc_stats
from src.traits import generate_random_traits
from .adapter import JointWeights,PitcherJointAdapter
from .targets import KBO_TARGETS,TOLERANCES,OBJECTIVE_WEIGHTS,SEARCH_RANGES

MAIN_BASE='44b4bbb9113e351ceb35aac75f02a8ee6eab3723'
VELOCITY_V2_SHA='c405b3e9c1ec2633fabd0f033c0c923b165bd6af'
FULL_AGES=((20,.02),(21,.03),(22,.05),(23,.07),(24,.09),(25,.10),(26,.11),(27,.11),(28,.11),(29,.10),(30,.08),(31,.05),(32,.035),(33,.025),(34,.015),(35,.01),(36,.005))

def age(r): return int(r.weighted_choice(FULL_AGES))
def exp(a): return GrowthExperience(first_team_pa=0,farm_pa=420) if a<=21 else GrowthExperience(first_team_pa=160,farm_pa=260) if a<=23 else GrowthExperience(first_team_pa=420,farm_pa=0)
def build_hitters(n,seed):
 r=RNG(seed);out=[]
 for i in range(n):
  pos=r.choice(tuple(config.POSITIONS)); p=Player(name=f'H{i}',age=18,stats=generate_high_school_npc_stats(r,pos),traits=generate_random_traits(r),position=pos,development_profile=r.weighted_choice(config.DEVELOPMENT_PROFILE_WEIGHTS));target=age(r)
  while p.age<target: apply_season_growth(p,r,experience=exp(p.age))
  out.append(p)
 return out
def build_pitchers(n,seed):
 r=RNG(seed);out=[]
 for i in range(n):
  p=generate_pitcher(f'P{i}',r,player=False,age=18);target=age(r)
  while p.age<target: apply_pitcher_season_growth(p,r)
  out.append(p)
 return out
def hs(p):
 hand='L' if p.bats_throws.startswith('L') else 'R';return HitterSnapshot(float(p.stats.contact),float(p.stats.power),float(p.stats.discipline),float(p.stats.speed),hand,'balanced')
def neutral(**kw):
 d=dict(velocity=97,stuff=100,control=100,breaking=100,stamina=100,resilience=100,talent=100);d.update(kw);return PitcherStats(**d)
def metrics(c,b,pa,hard=0):
 bb=c['walk'];so=c['strikeout'];hr=c['home_run'];one=c['single'];two=c['double'];three=c['triple'];h=one+two+three+hr;ab=max(1,pa-bb);bip=max(1,ab-so-hr);balls=max(1,sum(b.values()))
 return {'AVG':h/ab,'OBP':(h+bb)/pa,'SLG':(one+2*two+3*three+4*hr)/ab,'OPS':(h+bb)/pa+(one+2*two+3*three+4*hr)/ab,'BB%':bb/pa,'K%':so/pa,'HR%':hr/pa,'1B%':one/pa,'2B%':two/pa,'3B%':three/pa,'BABIP':(h-hr)/bip,'GB%':b['ground_ball']/balls,'LD%':b['line_drive']/balls,'FB%':b['fly_ball']/balls,'HardContact%':hard/balls}
def sim(weights,hitters,pitchers,pa,seed):
 choose=random.Random(seed^0xA17E);rng=random.Random(seed^0xC0DE);c=Counter();b=Counter();hard=0
 for _ in range(pa):
  h=hitters[choose.randrange(len(hitters))];p=pitchers[choose.randrange(len(pitchers))];o=PitcherJointAdapter(p.stats,weights).make_engine(hs(h),100.0,rng).simulate_plate_appearance();c[o.result]+=1
  if o.batted_ball is not None:
   b[o.batted_ball.ball_type]+=1;hard+=int(o.batted_ball.exit_quality>=.75)
 return metrics(c,b,pa,hard)
def matchup(weights,stats,pa,seed,kmh=146.0):
 rng=random.Random(seed);c=Counter();b=Counter();hard=0;h=HitterSnapshot(100,100,100,100);ad=PitcherJointAdapter(stats,weights,physical_kmh_override=kmh)
 for _ in range(pa):
  o=ad.make_engine(h,100.0,rng).simulate_plate_appearance();c[o.result]+=1
  if o.batted_ball is not None:b[o.batted_ball.ball_type]+=1;hard+=int(o.batted_ball.exit_quality>=.75)
 return metrics(c,b,pa,hard)
def loss(m): return sum(OBJECTIVE_WEIGHTS[k]*abs(m[k]-KBO_TARGETS[k])/TOLERANCES[k] for k in OBJECTIVE_WEIGHTS)/sum(OBJECTIVE_WEIGHTS.values())
def pass_tol(m): return all(abs(m[k]-KBO_TARGETS[k])<=v for k,v in TOLERANCES.items())
def randw(r): return JointWeights(**{k:r.uniform(*v) for k,v in SEARCH_RANGES.items()})
def avg_runs(runs): return {k:statistics.fmean(x[k] for x in runs) for k in runs[0]}
def pct(xs,p):
 s=sorted(xs);x=(len(s)-1)*p/100;lo=int(math.floor(x));hi=int(math.ceil(x));return s[lo] if lo==hi else s[lo]*(hi-x)+s[hi]*(x-lo)
def velocity_dist(pitchers):
 v=[base_avg_kmh(x.stats.velocity) for x in pitchers];return {'mean':statistics.fmean(v),'sd':statistics.pstdev(v),'p10':pct(v,10),'p25':pct(v,25),'p50':pct(v,50),'p75':pct(v,75),'p90':pct(v,90),'p95':pct(v,95),'p99':pct(v,99),'max':max(v)}
def prime_diag(n,seed):
 r=RNG(seed);cols={k:[] for k in ('velocity','stuff','control','breaking','stamina','resilience','ability')}
 for i in range(n):
  p=generate_pitcher(str(i),r,player=False,age=18)
  while p.age<28:apply_pitcher_season_growth(p,r)
  for k in cols:cols[k].append(p.stats.current_ability() if k=='ability' else getattr(p.stats,k))
 return {k:{'mean':statistics.fmean(v),'sd':statistics.pstdev(v)} for k,v in cols.items()}
def deltas(weights,pa,seed):
 base=matchup(weights,neutral(),pa,seed);out={}
 for stat in ('stuff','control','breaking'):
  m=matchup(weights,neutral(**{stat:120}),pa,seed);out[stat]={k:m[k]-base[k] for k in ('AVG','OBP','SLG','OPS','BB%','K%','HR%','HardContact%')}
 for d in (3,5,8):
  m=matchup(weights,neutral(),pa,seed,146+d);out[f'velocity_plus_{d}kmh']={k:m[k]-base[k] for k in ('AVG','SLG','BB%','K%','HR%')}
 return {'baseline':base,'plus20':out}
def archetypes(weights,pa,seed):
 profiles={'power_pitcher':(155,125,90,90),'command_starter':(145,100,140,120),'breaking_specialist':(144,110,100,145),'high_stuff_low_weapons':(143,150,100,80),'balanced_ace':(151,125,125,125)};out={}
 for i,(n,(v,s,c,b)) in enumerate(profiles.items()):out[n]=matchup(weights,neutral(stuff=s,control=c,breaking=b),pa,seed+i,v)
 return out
def synergy(weights,pa,seed):
 p={'A_158_S75':(158,75),'B_142_S150':(142,150),'C_151_S120':(151,120)};return {n:matchup(weights,neutral(stuff=s),pa,seed+i,v) for i,(n,(v,s)) in enumerate(p.items())}
def semantic_gates(d):
 x=d['plus20'];control_owner=x['control']['BB%']<min(x['stuff']['BB%'],x['breaking']['BB%'])-.003
 breaking_whiff=x['breaking']['K%']>x['stuff']['K%']+.001
 stuff_quality=x['stuff']['HardContact%']<x['breaking']['HardContact%']+.003 and x['stuff']['SLG']<-.005
 stuff_universal=x['stuff']['K%']>.01 and x['stuff']['BB%']<-.004 and x['stuff']['AVG']<-.01 and x['stuff']['SLG']<-.02 and x['stuff']['HR%']<-.003
 control_universal=x['control']['SLG']<-.02 or x['control']['HR%']<-.004
 return {'control_owns_bb':control_owner,'breaking_more_k_than_stuff':breaking_whiff,'stuff_quality_identity':stuff_quality,'stuff_not_universal':not stuff_universal,'control_not_universal':not control_universal}
def main():
 a=argparse.ArgumentParser();a.add_argument('--hitters',type=int,default=2000);a.add_argument('--pitchers',type=int,default=2000);a.add_argument('--candidates',type=int,default=30);a.add_argument('--search-pa',type=int,default=100000);a.add_argument('--validation-pa',type=int,default=1000000);a.add_argument('--top',type=int,default=3);a.add_argument('--seeds',type=int,default=5);a.add_argument('--diag-pa',type=int,default=300000);a.add_argument('--seed',type=int,default=260906);a.add_argument('--outdir',default='reports');z=a.parse_args();Path(z.outdir).mkdir(parents=True,exist_ok=True)
 hitters=build_hitters(z.hitters,z.seed);pitchers=build_pitchers(z.pitchers,z.seed+1);r=random.Random(z.seed+2);rows=[]
 cand=[JointWeights()]+[randw(r) for _ in range(z.candidates-1)]
 for w in cand:
  m=sim(w,hitters,pitchers,z.search_pa,z.seed+3);rows.append((loss(m),w,m))
 rows.sort(key=lambda x:x[0]);validated=[]
 for rank,(l,w,m) in enumerate(rows[:z.top],1):
  runs=[sim(w,hitters,pitchers,z.validation_pa,z.seed+100+s) for s in range(z.seeds)];mean=avg_runs(runs);validated.append({'rank':rank,'search_loss':l,'weights':w.as_dict(),'metrics':mean,'loss':loss(mean),'passed_tolerances':pass_tol(mean),'seed_sd':{k:statistics.pstdev(x[k] for x in runs) for k in ('AVG','OBP','SLG','BB%','K%','HR%')}})
 validated.sort(key=lambda x:x['loss']);best=validated[0];w=JointWeights(**best['weights']);dg=deltas(w,z.diag_pa,z.seed+900);sg=semantic_gates(dg);arch=archetypes(w,z.diag_pa,z.seed+1000);syn=synergy(w,z.diag_pa,z.seed+1100);vd=velocity_dist(pitchers);prime=prime_diag(5000,z.seed+1200)
 extreme_ok=True
 try:
  for q in (30,50,70,100,130,160,200,250):
   m=matchup(w,neutral(stuff=q,control=q,breaking=q),5000,z.seed+q);extreme_ok=extreme_ok and all(math.isfinite(v) for v in m.values())
 except Exception:extreme_ok=False
 velocity_preserved=abs(vd['mean']-145.4462)<=1.0 and abs(vd['sd']-3.7181)<=1.5
 joint_ready=best['passed_tolerances'] and all(sg.values()) and extreme_ok and velocity_preserved
 final={'main_base':MAIN_BASE,'velocity_v2_source_sha':VELOCITY_V2_SHA,'velocity_fixed':{'reference_kmh':146.0,'gameplay_points_per_kmh':1.5},'population':{'hitters':len(hitters),'pitchers':len(pitchers),'physical_velocity':vd,'prime_raw':prime},'best':best,'diagnostics':dg,'semantic_gates':sg,'archetypes':arch,'synergy':syn,'extreme_rating_safe':extreme_ok,'velocity_distribution_preserved':velocity_preserved,'gate':'PITCHER_JOINT_CALIBRATION_V2_READY' if joint_ready else 'PITCHER_JOINT_CALIBRATION_V2_NOT_READY'}
 with open(Path(z.outdir)/'pitcher_joint_v2_final.json','w') as f:json.dump(final,f,indent=2)
 with open(Path(z.outdir)/'pitcher_joint_v2_candidates.csv','w',newline='') as f:
  cw=csv.writer(f);cw.writerow(['rank','loss','passed','w_control_zone','w_stuff_quality','w_stuff_contact','w_breaking_contact','w_breaking_quality','AVG','OBP','SLG','BB%','K%','HR%'])
  for x in validated:
   ww=x['weights'];m=x['metrics'];cw.writerow([x['rank'],x['loss'],x['passed_tolerances'],ww['w_control_zone'],ww['w_stuff_quality'],ww['w_stuff_contact'],ww['w_breaking_contact'],ww['w_breaking_quality'],m['AVG'],m['OBP'],m['SLG'],m['BB%'],m['K%'],m['HR%']])
 print(json.dumps({'gate':final['gate'],'best':best,'semantic':sg,'velocity':vd,'prime':prime},indent=2))
if __name__=='__main__':main()
