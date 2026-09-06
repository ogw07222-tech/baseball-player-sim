from __future__ import annotations
import json,sys
from pathlib import Path
from src.hitting.model import HitterSnapshot
from src.hitting.normalization import normalize_hitter
from tools.pitcher_joint_v3 import calibrate as v3


def normalized_hs(p):
    g=normalize_hitter(float(p.stats.contact),float(p.stats.power),float(p.stats.discipline),float(p.stats.speed))
    return HitterSnapshot(g.contact,g.power,g.discipline,g.speed,'L' if p.bats_throws.startswith('L') else 'R','balanced')


def main():
    out='reports/v4_quick'
    Path(out).mkdir(parents=True,exist_ok=True)
    v3.hs=normalized_hs
    sys.argv=[sys.argv[0],'--hitters','1200','--pitchers','1200','--candidates','30','--search-pa','50000','--validation-pa','300000','--top','3','--seeds','3','--diag-pa','100000','--seed','260917','--outdir',out]
    v3.main()
    p=Path(out)/'pitcher_joint_v3_final.json'
    d=json.loads(p.read_text())
    result={
        'status':'QUICK_DIAGNOSTIC_ONLY',
        'source_gate':d.get('gate'),
        'best':d.get('best'),
        'semantic_gates':d.get('semantic_gates'),
        'velocity_distribution_preserved':d.get('velocity_distribution_preserved'),
        'extreme_safe':d.get('extreme_safe'),
        'archetypes':d.get('archetypes'),
    }
    (Path(out)/'pitcher_joint_v4_quick.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
