# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: Phase2D integrated/task-start base@081c45ed9382d16c3569398d1ada1dbc842d6cf2; PR68 validated HEAD@5cbdf634c7f514dfb26be37694a6d2173c258b6c; canonical 05 checkout@1b040ead8b509e3fa96e58625fc7b14404dfed1e; latest main before status sync@48011c849a813a4e8a570067670ada9e5f633836
STATE: PASS_WITH_WATCHES
CURRENT_TASK: Phase 2E-A ground travel / final-location shadow independent validation
RESULT: PHASE2E_A_VALIDATION_PASS / MERGE_ALLOWED_YES_FROM_05

## FINAL_DECISION
- VALIDATED_HEAD = `5cbdf634c7f514dfb26be37694a6d2173c258b6c`.
- SOURCE_IDENTITY = PASS.
- PHASE2E_A_VALIDATION = PASS.
- MERGE_ALLOWED = YES from 05 gameplay-validation perspective for the exact validated HEAD only.
- Phase2E-A remains shadow/metadata-only; no physical hit-type, retrieval, throw, runner-advancement, or outcome authority migration is approved.
- Explicit WATCHES: engineering coefficients are not KBO-calibrated; +9.42% PA / +4.71% game incremental same-run runtime cost should remain under cumulative physics performance watch.
- No production gameplay coefficient, legacy outcome logic, rating scale, trajectory/stadium coefficient, or draft balance code was modified by 05.

## SOURCE_STATE_AND_IDENTITY
- PR #68: `Gameplay: Phase 2E-A ground travel final-location shadow`.
- PR branch: `feature/phase2e-a-ground-travel-shadow`.
- Task-start PR base: `081c45ed9382d16c3569398d1ada1dbc842d6cf2`.
- Exact independently validated PR HEAD: `5cbdf634c7f514dfb26be37694a6d2173c258b6c`.
- 01 implementation checkpoint: `f6053039f25310378922df6030f832c67cc5f4c9`; checkpoint -> PR HEAD changes only `docs/workstream-status/01-gameplay.md`, so production/test code is identical.
- PR changed files are limited to:
  - `docs/workstream-status/01-gameplay.md`
  - new `src/hitting/ground_travel.py`
  - new `src/hitting/ground_travel_parameters.py`
  - modified `src/hitting/physical.py`
  - new `tests/test_phase2e_a_ground_travel.py`
- Intended authority files remain unchanged: `src/hitting/model.py`, `src/hitting/defense.py`, `src/hitting/baserunning.py`, Phase2B trajectory coefficients, Phase2C stadium geometry.
- Key PR-head blobs independently read:
  - `ground_travel.py` = `cae9d2e8c979d83781dd39c4a579856f7b56ad4c`
  - `ground_travel_parameters.py` = `dd69d779eed5645c2d2d254fc2ff0cebec1f33`
  - `physical.py` = `2d5242375ed35775a261d51a96c62880015ad368`
  - `model.py` = `585d4cd0eb4c5464d02fe0805d359b0e9cafe39d`
  - `trajectory.py` = `f22b84a1cab56be16983d787547e5eeb5b092e03`
  - `stadium.py` = `780e067781c7ad24bf9bdfe60d1f6cbcb23adec0`
  - `test_phase2e_a_ground_travel.py` = `89e75429d0054c779099c24050745f1543dab608`
- Latest main before this status sync: `48011c849a813a4e8a570067670ada9e5f633836`. Divergence from Phase2E task-start base is only Interactive Event API transport/resolve files (`src/api/app.py` and its test), not `src/hitting/*`.

## CANONICAL_VALIDATION_RUN
- Validation branch: `validation/phase2e-a-candidate-05`.
- Canonical validation checkout: `1b040ead8b509e3fa96e58625fc7b14404dfed1e`.
- Actions run: `34670031185` — SUCCESS.
- Job: `103489534455` — SUCCESS.
- Artifact ID: `10290038620`.
- Artifact digest: `sha256:0e8ad04744576f6df44239e8645c4c190376aac3e1f1fc9a3e7ff0adbc4d48f6`.
- Seed: `20260912` for PA/distribution regression; `20260913` for 1,000-game exact regression.
- Corpus: 200,000 PA -> 142,770 physical BIP states.
- Performance: same-run actual Phase2D base worktree vs candidate, 50,000 PA + 500 games each.
- Full Python discover: 466 tests, 465 PASS, 1 FAIL, 0 ERROR; sole failure is the pre-existing draft-distribution balance gate.

## VALID_STATE_DISTRIBUTION
200k PA -> 142,770 physical BIP states:
- valid GroundTravelState: 142,202 = 99.6022%.
- invalid: 568 = 0.3978%.
- all production-corpus invalid states are `air_wall_precedes_ground`, exactly as designed.
By trajectory class:
- ground_like: 71,694 / 71,694 valid = 100%.
- line_drive: 39,937 / 40,158 valid = 99.4497%; 221 air-wall invalid.
- fly_ball: 27,826 / 28,173 valid = 98.7683%; 347 air-wall invalid.
- popup: 2,745 / 2,745 valid = 100%.
- VALID_STATE_DISTRIBUTION = PASS.

## IMPACT_SPEED
Valid n=142,202 impact horizontal-speed proxy (ft/s):
- mean 83.6716; median 85.6413.
- P10 43.6965; P25 58.9018; P75 110.0500; P90 119.3357; P95 123.8841; P99 131.9586.
- max 156.1988.
- 220 ft/s clamp hits: 0 / 142,202 = 0%.
Class means:
- ground_like 108.8427.
- line_drive 69.5375.
- fly_ball 45.3720.
- popup 20.1344.
No clamp pileup or non-finite tail exists.
Population correlations reflect the model definition and class mixture: impact vs EV +0.256; vs hang time -0.927; vs LA -0.831. Raw pooled first-impact-distance correlation is -0.710 because high-LA airborne classes travel farther while retaining much lower impact-speed class corrections/longer hang time; the controlled same-class/same-hang distance sweep is monotone increasing and is the authoritative structural gate.
- IMPACT_SPEED = PASS.

## BOUNCE_AND_POST_IMPACT
Overall valid states:
- post-impact speed mean/median 46.1142 / 47.0315 ft/s; P95 71.8528; P99 76.5360; max 90.5953.
- bounce distance mean/median 6.2602 / 6.8634 ft; P95 8.6595; P99 9.2132; max 10.8714.
- rollout-start speed mean/median 35.9601 / 36.9918 ft/s; P95 58.9193; P99 62.7595; max 74.2882.
Class ordering is structurally coherent under the declared retention/bounce parameters: ground_like is fastest/longest, then line_drive, fly_ball, popup. No negative values, extreme discontinuity spike, or unbounded tail was found.
- BOUNCE = PASS.

## ROLLOUT
Rollout distance (ft), n=142,202:
- mean 22.9330; median 19.5485.
- P1 .1004; P5 1.2099; P10 1.6732; P25 7.3186; P75 39.1339; P90 46.0179; P95 49.5926; P99 56.2679; max 78.8390.
Total ground-travel distance (bounce + rollout, after wall clamp when applicable):
- mean 29.1543; median 26.4683.
- P1 .8514; P5 3.6988; P10 4.6036; P25 12.6530; P75 46.7864; P90 54.3201; P95 58.2057; P99 65.4343; max 89.7104.
Class ground-travel means:
- ground_like 46.3562 ft.
- line_drive 17.1242 ft.
- fly_ball 4.8966 ft.
- popup remains near-zero/short by construction.
No 450-ft model travel clamp pileup was observed; no runaway tail or negative travel exists. EV/LA/impact-distance bucket distributions remain finite and continuous enough for shadow metadata use.
- ROLLOUT = PASS.

## FINAL_LOCATION
Valid n=142,202:
- final radial distance mean 207.6996 ft; median 248.3010; P90 327.6763; P95 343.7509; P99 371.6578; max 400.2300.
- final-minus-first-impact radial delta equals effective ground travel and is always non-negative except that wall stop may truncate planned travel; invariant checks PASS.
- finite final X/Y/radial coordinates: PASS.
- Phase2A spray ray preserved: PASS.
- wall_ground_contact rate: 0.49718%.
- FINAL_LOCATION = PASS.

## MIRROR
48 controlled paired cases across all four trajectory classes, 4 first-impact distances, and 3 mirrored spray magnitudes:
- impact speed exact equal.
- post-impact speed exact equal.
- bounce distance exact equal.
- rollout distance exact equal.
- total ground travel exact equal.
- final radial exact equal.
- final Y exact equal.
- |X| exact equal and X sign inverted.
- MIRROR = PASS.

## MONOTONICITY
Independent multi-point sweeps, not single unit cases:
- same hang/class, greater first-impact distance -> impact-speed proxy non-decreasing: PASS.
- greater rollout-start speed -> rollout non-decreasing: PASS.
- greater effective deceleration -> rollout non-increasing: PASS.
- greater post-impact retention -> ground travel non-decreasing: PASS. Representative distances: 5.8451, 14.8765, 27.8916, 44.8903, 65.8728 ft for retention .20/.35/.50/.65/.80.
- zero rollout speed -> rollout exactly 0: PASS.
- MONOTONICITY = PASS.

## WALL_STOP
Controlled cases:
- unconstrained final point inside wall -> valid, `wall_ground_contact=False`: PASS.
- planned final exceeds 330-ft wall -> final radial exactly 330 ft and `wall_ground_contact=True`: PASS.
- airborne wall interaction before first ground -> invalid with `air_wall_precedes_ground`: PASS.
- mirrored wall geometry -> radial/Y exact equal and X mirrored: PASS.
- no rebound/carom loop exists.
- WALL_STOP = PASS.

## INVALID_STATE
Independent forced corpus all returns `valid=False`, finite safe fields, and zero ground travel:
- trajectory None -> `missing_trajectory`.
- trajectory.valid=False -> `invalid_trajectory`.
- unsupported class -> `unsupported_trajectory_class`.
- zero hang time -> `invalid_hang_time`.
- missing wall -> `missing_wall_context`.
- invalid wall radius -> `invalid_wall_radius`.
- non-finite input -> `non_finite_input`.
- non-positive rollout deceleration -> `invalid_rollout_deceleration`.
- INVALID_STATE = PASS.

## DETERMINISM_RNG_AND_REGRESSION
200,000 PA enabled/disabled comparison:
- legacy PA counters exact identical: single 34,397; double 7,838; triple 380; HR 5,526; out 93,453; ROE 1,333; BB 18,807; K 35,653; HBP 2,613.
- Phase2A/B/C/D upstream metadata hash exact identical: `fa7a1935ee0f68b3061ce2a2c767e760f30d274ccbc03a2ab1e569397a274d3a`.
- parent RNG final-state hash exact identical: `1f0ca21b4d72386c785d1a39a40efa9d80f1b72c5d054e818d6c896f0bc62fb6`.
- duplicate 20k Phase2E-A enabled replay exact identical.
Separate 1,000-game enabled/disabled comparison:
- production game result sequence exact equal; sequence hash `fc673c724c0f6a7d85178ac5eae34cefbc343146386fe8ad25db4effa6551d2a`.
- final game RNG exact equal; hash `fb7195e20a39764cbc2ba21edad90fe647f7f8849817a817d1abfcf30087ed78`.
Therefore Phase2E-A consumes zero RNG and does not perturb Phase2D child resolution or any canonical gameplay state.
- DETERMINISM = PASS.
- RNG_PURITY = PASS.
- PHASE2ABCD_REGRESSION = PASS.
- LEGACY_REGRESSION = PASS.

## PERFORMANCE
Same-run paired benchmark, same Actions job and runner:
- Phase2D base `081c45...`: 115.2799 us/PA; 13.3547 ms/game.
- Phase2E-A candidate: 126.1449 us/PA; 13.9830 ms/game.
- incremental delta: +9.4249%/PA; +4.7054%/game.
Architecture audit:
- O(1) fixed algebra.
- one representative bounce only.
- no timestep/frame loop.
- no bounce loop.
- no numerical integration loop.
- no mesh traversal, dynamic search, fielder scan, or pathfinding.
This is materially smaller than the previously observed Phase2D increment but cumulative Phase2 physics cost remains a performance concern before authority migration.
- PERFORMANCE = WATCH, non-blocking for shadow-only correctness.

## CALIBRATION
Current class corrections/retention/deceleration are explicitly engineering baselines, not KBO-calibrated values. The 200k corpus shows structurally usable, finite, non-degenerate distributions with no 220-fps impact clamp hits and no 450-ft travel clamp hits. No coefficient is approved for real-KBO authority from this validation alone.
- CALIBRATION = WATCH.

## GLOBAL_CI_CONTEXT
Canonical 05 full discover independently reproduced:
- 466 tests total.
- 465 PASS.
- 1 FAIL.
- 0 ERROR.
Sole failure:
- `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`.
- observed `undrafted = 0.056666666666666664`; historical assertion requires `> 0.10` (and `<0.35`).
- Phase2E-A targeted tests pass and all production integration prerequisites passed in PR CI; Phase2E-A does not touch draft/generation balance.
- GLOBAL_CI_OUT_OF_SCOPE_FAILURE = VERIFIED.

## GATES
- SOURCE_IDENTITY = PASS
- VALID_STATE_DISTRIBUTION = PASS
- IMPACT_SPEED = PASS
- BOUNCE = PASS
- ROLLOUT = PASS
- FINAL_LOCATION = PASS
- MIRROR = PASS
- MONOTONICITY = PASS
- WALL_STOP = PASS
- INVALID_STATE = PASS
- DETERMINISM = PASS
- RNG_PURITY = PASS
- PHASE2ABCD_REGRESSION = PASS
- LEGACY_REGRESSION = PASS
- PERFORMANCE = WATCH
- CALIBRATION = WATCH
- GLOBAL_CI_OUT_OF_SCOPE_FAILURE = VERIFIED
- FINAL = PHASE2E_A_VALIDATION_PASS
- MERGE_ALLOWED = YES_FROM_05_EXACT_HEAD_ONLY

## HANDOFF_TO_07
- Exact independently validated PR #68 HEAD: `5cbdf634c7f514dfb26be37694a6d2173c258b6c`.
- 07 must recheck the PR HEAD and current main before integration. The latest main divergence observed by 05 is unrelated Interactive Event API code and does not touch `src/hitting/*`.
- Use an expected-head check. If rebase/conflict resolution changes any validated Phase2E-A production/test blob, this signoff does not automatically carry forward and 05 source-identity revalidation is required.
- Do not interpret this PASS as physical hit-type/retrieval/throw/runner-advancement authority approval; Phase2E-A remains metadata/shadow-only.
