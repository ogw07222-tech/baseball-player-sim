from __future__ import annotations
import csv,json,random
from pathlib import Path
from tools.pitcher_joint_v3.adapter import JointWeights
from tools.pitcher_joint_v3 import calibrate as v3
from src.hitting.model import HitterSnapshot
from src.hitting.normalization import normalize_hitter

METRICS=('AVG','OBP','SLG','BB%','K%','HR%','BABIP','HardContact%')
PARAMS=('w_control_zone','w_stuff_quality','w_stuff_contact','w_breaking_contact','w_breaking_quality')
STEP={'w_control_zone':.05,'w_stuff_quality':.03,'w_stuff_contact':.02,'w_breaking_contact':.03,'w_breaking_quality':.03}

def _hs(p):
    g=normalize_hitter(float(p.stats.contact),float(p.stats.power),float(p.stats.discipline),float(p.stats.speed))
    return HitterSnapshot(g.contact,g.power,g.discipline,g.speed,'L' if p.bats_throws.startswith('L') else 'R','balanced')

def _weights(d): return JointWeights(**{k:float(d[k]) for k in PARAMS})

def main(pa=250000,seed=261006):
    src=Path('reports/pitcher_joint_v4_final.json')
    if not src.exists(): raise SystemExit('pitcher_joint_v4_final.json required')
    final=json.loads(src.read_text());best=final['best'];basew=_weights(best['weights'])
    v3.hs=_hs
    hitters=v3.build_hitters(1600,seed);pitchers=v3.build_pitchers(1600,seed+1)
    base=v3.sim(basew,hitters,pitchers,pa,seed+2)
    rows=[]
    for p in PARAMS:
        h=STEP[p];d=basew.as_dict();d[p]+=h;plus=v3.sim(_weights(d),hitters,pitchers,pa,seed+2)
        d=basew.as_dict();d[p]-=h;minus=v3.sim(_weights(d),hitters,pitchers,pa,seed+2)
        for m in METRICS:
            rows.append({'parameter':p,'metric':m,'step':h,'derivative':(plus[m]-minus[m])/(2*h),'base':base[m],'plus':plus[m],'minus':minus[m]})
    out=Path('reports');
    with open(out/'pitcher_joint_v4_jacobian.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Residual ranking against frozen target/tolerance.
    residual=[]
    for m,t in v3.KBO_TARGETS.items():
        if m in best['metrics'] and m in v3.TOLERANCES:
            x=best['metrics'][m];residual.append({'metric':m,'actual':x,'target':t,'residual':x-t,'normalized_residual':(x-t)/v3.TOLERANCES[m]})
    residual.sort(key=lambda x:abs(x['normalized_residual']),reverse=True)
    with open(out/'pitcher_joint_v4_residual_analysis.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(residual[0]));w.writeheader();w.writerows(residual)
    summary={'source_gate':final.get('gate'),'best_weights':basew.as_dict(),'base_metrics':base,'largest_normalized_residuals':residual[:5]}
    (out/'pitcher_joint_v4_jacobian_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
