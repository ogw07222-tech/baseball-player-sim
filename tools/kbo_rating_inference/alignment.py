from __future__ import annotations

import csv,json,math,statistics
from pathlib import Path
from tools.kbo_rating_inference.core import weighted_summary

def read_csv(path):
 p=Path(path)
 if not p.exists() or p.stat().st_size==0:return []
 with p.open(encoding='utf-8') as f:return list(csv.DictReader(f))
def write_csv(path,rows):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 if not rows:p.write_text('');return
 fields=[]
 for row in rows:
  for key in row:
   if key not in fields:fields.append(key)
 with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def f(row,key,default=0.0):
 try:return float(row.get(key,default))
 except (TypeError,ValueError):return default
def weighted_wasserstein_quantile(a,aw,b,bw):
 qs=[i/100 for i in range(1,100)]
 def wq(xs,ws,q):
  pairs=sorted(zip(xs,ws));target=q*sum(ws);acc=0
  for x,w in pairs:
   acc+=w
   if acc>=target:return x
  return pairs[-1][0]
 return statistics.fmean(abs(wq(a,aw,q)-wq(b,bw,q)) for q in qs)
def rankdata(xs):
 order=sorted(range(len(xs)),key=lambda i:xs[i]);r=[0.0]*len(xs);i=0
 while i<len(order):
  j=i
  while j+1<len(order) and xs[order[j+1]]==xs[order[i]]:j+=1
  rank=(i+j+2)/2
  for k in range(i,j+1):r[order[k]]=rank
  i=j+1
 return r
def corr(x,y):
 if len(x)<3:return None
 rx,ry=rankdata(x),rankdata(y);mx=statistics.fmean(rx);my=statistics.fmean(ry);num=sum((a-mx)*(b-my) for a,b in zip(rx,ry));den=math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry));return num/den if den else 0.0
def main():
 generated=read_csv('reports/kbo_generated_first_team_hitter_population.csv');real=read_csv('data/kbo_real_hitter_ratings_inferred.csv');hitter_summary=json.loads(Path('reports/kbo_real_hitter_inference_summary.json').read_text()) if Path('reports/kbo_real_hitter_inference_summary.json').exists() else {'gate':'NOT_RUN'};pitcher_summary=json.loads(Path('reports/kbo_real_pitcher_inference_summary.json').read_text()) if Path('reports/kbo_real_pitcher_inference_summary.json').exists() else {'gate':'NOT_RUN'};rows=[];aligned=True
 if generated and real:
  gw=[f(r,'first_team_PA') for r in generated];rw=[f(r,'PA') for r in real]
  for stat in ('contact','power','discipline','speed'):
   g=[f(r,'raw_'+stat) for r in generated];rr=[f(r,'raw_'+stat) for r in real];gs=weighted_summary(g,gw);rs=weighted_summary(rr,rw);wd=weighted_wasserstein_quantile(g,gw,rr,rw);row={'stat':stat,'generated_mean':gs['mean'],'real_mean':rs['mean'],'mean_diff':gs['mean']-rs['mean'],'generated_sd':gs['sd'],'real_sd':rs['sd'],'sd_diff':gs['sd']-rs['sd'],'p10_diff':gs['p10']-rs['p10'],'p25_diff':gs['p25']-rs['p25'],'p50_diff':gs['p50']-rs['p50'],'p75_diff':gs['p75']-rs['p75'],'p90_diff':gs['p90']-rs['p90'],'wasserstein_q':wd};rows.append(row)
   if abs(row['mean_diff'])>12 or abs(row['sd_diff'])>10 or wd>14:aligned=False
 else:aligned=False
 write_csv('reports/kbo_generated_vs_real_rating_distribution.csv',rows);examples=read_csv('reports/kbo_hitter_fit_examples.csv')+read_csv('reports/kbo_pitcher_fit_examples.csv');write_csv('reports/kbo_player_fit_examples.csv',examples);correlations={}
 if real:
  for rating,metric in (('raw_contact','AVG'),('raw_contact','K_pct'),('raw_power','SLG'),('raw_power','HR_pct'),('raw_discipline','BB_pct'),('raw_speed','SB')):correlations[f'{rating}__{metric}']=corr([f(r,rating) for r in real],[f(r,metric) for r in real])
 inference_ready=hitter_summary.get('gate')=='KBO_REAL_HITTER_RATING_INFERENCE_READY' and pitcher_summary.get('gate')=='KBO_REAL_PITCHER_RATING_INFERENCE_READY';gate=aligned and inference_ready;result={'gate':'KBO_GENERATED_REAL_RATING_ALIGNMENT_READY' if gate else 'KBO_GENERATED_REAL_RATING_ALIGNMENT_NOT_READY','distribution_shape_pass':aligned,'requires_both_real_inference_gates':inference_ready,'hitter_inference_gate':hitter_summary.get('gate'),'pitcher_inference_gate':pitcher_summary.get('gate'),'rank_correlations':correlations,'comparison_rows':rows};Path('reports/kbo_inverse_search_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
