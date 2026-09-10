# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@2f9a0c7a3c14ca462e4be3d95db3ad4a28635d56
STATE: BLOCKED
CURRENT_TASK: Heavy Production Sanity Gate completion
RESULT: OPEN

## LAST_COMPLETED
- Production implementation regression evidence remains green: 253/253 Python unit tests PASS, Auto career smoke PASS, Balance smoke PASS, natural-event 100k sanity PASS, catcher unit-generation gates PASS, and web tests/build PASS on the unchanged production implementation lineage after PR #33/#36.
- Heavy pitcher-usage validation was executed with seed `20260906`, 500 seasons × 144 games. Core results: starter IP/start mean 5.8677, median 5.8773, SD 0.1800, P90 6.0972, P95 6.1667, P99 6.2477, min 5.1968, max 6.4074; role switches/team-season mean 8.792; unavailable-use violations 0; bullpen exhaustion 1/500 seasons. Relief appearances/pitcher-season mean 39.318, median 34, SD 31.761, P90 82, P95 101, P99 109, max 116.
- Heavy catcher-generation validation was executed with seed `20260906`, 200,000 samples. Defense mean/SD 83.032/17.328, Throwing 92.466/18.312, Game Calling 85.707/15.200; 200+ tails were 0 across all three ratings, Throwing 170+ was 3/200k, invalid values 0. Archetype shares matched configured weights closely and correlations remained weak/moderate rather than collapsed.
- Work start source of truth was re-checked as `main@2f9a0c7a3c14ca462e4be3d95db3ad4a28635d56`. The latest commits since the prior validation checkpoint add reports/docs and do not provide a committed canonical `reports/integration-local/full-game.json` output.

## CURRENT_FINDINGS
- `PR33_UNIT_REGRESSION = PASS` remains supported.
- Pitcher heavy evidence is structurally clean: unavailable-use invariant violations = 0, bullpen exhaustion is very rare, and workload distributions are non-collapsed. The 100+ relief-appearance tail requires matched KBO interpretation before any balance/tuning conclusion.
- Catcher heavy distribution is structurally healthy: no invalid/negative values, no 200+ tails, expected archetype shares, and no covariance collapse.
- The mandatory canonical `python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json` has still not been executed in a full current-main checkout in this chat.
- Local network/DNS prevents `git clone`, `raw.githubusercontent.com`, and repository archive retrieval in the execution sandbox. GitHub connector can inspect source but does not expose a Codespaces execution action. GitHub Actions was intentionally not used for heavy compute, per workstream policy.
- Because the required 10,000-game full-game run is missing, `PRODUCTION_SANITY` and `PRODUCTION_READINESS` cannot be truthfully closed to PASS.

## BLOCKERS
- Canonical 10,000-game full-game provider heavy run cannot be launched from the available local execution environment because a complete repository checkout cannot be obtained.
- No reusable committed `reports/integration-local/full-game.json` exists at the checked source-of-truth HEAD.

## OPEN_ITEMS
- In an actual Codespaces/local checkout at current main, execute: `python tools/production_game_provider_sanity.py --games 10000 --seed 20260906 --output reports/integration-local/full-game.json`.
- Re-run `python tools/pitcher_usage_sanity.py --seasons 500 --seed 20260906` and `python tools/catcher_generation_sanity.py --samples 200000 --seed 20260906` in that same checkout to confirm canonical equivalence with the already observed heavy results.
- For the full-game run, record completion rate, cap/safety hits, runs/game, innings, PA/game, deterministic replay, impossible score/state/counting violations, and P10/P50/P90/P95/P99/min/max/tail summaries.
- If the canonical full-game run returns completion 100%, cap hits 0, invariant violations 0, deterministic replay PASS, and no obvious distribution collapse, set `PRODUCTION_SANITY = PASS` and `PRODUCTION_READINESS = PASS`; otherwise route the defect without tuning here.

## DEPENDENCIES
- 01: gameplay/state/counting defect from the 10k full-game run.
- 02: catcher/rating-generation defect if canonical generation diverges or distribution guards fail.
- 07: runtime/integration/tooling defect in canonical execution or report plumbing.
- 08: matched KBO baseline interpretation of workload tails and run environment.

## NEXT_ACTION
- Execute the three canonical heavy commands verbatim in a real current-main Codespaces/local checkout, with priority on the still-missing 10k full-game provider run, then close the production gates based on measured evidence only.

## RELATED_PRS
- #33 merged
- #36 merged

## RELATED_BRANCHES
- main

## GATES
- PR33_UNIT_REGRESSION = PASS
- PRODUCTION_SANITY = OPEN
- PRODUCTION_READINESS = OPEN
