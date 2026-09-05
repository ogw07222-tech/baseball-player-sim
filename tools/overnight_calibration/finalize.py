from __future__ import annotations
import json
from pathlib import Path

R=Path('reports')

def load(name):
    p=R/name
    return json.loads(p.read_text()) if p.exists() else {}

def gate_value(data,key='gate'):
    g=str(data.get(key,''))
    if g.endswith('NOT_READY'):return 'NOT_READY'
    if g.endswith('READY'):return 'READY'
    return 'NOT_RUN'

def main():
    cpd=load('hitter_cpd_scale_final.json');norm=load('hitter_cpd_normalization_final.json');speed=load('hitter_speed_ratio_final.json');pv4=load('pitcher_joint_v4_final.json');full=load('full_population_validation.json')
    a=gate_value(cpd);b=gate_value(norm);c=gate_value(speed);h='READY' if a==b==c=='READY' else 'NOT_READY'
    p=gate_value(pv4) if pv4 else 'NOT_RUN';f=gate_value(full) if full else 'NOT_RUN'
    lines=['# Overnight Hitter / Pitcher Calibration Summary','', '## Source','- starting main SHA: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`','- overnight base SHA: `5aad8004650c07a6f82560eaaf2c5ff89580598a`','- working branch: `feature/overnight-hitter-pitcher-calibration`','- Velocity v2 source: `c405b3e9c1ec2633fabd0f033c0c923b165bd6af`','- pitcher SCB source: `6818e48504af2eb7f9cd71a3b8a0fbe3497136f3`','', '## Hitter C/P/D raw scale',f"- gate: `{cpd.get('gate','NOT_RUN')}`",f"- prime mixed mean: `{json.dumps(cpd.get('prime_26_28_30_mean',{}),sort_keys=True)}`",'- representation shift is development-only; age-18 generation is unchanged.','', '## Hitter C/P/D gameplay normalization',f"- gate: `{norm.get('gate','NOT_RUN')}`",f"- model: `{norm.get('model','n/a')}`",f"- selected slope: `{norm.get('selected_common_slope','n/a')}`",f"- multi-seed population mean: `{json.dumps(norm.get('actual_population_multi_seed_mean',{}),sort_keys=True)}`",'', '## Speed',f"- gate: `{speed.get('gate','NOT_RUN')}`",f"- selected: `{json.dumps(speed.get('selected'),sort_keys=True)}`",f"- inning infrastructure note: {speed.get('persistent_inning_engine','not run')}",'', '## Production wiring',f"- hitter contract: **{h}**",'- raw PlayerStats/save format remains canonical. H3.2.1 formulas are frozen.','', '## Pitcher Joint v4',f"- gate: `{pv4.get('gate','NOT_RUN') if pv4 else 'NOT_RUN'}`",f"- best candidate: `{json.dumps(pv4.get('best',{}).get('weights',{}),sort_keys=True) if pv4 else '{}'}`",'', '## Full population validation',f"- gate: `{full.get('gate','NOT_RUN') if full else 'NOT_RUN'}`",'', '## Final gate table',f'HITTER_CPD_RAW_SCALE_READY = {a}',f'HITTER_CPD_GAMEPLAY_SCALE_READY = {b}',f'HITTER_SPEED_RATIO_READY = {c}',f'HITTER_DISPLAY_GAMEPLAY_CONTRACT_READY = {h}',f'PITCHER_JOINT_CALIBRATION_V4_READY = {p}',f'FULL_HITTER_PITCHER_VALIDATION_READY = {f}','']
    if h!='READY':lines+=['## Remaining blocker','Hitter production normalization and Pitcher Joint v4 are intentionally not promoted/executed until all three hitter gates are READY. Successful sub-contracts and diagnostics remain preserved.','']
    if p=='NOT_READY':lines+=['## Pitcher v4 blocker','See `pitcher_joint_v4_residuals.csv`, sensitivity and archetype reports. Failed coefficients remain calibration-only.','']
    R.mkdir(exist_ok=True);(R/'overnight_hitter_pitcher_calibration_summary.md').write_text('\n'.join(lines))
    print('\n'.join(lines[-8:]))
if __name__=='__main__':main()
