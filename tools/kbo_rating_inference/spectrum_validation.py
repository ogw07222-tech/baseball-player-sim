from __future__ import annotations

import csv,json,math,statistics
from collections import defaultdict
from pathlib import Path

from tools.kbo_rating_inference.core import weighted_summary


def read(path):
 p=Path(path)
 if not p.exists() or p.stat().st_size==0:return []
 with p.open(encoding='utf-8') as f:return list(csv.DictReader(f))
def write(path,rows):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 if not rows:p.write_text('');return
 fields=[]
 for r in rows:
  for k in r:
   if k not in fields:fields.append(k)
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def fv(r,k,d=0.0):
 try:
  x=float(r.get(k,''));return x if math.isfinite(x) else d
 except (TypeError,ValueError):return d
def ranks(xs):
 order=sorted(range(len(xs)),key=lambda i:xs[i]);out=[0.0]*len(xs);i=0
 while i<len(order):
  j=i
  while j+1<len(order) and xs[order[j+1]]==xs[order[i]]:j+=1
  rank=(i+j+2)/2
  for p in range(i,j+1):out[order[p]]=rank
  i=j+1
 return out
def spearman(x,y):
 if len(x)<5:return None
 a,b=ranks(x),ranks(y);ma=statistics.fmean(a);mb=statistics.fmean(b);num=sum((u-ma)*(v-mb) for u,v in zip(a,b));den=math.sqrt(sum((u-ma)**2 for u in a)*sum((v-mb)**2 for v in b));return num/den if den else 0.0
def wq(vals,weights,q):
 pairs=sorted(zip(vals,weights));target=q*sum(weights);acc=0.0
 for v,w in pairs:
  acc+=w
  if acc>=target:return v
 return pairs[-1][0]
def wasserstein_q(a,aw,b,bw):return statistics.fmean(abs(wq(a,aw,q)-wq(b,bw,q)) for q in [i/100 for i in range(1,100)])
def bucket_family(name):
 n=str(name)
 if 'P00_' in n or 'P10_25' in n or 'P20_40' in n:return 'low'
 if 'P25_50' in n or 'P50_75' in n or 'P40_60' in n:return 'middle'
 return 'high'
def fit_bucket(rows,kind):
 groups=defaultdict(list)
 for r in rows:groups[(r.get('role','hitter'),r.get('performance_bucket',''))].append(r)
 out=[]
 for (role,b),rs in sorted(groups.items()):
  losses=[fv(r,'fit_loss',99) for r in rs if str(r.get('fit_loss','')).strip()!=''];usage_key='PA' if kind=='hitter' else 'BF';weights=[max(1,fv(r,usage_key)) for r in rs]
  out.append({'kind':kind,'role':role,'performance_bucket':b,'family':bucket_family(b),'players':len(rs),'usage_weight':sum(weights),'median_fit_loss':statistics.median(losses) if losses else '', 'mean_fit_loss':statistics.fmean(losses) if losses else ''})
 return out
def segment(values,weights,lo,hi):
 qlo=wq(values,weights,lo);qhi=wq(values,weights,hi);sel=[(v,w) for v,w in zip(values,weights) if v>=qlo and (v<=qhi if hi>=1 else v<qhi)]
 return sum(v*w for v,w in sel)/sum(w for _,w in sel) if sel else math.nan
def alignment_rows(gen,real,kind):
 stats=('contact','power','discipline','speed') if kind=='hitter' else ('velocity','stuff','control','breaking');gw=[max(1,fv(r,'first_team_PA' if kind=='hitter' else 'BF',fv(r,'usage_weight',1))) for r in gen];rw=[max(1,fv(r,'PA' if kind=='hitter' else 'BF')) for r in real];out=[]
 if not gen or not real:return out
 for s in stats:
  g=[fv(r,'raw_'+s) for r in gen];rr=[fv(r,'raw_'+s) for r in real if str(r.get('raw_'+s,'')).strip()!=''];rrw=[rw[i] for i,r in enumerate(real) if str(r.get('raw_'+s,'')).strip()!='']
  if not rr:continue
  gs=weighted_summary(g,gw);rs=weighted_summary(rr,rrw);wd=wasserstein_q(g,gw,rr,rrw)
  for label,lo,hi in (('bottom25',0,.25),('middle50',.25,.75),('top25',.75,1)):
   out.append({'kind':kind,'stat':s,'segment':label,'generated_segment_mean':segment(g,gw,lo,hi),'real_segment_mean':segment(rr,rrw,lo,hi),'segment_mean_diff':segment(g,gw,lo,hi)-segment(rr,rrw,lo,hi),'overall_mean_diff':gs['mean']-rs['mean'],'overall_sd_diff':gs['sd']-rs['sd'],'wasserstein_q':wd})
 return out
def correlations(hitters,pitchers):
 out=[]
 def add(kind,rating,metric,rows,sign_note=''):
  q=[r for r in rows if str(r.get(rating,'')).strip()!=''];rho=spearman([fv(r,rating) for r in q],[fv(r,metric) for r in q]);out.append({'kind':kind,'rating':rating,'metric':metric,'spearman':rho,'expected':sign_note})
 add('hitter','raw_contact','AVG',hitters,'positive');add('hitter','raw_contact','K_pct',hitters,'negative tendency');add('hitter','raw_power','SLG',hitters,'positive');add('hitter','raw_power','HR_pct',hitters,'positive');add('hitter','raw_discipline','BB_pct',hitters,'positive');add('hitter','raw_speed','SB',hitters,'positive')
 add('pitcher','raw_velocity','avg_fastball_kmh',pitchers,'strong positive/measured');add('pitcher','raw_control','actual_BB_pct',pitchers,'negative');add('pitcher','raw_breaking','actual_K_pct',pitchers,'positive');add('pitcher','raw_stuff','actual_OPP_SLG',pitchers,'negative')
 return out
def tail(rows,weight_key,stats):
 out={}
 total=sum(max(1,fv(r,weight_key)) for r in rows)
 for s in stats:
  valid=[r for r in rows if str(r.get('raw_'+s,'')).strip()!='']
  denom=sum(max(1,fv(r,weight_key)) for r in valid)
  out[s]={str(t):sum(max(1,fv(r,weight_key)) for r in valid if fv(r,'raw_'+s)>=t)/denom if denom else None for t in (150,170,200)}
 return out
def main():
 h=read('data/kbo_real_hitter_ratings_inferred.csv');p=read('data/kbo_real_pitcher_ratings_inferred.csv');gh=read('reports/kbo_generated_first_team_hitter_population.csv');gp=read('reports/kbo_generated_first_team_pitcher_population.csv');contract=json.loads(Path('reports/kbo_broad_spectrum_contract.json').read_text()) if Path('reports/kbo_broad_spectrum_contract.json').exists() else {'gate':'NOT_RUN'}
 fits=fit_bucket(h,'hitter')+fit_bucket(p,'pitcher');align=alignment_rows(gh,h,'hitter')+alignment_rows(gp,p,'pitcher');corr=correlations(h,p);write('reports/kbo_generated_vs_real_spectrum.csv',align);write('reports/kbo_rating_metric_correlations.csv',corr)
 family=defaultdict(list)
 for x in fits:
  if x['median_fit_loss']!='':family[(x['kind'],x['family'])].append(float(x['median_fit_loss']))
 family_loss={f'{k[0]}_{k[1]}':statistics.fmean(v) for k,v in family.items()}
 all_families=all(f'{kind}_{fam}' in family_loss for kind in ('hitter','pitcher') for fam in ('low','middle','high'))
 fit_ok=all_families and all(v<4.5 for v in family_loss.values())
 alignment_ok=bool(align) and all(abs(float(x['overall_mean_diff']))<=15 and abs(float(x['overall_sd_diff']))<=12 and float(x['wasserstein_q'])<=16 for x in align)
 tails={'hitter':tail(h,'PA',('contact','power','discipline','speed')),'pitcher':tail(p,'BF',('velocity','stuff','control','breaking'))}
 tail_ok=True
 for kind in tails.values():
  for stat,v in kind.items():
   if v['200'] is not None and v['200']>.001:tail_ok=False
 inference_ready=contract.get('gate')=='KBO_BROAD_PLAYER_SPECTRUM_READY' and fit_ok and tail_ok
 align_ready=inference_ready and alignment_ok
 first_joint=json.loads(Path('reports/pitcher_joint_v4_first_team_final.json').read_text()) if Path('reports/pitcher_joint_v4_first_team_final.json').exists() else {'gate':'NOT_RUN'}
 joint_ready=align_ready and first_joint.get('gate')=='PITCHER_JOINT_CALIBRATION_V4_READY'
 broad_joint={'gate':'PITCHER_JOINT_CALIBRATION_V4_READY' if joint_ready else ('PITCHER_JOINT_CALIBRATION_V4_NOT_READY' if first_joint.get('gate')!='NOT_RUN' else 'PITCHER_JOINT_CALIBRATION_V4_NOT_RUN'),'broad_population_gate':contract.get('gate'),'spectrum_inference_ready':inference_ready,'spectrum_alignment_ready':align_ready,'underlying_first_team_joint':first_joint}
 Path('reports/pitcher_joint_v4_broad_population_final.json').write_text(json.dumps(broad_joint,indent=2));Path('reports/pitcher_joint_v4_broad_population_summary.md').write_text('# Pitcher Joint v4 — Broad Population\n\nGate: `%s`\n\nBroad spectrum gate: `%s`\nInference broad-ready: **%s**\nGenerated-real spectrum alignment: **%s**\n\nVelocity remains frozen; only S/C/B gameplay weights are eligible for search.\n'%(broad_joint['gate'],contract.get('gate'),inference_ready,align_ready))
 result={'KBO_BROAD_PLAYER_SPECTRUM_READY':contract.get('gate')=='KBO_BROAD_PLAYER_SPECTRUM_READY','KBO_REAL_PLAYER_INFERENCE_BROAD_READY':inference_ready,'KBO_GENERATED_REAL_SPECTRUM_ALIGNMENT_READY':align_ready,'PITCHER_JOINT_CALIBRATION_V4_READY':joint_ready,'fit_family_mean_loss':family_loss,'tails':tails,'alignment_rows':len(align),'correlations':corr}
 Path('reports/kbo_broad_spectrum_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
