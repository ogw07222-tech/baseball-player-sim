from __future__ import annotations

import json
from pathlib import Path

from tools.kbo_rating_inference import joint_v4_first_team as base


def main():
    p=Path('reports/kbo_broad_spectrum_contract.json')
    contract=json.loads(p.read_text()) if p.exists() else {'gate':'NOT_RUN'}
    if contract.get('gate')!='KBO_BROAD_PLAYER_SPECTRUM_READY':
        result={'gate':'PITCHER_JOINT_CALIBRATION_V4_NOT_RUN','reason':'broad real-player spectrum contract not READY','broad_spectrum_gate':contract.get('gate')}
        Path('reports/pitcher_joint_v4_first_team_final.json').write_text(json.dumps(result,indent=2))
        Path('reports/pitcher_joint_v4_first_team_summary.md').write_text('# Pitcher Joint v4 — Broad Population Guard\n\nGate: `PITCHER_JOINT_CALIBRATION_V4_NOT_RUN`\n\nReason: broad real-player spectrum contract is not READY. Bottom/middle/top and starter/reliever coverage must be established before coefficient search.\n')
        print(json.dumps(result,indent=2));return
    base.main()

if __name__=='__main__':main()
