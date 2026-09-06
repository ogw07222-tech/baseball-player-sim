from __future__ import annotations
import json
from pathlib import Path

def load(path,default):
 p=Path(path)
 return json.loads(p.read_text()) if p.exists() else default
def main():
 pop=load('reports/kbo_first_team_population_summary.json',{'gate':'KBO_FIRST_TEAM_POPULATION_CONTRACT_NOT_READY'});hit=load('reports/kbo_real_hitter_inference_summary.json',{'gate':'KBO_REAL_HITTER_RATING_INFERENCE_NOT_READY'});pit=load('reports/kbo_real_pitcher_inference_summary.json',{'gate':'KBO_REAL_PITCHER_RATING_INFERENCE_NOT_READY'});align=load('reports/kbo_inverse_search_validation.json',{'gate':'KBO_GENERATED_REAL_RATING_ALIGNMENT_NOT_READY'});joint=load('reports/pitcher_joint_v4_first_team_final.json',{'gate':'PITCHER_JOINT_CALIBRATION_V4_NOT_RUN'});prov=load('reports/kbo_real_data_provenance.json',{})
 real_ready=hit.get('gate')=='KBO_REAL_HITTER_RATING_INFERENCE_READY' and pit.get('gate')=='KBO_REAL_PITCHER_RATING_INFERENCE_READY'
 gates={
  'KBO_FIRST_TEAM_POPULATION_CONTRACT_READY':'READY' if pop.get('gate')=='KBO_FIRST_TEAM_POPULATION_CONTRACT_READY' else 'NOT_READY',
  'KBO_REAL_PLAYER_RATING_INFERENCE_READY':'READY' if real_ready else 'NOT_READY',
  'KBO_GENERATED_REAL_RATING_ALIGNMENT_READY':'READY' if align.get('gate')=='KBO_GENERATED_REAL_RATING_ALIGNMENT_READY' else 'NOT_READY',
  'PITCHER_JOINT_CALIBRATION_V4_READY':'READY' if joint.get('gate')=='PITCHER_JOINT_CALIBRATION_V4_READY' else ('NOT_RUN' if str(joint.get('gate','')).endswith('NOT_RUN') else 'NOT_READY'),
  'FULL_HITTER_PITCHER_VALIDATION_READY':'NOT_RUN',
 }
 blockers=[]
 if gates['KBO_FIRST_TEAM_POPULATION_CONTRACT_READY']!='READY':blockers.append('population selection / usage weighting')
 if hit.get('gate')!='KBO_REAL_HITTER_RATING_INFERENCE_READY':blockers.append('hitter real-data completeness or inverse-fit context/identifiability')
 if pit.get('gate')!='KBO_REAL_PITCHER_RATING_INFERENCE_READY':blockers.append('pitcher measured-velocity coverage, data quality, or S/C/B semantics')
 if gates['KBO_GENERATED_REAL_RATING_ALIGNMENT_READY']!='READY':blockers.append('generated-vs-real rating distribution alignment')
 if gates['PITCHER_JOINT_CALIBRATION_V4_READY']=='NOT_READY':blockers.append('league model residual / S-C-B semantic gate')
 result={'gates':gates,'data_provenance':prov,'population':pop,'hitter_inference':hit,'pitcher_inference':pit,'alignment':align,'joint_v4':joint,'remaining_blockers':blockers,'merge_recommendation':'Do not merge calibration-dependent coefficients unless all prerequisite gates are READY. Frozen hitter normalization, Velocity v2, H3.2.1 and S/C/B raw recenter remain unchanged.'}
 Path('reports/kbo_rating_inference_final.json').write_text(json.dumps(result,indent=2))
 lines=['# KBO First-Team Population + Real-Player Rating Inference','', '## Gate table','']+[f"{k} = {v}" for k,v in gates.items()]+['','## Provenance',f"Hitter source mode: {prov.get('hitter_mode','unknown')}",f"Pitcher source mode: {prov.get('pitcher_mode','unknown')}",'','## Remaining blockers']+[f'- {x}' for x in blockers]+['','## Merge recommendation',result['merge_recommendation']]
 Path('reports/kbo_rating_inference_final.md').write_text('\n'.join(lines)+'\n');print(json.dumps(gates,indent=2))
if __name__=='__main__':main()
