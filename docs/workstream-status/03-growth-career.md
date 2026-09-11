# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-11
TASK_START_MAIN: f336b9be10f252300971be3d146b51ad7ff91537
CURRENT_MAIN_AT_PR_OPEN: 4a945793715fdfaee6c91a33c5c24a3970e0402d
STATE: P1_ADVANCE_BREADTH_IMPLEMENTED
CURRENT_TASK: P1 Career Backend Advance Breadth
RESULT: PASS

## SOURCE_OF_TRUTH_AUDIT
Current production progression architecture on task start:
- `ProductionAdvanceService.advance_one_game()` is the canonical P0 game mutation primitive used by the production API.
- `advance_one_week()` and `advance_one_month()` already compose scheduled games through the same `CareerGameAdvanceProvider` and `CompositionalAdvanceOrchestrator` path.
- week/month bulk progression is structurally the same gameplay path as repeated next-game calls; no separate gameplay simulator exists.
- `CareerEngine.finalize_completed_pro_season()` owns canonical season finalization.
- `ProductionAdvanceService.finalize_season()` delegates to that primitive.
- `start_next_season()` creates a fresh ProSeasonSession/schedule/advance state after finalization.
- persistence serializes engine RNG, session state, production advance state, and pitcher-usage state.

Main advanced by one documentation-only 05 Balance Lab commit while this task was being prepared; no Growth/Career backend code changed between task-start main and the PR base.

## CHOSEN_P1_BREADTH
Approved for 07 production exposure:
1. `next_game` -> existing `ProductionAdvanceService.advance_one_game()`
2. `next_week` -> existing `ProductionAdvanceService.advance_one_week()`
3. `next_month` -> existing `ProductionAdvanceService.advance_one_month()`

Not yet approved as a single automatic command:
- `season` / automatic finish-and-start-next-season transition

Reason for deferral:
- canonical explicit finalization/start-next-season primitives already exist and are tested;
- multi-season pitcher-usage offseason reset semantics are still a separate 01/07 integration concern;
- P1 breadth does not need to hide finalization + next-season lifecycle behind a new automatic command yet.

## COMMAND_SEMANTICS
### next_game
- simulate exactly the next scheduled game after the persisted production cursor;
- aggregate the game exactly once into season/career production state;
- preserve existing P0 behavior and formulas.

### next_week
- requested window is current production cursor through +7 calendar days;
- simulate every canonical scheduled game with `start < game_date <= start + 7 days`;
- game results, stats, events, roster effects, fatigue/injury, and pitcher-usage effects are exactly the composition of repeated `next_game` calls with the same seed/state;
- persistent cursor/end date remains the final simulated scheduled game date to preserve exact next-game composition semantics;
- if fewer than a full week's games remain before game 144, simulate only those remaining games and stop exactly at game 144.

### next_month
- requested window is current production cursor through one calendar month using existing `_add_one_calendar_month` semantics;
- simulate every canonical scheduled game in that window;
- state/RNG/stat effects are exactly the composition of repeated `next_game` calls;
- persistent cursor/end date is the final simulated scheduled game date;
- near season end, consume only remaining scheduled games and stop exactly at game 144.

### completed-season boundary
New domain error:
`SeasonCompleteError`

For `advance_one_game`, `advance_one_week`, and `advance_one_month`:
- if the current ProSeasonSession is already finished, reject before gameplay/RNG/stat/lifecycle mutation;
- do not auto-finalize;
- do not auto-start another session from a still-unfinalized completed season;
- caller must perform explicit canonical season finalization first.

This prevents a completed-season week/month call from becoming a successful no-op mutation that would still consume an API revision/idempotency operation when 07 exposes it.

## IMPLEMENTATION
BRANCH: `feature/p1-career-advance-breadth`
PR: #50 `Growth/Career: P1 production advance breadth`

Changed production behavior:
- `src/production_advance.py`
  - added `SeasonCompleteError`;
  - added shared `_ensure_advance_allowed()` guard;
  - game/week/month all reject completed-session advancement before mutation.

No FastAPI, store, persistence transaction, frontend, gameplay probability, rating, or event-catalog files were changed.

## TEST_COVERAGE
New: `tests/test_p1_career_advance_breadth.py`

Covers:
- next_week == exact repeated-next_game composition;
- next_month == exact repeated-next_game composition;
- week deterministic save/load equivalence;
- month deterministic save/load equivalence;
- week near season end stops exactly at game 144;
- month near season end stops exactly at game 144;
- completed-season game/week/month calls raise `SeasonCompleteError`;
- rejected completed-season calls preserve serialized state and RNG exactly;
- completed period advance does not finalize, apply growth, increment age/year, or start next season.

Existing regression coverage retained:
- `tests/test_production_integration_consolidation.py` week/month composition;
- `tests/test_season_lifecycle_bridge.py` finalization/save-load/exactly-once lifecycle;
- P0 API vertical-slice next_game path;
- production persistence and durable-store regression suites.

## CI
PR #50 implementation head before this status-only update:
`e9a1135d58c9792afc3dc4aa03d85455497f8de1`
Workflow: tests #711

PASS:
- Vercel Python packaging
- Python compile
- external durable store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice tests
- related production integration tests
- full Python unit suite
- auto-career smoke
- balance smoke
- high-school/draft calibration gate
- web build/tests

## EXACT_07_BACKEND_HANDOFF
03 owns only the following domain/service contract. 07 may wire it to HTTP/SessionStore CAS/idempotency without changing these semantics.

Suggested command mapping:
- API `next_game` -> `ProductionAdvanceService(engine).advance_one_game()`
- API `week` or product-facing `next_week` -> `ProductionAdvanceService(engine).advance_one_week()`
- API `month` or product-facing `next_month` -> `ProductionAdvanceService(engine).advance_one_month()`

Return source:
- use the returned `AdvanceSummary` plus normal authoritative post-mutation presentation/state;
- `AdvanceSummary.period_type`: `GAME`, `WEEK`, or `MONTH`;
- `games_played` is the exact number of simulated games in that mutation;
- `start_date` is the persisted cursor before the command;
- `end_date` is the final simulated scheduled-game date under the compositional production cursor contract;
- `season_after`, period stats, roster changes, and major events are post-command authoritative values.

Boundary/error mapping requirement:
- `SeasonCompleteError` means the current season reached game 144 and requires explicit lifecycle handling;
- 07 should map it to a non-retry-by-replay domain/API response and must not commit a mutated simulation payload for the rejected command;
- CAS/idempotency/revision behavior remains entirely 07-owned.

Do not expose a single automatic `season` command from this PR. For later season command design, compose only the existing canonical `finalize_season()` and `start_next_season()` after pitcher-usage offseason state policy is explicitly settled.

## BLOCKERS / OPEN
- Automatic `season` command: OPEN pending 01/07 pitcher-usage offseason reset/integration semantics.
- HTTP command wiring for week/month: OPEN, owned by 07.
- UI controls/results for week/month: OPEN, owned by 06.
- Long-run lifecycle validation remains separate 05 work.

## OUT_OF_SCOPE / UNCHANGED
- FastAPI routes/request models
- Neon / SessionStore / transaction semantics
- frontend
- gameplay probabilities
- hitter/pitcher formulas
- rating scale / Talent semantics
- event catalog
- contract / FA / service time / trade / posting

## GATES
- P1_ADVANCE_ARCHITECTURE_AUDIT = PASS
- NEXT_GAME_REGRESSION = PASS
- NEXT_WEEK_DOMAIN_CONTRACT = PASS
- NEXT_MONTH_DOMAIN_CONTRACT = PASS
- WEEK_COMPOSITION = PASS
- MONTH_COMPOSITION = PASS
- SAVE_LOAD_EQUIVALENCE = PASS
- SEASON_BOUNDARY_GUARD = PASS
- FULL_RELEVANT_PYTHON_TESTS = PASS
- P1_WEEK_MONTH_IMPLEMENTATION = PASS
- AUTOMATIC_SEASON_COMMAND = OPEN
- P1_HTTP_WIRING = OPEN
- P1_UI_WIRING = OPEN

## NEXT_ACTION
- 07 reviews/merges PR #50 and wires week/month into the existing authoritative CAS/idempotency mutation path.
- 06 may expose controls only after 07 publishes the production API contract.
- 03 does not tune gameplay/growth/rating formulas in this batch.
