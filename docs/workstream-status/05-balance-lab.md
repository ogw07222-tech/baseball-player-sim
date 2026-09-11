# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: integrated Phase2B main@9d406589d6c71a92fa91843047116200c12826b3; prior canonical Phase2B validation@3e457c8203172b033d4ba3f94da468df28c5550c; Phase2C prebaseline harness branch validation/phase2c-prebaseline-05@3b7aa2dc4f1596dcc1fee35e57eb452b03a10938
STATE: OPEN
CURRENT_TASK: Phase 2C stadium / wall / physical-HR-shadow independent validation
RESULT: PRE2C_BASELINE_LOCKED / PHASE2C_CANDIDATE_NOT_YET_AVAILABLE

## FINAL_DECISION
- Canonical pre-Phase2C baseline is integrated Phase2B main `9d406589d6c71a92fa91843047116200c12826b3` (`Merge PR #60: Phase 2B analytical trajectory and landing position`).
- Phase2C production branch/PR was not present at final source check; candidate-dependent validation gates remain OPEN.
- PHASE2C_VALIDATION = OPEN.
- PHASE2D_ALLOWED = NO until a real Phase2C production candidate is independently validated.
- 05 made no stadium-dimension, trajectory-coefficient, HR-rate, or production-gameplay tuning changes.

## SOURCE_STATE
- pre2C integrated main: `9d406589d6c71a92fa91843047116200c12826b3`.
- Merge parents: prior main `4043ec9734a2bc95e4e90b58867e30032f81fc82` and Phase2B branch head `72980c04c3e2f6b66a2d215f45287d1de90c6bc8`.
- Phase2C branch search (`phase2c`, `stadium`) returned no production feature branch; only 05 validation branch exists.
- Phase2C branch HEAD: OPEN / unavailable.
- Phase2C validation checkout: OPEN / unavailable.
- Production blob identity versus candidate: OPEN / unavailable.

## BASELINE
The merged Phase2B production code is the same candidate code independently validated in 05 before integration. Canonical fixed-seed baseline (`seed=20260911`) is therefore inherited from the successful Phase2B validation evidence:

Production 10k games:
- PA/game 80.449.
- Runs/game 9.5594.
- Hits/game 19.3175.
- HR/game 2.1883.
- BB/game 7.6208.
- K/game 14.4689.
- HBP/game 1.0592.
- 1B/PA 17.1627%; 2B/PA 3.9442%; 3B/PA 0.1851%; HR/PA 2.7201%.
- AVG .26978; SLG .40994; ISO .14016; BABIP .31081.
- duplicate neutral 20k PA and 250 full games were exact deterministic replays.

Phase2A physical baseline, 200k production PA -> 142,885 states:
- EV mean/SD 84.05575 / 6.29527 mph.
- LA mean/SD 9.95008 / 19.20555 deg.
- Timing mean/SD -0.00077 / 0.34168.
- Spray mean/SD 0.06213 / 17.63648 deg.

Phase2B trajectory baseline, same physical population:
- carry mean/SD 180.3103 / 121.2608 ft; P5/P50/P95 7.120 / 230.233 / 331.405; max 445.052.
- hang mean/SD 2.6020 / 2.1001 s; P5/P50/P95 0.0644 / 2.7106 / 6.0328; max 7.3579.
- apex mean/SD 22.1454 / 28.6009 ft; P5/P50/P95 3 / 8.562 / 84.474; max 260.
- 100 mph / 29 deg = 397.0 ft; best 0-60 deg carry at 29 deg, not 45 deg.
- landing coordinate mirror invariants PASS.

Legacy final HR remains authoritative in this baseline. Any Phase2C shadow-only candidate must reproduce these legacy final outcomes and Phase2A/Phase2B state distributions exactly under fixed seed.

## DATA_QUALITY_WATCH
08 Phase2C research pack remains the reference contract, not a tuning authority:
- VERIFIED: use as directly sourced geometry evidence where documented.
- APPROXIMATED: acceptable for engineering/validation fixtures, not proof of exact real-KBO calibration.
- CONFLICTING: preserve disagreement; do not silently average.
- Generic stadium is an engineering fixture (`GENERIC_ENGINEERING_BASELINE`), not a measured KBO mean or calibration target.
- Jamsil wall height remains conflicting (~2.6 vs 2.7 m sources).
- Gocheok LF/RF/CF and 4.0 m wall have strong primary-source support.
- Daejeon asymmetry is the preferred structural smoke fixture; exact Monster Wall angular sector remains only partially sourced.

## PREVALIDATION_HARNESS
- Branch `validation/phase2c-prebaseline-05` was created directly from integrated Phase2B main.
- Validation-only historical 05 tools were copied onto the branch to make baseline replay available without modifying production `src/`.
- First workflow attempt failed before metrics because shallow checkout could not resolve the historical source tree; source check was corrected with `fetch-depth: 0`.
- Second workflow source identity and compile stages PASSed, then an older copied offense diagnostic failed against the now-current API before data collection. This is a harness compatibility failure, not evidence of a gameplay regression.
- Because a canonical successful Phase2B fixed-seed validation artifact already exists for the exact merged production blobs, 05 does not reinterpret these harness setup failures as baseline failures.
- Candidate validation harness will be adapted to the actual Phase2C API once the real branch exists; no speculative production-interface assumptions are being used to issue PASS gates.

## REQUIRED_PHASE2C_GATES_WHEN_CANDIDATE_EXISTS
For a real current Phase2C production HEAD, 05 must independently measure using one deterministic BIP corpus:
- Generic / Jamsil-like / Gocheok-like / Daejeon-asymmetric wall reached, clear, below-wall/contact, near-wall, physical-HR-shadow and clearance distributions.
- LF/LC/CF/RC/RF sector wall-reached and physical-HR-shadow rates.
- Daejeon expected asymmetry.
- wall-height and wall-radius monotonicity with controlled fixtures.
- impossible-HR invariants: no HR without reaching wall, no HR below wall, no invalid/non-finite trajectory HR, no invalid radius state.
- symmetric-park +/-spray radius/height/result mirror invariance.
- exact Phase1/Phase2A/Phase2B and legacy final-result regression under fixed seed.
- same-state and same-seed determinism.
- paired same-run Phase2B-vs-Phase2C 50k+ PA and 500+ game benchmark; fixed-sector O(1) behavior.

## GATES
- PRE2C_BASELINE_SOURCE = PASS
- SOURCE_IDENTITY = OPEN (Phase2C candidate unavailable)
- STADIUM_GEOMETRY = OPEN
- HEIGHT_AT_WALL = OPEN
- WALL_INTERSECTION = OPEN
- HR_SHADOW = OPEN
- ASYMMETRY = OPEN
- MIRROR = OPEN
- IMPOSSIBLE_HR = OPEN
- PHASE2B_REGRESSION = OPEN
- PHASE1_REGRESSION = OPEN
- DETERMINISM = OPEN
- PERFORMANCE = OPEN

## HANDOFF_TO_01
MEASURED:
- Phase2B is integrated on main and its independently validated fixed-seed baseline is locked for Phase2C comparison.
- 08 stadium data-quality labels and engineering-fixture constraints are explicitly retained.
- No Phase2C production candidate existed at final source check, so there is no valid source against which stadium/HR-shadow gates can be run.

HANDOFF:
- When Phase2C branch is created, provide no special validation-only implementation to 05; 05 will inspect the actual current production HEAD and adapt its harness to the candidate's real public/internal contract.
- Keep Phase2C shadow-only: legacy 1B/2B/3B/HR/OUT/Runs/game result must not change.
- Keep physical fair/foul non-authoritative unless separately approved.
- Do not use approximate park geometry as proof of exact KBO calibration.
- Preserve fixed-sector O(1) wall lookup and expose enough deterministic wall-resolution state for impossible-HR and sector diagnostics.
