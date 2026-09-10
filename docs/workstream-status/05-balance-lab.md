# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@8c8cf85760f4728ff7cbc20eff2d06e12b09d194
STATE: DONE
CURRENT_TASK: Post-KBO-rule Heavy Validation
RESULT: PASS

## LAST_COMPLETED
- Task-start latest main was `01410033c1998272db38e1488895c0903d0b5b1b`, the merge commit for PR #40 (`Fix KBO regular-season 11-inning draw termination`). PR #40 changes the core inning termination rule only; no gameplay probability, rating, growth, event, or pitcher-usage tuning was introduced.
- Validation-only instrumentation in `tools/production_game_provider_sanity.py` was updated so KBO regular-season draws are valid outcomes and explicit guards cover max inning 11, 12+ innings, draw-at-11 semantics, draw winner/loser/team-result semantics, deterministic replay, structural counting, and distribution tails.
- Canonical post-PR40 10,000-game heavy run completed on exact checkout `7112ce550e0933a80b0c75701de46fbd03047077`, seed `20260906`, Python 3.12, via GitHub Actions run `34488552895`.
- Heavy run artifact: `heavy-validation-34488552895-7112ce550e0933a80b0c75701de46fbd03047077`, artifact ID `10156752284`, containing `metadata.json` and `full-game.json` with 30-day retention.
- Standard repository CI for the same execution SHA completed GREEN in run `34488552783`: Python compile/unit tests, Auto career smoke, Balance smoke, draft calibration gate, web build, and web tests all PASS.
- After the one-time bootstrap push trigger, `.github/workflows/heavy-validation.yml` was restored to `workflow_dispatch` only. Current pre-status-update main is `8c8cf85760f4728ff7cbc20eff2d06e12b09d194`.

## POST_KBO_RULE_FULL_GAME_10K
- Command: `python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json`.
- Completion: 10,000 / 10,000 = 100.0%.
- KBO regular-season max inning contract: 11.
- Max innings observed: 11.
- 12+ inning games: 0 / 10,000.
- Regulation 9-inning games: 89.50%.
- 10-inning games: 4.47%.
- 11-inning games: 6.03%.
- Draws: 349 / 10,000 = 3.49%. Every observed final tie satisfied the 11-inning draw semantics checked by the invariant layer; no draw winner/loser/team-result semantic violations occurred.
- Extra-inning games: 10.50%.
- Walkoffs: 7.31%.
- Safety-cap hits: 0.
- Invariant violations: 0; violation map `{}`.
- Deterministic replay: PASS, replay seed `70260906`, result 4-5 in 9 innings with 72 events reproduced exactly.
- Obvious distribution collapse: false.
- Total runs/game: mean 8.1360, median/P50 8, SD 4.1898, min/max 0/31, P10/P90/P95/P99 = 3/14/16/20.
- Runs/team-game: mean 4.0680, median/P50 4, SD 2.9344, min/max 0/29, P10/P90/P95/P99 = 1/8/10/13.
- Innings/game: mean 9.1653, median/P50 9, SD 0.5085, min/max 9/11, P10/P90/P95/P99 = 9/10/11/11.
- PA/game: mean 77.3202, median/P50 77, SD 7.6344, min/max 56/112, P10/P90/P95/P99 = 68/87/91/99.
- Events/game: mean 79.1124, median/P50 78, SD 7.9179, min/max 57/114, P10/P90/P95/P99 = 70/90/94/102.
- Extreme tails: 12+ innings = 0; 20+ total runs = 112/10,000; team-games 15+ runs = 81/20,000; games 100+ PA = 84/10,000; games 150+ events = 0.

## PREVIOUS_10K_COMPARISON
- Previous pre-PR40 canonical 10k: total runs/game 8.1703, innings/game 9.2427, PA/game 77.8656, events/game 79.6605, extra innings 10.10%, walkoffs 8.96%, max innings 37.
- Post-PR40 deltas: total runs/game -0.0343 (-0.42%); innings/game -0.0774 (-0.84%); PA/game -0.5454 (-0.70%); events/game -0.5481 (-0.69%); extra innings +0.40 percentage points; walkoffs -1.65 percentage points.
- The pathological unlimited-extra-inning tail is removed: max innings 37 -> 11; 15+ inning games 72 -> 0; PA max 276 -> 112; events max 282 -> 114.
- The slight increase in extra-inning entry rate is not a structural concern: the metric measures games reaching inning 10+, while PR #40 changes termination after inning 11 and converts unresolved ties into draws rather than forcing a later winner.

## CURRENT_FINDINGS
- `KBO_REGULAR_SEASON_EXTRA_INNING_RULE = PASS` under canonical 10k production execution.
- `DRAW_SEMANTICS_HEAVY = PASS`: 349 draws, all terminating at inning 11 under the checked result contract, with zero draw semantic violations.
- `FULL_GAME_10K_POST_KBO_RULE = PASS`: completion 100%, max innings 11, 12+ innings 0, cap hits 0, invariant violations 0, deterministic replay PASS, no distribution collapse.
- `PRODUCTION_SANITY = PASS` remains closed after PR #40.
- `PRODUCTION_READINESS = PASS` remains closed for the scoped production simulation gate.
- No tuning action is justified or performed by this validation.

## BLOCKERS
- None for post-KBO-rule production sanity/readiness.

## OPEN_ITEMS
- R1V independent rating-generation validation remains a separate 02/05 follow-up and is not a blocker for this rule-validation gate.
- 08 may interpret empirical KBO run environment, draw rate, extra-inning rate, and workload distributions against matched real-world baselines; no calibration is performed here.

## DEPENDENCIES
- 01: no rule/inning defect routed; PR #40 heavy validation passed.
- 07: no aggregation/draw-counting defect exposed by the heavy result contract; PR #40 unit coverage separately includes draw aggregation semantics.
- 08: empirical baseline interpretation only, if desired.

## NEXT_ACTION
- No further Balance Lab action is required for the KBO 11-inning/draw production gate unless simulation logic changes again. Preserve the manual heavy-validation workflow for future production-rule checkpoints.

## RELATED_PRS
- #33 merged
- #36 merged
- #38 merged
- #40 merged

## RELATED_RUNS
- Post-KBO-rule canonical 10k PASS: 34488552895
- Same-SHA standard CI PASS: 34488552783
- Artifact: 10156752284

## RELATED_BRANCHES
- main

## GATES
- PR33_UNIT_REGRESSION = PASS
- FULL_GAME_10K_CANONICAL = PASS
- FULL_GAME_10K_POST_KBO_RULE = PASS
- KBO_REGULAR_SEASON_EXTRA_INNING_RULE = PASS
- DRAW_SEMANTICS_HEAVY = PASS
- PITCHER_HEAVY_500 = PASS
- CATCHER_HEAVY_200K = PASS
- R1V_INDEPENDENT_VALIDATION = OPEN
- PRODUCTION_SANITY = PASS
- PRODUCTION_READINESS = PASS
