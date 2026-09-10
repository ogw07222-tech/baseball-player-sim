# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@f19bf424c910bfa66bf05cc20d20a930f27f8c88
IMPLEMENTATION_BASE: main@9aa458735721570581f4968060590acf3fc9c957
STATE: IMPLEMENTED_AWAITING_LONG_RUN_VALIDATION
CURRENT_TASK: Production Season Lifecycle Bridge v1 implementation
RESULT: IMPLEMENTATION_PASS

## LAST_COMPLETED
- Implemented the approved Production Season Lifecycle Bridge v1 on `feature/production-season-lifecycle-v1`.
- Added canonical `CareerEngine.finalize_completed_pro_season()` and `SeasonFinalizationResult`.
- Refactored `finish_pro_season()` to delegate lifecycle-owned finalization to the same primitive.
- Added explicit `ProductionAdvanceService.finalize_season()` and `start_next_season()` boundary operations.
- Added lifecycle/save-load/idempotency/headless-equivalence regression tests.
- PR #38 remains open against main and is currently mergeable.
- Rechecked latest main after implementation; intervening main work does not replace the lifecycle primitive or Growth/Career backend contract.

## IMPLEMENTATION_CONTRACT
### Finalization primitive
`CareerEngine.finalize_completed_pro_season()` requires:
- phase == PRO
- current_session exists
- current_session.finished == True
- no unresolved pending event

On success it performs exactly once:
1. awards determination/persistence
2. SeasonRecord append
3. GrowthExperience creation from FIRST/FARM PA
4. existing season growth
5. existing offseason trait hook
6. existing coach replacement hook
7. engine year +1
8. current_session clear
9. seasonal modifier/form reset
10. existing fatigue offseason carryover

Retirement remains caller-controlled and is not implicitly evaluated by finalization.

### Idempotency and persistence
- No new persisted lifecycle marker is used.
- A finished `current_session` is the pre-finalization state.
- Successful finalization clears `current_session`; repeated finalization rejects before RNG-consuming work.
- A game-144 save preserves the finished session and remains finalizable after load.
- Production finalization removes stale `advance_state`.
- Finalized save/load does not replay growth or awards.
- SAVE_VERSION is unchanged; existing supported saves remain backward compatible.

### Production advance bridge
- `ProductionAdvanceService.season_complete` exposes the boundary.
- `finalize_season()` invokes only the canonical CareerEngine finalization primitive.
- `start_next_season()` explicitly creates the next ProSeasonSession, rebuilds the schedule using the incremented engine year, and creates fresh production advance state.
- Service construction does not finalize a season.
- Read-only state access does not intentionally consume lifecycle RNG.

### Result contract
`SeasonFinalizationResult` exposes:
- completed_year
- next_year
- age_before
- age_after
- completed SeasonRecord
- GrowthResult
- awards
- `as_dict()` for validation/UI-adapter consumption

## TEST_COVERAGE
`tests/test_season_lifecycle_bridge.py` covers:
- finalize before completion rejected with zero RNG consumption
- completed season finalizes exactly once
- repeated finalize rejects with zero additional RNG consumption
- pending event blocks finalization before RNG consumption
- `finish_pro_season()` equivalence with direct canonical finalization for equivalent completed state
- service constructor does not auto-finalize game 144
- game 144 save/load -> finalize exactly once
- game 143 save/load -> game 144 -> finalize -> next season
- finalize -> save/load -> fresh next season without replaying growth
- old save without advance_state remains loadable

## CI_STATUS
PR: #38
BRANCH: feature/production-season-lifecycle-v1
IMPLEMENTATION_HEAD: 411529269b042708bb45fadbedb181f4b8067a6e
STATUS_HEAD_BEFORE_THIS_UPDATE: 0141428a353b3077e50ddf05fa3002456f80b4bd
- tests workflow #585 on implementation head: SUCCESS
- tests workflow #589 on status-updated head: SUCCESS
- Python compile: PASS
- full unit test suite: PASS
- auto career smoke: PASS
- balance smoke: PASS
- high-school/draft calibration gate: PASS
- web build/tests: PASS

Local clone/full-suite-before-push was unavailable because the execution environment could not resolve github.com; GitHub PR CI supplied the full-suite checkpoint.

## UNCHANGED / OUT_OF_SCOPE
- gameplay probabilities
- hitter/pitcher formulas
- rating scale
- Talent semantics
- event catalog
- contract / FA / service-time / trade / posting

## REMAINING_OPEN_ITEMS
- 05 long-run lifecycle equivalence/distribution validation.
- 07 integration review and merge decision for PR #38 against current main.
- Realistic FARM/FIRST playing-time opportunity redesign.
- Persistent injury-development consequences.
- Contract/FA/trade/posting/service-time foundation.
- Future multi-season pitcher-usage offseason reset semantics require 01/07 review; this batch did not alter gameplay usage formulas/state policy.

## MONTE_CARLO_HANDOFF_FOR_05
Validation only; no tuning.
Required checks:
- N >= 1,000 full careers through the canonical season-boundary path when runtime permits
- duplicate finalized seasons = 0
- missing finalized seasons = 0
- finalized season count == age increment count == engine year increment count until retirement
- matched-seed save/load interruptions at random game-143/game-144/post-finalize boundaries produce identical terminal state
- deterministic replay mismatch rate = 0
- compare old headless vs canonical lifecycle distributions for debut age, peak age, peak ability, retirement age, career PA, FARM PA, injuries, awards
- material distribution deltas should not appear because no progression tuning/formula changes were made

## DEPENDENCIES
- 05: long-run deterministic/distribution validation.
- 07: PR #38 integration review, current-main compatibility, merge/CI.
- 01: no gameplay formula change; future pitcher-usage offseason state review only.
- 02: no rating/Talent change.
- 04: no event catalog change; existing pending-event contract reused.
- 06: optional later consumption of SeasonFinalizationResult; no blocking UI work.
- 08: no blocking data requirement for v1.

## NEXT_ACTION
- Hand PR #38 to 05 for long-run lifecycle validation.
- Hand PR #38 to 07 for final integration/rebase/merge against latest main.
- Do not tune growth, retirement, roster, gameplay, or rating coefficients in this batch.

## RELATED_PRS
- #38 Growth/Career: Production Season Lifecycle Bridge v1

## RELATED_BRANCHES
- feature/production-season-lifecycle-v1

## GATES
- GROWTH_CAREER_AUDIT = PASS
- FIRST_PRODUCTION_BATCH_SELECTION = PASS
- PRODUCTION_SEASON_LIFECYCLE_CONTRACT = PASS
- PRODUCTION_SEASON_LIFECYCLE_IMPLEMENTATION = PASS
- SAVE_LOAD_IDEMPOTENCY_REGRESSION = PASS
- HEADLESS_FINALIZATION_EQUIVALENCE = PASS
- FULL_UNIT_SUITE = PASS
- FINAL_CI = PASS
- CURRENT_MAIN_INTEGRATION = OPEN
- LONG_RUN_LIFECYCLE_VALIDATION = OPEN
- REALISTIC_PLAYING_TIME_OPPORTUNITY = OPEN
- PERSISTENT_INJURY_DEVELOPMENT = OPEN
- CONTRACT_FA_TRADE_POSTING = OPEN
