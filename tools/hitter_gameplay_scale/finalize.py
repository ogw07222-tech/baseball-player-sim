from __future__ import annotations
import csv,json
from pathlib import Path

REPORTS=Path('reports')

def _speed_delta(rows,baseline:int,delta:int)->float:
    for r in rows:
        if r.get('kind')=='pa' and r.get('stat')=='speed' and r.get('baseline_raw')==str(baseline) and r.get('delta_raw')==str(delta):
            return float(r['dSLG'])
    raise KeyError((baseline,delta))

def main():
    final=json.loads((REPORTS/'hitter_gameplay_scale_final.json').read_text())
    with open(REPORTS/'hitter_gameplay_sensitivity.csv') as f:sens=list(csv.DictReader(f))
    with open(REPORTS/'hitter_profile_validation.csv') as f:profiles=list(csv.DictReader(f))
    speed130=_speed_delta(sens,130,10);speed150=_speed_delta(sens,150,10)
    blockers=[
        'Raw/display prime means are Contact 94.27, Power 92.78, Discipline 87.34, Speed 98.04, materially below the intended ~110 prime display semantics.',
        f'Speed high-end batting-output separation compresses strongly inside existing H3: raw 130->140 dSLG={speed130:.6f}, raw 150->160 dSLG={speed150:.6f}; full baserunning/steal separation was not validated in this task.',
        'Because the display-ratio contract is not ready, the normalization module is intentionally not wired into production simulation.py yet.'
    ]
    final['gate_contract']='HITTER_GAMEPLAY_SCALE_NOT_READY'
    final['gate_ratio']='HITTER_DISPLAY_GAMEPLAY_RATIO_NOT_READY'
    final['normalization_candidate']={
        'model':'linear','status':'VALIDATED_CANDIDATE_NOT_PROMOTED',
        'slope':0.60,'contact_power_discipline_behavior':'sane and monotonic',
        'blockers':blockers
    }
    final['production_wiring']='NOT_PROMOTED'
    (REPORTS/'hitter_gameplay_scale_final.json').write_text(json.dumps(final,indent=2))
    pop=final['population_offense_neutral_pitcher'];refs=final['references']
    prof='\n'.join(f"- {r['profile']}: OPS {float(r['OPS']):.4f}" for r in profiles)
    summary=f'''# Hitter Raw Career Rating ↔ H3 Gameplay Scale Calibration\n\n## Final gates\n- `HITTER_GAMEPLAY_SCALE_NOT_READY`\n- `HITTER_DISPLAY_GAMEPLAY_RATIO_NOT_READY`\n\nThe linear normalization candidate itself is technically healthy, but the full user-facing display contract is not ready for production promotion.\n\n## Source / architecture\n- Base: `6818e48504af2eb7f9cd71a3b8a0fbe3497136f3` (`feature/pitcher-scb-scale-recenter`)\n- Raw `PlayerStats` and save schema are unchanged.\n- Candidate derived contract: `gameplay = 100 + (raw - stat_specific_prime_reference) * 0.60`.\n- Existing H3.2.1 formula code is unchanged.\n- The candidate is intentionally **not wired into `src/simulation.py`** while the display-ratio gate is NOT_READY.\n\n## Measured 26–30 mixed raw references (30k cohort)\n- Contact: {refs['contact']:.2f}\n- Power: {refs['power']:.2f}\n- Discipline: {refs['discipline']:.2f}\n- Speed: {refs['speed']:.2f}\n\nThese values map to gameplay 100 under the candidate. The key blocker is that they do **not** match the intended display semantics where a prime KBO-average hitter should sit around raw 110. A displayed raw 110 is therefore already materially above the actual production-grown population center.\n\n## Candidate slope / ratio\nSelected diagnostic slope: **0.60 gameplay points per raw point**. Raw +10 therefore equals gameplay +6 before H3's own nonlinear response. This maps raw SDs around 20–24 to gameplay SDs around 12–14 without adding a second strong nonlinear compression layer.\n\nContact, Power and Discipline maintain useful low/mid/high separation. Speed is the unresolved exception: existing H3 speed resolution strongly saturates at the high end. In the measured PA diagnostic, raw Speed 130→140 changed SLG by only {speed130:.4f}, and 150→160 by only {speed150:.4f}. Full steal/baserunning separation was not measured, so Speed cannot yet be declared display-ratio READY.\n\n## Production-grown hitter population vs neutral H3 pitcher\n- AVG {pop['AVG']:.4f}\n- OBP {pop['OBP']:.4f}\n- SLG {pop['SLG']:.4f}\n- OPS {pop['OPS']:.4f}\n- BB% {pop['BB']:.3%}\n- K% {pop['K']:.3%}\n- HR% {pop['HR']:.3%}\n- BABIP {pop['BABIP']:.4f}\n\nThis is a large improvement over feeding low raw career ratings directly into H3 and demonstrates that the scale mismatch is real. It is not used as a hidden KBO fit; remaining league deltas are intentionally left for later calibration.\n\n## Profile diagnostic\n{prof}\n\nProfiles are distinct, but their absolute strength also exposes the display-scale mismatch: raw 110/110/110 is much stronger than the measured prime population because the current raw prime references are below 100.\n\n## Failure policy / next prerequisite\nDo not retune H3, Velocity, KBO tolerances, or pitcher S/C/B to absorb this. The next prerequisite is a **hitter raw-scale re-centering task** for Contact/Power/Discipline (and a dedicated Speed/baserunning ratio validation) so player-facing prime ratings can live around 108–112. After that, re-measure references and rerun this same normalization gate. Only after both hitter gates become READY should Pitcher Joint Calibration v4 begin.\n'''
    (REPORTS/'hitter_gameplay_scale_summary.md').write_text(summary)
    print(json.dumps({'gate_contract':final['gate_contract'],'gate_ratio':final['gate_ratio'],'blockers':blockers},indent=2))
if __name__=='__main__':main()
