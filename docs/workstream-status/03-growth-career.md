# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@44cfcbad694e4d393ffe568ad0e3121628129844
STATE: CONTRACT_READY
CURRENT_TASK: Convert growth/career audit into first production implementation contract
RESULT: NEXT_BATCH_SELECTED

## LAST_COMPLETED
- Re-audited the current main growth/career path from high school through retirement.
- Confirmed existing production foundations for high school/draft, FARM/FIRST movement, probabilistic growth, development profiles, coach effects, playing-time growth input, aging/decline, retirement, career history, and save/load.
- Confirmed no production domain implementation for contract, FA, trade, posting, or service time.
- Selected the first bounded production batch: Production Season Lifecycle Bridge.
- Rechecked concurrent main movement after the audit; intervening commits only changed workstream status files 02 and 04, so no growth/career production code changed.

## CURRENT_STATE_MACHINE
- HIGH_SCHOOL: age 18 player runs high-school tournaments and accumulates high-school production.
- DRAFT: draft evaluation uses high-school production plus noisy scouting; selected or developmental signing assigns a KBO team.
- PRO / SEASON_START: a ProSeasonSession is created with FARM or FIRST initial assignment.
- PRO / IN_SEASON: scheduled games update participation, stats, fatigue, injury, form, events, and 10-game FARM/FIRST reconsideration.
- PRO / SEASON_FINISHED: games_completed reaches 144, but the canonical ProductionAdvanceService currently has no explicit bridge into career season finalization.
- HEADLESS FINALIZATION: CareerEngine.finish_pro_season() already owns award determination, SeasonRecord append, GrowthExperience construction, season growth, age +1, trait/coach offseason processing, year +1, session reset, modifier reset, and fatigue carryover.
- RETIREMENT: CareerEngine.should_retire() evaluates age, recent first-team PA, ability, debut failure, and severe injury; retire() enters RETIRED.

## PRIORITIZED_GAPS
### CRITICAL
- Canonical production date advance can complete game 144 without a first-class season-finalization / next-season transition operation. Long-running production career progression is therefore not closed even though the headless career loop is.

### HIGH
- FARM/FIRST opportunity uses aggregate team depth, current ability, recent OPS noise, and fixed reconsideration cadence rather than explicit roster competition / lineup opportunity.
- Injury affects development mainly through missed playing time; there is no general persistent post-injury development consequence contract.
- Contract, FA, trade, posting, and service-time systems do not exist.

### MEDIUM
- Peak is emergent from age bias, development profile, talent, experience, coaches, events, and randomness, but the current peak-age distribution remains a calibration concern.
- Career history stores seasons, growth, injuries, traits, teams, awards, and events, but there is no explicit lifecycle transition history.
- Awards have a production hook but competitor abstraction remains provisional.

### LOW
- Existing growth unit tests cover determinism/basic invariants more strongly than long-run distribution invariants; this is primarily a 05 validation coverage gap rather than a blocker for the first lifecycle bridge.

## SELECTED_NEXT_IMPLEMENTATION_BATCH
NAME: Production Season Lifecycle Bridge v1
OWNER: 03 - Growth & Career
INTEGRATION_OWNER: 07 - Integration & GitHub

RATIONALE:
- Highest-value current gap: production gameplay reaches a hard season boundary but cannot canonically progress into the next season.
- Reuses existing CareerEngine.finish_pro_season() semantics rather than inventing new growth, rating, gameplay, or event formulas.
- Does not require KBO contract/FA/service-time policy before implementation.
- Does not change 01 gameplay probabilities or 02 rating scale/inference.
- Does not duplicate 04 event narrative ownership.
- Has deterministic, testable, save/load-visible outputs for 05.

## EXACT_CONTRACT
### State model
Use the existing CareerEngine.phase plus ProSeasonSession as canonical domain state. Do not add a parallel career state machine in v1.

Required lifecycle states/conditions:
1. PRO_IN_SEASON: current_session exists and games_completed < KBO_FIRST_TEAM_GAMES.
2. PRO_SEASON_COMPLETE: current_session exists and current_session.finished is true.
3. PRO_READY_NEXT_SEASON: previous session has been finalized exactly once, engine.year advanced exactly once, player.age advanced exactly once, and current_session is None.
4. RETIRED: existing phase == RETIRED.

### New fields
Minimize new persisted fields.
- Preferred v1: no new Player rating/growth fields.
- Add a season-finalization identity/guard only if implementation proves existing state cannot guarantee idempotency across service recreation/save-load. Preferred representation: finalized season year metadata in career state, not a gameplay field.
- Do not add contract/service-time/FA fields in this batch.

### New domain operation
Introduce one explicit canonical operation with semantics equivalent to:
`finalize_completed_pro_season()`

Preconditions:
- phase == PRO
- current_session is not None
- current_session.finished == True
- no unresolved pending event; either resolve through existing event contract before finalization or reject finalization explicitly

Effects, in this exact logical order unless tests demonstrate an existing required order:
1. determine and persist season awards using existing logic
2. append the completed SeasonRecord exactly once
3. construct GrowthExperience from completed FIRST/FARM PA
4. apply existing season growth exactly once
5. apply existing offseason trait-change hook
6. apply existing coach-replacement hook
7. increment engine.year exactly once
8. clear current_session
9. clear season modifiers and form state
10. apply existing fatigue offseason carryover
11. evaluate retirement only through an explicit caller-controlled transition step; do not silently add a second retirement RNG draw inside generic service construction

`finish_pro_season()` should delegate to the same finalization primitive after it has completed remaining games, preventing duplicate lifecycle implementations.

### ProductionAdvance integration
- ProductionAdvanceService must expose season-boundary state instead of allowing an opaque dead end after game 144.
- The first implementation may expose an explicit `finalize_season()` / `advance_to_next_season()` operation rather than automatically consuming offseason RNG after the 144th game.
- Creating/recreating ProductionAdvanceService must never itself finalize a season or consume lifecycle RNG.
- Starting the next season must rebuild the schedule from the incremented engine.year and attach a fresh advance state without replaying prior-season games.
- Do not alter ProductionGameProvider or gameplay probability formulas.

### Persistence
- Existing Player, CareerEngine, current_session, RNG state, advance_state, and pitcher_usage_state serialization remain authoritative.
- A save at game 143 must resume at game 143 with identical next-game RNG behavior.
- A save immediately after game 144 but before finalization must remain finalizable exactly once after load.
- A save immediately after finalization must load with incremented player age/year and no current_session, without reapplying growth/awards.
- If an idempotency marker is added, it must be serialized in CareerEngine.as_dict()/restore_state().

### Backward compatibility
- Current SAVE_VERSION remains unchanged if no new required persisted field is introduced.
- If a new finalization marker is introduced, old saves must infer a safe default from current_session/year/player.seasons and must never fabricate a completed season or replay growth.
- Existing save versions 1/2/3 must continue to load unless 07 determines a version bump is unavoidable.

### Deterministic RNG behavior
- Finalization is the only operation in this batch allowed to consume growth/award/trait/coach RNG at season boundary.
- Service constructors, read-only summaries, save, and load consume zero RNG draws.
- Repeated finalization calls must either return the already-finalized result without consuming RNG or raise a deterministic domain error before consuming RNG.
- Headless finish_pro_season and production `144 games + finalize` must be seed-equivalent for all lifecycle-owned operations when fed equivalent completed SeasonRecord/session state.

### UI exposure needs
03 does not implement UI.
Minimum 06-facing contract after implementation:
- season_complete: bool
- completed_year
- age_before / age_after when finalized
- growth deltas / ability before-after from GrowthResult
- awards earned
- retirement_eligible/result only when explicit retirement transition is evaluated
- next_season_year when career continues
No frontend redesign is required for this batch.

### Event hooks
- Reuse existing pending-event resolution rules.
- No new narrative event catalog entries.
- Existing coach-change/offseason records remain valid.
- Future 04 integration may consume a generic season-finalized lifecycle hook, but v1 must not require 04 changes.

## REQUIRED_TESTS
### Domain tests
- cannot finalize before 144 completed games
- completed season finalizes exactly once
- SeasonRecord appended once
- growth applied once
- player age increments once
- engine year increments once
- current_session cleared once
- awards not duplicated
- season modifiers/form reset according to existing behavior
- pending-event behavior is explicit and deterministic
- repeated finalization consumes no additional RNG

### Production integration tests
- 143 -> save/load -> game 144 -> finalize -> next season works
- game 144 -> save/load -> finalize works exactly once
- finalize -> save/load -> next season creates a fresh schedule/year/session
- week/month/game composition up to season boundary remains consistent
- ProductionAdvanceService reconstruction does not consume RNG or auto-finalize
- existing PR #33 production regression tests remain green

### Equivalence test
- For the same seed and equivalent completed season state, legacy/headless finish_pro_season finalization and the new production finalization primitive produce identical growth result, age/year transition, awards, traits/coaches, and RNG post-state.

## MONTE_CARLO_VALIDATION_FOR_05
This first batch is lifecycle integration, not tuning. 05 should validate regression/equivalence rather than optimize coefficients.

Required outputs:
- N >= 1,000 full careers using the new canonical season-boundary path when runtime permits
- zero duplicate/missing finalized seasons
- seasons count == number of successful finalization transitions
- age increment count == finalized season count until retirement
- year increment count == finalized season count
- save/load interruption at random season-boundary checkpoints produces identical terminal career state for matched seeds
- old headless vs new lifecycle path distribution comparison for debut age, peak age, peak ability, retirement age, career PA, FARM PA, injuries, awards
- distribution deltas should be approximately zero except where the old path was structurally unreachable from production advance
- deterministic replay mismatch rate must be 0 for matched seed/state tests

Do not tune growth/retirement/roster coefficients in this validation batch.

## DATA_REQUIREMENTS_FOR_08
NONE BLOCKING for Production Season Lifecycle Bridge v1.

Future requests before subsequent systems:
- KBO registered-player / first-team-Futures roster movement rules and practical opportunity constraints for roster-depth redesign.
- KBO service-time and FA eligibility rules, contract renewal/arbitration-like mechanisms if applicable, release/waiver rules, and posting eligibility/process before contract/FA/posting implementation.
- Historical debut/retirement/tenure distributions by position for later calibration, not for this lifecycle bridge.

## DEPENDENCIES
- 00: approve Production Season Lifecycle Bridge v1 as the next cross-system implementation priority.
- 01: no formula change; only regression protection that game results remain unchanged before the season boundary.
- 02: no rating-scale or Talent change.
- 04: existing event/pending-event hooks reused; no new narrative ownership.
- 05: lifecycle equivalence + long-run distribution regression validation after implementation.
- 06: consume season-complete/finalization summary later; no blocking UI work.
- 07: integrate ProductionAdvanceService season-boundary operation, persistence compatibility, branch/PR/CI.
- 08: no blocking data for v1; research required for later roster/contract/FA/posting batches.

## BLOCKERS
- No external-data blocker for the selected v1 contract.
- Implementation must settle whether existing state alone is sufficient for exact-once finalization; add a persisted guard only if necessary.

## OPEN_ITEMS
- Exact naming/location of the finalization primitive and result DTO.
- Whether retirement evaluation belongs in the same explicit offseason command or a separate command; requirement is that it occurs at most once per season and never from a constructor/read operation.
- Post-v1 priority between realistic playing-time opportunity, persistent injury-development effects, and contract/service-time foundation requires 00 ordering plus 05/08 inputs.

## NEXT_ACTION
- 00 approves/adjusts Production Season Lifecycle Bridge v1.
- After approval, implement in one bounded 03 feature branch with 07 integration review.
- Run targeted lifecycle/save-load tests locally first, then 05 regression Monte Carlo, then one consolidated PR/CI checkpoint.

## RELATED_PRS
- None assigned for this contract yet.

## RELATED_BRANCHES
- main

## GATES
- GROWTH_CAREER_AUDIT = PASS
- FIRST_PRODUCTION_BATCH_SELECTION = PASS
- PRODUCTION_SEASON_LIFECYCLE_CONTRACT = PASS
- PRODUCTION_SEASON_LIFECYCLE_IMPLEMENTATION = OPEN
- LONG_RUN_LIFECYCLE_VALIDATION = OPEN
- REALISTIC_PLAYING_TIME_OPPORTUNITY = OPEN
- PERSISTENT_INJURY_DEVELOPMENT = OPEN
- CONTRACT_FA_TRADE_POSTING = OPEN
