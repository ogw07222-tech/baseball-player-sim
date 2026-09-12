# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: pre2C integrated Phase2B main@9d406589d6c71a92fa91843047116200c12826b3; task-start main@b030a9612e780d1f3225e8ca9bdc1b6dd8b9bed9; PR61 current head@b3dd53e7fbb82a75b3586240a35fe4d59c381a7b; production checkpoint@aeb8237d836119333430d096797ddbcb2a216b85; canonical 05 validation@41ba390d0a193c0a68d221ca5a42a42504ffbf42
STATE: BLOCKED
CURRENT_TASK: Resume Phase 2C validation against actual 01 candidate
RESULT: FAIL_INVALID_TRAJECTORY_CAN_PRODUCE_PHYSICAL_HR_SHADOW

## FINAL_DECISION
- SOURCE_IDENTITY = PASS.
- PHASE2C_VALIDATION = FAIL.
- PHASE2D_ALLOWED = NO.
- INTEGRATION_READY = NO from 05 validation perspective.
- Single correctness blocker: `resolve_wall_interaction()` does not gate on `trajectory.valid`, so an explicitly invalid but otherwise deep/high trajectory can produce `physical_hr_shadow=True`.
- No production code, stadium dimensions, trajectory coefficients, or HR tuning was modified by 05.

## SOURCE_STATE
- Canonical pre-Phase2C integrated Phase2B baseline: `9d406589d6c71a92fa91843047116200c12826b3`.
- Task-start latest main: `b030a9612e780d1f3225e8ca9bdc1b6dd8b9bed9`.
- PR #61 `Gameplay: Phase 2C stadium wall and physical HR shadow`: OPEN / mergeable / non-draft.
- PR #61 current HEAD at final validation recheck: `b3dd53e7fbb82a75b3586240a35fe4d59c381a7b`.
- Production/test checkpoint: `aeb8237d836119333430d096797ddbcb2a216b85`.
- `aeb8237... -> b3dd53e...` changes only `docs/workstream-status/01-gameplay.md`; therefore current PR HEAD production code equals the validated production checkpoint.

## SOURCE_IDENTITY
05 validation branch: `validation/phase2c-candidate-05`.
Canonical validation checkout: `41ba390d0a193c0a68d221ca5a42a42504ffbf42`.
The checkout adds validation-only tools/workflow to PR #61 HEAD; production `src/` is unchanged.

Workflow object-level identity assertions against exact PR #61 HEAD PASSed for:
- `src/hitting/stadium.py` = `3f931147c81ccade109420d5ad7df60255dd4d41`
- `src/hitting/trajectory.py` = `f22b84a1cab56be16983d787547e5eeb5b092e03`
- `src/hitting/physical.py` = `752395dd4462a07d93df618d3bde04ebad3ebf9a`
- `src/hitting/model.py` = `2718635ccb9e53fbed63f0d5d5ba2ad7c17ac8e1`
- `src/hitting/physical_parameters.py` = `57026c6ec6a84ad795247ce205c053d0568bca64`
- `src/hitting/trajectory_parameters.py` = `622a7ebbc186407d47818727fbd3aa21262baae2`

`VALIDATED_PRODUCTION_CODE == PR61_CURRENT_MERGE_TARGET_PRODUCTION_CODE` = YES.

## CANONICAL_VALIDATION_RUN
- Actions run: `34659878385` — SUCCESS as an evidence-collection workflow.
- Job: `103459968680`.
- Artifact ID: `10287360692`.
- Artifact digest: `sha256:72ad3a85f088751475bb0f209b27bf787ccc8bfc5990e3bfc9a56a79f1abe7e8`.
- Seed: `20260911`.
- Production corpus: 200,000 neutral PA -> 142,885 physical BIP states.
- Regression: neutral/generated Phase1 diagnostics plus production 10,000 games; Phase2A 200k physical; Phase2B 200k trajectory; deterministic 250 games.
- Performance: actual pre2C git worktree vs current candidate in same Actions job, 50k PA + 500 games each.
- Identity, compile, corpus generation, Phase1, Phase2A, Phase2B, targeted Phase2C tests, Phase1/2A/2B tests, production integration, deterministic replay, paired performance, and artifact upload all completed successfully. The final FAIL is an independently measured invariant not covered by the candidate's targeted tests.

## BASELINE_AND_REGRESSION
Phase1 final results remain exact at the canonical fixed seed/sample:
- Runs/game 9.5594.
- Hits/game 19.3175.
- HR/game 2.1883.
- BB/game 7.6208.
- K/game 14.4689.
- HBP/game 1.0592.
- 1B/PA 17.162674%; 2B/PA 3.944238%; 3B/PA 0.185086%; HR/PA 2.720108%.
- neutral Swing 48.1686%; Z-Swing 70.3280%; Chase 20.9574%; Contact/Swing 77.2130%; BB 9.3990%; K 17.8735%; HBP 1.2965%; Looking-K 40.3978%.

Phase2A exact baseline retained:
- 142,885 production states.
- EV mean/SD 84.05575 / 6.29527 mph.
- LA mean/SD 9.95008 / 19.20555 deg.
- Timing mean/SD -0.00077 / 0.34168.
- Spray mean/SD 0.06213 / 17.63648 deg.

Phase2B exact baseline retained:
- carry mean/SD 180.3103 / 121.2608 ft; P5/P50/P95 7.1196 / 230.2328 / 331.4052; max 445.0522.
- hang mean/SD 2.6020 / 2.1001 s; P5/P50/P95 .06437 / 2.71058 / 6.03283; max 7.35794.
- apex mean/SD 22.1454 / 28.6009 ft; P5/P50/P95 3 / 8.5617 / 84.4738; max 260.
- 100 mph / 29 deg remains exactly 397 ft; best carry angle remains 29 deg.
- Candidate wall shadow therefore does not change Phase1 outcomes or Phase2A/2B state/trajectory distributions.

## PRODUCTION_ATTACHMENT_AND_HEIGHT_AT_WALL
- All 142,885 BIP physical states have a trajectory: PASS.
- All 142,885 have a wall interaction: PASS.
- Production attachment uses only `generic_neutral_v1`: PASS / expected Phase2C contract.
- 100 mph / 29 deg profile: launch height = 3.0 ft; height at stored apex distance = 64.286409 ft, exactly stored apex; first impact = 0; beyond first impact = 0; values finite.
- HEIGHT_AT_WALL structural gate = PASS.

## STADIUM_CORPUS
All percentages below are per attached production physical BIP state (`n=142,885`), not per PA and not authoritative game HR rates.

Generic engineering baseline (`APPROXIMATED`, not a KBO average):
- wall reached 0.41152%.
- clears wall 0.12248%.
- reaches-but-not-clear 0.28904%.
- wall-contact within 0.25 ft 0.00910%.
- near-wall within +/-10 ft 0.52140%.
- physical-HR shadow 0.10848% of BIP; 0.10961% of fair-shadow BIP.
- reached-ball clearance mean -1.710 ft; P5 -9.523, P50 -4.349, P95 +13.658, max +38.775 ft.

Jamsil-like (`CONFLICTING` fixture):
- wall reached 0.46611%; physical-HR shadow 0.15117%.
- source geometry remains structural validation only; power alleys synthesized and wall-height source conflict retained.

Gocheok-like (`APPROXIMATED` fixture):
- wall reached 0.67887%; physical-HR shadow 0.13787%.
- source-quality label correctly prevents treating synthesized power alleys as verified calibration.

Daejeon asymmetric (`APPROXIMATED` exact-sector fixture):
- wall reached 0.59768%; physical-HR shadow 0.10988%.
- expected geometry asymmetry is visible: LF wall-reached 2.2062%, RF 3.4886%; LF HR-shadow 0.8537%, RF 0.1766% because RF is shorter but substantially taller.
- This is a structural asymmetry PASS, not proof of exact KBO park calibration because Monster-Wall angular extent is approximated.

## SECTOR_SANITY
Generic LF/LC/CF/RC/RF HR-shadow rates:
- LF 0.5543%; LC 0.0697%; CF 0.0377%; RC 0.0547%; RF 0.4526%.
Symmetric fixture geometry itself mirrors exactly under controlled +/- spray; corpus LF/RF rate differences reflect the generated spray/state sample rather than a geometry mirror failure.

## SENSITIVITY
Same deterministic corpus, controlled uniform fixtures:
- baseline radius 350 ft / height 8 ft: 1,153 physical-HR shadows.
- same radius, height 16 ft: 510.
- radius 375 ft, same height 8 ft: 245.
- wall-height increase -> HR shadow non-increasing: PASS.
- wall-radius increase -> HR shadow non-increasing: PASS.

## MIRROR
Controlled identical EV/LA at +/-30 deg in generic symmetric park:
- wall radius exact equal.
- wall height exact equal.
- ball height at wall equal within machine precision.
- physical-HR shadow exact equal.
- MIRROR = PASS.

## IMPOSSIBLE_HR
Independent invariant probe:
- wall not reached -> HR shadow false: PASS.
- reaches wall but below wall top -> HR shadow false: PASS.
- negative wall radius fixture rejected: PASS.
- non-finite wall geometry rejected: PASS.
- **trajectory explicitly constructed with `valid=False`, 430-ft distance, 110-ft apex, fair center spray against 350-ft / 8-ft wall -> `physical_hr_shadow=True`: FAIL.**

Root cause confirmed in current production source:
- `resolve_wall_interaction()` checks distance, height, fair-shadow state and fair-angle geometry but never gates on `trajectory.valid`.
- `BattedBallTrajectory.valid` is a public schema field and is validated only as data presence/type; invalid trajectory state is therefore not rejected or forced non-HR by the wall resolver.
- Candidate targeted tests do not include an invalid-trajectory HR case, so targeted test PASS does not cover this invariant.

## DETERMINISM
- Same wall input -> exact `WallInteraction`: PASS.
- 250 full games repeated with the same seed -> exact game sequence: PASS.
- final parent RNG state exact equal: PASS.
- Candidate adds no random draw in trajectory/stadium/wall resolution.

## PERFORMANCE
Paired same Actions-job measurement using the actual pre2C integrated git worktree and current candidate:
- Phase2B baseline: 74.1409 us/PA; 9.2064 ms/game.
- Phase2C candidate: 78.3992 us/PA; 9.5304 ms/game.
- delta: +5.74% per PA; +3.52% per game.
- Fixed-sector wall lookup remains O(1); targeted 50k-query guard also PASSes.
- PERFORMANCE = PASS_WITH_CUMULATIVE_WATCH. Incremental Phase2C cost is moderate, but cumulative Phase2 physics cost should continue to be measured as Phase2D adds defense.

## DATA_QUALITY
- Generic remains an engineering fixture, not KBO mean/calibration authority.
- Jamsil fixture remains CONFLICTING.
- Gocheok and Daejeon convenience fixtures remain APPROXIMATED where synthesized power-alley/sector geometry is used.
- No real-KBO calibration PASS is inferred from these shadow rates.

## GATES
- SOURCE_IDENTITY = PASS
- STADIUM_GEOMETRY = PASS_WITH_DATA_QUALITY_WATCH
- HEIGHT_AT_WALL = PASS
- WALL_INTERSECTION = FAIL (invalid trajectory is not rejected/gated)
- HR_SHADOW = FAIL (invalid trajectory may become physical HR shadow)
- ASYMMETRY = PASS
- MIRROR = PASS
- IMPOSSIBLE_HR = FAIL
- PHASE2B_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- DETERMINISM = PASS
- PERFORMANCE = PASS_WITH_CUMULATIVE_WATCH

## HANDOFF_TO_01
MEASURED:
- All requested structural stadium, interpolation, height-at-wall, asymmetry, mirror, monotonicity, legacy-result, Phase2A/2B regression, determinism, and performance checks pass.
- One required impossible-HR invariant fails: `BattedBallTrajectory(valid=False)` can clear the wall and set `physical_hr_shadow=True`.

ROOT_CAUSE:
- `resolve_wall_interaction()` does not inspect `trajectory.valid` before calculating wall reach/height/clearance/HR shadow.

REQUIRED_CORRECTION BEFORE 05 SIGNOFF:
- Add an explicit invalid-trajectory policy before wall HR resolution. At minimum, an invalid trajectory must never produce `physical_hr_shadow=True` and must not silently behave as a valid wall-clearing trajectory.
- Add a targeted regression test for `valid=False` covering the impossible-HR invariant.
- Do not tune wall dimensions, trajectory coefficients, or HR rates while making this correction.
- After 01 updates PR #61 production code, 05 must revalidate the new current HEAD because source identity will have changed.
