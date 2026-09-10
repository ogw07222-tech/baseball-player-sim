# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@d710104d7594a0ed3ba287cf3d89cec25d6689b3
STATE: DONE
CURRENT_TASK: Heavy Production Sanity Gate via GitHub Actions
RESULT: PASS

## LAST_COMPLETED
- Task-start main was `4aba1adcd60acb98558145e42dca2cfc45423388` (PR #38 merge). Validation-only instrumentation was added to `tools/production_game_provider_sanity.py`; no simulation/gameplay/rating/growth coefficient was changed.
- Added `.github/workflows/heavy-validation.yml` as a reproducible heavy-validation runner. After the one-time bootstrap run, the final workflow is `workflow_dispatch` only and accepts suite/seed/games/seasons/samples inputs.
- First bootstrap run `34481553341` failed before simulation because direct `python tools/...` execution lacked repo-root import resolution (`ModuleNotFoundError: src`). This was classified as validation-workflow plumbing, not simulation failure. The workflow was corrected with `PYTHONPATH=.` while preserving the canonical command.
- Canonical full-game run `34481649185` completed successfully on exact checkout `3543588a960c8dc491b5ce5f92caca0a059ddcec`, Python 3.12, suite `full_game`, seed `20260906`, games `10000`.
- Artifact preserved as `heavy-validation-34481649185-3543588a960c8dc491b5ce5f92caca0a059ddcec` (artifact ID `10153858964`, 30-day retention) containing `metadata.json` and `full-game.json`.
- Current main `d710104d7594a0ed3ba287cf3d89cec25d6689b3` is later than the validation SHA only by documentation/workflow-finalization changes relevant to this workstream; the measured production simulation implementation is unchanged from the successful run.

## FULL_GAME_10K
- Command: `python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json`.
- Completion: 10,000 / 10,000 = 100.0%.
- Safety-cap hits: 0 / 10,000.
- Invariant violations: 0; violation map `{}`.
- Deterministic replay: PASS using seed `70260906`; replay result 4-5, 9 innings, 72 events reproduced exactly.
- Obvious distribution collapse: false.
- Total runs/game: mean 8.1703, median/P50 8, SD 4.1735, min/max 1/31, P10/P90/P95/P99 = 3/14/16/20.
- Runs/team-game: mean 4.08515, median/P50 4, SD 2.9302, min/max 0/30, P10/P90/P95/P99 = 1/8/10/13.
- Innings/game: mean 9.2427, median/P50 9, SD 0.9592, min/max 9/37, P10/P90/P95/P99 = 9/10/11/14.
- PA/game: mean 77.8656, median/P50 76, SD 9.9408, min/max 56/276, P10/P90/P95/P99 = 68/88/94/116.
- Events/game: mean 79.6605, median/P50 78, SD 10.3012, min/max 56/282, P10/P90/P95/P99 = 70/90/96/118.
- Tail frequencies: 15+ innings = 72/10,000 (0.72%); 20+ total runs = 123/10,000 (1.23%); team-games 15+ runs = 83/20,000 (0.415%); games 100+ PA = 302/10,000 (3.02%); games 150+ events = 19/10,000 (0.19%).
- Context metrics: hits/team-game 9.24235; HR/game 2.1067; BB/game 6.3179; K/game 16.6641; extra innings 10.10%; walkoffs 8.96%; runtime 57.69 s (~173.33 games/s).

## PITCHER_CATCHER_HEAVY
- Existing pitcher-usage heavy validation remains applicable to the unchanged pitcher-usage implementation: seed `20260906`, 500 seasons × 144 games; starter IP/start mean 5.8677, median 5.8773, SD 0.1800, P90/P95/P99 6.0972/6.1667/6.2477, min/max 5.1968/6.4074; unavailable-use violations 0; bullpen exhaustion 1/500 seasons; role switches/team-season mean 8.792; relief appearances/pitcher-season mean 39.318, median 34, SD 31.761, P90/P95/P99 82/101/109, max 116.
- Existing catcher heavy validation remains applicable to the unchanged catcher/player-generation implementation: seed `20260906`, 200,000 samples; Defense mean/SD 83.032/17.328, Throwing 92.466/18.312, Game Calling 85.707/15.200; 200+ tails 0, Throwing 170+ = 3/200k, invalid values 0; archetype proportions matched configured weights and covariance did not collapse.

## CURRENT_FINDINGS
- `PR33_UNIT_REGRESSION = PASS` remains supported by the existing 253-test regression suite and prior smoke evidence.
- `PRODUCTION_SANITY = PASS`: canonical 10k full-game production-provider execution satisfies all declared structural PASS conditions: completion 100%, cap hits 0, invariant violations 0, deterministic replay PASS, and no obvious distribution collapse.
- `PRODUCTION_READINESS = PASS` for the currently scoped production-integration gate. No gameplay/state/counting blocker was exposed by the heavy run.
- Extreme tails exist but are sparse rather than collapsed: max 37 innings, 31 total runs, 276 PA, 282 events. These are empirical-tail observations, not automatic failures; no safety cap or structural invariant was violated.
- R1V independent rating-generation validation remains OPEN as a separate cross-workstream item. 02's committed R1 reports exist, but main does not currently contain a dedicated R1 reproduction validator/command equivalent to the heavy production sanity scripts. This does not block the production integration sanity/readiness gate closed here.

## BLOCKERS
- None for the Production Sanity / Production Readiness gate closed by this task.
- R1V remains an independent 02/05 follow-up, not a production-sanity blocker.

## OPEN_ITEMS
- R1V: reproduce Rating Generation R1 directly from latest-main production modules with a committed/explicit independent validator and compare against `reports/rating_r1_*` metrics; do not tune production ratings during validation.
- 08 may compare run environment and pitcher workload tails against matched KBO baselines; these empirical calibration questions are outside the structural production-sanity PASS decision.

## DEPENDENCIES
- 01: no routed gameplay/state/counting defect from this 10k run.
- 02: owns rating/generation interpretation and any future R1/R2 decisions; R1V independent reproduction remains OPEN.
- 03: no growth/career defect exposed by this full-game gate.
- 07: heavy-validation workflow plumbing is now resolved and reusable via manual dispatch.
- 08: empirical KBO baseline interpretation for run environment/workload tails only.

## NEXT_ACTION
- Production sanity gate is closed. Next Balance Lab work is independent R1V/reference validation when 02 supplies or approves a reproducible production-module harness/contract; otherwise no further action is required for this gate.

## RELATED_PRS
- #33 merged
- #36 merged
- #38 merged

## RELATED_RUNS
- Heavy bootstrap/import-path failure: 34481553341
- Canonical 10k PASS: 34481649185
- Artifact: 10153858964

## RELATED_BRANCHES
- main

## GATES
- PR33_UNIT_REGRESSION = PASS
- FULL_GAME_10K_CANONICAL = PASS
- PITCHER_HEAVY_500 = PASS
- CATCHER_HEAVY_200K = PASS
- R1V_INDEPENDENT_VALIDATION = OPEN
- PRODUCTION_SANITY = PASS
- PRODUCTION_READINESS = PASS
