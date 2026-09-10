# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@e642fa2545bdc05ad8cc2b363b7bd199173409b1
STATE: ACTIVE
CURRENT_TASK: Latest main production integration validation
RESULT: OPEN

## LAST_COMPLETED
- Latest-main GitHub Actions run 34472217585 completed green on `e642fa2545bdc05ad8cc2b363b7bd199173409b1`: Python compile PASS, 253/253 unit tests PASS, Auto career smoke PASS, Balance smoke PASS, 10k-player/10k-NPC/10k-draft calibration gate PASS, and web build/tests PASS.
- The same 253-test run includes PR #33 regressions for persistent inning state, natural baseball events, stat aggregation, production full-game provider/contracts, pitcher usage/rotation reconciliation, catcher foundation, week/month compositional equivalence, save/load continuation, deterministic seed behavior, score/base/out invariants, and non-negative/probability-safety checks.
- Natural-event 100k sanity embedded in the suite completed with seed `20260906`: 1,248 games, 100,023 events, 97,802 PA, 0 invariant test failures.
- Catcher generation distribution test completed with 100,000 catchers and archetype-diversity coverage with 20,000 catchers; all configured distribution/tail guards passed.

## CURRENT_FINDINGS
- `PR33_UNIT_REGRESSION` is strongly green on latest production main.
- The previous `game_calling` CLI presentation blocker is resolved by merged PR #36; its latest-main Auto career smoke now passes. PR #36 changed only the CLI stat-label mapping and did not alter gameplay formulas.
- Natural-event observed summary at seed `20260906`: SF 1.110/600 PA, GDP 8.245/600 PA, XBT 35.901/600 PA, tag-up success 20.98%, first-to-home-on-double success 60.34%; no obvious event-distribution collapse was detected by the existing 100k gate.
- Full-game provider structural contracts are green: game completion, non-negative score, batting/pitching counting consistency, lineup/state behavior, extra-inning/walkoff handling, and deterministic same-seed behavior all pass unit coverage.
- Week/month advance equals repeated-game advance in both production-provider and aggregation regression coverage; save/load continuation and pitcher-usage state round trips also pass.
- Existing heavy runner still defines production-specific runs of 10,000 full games, 500 pitcher-usage seasons, and 200,000 catcher generations, but those heavy outputs are not persisted under `reports/` and were not executed by this chat because the available local sandbox cannot resolve `github.com`; large GitHub Actions compute was intentionally not triggered.
- Existing `production_game_provider_sanity.py` and `pitcher_usage_sanity.py` do not expose all requested SD/percentile/tail fields, so a full long-run distribution verdict requires local/Codespaces execution plus one-off analysis or validation-instrumentation enhancement without gameplay tuning.

## BLOCKERS
- Heavy production-specific evidence is still missing for the current main: 10,000-game full-game distribution and safety-cap summary, 500-season pitcher workload/role distribution, and dedicated 200,000-catcher percentile report.
- Requested long-run percentile/tail coverage for score, innings, relief workload, consecutive-day usage, bullpen exhaustion, and role-switch frequency is not fully emitted by current sanity scripts.

## OPEN_ITEMS
- Run `tools/production_game_provider_sanity.py --games 10000 --seed 20260906` locally/Codespaces and capture completion rate, cap hits, scoring/inning/PA distributions and tails.
- Run `tools/pitcher_usage_sanity.py --seasons 500 --seed 20260906` locally/Codespaces and capture starter IP/start, relief workload, consecutive-day usage, unavailable-use violations, bullpen exhaustion, role-switch frequency and distribution tails.
- Run `tools/catcher_generation_sanity.py --samples 200000 --seed 20260906` locally/Codespaces and retain mean/SD/P10/P50/P90/P95/P99/min/max/tail counts.
- Add one-off validation analysis for requested median/SD/percentiles where current sanity scripts only emit aggregate means; do not tune gameplay parameters.

## DEPENDENCIES
- 07: only if heavy runs expose an integration/runtime defect or if persistent report plumbing is added.
- 01: only if heavy validation exposes gameplay-formula defects.
- 02: only if catcher/player rating distributions fail after heavy execution.
- 08: only for real KBO baseline comparison and matched-sample interpretation.

## NEXT_ACTION
- Execute the existing heavy production integration sanity set in local/Codespaces against `main@e642fa2545bdc05ad8cc2b363b7bd199173409b1`, then compute the missing percentile/tail summaries and close `PRODUCTION_SANITY` without parameter tuning.

## RELATED_PRS
- #33 merged
- #36 merged (CLI presentation fix; latest-main smoke PASS)

## RELATED_BRANCHES
- main

## GATES
- PR33_UNIT_REGRESSION = PASS
- PRODUCTION_SANITY = OPEN
- PRODUCTION_READINESS = OPEN
