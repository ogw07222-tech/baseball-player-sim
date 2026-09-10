# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@774431d9b221407bebeddb02001eeeed6c40bef2
STATE: READY_FOR_INTEGRATION
CURRENT_TASK: KBO regular-season 11-inning / draw termination rule
RESULT: PASS

## LAST_COMPLETED
- Root cause confirmed in `PersistentInningEngine._finish_half_inning()`: tied games after the bottom of inning 9+ incremented unconditionally with no regular-season inning ceiling.
- Implemented the KBO regular-season core rule on `fix/kbo-regular-season-extra-innings`: regulation is 9 innings; tied games may enter innings 10 and 11; a tie after a completed bottom 11th terminates as a draw; inning 12 cannot be entered.
- Existing walkoff and final-half semantics are preserved: an away lead after top 11 still requires bottom 11; a bottom-half home lead at inning 9+ ends immediately by walkoff; a home lead after a completed top half at inning 9+ skips an unnecessary bottom half.
- `ProductionGameResult` required no schema change: tied score already yields `winner=None`, `loser=None`, and `team_result_for(...) == "T"`.
- Production advance/stat aggregation already has explicit tie support. A draw increments games/player stats and `team_ties`, without incrementing team wins or losses.
- Production pitcher W/L remains unsupported, so draw termination does not invent pitcher decisions.
- Persistent inning state currently has no dedicated mid-game save/load serialization contract; extra-inning save/load is therefore not modified by this task.

## VALIDATION
- PR #40 source commit: `0182ae460bac8765373e38459159d87f9931c0a6`.
- Main diff at validation checkpoint: `src/inning.py` +7 lines and one dedicated extra-inning regression test module; no hitting/pitching probability, ratings, growth, event, or pitcher-usage changes.
- GitHub Actions run `34483832068`: compile PASS; full Python `unittest discover` PASS; auto-career smoke PASS; balance smoke PASS; web build/tests PASS at the gameplay validation checkpoint.
- Dedicated coverage includes 9 tie -> 10, 10 tie -> 11, completed 11 tie -> draw, no inning 12, top-11 away lead -> bottom 11, bottom-11 walkoff, regulation walkoff/non-tie regressions, skip unnecessary bottom half, draw aggregation, pitcher W/L unsupported contract, deterministic full-game replay, and representative full games capped at 11.
- Large 10,000-game Monte Carlo rerun is intentionally deferred to 05 - Balance Lab after integration.

## CURRENT_FINDINGS
- This is a core baseball-game rule in `PersistentInningEngine`, so fixed-provider, dynamic pitcher-provider, PLAYER mode, and future GM/Manager/automated league callers that reuse the engine receive the same termination semantics.
- No downstream result or aggregation schema migration is required for draws.

## BLOCKERS
- None for gameplay implementation.

## OPEN_ITEMS
- Merge/integration of PR #40 is outside this workstream's release-management scope.
- After integration, 05 - Balance Lab should rerun canonical 10k heavy production sanity on latest main.

## DEPENDENCIES
- 05: post-integration heavy production sanity rerun.
- 07: production integration / merge handling if required.
- 00: any future game-mode-specific rule variants; the current 11-inning limit is the KBO regular-season core contract.

## NEXT_ACTION
- 05 handoff after PR #40 integration: require max innings <= 11; games tied after completed inning 11 terminate as draws; 12+ innings = 0; safety-cap hits = 0; invariant violations = 0; deterministic replay = PASS.

## RELATED_PRS
- #33 merged
- #40 open — KBO regular-season 11-inning draw termination

## RELATED_BRANCHES
- main
- fix/kbo-regular-season-extra-innings

## RELATED_RUNS
- PR #40 tests: 34483832068

## GATES
- H321_PRODUCTION_CONTRACT = PASS
- KBO_REGULAR_SEASON_EXTRA_INNING_RULE = PASS
- DRAW_RESULT_COMPATIBILITY = PASS
- DRAW_AGGREGATION_COMPATIBILITY = PASS
- GAMEPLAY_REGRESSION = PASS
- HEAVY_10K_POST_FIX = HANDOFF_TO_05
