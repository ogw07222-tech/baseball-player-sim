# KBO Broad Player Spectrum Calibration — Final Status

> This report records implementation status only. Numeric calibration gates remain NOT_READY/NOT_RUN because GitHub-hosted jobs executed zero steps.

1. **Branch**: `feature/kbo-broad-player-spectrum`
2. **Base SHA**: `6efa3bd8717bf6ae8550773d0b439cea834d7ce1` (PR #25 HEAD at branch creation)
3. **Head SHA**: see branch HEAD; this file is part of the final report-only commit sequence.
4. **Hitter sample size**: NOT EXECUTED. Target contract is all 2025 hitters with `PA >= 100`; robust subset `PA >= 300`.
5. **Pitcher sample size**: NOT EXECUTED. Target contract is all 2025 pitchers with `BF >= 100`; robust subset `BF >= 300`.
6. **Hitter bucket counts**: NOT EXECUTED. Required buckets are P0-10 / P10-25 / P25-50 / P50-75 / P75-90 / P90-100.
7. **Pitcher starter/reliever bucket counts**: NOT EXECUTED. Starter and reliever are stratified separately into P20 buckets; swingmen are tagged separately.
8. **PA/BF weighting**: hitters use first-team PA; pitchers use BF. Equal-player league weighting is prohibited.
9. **Shrinkage policy**: fixed pseudo-count shrinkage toward 2025 league context for lower-usage rows; hitter prior 250 PA, pitcher prior 220 BF. Original observed stats are retained.
10. **Hitter inferred distribution**: NOT EXECUTED. Output schema includes C/P/D/S raw + gameplay ratings and broad-spectrum labels.
11. **Pitcher inferred distribution**: NOT EXECUTED. Measured Velocity is fixed; S/C/B remain conditional on valid Joint context.
12. **Velocity measured-data coverage**: partial evidence exists from PR #25 (e.g. Won Tae In, Dong Ju Moon, Kwang Hyun Kim, Tucker Davidson). Missing velocity is never fabricated.
13. **Low-end fit**: NOT EXECUTED. Bottom buckets are mandatory and cannot be dropped to improve fit.
14. **Middle fit**: NOT EXECUTED.
15. **Elite fit**: NOT EXECUTED. Elite rows receive no special overweighting.
16. **Generated-vs-real alignment**: NOT EXECUTED. Validation compares overall mean/SD/Wasserstein plus bottom25/middle50/top25 segment means.
17. **Rating correlations**: NOT EXECUTED. Report contract includes Contact↔AVG/K, Power↔SLG/HR, Discipline↔BB/K, Speed↔SB, Velocity↔measured km/h, Control↔BB, Breaking↔K, Stuff↔OppSLG.
18. **Joint v4 result**: `PITCHER_JOINT_CALIBRATION_V4_NOT_RUN`. Search is guarded by broad-spectrum readiness; Velocity is frozen and only five S/C/B semantic weights are searched.
19. **Tests**: broad-spectrum tests are implemented for quantile retention, shrinkage, role separation, hitter/reliever coverage and role-aware usage weighting. They have not executed on GitHub because no runner steps were allocated.
20. **CI**: workflow run `34017664447` created both jobs but reported zero executed steps; classified as execution-infrastructure failure rather than test/calibration failure.
21. **Remaining blocker**: first, GitHub runner execution. After execution, any remaining failure must be classified as source coverage, low/middle/high fit, generated-real alignment, pitcher role/usage proxy, velocity coverage, S/C/B semantics, or league-model residual.
22. **Merge recommendation**: keep as Draft / calibration tooling only. Do not promote coefficients or READY gates until an actual workflow run produces stable broad-spectrum reports.

## Gates

- `KBO_BROAD_PLAYER_SPECTRUM_READY = NOT_READY`
- `KBO_REAL_PLAYER_INFERENCE_BROAD_READY = NOT_READY`
- `KBO_GENERATED_REAL_SPECTRUM_ALIGNMENT_READY = NOT_READY`
- `PITCHER_JOINT_CALIBRATION_V4_READY = NOT_RUN`

## Core implementation files

- `tools/kbo_rating_inference/broad_spectrum.py`
- `tools/kbo_rating_inference/pitcher_first_team_usage.py`
- `tools/kbo_rating_inference/infer_hitters_broad.py`
- `tools/kbo_rating_inference/infer_pitchers_broad.py`
- `tools/kbo_rating_inference/spectrum_validation.py`
- `tools/kbo_rating_inference/joint_v4_broad_runner.py`
- `tests/test_kbo_broad_spectrum.py`

No production gameplay formula is intentionally changed by this task.
