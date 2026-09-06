from __future__ import annotations
import csv,json,sys
from pathlib import Path
from src.hitting.model import HitterSnapshot
from src.hitting.normalization import normalize_hitter
from tools.pitcher_joint_v3 import calibrate as v3


def normalized_hs(p):
    g=normalize_hitter(float(p.stats.contact),float(p.stats.power),float(p.stats.discipline),float(p.stats.speed))
    return HitterSnapshot(g.contact,g.power,g.discipline,g.speed,'L' if p.bats_throws.startswith('L') else 'R','balanced')


def main():
    # v4 deliberately reuses frozen v3 target/tolerance, pitcher population,
    # Velocity v2 physical path and SCB semantic adapter. The sole architectural
    # change at search input is the approved hitter raw->gameplay adapter.
    v3.hs=normalized_hs
    v3.main()
    out=Path('reports')
    src=out/'pitcher_joint_v3_final.json'
    if not src.exists():return
    data=json.loads(src.read_text())
    old=data.get('gate','')
    data['gate']='PITCHER_JOINT_CALIBRATION_V4_READY' if old.endswith('_READY') and not old.endswith('_NOT_READY') else 'PITCHER_JOINT_CALIBRATION_V4_NOT_READY'
    data['hitter_input_contract']='approved src.hitting.normalization.normalize_hitter'
    data['v4_note']='Velocity v2, physical caps, SCB raw scale and frozen KBO objective/tolerances reused unchanged.'
    (out/'pitcher_joint_v4_final.json').write_text(json.dumps(data,indent=2))
    c3=out/'pitcher_joint_v3_candidates.csv'
    if c3.exists():(out/'pitcher_joint_v4_candidates.csv').write_text(c3.read_text())
    diag=data.get('diagnostics',{}).get('plus20',{})
    rows=[]
    for stat,vals in diag.items():rows.append({'diagnostic':stat,**vals})
    if rows:
        fields=[]
        for r in rows:
            for k in r:
                if k not in fields:fields.append(k)
        with open(out/'pitcher_joint_v4_sensitivity.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    arch=[]
    for name,vals in data.get('archetypes',{}).items():arch.append({'archetype':name,**vals})
    if arch:
        with open(out/'pitcher_joint_v4_archetypes.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(arch[0]));w.writeheader();w.writerows(arch)
    best=data.get('best',{});metrics=best.get('metrics',{})
    target=v3.KBO_TARGETS;tol=v3.TOLERANCES
    residual=[]
    # OPS is a reported target but intentionally has no standalone tolerance;
    # the frozen objective is defined by the component metrics in TOLERANCES.
    for k,t in target.items():
        if k in metrics and k in tol:
            residual.append({'metric':k,'actual':metrics[k],'target':t,'residual':metrics[k]-t,'tolerance':tol[k],'normalized_residual':(metrics[k]-t)/tol[k]})
    if residual:
        with open(out/'pitcher_joint_v4_residuals.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(residual[0]));w.writeheader();w.writerows(residual)
    summary=['# Pitcher Joint Calibration v4','',f"Gate: `{data['gate']}`",'', 'v4 reuses the frozen Velocity v2 physical path, physical caps, SCB raw scale and frozen 2025 KBO target/tolerances. Hitter profiles are converted through the approved raw→gameplay normalization before H3. Failed coefficients remain calibration-only.','', '## Best candidate',f"`{json.dumps(best.get('weights',{}),sort_keys=True)}`",'', '## Metrics']
    summary += [f"- {k}: {v:.6f}" for k,v in metrics.items() if isinstance(v,(int,float))]
    summary += ['', '## Semantic gates']+[f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in data.get('semantic_gates',{}).items()]
    (out/'pitcher_joint_v4_summary.md').write_text('\n'.join(summary)+'\n')

if __name__=='__main__':main()
