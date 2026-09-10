# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@9aa458735721570581f4968060590acf3fc9c957
STATE: IMPLEMENTED_AWAITING_LONG_RUN_VALIDATION
CURRENT_TASK: Production Season Lifecycle Bridge v1 implementation
RESULT: IMPLEMENTATION_PASS_CI_PENDING_FINAL_GATE

## LAST_COMPLETED
- Implemented the approved Production Season Lifecycle Bridge v1 on `feature/production-season-lifecycle-v1`.
- Added canonical `CareerEngine.finalize_completed_pro_season()` and `SeasonFinalizationResult`.
- Refactored `finish_pro_season()` to delegate lifecycle-owned finalization to the same primitive.
- Added explicit `ProductionAdvanceService.finalize_season()` and `start_next_season()` boundary operations.
- Added lifecycle/save-load/idempotency/headless-equivalence regression tests.
- PR #38 opened against main.

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
- No new persisted lifecycle marker was required.
- Pre-finalization identity is represented by an existing finished `current_session`.
- Successful finalization clears `current_session`, so a repeated call rejects before any RNG-consuming work.
- A game-144 save preserves the finished session and is finalizable after load.
- Production finalization removes stale `advance_state`; a finalized save therefore cannot replay the completed production-season aggregate as the next season.
- SAVE_VERSION remains unchanged; existing save versions remain supported through existing persistence defaults.

### Production advance bridge
- `ProductionAdvanceService.season_complete` exposes the explicit boundary.
- `finalize_season()` invokes only the canonical CareerEngine finalization primitive.
- `start_next_season()` explicitly creates the next ProSeasonSession, rebuilds the schedule from incremented engine.year, and attaches a fresh production advance state.
- Service construction does not finalize a completed season.
- Existing gameplay probability/formula providers are unchanged.

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

## TEST_COVERAGE_ADDED
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
IMPLEMENTATION_HEAD_BEFORE_STATUS_UPDATE: 411529269b042708bb45fadbedb181f4b8067a6e
WORKFLOW: tests run #585
- Python compile: PASS
- full unit-tests step: PASS
- auto career smoke: PASS
- balance smoke: PASS
- web build/tests: PASS
- high-school/draft calibration gate: still running at status-update time

Local clone/full-suite-before-push could not be performed because the execution environment could not resolve github.com. Validation therefore used one PR CI checkpoint after the bounded implementation push.

## UNCHANGED / OUT_OF_SCOPE
- gameplay probabilities
- hitter/pitcher formulas
- rating scale
- Talent semantics
- event catalog
- contract / FA / service-time / trade / posting

## REMAINING_OPEN_ITEMS
- 05 long-run lifecycle equivalence/distribution validation.
- 07 integration review and merge decision for PR #38.
- Realistic FARM/FIRST playing-time opportunity redesign remains separate.
- Persistent injury-development consequences remain separate.
- Contract/FA/trade/posting/service-time foundation remains separate.
- Pitcher-usage offseason reset semantics should be reviewed by 01/07 when multi-season production play is integrated; this batch intentionally did not alter gameplay usage formulas/state policy.

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
- distribution deltas should be approximately zero because no tuning/formula changes were made

## DEPENDENCIES
- 05: long-run deterministic/distribution validation.
- 07: PR #38 integration review, current-main compatibility, merge/CI.
- 01: no formula work; only review future pitcher-usage offseason state semantics if needed.
- 02: no rating/Talent changes.
- 04: no event catalog changes; existing pending-event contract reused.
- 06: optional later consumption of SeasonFinalizationResult; no blocking UI work.
- 08: no blocking data requirement for this v1 implementation.

## NEXT_ACTION
- Confirm PR #38 final CI conclusion.
- Hand PR #38 to 05 for long-run validation and 07 for integration review.
- Do not tune growth/retirement/roster coefficients in this batch.

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
- FINAL_CI = OPEN
- LONG_RUN_LIFECYCLE_VALIDATION = OPEN
- REALISTIC_PLAYING_TIME_OPPORTUNITY = OPEN
- PERSISTENT_INJURY_DEVELOPMENT = OPEN
- CONTRACT_FA_TRADE_POSTING = OPEN
