# 05 - Balance Lab

WORKSTREAM: 05 - Balance Lab
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@f336b9be10f252300971be3d146b51ad7ff91537
STATE: DONE
CURRENT_TASK: P1 Production Integration Regression Baseline
RESULT: PASS_WITH_ONE_OPEN_EQUIVALENCE_GAP

## BASELINE_SOURCE
- Exact baseline source: `main@f336b9be10f252300971be3d146b51ad7ff91537`.
- Latest-main CI run `34578255430` completed PASS on the same SHA.
- Compared with prior post-KBO heavy baseline source `67f752a375a708d9d9834f09c6954aced4b950f9`: 58 commits added API/persistence/deployment/frontend integration, while core full-game simulation modules (`src/inning.py`, `src/game_provider.py`, pitcher/catcher/gameplay formula modules) were not changed in that compare. Therefore the existing post-KBO canonical 10k distribution baseline remains the valid simulation-distribution reference until one of those production simulation modules changes.

## CURRENT_MAIN_REGRESSION_EVIDENCE
- Latest-main GitHub Actions run `34578255430` PASS:
  - Vercel Python packaging validation PASS.
  - External durable store tests PASS.
  - Vercel FastAPI entrypoint smoke PASS.
  - API vertical-slice tests PASS.
  - Related production integration tests PASS (`test_production_game_provider`, `test_production_integration_consolidation`, `test_season_lifecycle_bridge`).
  - Full unittest discovery PASS.
  - Auto-career smoke PASS with seed `20260903`.
  - Balance smoke PASS with seed `20260903`.
  - High-school/draft calibration gate PASS with seed `20260905`.
  - Web build/tests PASS.

## P1_REGRESSION_BASELINE
- NEXT_GAME_DETERMINISM = PASS.
  - API save/load deterministic resume test deserializes the same persisted payload twice, advances one game through `ProductionAdvanceService`, and requires byte-equivalent `serialize_game(...)` output.
  - Same idempotency-key replay returns the exact prior committed response without a second simulation mutation.
- GAME_COMPLETION = PASS.
  - Current production-provider and integration tests pass on exact main.
  - Representative full-game distribution reference is inherited by code identity from canonical post-KBO 10k run `34488552895`: 10,000/10,000 completed, safety-cap hits 0.
- STAT_AGGREGATION = PASS.
  - API vertical slice requires first `next_game` to advance dashboard progress to game 1 and persisted `current_session.games_completed` to 1.
  - Production deployment smoke independently observed game/stat aggregates persist after `next_game`.
- REVISION_SIMULATION_STATE_SEPARATION = PASS.
  - First mutation advances revision 1 -> 2 and simulation game count 0 -> 1.
  - Idempotent replay remains revision 2 / game 1.
  - stale `expected_revision=1` returns `REVISION_CONFLICT` without simulation re-execution.
- SAVE_LOAD_EQUIVALENCE = PASS.
  - API deterministic-resume test passes on current main.
  - Production integration save round-trip preserves advance state/team record.
  - Separate-client production persistence smoke previously recovered the same revision-2 simulation state.
- PRODUCTION_ADVANCE_COMPOSITION = PASS.
  - `advance_one_week()` equals repeated `advance_one_game()` over canonical dates, including advance state, team record, pitcher usage state, and completed games.
  - `advance_one_month()` equals repeated `advance_one_game()` over the same canonical dates.
- DIRECT_CAREER_VS_PRODUCTION_ADVANCE_EQUIVALENCE = OPEN.
  - No dedicated latest-main regression test was found that runs one identical seeded game once through a separate direct CareerEngine path and once through ProductionAdvanceService, then asserts full state/stat equivalence. Existing tests strongly cover production composition and persisted CareerEngine state, but this exact cross-path comparison is not explicitly pinned.
- NO_DUPLICATED_GAME_STAT_MUTATION = PASS.
  - Same idempotency key replay preserves revision 2 and `games_completed=1`; production smoke also observed no duplicate committed mutation.
- KBO_INNING_DRAW_SEMANTICS = PASS.
  - Core simulation modules are unchanged from canonical post-PR40 heavy run.
  - Reference: max innings 11; 12+ innings 0; draws 349/10,000 (3.49%); invariant violations 0; deterministic replay PASS.
- PITCHER_REGRESSION = PASS.
  - Pitcher production implementation remains unchanged from the validated heavy baseline; previous seed `20260906`, 500 seasons evidence remains reference: unavailable-use violations 0, bullpen exhaustion 1/500 seasons.
- CATCHER_REGRESSION = PASS.
  - Catcher/player-generation implementation remains unchanged from heavy baseline; previous seed `20260906`, 200,000 samples evidence remains reference: invalid values 0, 200+ tails 0, covariance/archetype structure intact.

## REPRESENTATIVE_GAME_DISTRIBUTION_BASELINE
Canonical post-KBO 10k reference (run `34488552895`, seed `20260906`; valid for current main by simulation-code identity):
- runs/game mean 8.1360; P10/P50/P90/P95/P99 = 3/8/14/16/20; min/max 0/31.
- innings/game mean 9.1653; P10/P50/P90/P95/P99 = 9/9/10/11/11; min/max 9/11.
- PA/game mean 77.3202; P10/P50/P90/P95/P99 = 68/77/87/91/99; min/max 56/112.
- events/game mean 79.1124; P10/P50/P90/P95/P99 = 70/78/90/94/102; min/max 57/114.
- regulation 9-inning games 89.50%; 10-inning 4.47%; 11-inning 6.03%; draws 3.49%; extra innings 10.50%; walkoffs 7.31%.
- completion 100%; safety-cap hits 0; invariant violations 0; deterministic replay PASS; distribution collapse false.

## DEPLOYED_P0_REFERENCE
- 07 production smoke evidence remains a useful integration reference: create career -> state -> one `next_game` -> revision 2; persisted game/stat mutation; idempotent replay; stale revision 409; separate-client recovery of the same revision-2 state; browser create/advance/reload persistence PASS.
- Forced cold-start identity proof remains an integration-specific OPEN item and is not classified as a simulation regression failure.

## P1_POST_MERGE_COMPARISON_RULE
After P1 merges, compare against this baseline in this order:
1. exact source SHA and changed-file set;
2. current CI: API vertical slice, production integration, full unit, auto-career, balance smoke;
3. next_game revision/idempotency/game-count invariants;
4. save/load deterministic resume;
5. production advance composition;
6. KBO 11-inning/draw invariants;
7. if any core simulation module changed, rerun canonical full-game 10k with seed `20260906` and compare distribution metrics above;
8. rerun pitcher/catcher heavy suites only if their owned production modules changed.

## ROUTING
- gameplay/state/counting/KBO rule regression -> 01.
- rating/generation/catcher generation regression -> 02.
- growth/career lifecycle regression -> 03.
- HTTP/revision/idempotency/persistence/duplicate mutation regression -> 07.
- empirical KBO baseline interpretation only -> 08.

## GATES
- P1_BASELINE_LATEST_MAIN_CI = PASS
- NEXT_GAME_DETERMINISM = PASS
- GAME_COMPLETION = PASS
- STAT_AGGREGATION = PASS
- REVISION_SIMULATION_STATE_SEPARATION = PASS
- SAVE_LOAD_EQUIVALENCE = PASS
- PRODUCTION_ADVANCE_COMPOSITION = PASS
- DIRECT_CAREER_VS_PRODUCTION_ADVANCE_EQUIVALENCE = OPEN
- NO_DUPLICATED_GAME_STAT_MUTATION = PASS
- KBO_REGULAR_SEASON_EXTRA_INNING_RULE = PASS
- DRAW_SEMANTICS_HEAVY = PASS
- PITCHER_HEAVY_500 = PASS
- CATCHER_HEAVY_200K = PASS
- REPRESENTATIVE_GAME_DISTRIBUTION_BASELINE = PASS
- PRODUCTION_SANITY = PASS
- PRODUCTION_READINESS = PASS
