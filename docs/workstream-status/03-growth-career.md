# 03 - Growth & Career

WORKSTREAM: 03 - Growth & Career
UPDATED_AT: 2026-09-11
TASK_START_MAIN: b4e836eb747aea42a5782fed71c39fcb3a982f17
CURRENT_MAIN_AT_PR_OPEN: 58f662324b99505ae6f73bb8188cdfb65224157d
STATE: P1_SOURCE_FACTS_IMPLEMENTED
CURRENT_TASK: P1 Canonical Career Event Source Facts
RESULT: PASS

## SOURCE_OF_TRUTH_AUDIT
- `next_game`, week, and month all use `ProductionAdvanceService` and the same canonical internal game path.
- `AdvanceSummary.major_events` previously retained only gameplay notable strings; it was not an authoritative career transition timeline.
- period-level roster before/after comparison could lose intermediate transitions such as FARM -> FIRST -> FARM.
- `career_history` already persisted draft/pro-entry/callup/debut/demotion facts.
- `injury_history` already persisted injury creation, but ordinary recovery completion was only a state clear.
- form transitions were authoritative state but had no canonical transition fact.
- event resolutions can directly mutate injury, form, traits, and ratings, so source facts must also be mirrored at `resolve_pending_event()` rather than inferred from final snapshots.
- canonical season finalization already owns growth, trait offseason hooks, age/year progression, and session clearing.

Task-start main was `b4e836eb747aea42a5782fed71c39fcb3a982f17`. Main advanced by one 07 status-document commit before PR open; no Growth/Career backend conflict was introduced.

## IMPLEMENTATION
BRANCH: `feature/p1-career-source-facts`
PR: #54 `Growth/Career: P1 canonical career source facts`
IMPLEMENTATION_HEAD: `0843e1243468475b8f22e20688a64a5a021b0788`

New source contract:
`src/career_source_facts.py` defines presentation-free `CareerSourceFact` with:
- `fact_type`
- `season`
- `game_number`
- `simulated_date`
- `phase`
- `local_ordinal`
- `player_identifier`
- `team_identifier`
- `before`
- `after`
- `authoritative_state_delta`
- `persistence_hint`
- `existing_identity`

No narrative title, summary, importance, presentation priority, HTTP DTO, or random presentation metadata is produced by 03.

## AUTHORITATIVE_SOURCE_FACTS
### In-season roster/debut
- `roster_promotion`: FARM -> FIRST authoritative roster-state transition.
- `roster_demotion`: FIRST -> FARM authoritative roster-state transition.
- `first_team_debut`: first actual FIRST-level game appearance.
- Existing `career_history` dedupe identity is reused via `existing_identity` where available.

### Injury/recovery
- `injury_created`: ordinary gameplay injury creation at the state mutation point.
- `injury_recovery_completed`: ordinary recovery transition from active injury to no injury.
- event-resolution direct mutation also exposes `injury_created`, `injury_cleared`, or `injury_changed` as applicable.
- gameplay injury creation reuses `injury_history` identity; event-driven injury mutation reuses its `event_history` identity.

### Form / Trait / rating-development
- `form_transition`: emitted only when authoritative form state actually changes.
- `trait_gained` / `trait_lost`: emitted for offseason trait changes and event-driven trait changes.
- `event_rating_change`: existing event resolution stat deltas, without changing rating calibration/formulas.
- `season_growth`: existing `GrowthResult` deltas and ability before/after from canonical season finalization.

### Lifecycle
- `season_finalized`: canonical completed-season transition including year, age, and active-session state delta.
- `SeasonFinalizationResult` now exposes `source_facts` in addition to the existing record/growth/award data.

## COMPOSITE_ADVANCE_SEMANTICS
- Each production game starts a source-fact capture context with the exact simulated game date.
- transition facts are emitted at the authoritative mutation point, not reconstructed from the period-end snapshot.
- `CareerGameAdvanceProvider` drains per-game facts after post-game career processing.
- `CompositionalAdvanceOrchestrator` returns all collected facts in `AdvanceSummary.source_facts`.
- WEEK/MONTH therefore preserve all intermediate facts in internal game execution order.
- FARM -> FIRST -> FARM in one period produces two distinct source facts even though the final roster snapshot is FARM.
- local ordinal is deterministic within a capture context; game date/game number provide deterministic cross-game coordinates.
- source-fact buffers are transient and are not added to save serialization. Save/load determinism comes from authoritative state/RNG/history; replaying the same next action produces the same ordered facts.
- completed-season rejection occurs before gameplay/career mutation and produces no source fact.
- near season end, only actually simulated remaining games can emit facts.

## EXISTING_PERSISTENCE_IDENTITIES
`persistence_hint` / `existing_identity` are hints for 04 normalization and do not create a second durable truth.

Current reusable channels:
- roster promotion/demotion/debut -> `career_history`
- gameplay injury creation -> `injury_history`
- event-driven transitions -> `event_history`
- offseason Trait changes -> `trait_history`
- season growth -> `growth_history`

Ordinary injury recovery currently has no pre-existing durable history identity; its source fact is authoritative for the current mutation but retention policy remains 04-owned.

## TEST_COVERAGE
New: `tests/test_p1_career_source_facts.py`

Covers:
- one roster transition source fact
- multiple transition facts in the same week
- FARM -> FIRST -> FARM within one month with both facts retained
- gameplay injury creation fact
- injury recovery-completion fact
- save/load + same action produces identical ordered source facts and terminal state
- deterministic date/game/local-ordinal coordinates
- completed-season failed advance produces no fact, state mutation, or RNG change
- partial period near game 144 contains only facts for the committed remaining game
- season finalization exposes `season_growth` and exactly one `season_finalized` fact

Existing regression coverage retained:
- P0 API vertical slice
- durable store / production config tests
- production game provider and week/month composition
- season lifecycle bridge
- full Python test discovery
- auto-career smoke
- balance smoke
- high-school/draft calibration
- web build/tests

## CI
Workflow: tests #763
Implementation head: `0843e1243468475b8f22e20688a64a5a021b0788`

PASS:
- Vercel Python packaging
- Python compile
- external durable store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice tests
- related production integration tests
- full Python unit suite, including new source-fact tests
- auto-career smoke
- balance smoke
- high-school/draft calibration gate
- web build/tests

## EXACT_04_HANDOFF
04 should consume only authoritative facts returned by 03:
- game/week/month: `AdvanceSummary.source_facts`
- season finalization: `SeasonFinalizationResult.source_facts`

04 may then define CanonicalEventDTO normalization, deterministic sorting/dedupe, title/summary, importance, presentation priority, and retention policy.

Rules for normalization:
- do not infer transitions from final snapshots when a source fact is present;
- preserve every distinct fact from a composite period, including reversible FARM/FIRST transitions;
- use `simulated_date`, `game_number`, `phase`, and `local_ordinal` as source ordering coordinates;
- reuse `existing_identity` when a durable history identity already exists;
- treat `persistence_hint` only as the known current source channel, not as an instruction to duplicate persistence;
- ordinary recovery has no existing durable identity, so 04 must decide retention without fabricating a second simulation transition;
- do not alter simulation state/RNG while normalizing or rendering.

## EXACT_07_HANDOFF
- 07 should normalize/transport returned source facts inside the existing authoritative transaction mutator.
- stale revision / failed mutation must commit neither simulation state nor an event response.
- idempotency replay must return the stored response rather than re-running simulation and regenerating facts.
- no save-schema or Neon schema change is required for this 03 source-fact layer.
- HTTP DTO shape remains 07/04-owned.

## UNAVAILABLE / NOT INVENTED
No new semantics were invented for:
- rivalry
- contract / salary / service time
- FA / posting
- transfer/trade/release
- milestone / record tracking
- full Futures/minor-league game simulation
- canonical retirement event timeline

Retirement state logic exists elsewhere, but a retirement source-fact contract was not added in this bounded P1 batch because it is not part of current production advance/finalization command flow.

## OUT_OF_SCOPE / UNCHANGED
- FastAPI routes/request DTOs
- SessionStore / Neon / transaction implementation
- frontend
- CanonicalEventDTO presentation schema
- gameplay probabilities and hitter/pitcher formulas
- rating scale/calibration
- event catalog probabilities/outcomes
- full second-team league simulation

## GATES
- P1_SOURCE_FACT_CONTRACT = PASS
- ROSTER_TRANSITION_FACTS = PASS
- FIRST_TEAM_DEBUT_FACT = PASS
- INJURY_CREATION_FACT = PASS
- RECOVERY_COMPLETION_FACT = PASS
- FORM_TRANSITION_FACTS = PASS
- TRAIT_AND_RATING_FACTS = PASS
- GROWTH_LIFECYCLE_FACTS = PASS
- COMPOSITE_FACT_RETENTION = PASS
- SAVE_LOAD_FACT_DETERMINISM = PASS
- SEASON_BOUNDARY_PARTIAL_PERIOD = PASS
- COMPLETED_SEASON_NO_SIDE_EFFECT = PASS
- FULL_RELEVANT_TESTS = PASS
- 04_CANONICAL_EVENT_NORMALIZATION = OPEN
- 07_TRANSACTIONAL_HTTP_TRANSPORT = OPEN
- FUTURE_UNAVAILABLE_SYSTEM_FACTS = OPEN

## NEXT_ACTION
- 04 normalizes `source_facts` into the canonical presentation/event DTO without changing 03 simulation semantics.
- 07 transports the normalized event timeline within existing CAS/idempotency transaction boundaries.
- 03 should only extend the source-fact vocabulary when new authoritative career semantics are actually implemented.
