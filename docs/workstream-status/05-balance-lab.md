# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-13
SOURCE_OF_TRUTH: PR70 exact HEAD@b2da105e0c29de519b71673076afe51173593b5c; task-start latest main@a59477e0375aae37bedbd59cc60ad3ee362cf1bd
STATE: FAIL
CURRENT_TASK: Phase 2E-B retrieval / physical hit-type shadow independent validation
RESULT: PHASE2E_B_VALIDATION_FAIL / MERGE_ALLOWED_NO

## FINAL_DECISION
- Exact independently validated PR HEAD: `b2da105e0c29de519b71673076afe51173593b5c`.
- SOURCE_IDENTITY = PASS.
- PHASE2E_B_VALIDATION = FAIL.
- MERGE_ALLOWED = NO from 05 until 01 corrects the fail-safe defect and 05 revalidates the corrected exact HEAD.
- Blocking defect: when an invalid/non-positive effective fielder speed reaches retrieval derivation, `build_retrieval_state()` performs `distance / speed` before rejecting `speed <= 0`, causing `ZeroDivisionError` rather than returning `valid=False`, `physical_result_shadow=None`, and an explicit invalid reason as required by the Phase2E-B fail-safe contract.
- Invalid owner, missing/invalid ground state, non-finite final location, invalid defender rating, invalid runner rating, and invalid throw speed fail safely in the independent probes.
- No production coefficient, gameplay formula, authority path, or tuning value was changed by 05.

## SOURCE_IDENTITY
- PR #70: `Gameplay: Phase 2E-B retrieval and physical hit-type shadow`.
- PR state at validation start: OPEN / mergeable / non-draft.
- exact PR HEAD: `b2da105e0c29de519b71673076afe51173593b5c`.
- 01 implementation checkpoint: `6d201690ff7ba56f5fda30663e0cf73678a8ee58`.
- checkpoint -> final HEAD: one docs-only status commit; production/test code identity preserved.
- task-start latest main: `a59477e0375aae37bedbd59cc60ad3ee362cf1bd`; compared with PR base `47ada4fe9f1d95da2760d7a8d56a8900aab6fdc3`, only `docs/workstream-status/05-balance-lab.md` changed, so production baseline is unchanged.
- independently verified production blobs:
  - `src/hitting/retrieval.py` = `5b18688098f35edf3775c92c102b2ca4d860069b`
  - `src/hitting/retrieval_parameters.py` = `317f3ab822b3165f8ad07be84dfb508a72dd7501`
  - `src/hitting/physical.py` = `74718c24f25341eaff9f1bb453ba5f70009c1d44`
  - `src/hitting/model.py` = `eaeb4d1b6e024d8d64fd6aa1b47a30aaf879aaca`

## CANONICAL_VALIDATION_EVIDENCE
- validation-only branch: `validation/phase2e-b-candidate-05` based directly on exact PR HEAD.
- canonical validation checkout: `326a80a900e89eed07459c3f4c6053a4015479f5` (PR production/test identity asserted exact; only validation tools/workflow added).
- GitHub Actions run: `34746969032` — SUCCESS.
- job: `103696561652` — SUCCESS.
- artifact: `10314478012`.
- artifact digest: `sha256:321d6586af2af5f9b28fff09fcede2aa77a1e789b5e04786c925799207119eb7`.
- supplemental invalid-edge branch: `validation/phase2eb-invalid-05`.
- invalid-edge run: `34747418245`; artifact `10314626891`, digest `sha256:4966c1b5138345b3560fcba58c2e19b6ebd97e188e8462d38bb3ffe41e52d046`.

## SAMPLE
- structural corpus: 200,000 PA, seed `20260913`, defense and runner speed cycling 60/80/100/120/140.
- candidate physical resolution attempts: 143,113; valid physical results 142,550; invalid-ground fail-safe 563 (0.3934%).
- retrieval-applicable states: 80,441; Phase2D-caught short-circuit states: 62,109.
- exact cross-version legacy regression: 200,000 PA and 1,000 full games, exact Phase2E-A baseline checkout vs exact Phase2E-B candidate.
- performance: three paired same-run rounds, each 50,000 PA + 500 full games per side.
- full Python context: 497 tests; 496 pass, 1 unrelated historical draft-distribution failure.
- web: build PASS; 6 files / 44 tests PASS.

## OWNERSHIP
Among 80,441 retrieval-applicable states:
- P 27,990 (34.796%)
- CF 16,918 (21.032%)
- 2B 6,461 (8.032%)
- SS 6,428 (7.991%)
- 1B 5,808 (7.220%)
- 3B 5,713 (7.102%)
- RF 4,971 (6.180%)
- LF 4,937 (6.137%)
- C 1,215 (1.510%)
Radial ownership is structurally coherent: <35 ft all C; 35–90 ft 73.9% P with corner IF on side sectors; 90–185 ft overwhelmingly SS/2B plus line-side 3B/1B; >185 ft exclusively OF. LF/RF shares are near mirror-equal. Hard depth/sector boundaries are intentional engineering thresholds and remain calibration WATCH items.
- OWNERSHIP = PASS.

## RETRIEVAL_DISTANCE_TIME
Overall retrieval distance ft: mean 42.704; median 35.570; P10 10.646; P25 18.255; P75 59.387; P90 88.303; P95 103.744; P99 127.763; max 234.114.
Overall total retrieval time s: mean 3.268; median 2.936; P10 1.598; P25 2.029; P75 4.168; P90 5.547; P95 6.281; P99 7.506; max 12.587.
Components:
- reaction: mean 0.550 s, range 0.360..0.780; zero pileup at configured 0.25/1.10 hard bounds.
- effective fielder speed: mean 20.180 ft/s, range 15.84..24.64; zero pileup at configured 14/27 hard bounds.
- movement: mean 2.054 s, median 1.741, P95 4.808, max 11.007.
- pickup/transfer: role constants 0.55/0.65/0.80 s.
Role pattern is coherent: P mean retrieval distance 16.16 ft / time 1.90 s; CF 76.90 ft / 5.02 s; LF/RF about 66.8 ft / 4.54 s.
- RETRIEVAL_DISTANCE = PASS.
- RETRIEVAL_TIME = PASS.

## DEFENSE_RATING
Controlled 60/80/100/120/140 plus ±1e6 extreme sweeps at representative IF and OF locations:
- reaction time monotonically non-increasing.
- effective speed monotonically non-decreasing.
- total retrieval time monotonically non-increasing.
- all ordinary/extreme rating outputs finite and positive under normal production parameters.
Corpus mean total retrieval time falls 3.719 s @60 -> 3.470 @80 -> 3.220 @100 -> 3.034 @120 -> 2.845 @140.
- DEFENSE_RATING = PASS.

## THROW_MODEL
By role, throw distances/speeds/release/relay/arrival were finite and positive for targets 1B/2B/3B. Representative effective speeds: PC 102.67 ft/s, IF 105.6 ft/s, OF 114.4 ft/s.
Controlled same-role 1B target sweep from 0 to 320 ft:
- throw distance monotonic PASS.
- total throw time monotonic PASS.
- below 220 ft relay penalty exactly 0.
- exactly 220 ft penalty 0.
- just above 220 ft fixed 0.65 s penalty.
- measured 219.99 -> 220.01 ft time jump = 0.650175 s.
The threshold contract works as authored but introduces a deliberate hard discontinuity requiring future calibration review.
- THROW_MODEL = WATCH.

## RUNNER_MODEL
Controlled arrival times by production speed scalar:
- speed 60 (low clamp): 1B 4.857 s / 2B 9.108 / 3B 13.359.
- 80: 4.565 / 8.540 / 12.515.
- 100: 4.200 / 7.830 / 11.460.
- 120: 3.835 / 7.120 / 10.405.
- 140 (high clamp): 3.543 / 6.552 / 9.561.
All cumulative times are monotonically non-increasing with speed. Multiplier saturates at 1.18 for rating <=64 and 0.82 for >=136. This is structurally bounded but the hard saturation is an engineering calibration choice.
- RUNNER_MODEL = WATCH.

## PHYSICAL_RESULT_DISTRIBUTION
Among 142,550 valid physical BIP shadow results:
- OUT 100,775 = 70.6945%
- 1B 34,856 = 24.4518%
- 2B 6,410 = 4.4967%
- 3B 509 = 0.3571%
- HR = 0 by construction and observed corpus.
- Phase2D-caught OUT share = 43.5700% of all valid physical BIP.
- retrieval-derived OUT share = 27.1245%.
By trajectory: ground_like OUT 53.36%; line_drive OUT 82.23%; fly_ball OUT 96.48%; popup OUT 89.27%. The very high line/fly physical OUT shares are not authority and remain a calibration WATCH rather than a structural blocker.
Wall-ground-contact retrieval subset: 1B 7.99%, 2B 63.58%, 3B 28.43%, OUT 0%; deep wall-stop balls do not collapse to OUT.
Defense monotonic direction is visible: OUT share 64.05% @60 -> 67.88 @80 -> 71.04 @100 -> 73.99 @120 -> 76.50 @140.
Runner speed moves outcomes in expected direction: OUT 77.56% @60 -> 63.93% @140, with extra-base shares increasing.
- RESULT_DISTRIBUTION = WATCH for calibration, structural non-collapse PASS.

## CONTROLLED_RESULTS_AND_MARGINS
Independent controlled cases reproduced:
- routine grounder -> OUT.
- remote retrieval -> 1B.
- deep gap -> 2B.
- very deep/wall-stop -> 3B.
- Phase2D caught -> OUT.
- no Phase2E-B case produced HR.
Timing margin convention was confirmed as defense_arrival - runner_arrival.
Near-boundary shares among 80,441 retrieval states:
- 1B: |margin|<0.05 = 1.721%; <0.10 = 3.532%; <0.25 = 8.672%.
- 2B: 0.679%; 1.304%; 3.240%.
- 3B: 0.068%; 0.157%; 0.370%.
No large near-zero mass was observed, though deterministic hard timing boundaries remain future calibration-sensitive.
- CONTROLLED_RESULTS = PASS.
- TIMING_MARGINS = PASS.

## PHASE2D_INTERFACE
62,109 Phase2D physical catches short-circuited directly to OUT. Independent corpus contradictory `caught AND 1B/2B/3B` count = 0. Retrieval/throw timing is not populated for caught states.
- PHASE2D_INTERFACE = PASS.

## INVALID_FAIL_SAFE
PASS cases:
- missing GroundTravel -> invalid `missing_ground_travel`, result None.
- invalid GroundTravel -> invalid `invalid_ground_travel`, result None.
- non-finite final location -> invalid `non_finite_final_location`, result None.
- invalid defender rating -> invalid `invalid_defender_rating`, result None.
- invalid runner rating -> invalid `invalid_timing_derivation`, result None.
- invalid throw speed -> invalid `invalid_timing_derivation`, result None.
- forced invalid owner -> invalid `invalid_retrieval_derivation`, result None.
FAIL case confirmed in both main structural harness and supplemental exact-head probe:
- force non-positive effective fielder speed -> `ZeroDivisionError('float division by zero')` from movement derivation; no finite invalid resolution object is returned.
Root cause is derivation order: movement performs `distance / speed` before the subsequent `speed <= 0` bound check can fail safe.
- INVALID_STATE = FAIL.

## MIRROR
Controlled LF/RF mirrored locations preserve mirrored owner, equal retrieval distance, reaction, speed, movement, pickup and total retrieval time. Mapped target-base mirror (LF->3B vs RF->1B) preserves throw distance/time to floating exact tolerance. Production LF/RF occurrence shares are also near equal.
- MIRROR = PASS.

## DETERMINISM_RNG_UPSTREAM_LEGACY
- duplicate candidate replay physical-resolution hash exact equal.
- candidate enabled vs Phase2E-B-disabled parent RNG hash exact equal.
- Phase2A/B/C/D/E-A upstream metadata hash exact equal.
- independent cross-version exact checkout comparison (`47ada4fe...` Phase2E-A baseline vs `b2da105...` candidate): 200k PA result counts and sequence hash exact equal; final PA RNG exact equal; 1,000 full-game repr sequence hash exact equal; final game RNG exact equal.
- therefore legacy H/1B/2B/3B/HR/BB/K/HBP/ROE/out/run/runner-advancement behavior is unchanged because the entire 1,000-game result sequence is byte-repr equivalent, not merely distribution-equivalent.
- DETERMINISM = PASS.
- RNG_PURITY = PASS.
- UPSTREAM_REGRESSION = PASS.
- LEGACY_REGRESSION = PASS.

## PERFORMANCE
Same-run isolated exact-checkout benchmark, 3 paired rounds; each round 50k PA + 500 games per side.
Medians:
- Phase2E-A baseline: 127.660 us/PA; Phase2E-B candidate: 148.639 us/PA; incremental +15.691%.
- baseline: 14.229 ms/game; candidate: 15.986 ms/game; incremental +11.411%.
Round deltas were consistent: PA +15.42%, +16.79%, +15.69%; game +11.40%, +12.39%, +11.41%.
Architecture remains O(1): no timestep integration, roster scan, pathfinding, nearest-player iteration, repeated throw loop, or relay-chain loop. However +15.7% PA / +11.4% game is a material addition on top of an already watched Phase2 stack.
Repository telemetry in the same canonical run measured cumulative Phase2 stack vs pre-Phase2 at ~1.670x PA and ~1.418x game; this is context only, not the isolated gate.
- PERFORMANCE = WATCH.

## CALIBRATION
Engineering-only parameters remain uncalibrated: ownership depths/sectors, anchors, reaction/speed/pickup, throw speed/release, 220-ft relay threshold/0.65s jump, runner reference times and 0.82..1.18 saturation. Structural corpus has no outcome collapse and wall-stop balls resolve to extra-base hits rather than mostly OUT, but airborne/line-drive physical OUT shares and hard sector/relay/runner boundaries require empirical calibration before any authority migration.
- CALIBRATION = WATCH.

## GLOBAL_CI_CONTEXT
PR #70 HEAD CI independently confirmed:
- web tests PASS.
- Python suite: 497 total, 496 PASS, 1 FAIL.
- sole failure remains `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`: undrafted `0.056666666666666664`, assertion requires `>0.10`.
Canonical 05 run reproduced the same sole repository-wide failure; all Phase2E-B and upstream targeted tests passed and web build/tests passed.
- GLOBAL_CI_OUT_OF_SCOPE_FAILURE = confirmed historical draft-distribution gate only.

## FINAL_GATES
- SOURCE_IDENTITY = PASS
- OWNERSHIP = PASS
- RETRIEVAL_DISTANCE = PASS
- RETRIEVAL_TIME = PASS
- DEFENSE_RATING = PASS
- THROW_MODEL = WATCH
- RUNNER_MODEL = WATCH
- RESULT_DISTRIBUTION = WATCH
- CONTROLLED_RESULTS = PASS
- TIMING_MARGINS = PASS
- PHASE2D_INTERFACE = PASS
- INVALID_STATE = FAIL
- MIRROR = PASS
- DETERMINISM = PASS
- RNG_PURITY = PASS
- UPSTREAM_REGRESSION = PASS
- LEGACY_REGRESSION = PASS
- PERFORMANCE = WATCH
- CALIBRATION = WATCH
- GLOBAL_CI_OUT_OF_SCOPE_FAILURE = CONFIRMED / NON-PHASE2E-B

FINAL = PHASE2E_B_VALIDATION_FAIL
MERGE_ALLOWED = NO
NEXT = 01 correction of non-positive fielder-speed fail-safe, then 05 exact-head revalidation. 07 integration is not authorized from 05 yet.
