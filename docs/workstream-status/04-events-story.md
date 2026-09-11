# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-11
TASK_START_MAIN: `b4e836eb747aea42a5782fed71c39fcb3a982f17`
LATEST_INTEGRATION_BASE: `58f662324b99505ae6f73bb8188cdfb65224157d`
IMPLEMENTATION_HEAD: `2d6ec0cadadc3522897cc3bd13f87a50955e170d`
STATE: ACTIVE
CURRENT_TASK: P1 Canonical Progression Event Timeline v1
RESULT: PASS_WITH_OPEN_EVENT_CATEGORIES

## LAST_COMPLETED
- Implemented CanonicalEventDTO v1 on `feature/p1-canonical-event-timeline-v1` / PR #53.
- Rebased/merged latest main before final validation; PR #53 is mergeable against current main.
- Added deterministic per-command event capture before/after each canonical game advance without changing gameplay/growth/roster formulas.
- WEEK/MONTH now preserve every captured internal-game event instead of reconstructing career transitions from period-final state.
- Existing FastAPI mutation envelope is unchanged; `AdvanceResultViewModel.notable_events` passes canonical DTO dictionaries through its existing event serialization path.
- Final CI run #765 (`34582277850`) is fully green: packaging/compile, external PostgreSQL store, Vercel entrypoint, API vertical slice, related production integration, full unit suite, auto-career smoke, balance smoke, draft calibration/artifact, web build/tests.

## CANONICAL_EVENT_DTO_V1
Implemented fields:
- `event_id`
- `event_type`
- `category`
- `occurred_at`
- `season`
- `game_number`
- `sequence`
- `title`
- `summary`
- `importance`
- `player_id` nullable
- `team_id` nullable
- `related_entity_ids`
- `state_effects`
- `rating_changes`
- `injury_effect`
- `trait_changes`
- `source_command`
- `presentation_priority`
- `persistence`
- `dedupe_key`
- additive ordering metadata: `phase`, internal `source_ordinal`

No random UUID is used.

## NORMALIZED_SOURCES
Production timeline currently normalizes only existing semantics:
- `GamePerformance.notable_events` -> transient `gameplay_notable` events.
- append-only `player.career_history` delta -> persistent roster/debut/recovery/system-mirror events.
- `player.event_history` delta -> persistent v0.4 career-event result including stat/rating, injury and Trait changes already recorded there.
- game-origin `player.injury_history` delta -> persistent injury-start facts; event-caused injuries are not duplicated because their authoritative event_history result is used instead.
- authoritative form before/after state -> transient `form_changed` event when final postgame form differs.

Existing draft/pro-entry facts remain durable in career_history but normally occur during career creation, not game/week/month advance.

## RECOVERY_PERSISTENCE
Generic injury recovery previously cleared state without a durable fact.
P1 v1 adds an observational `injury_recovered` system-mirror entry to the existing `career_history` only when an injury existed before the canonical game advance and is cleared after recovery.
- no injury formula change
- no recovery-speed change
- deterministic dedupe key: season + game + injury identity
- existing career_history is reused; no second persistent event store/table
- RNG-free deterministic template news

## COMPOSITE_CAPTURE
`CareerGameAdvanceProvider` now owns one mutation-local timeline cursor:
- period start snapshots authoritative history lengths + form/injury state before lifecycle setup;
- every internal `advance_game()` captures new source facts after gameplay/postgame processing;
- cursor advances after each game, preventing already-observed source facts from being emitted twice;
- composite provider accumulates every internal-game canonical event;
- finalization performs deterministic sort + dedupe + contiguous `sequence` assignment.

This preserves intermediate transitions such as:
`FARM -> FIRST -> FARM`
even when the period starts and ends in FARM.
Period-level final roster comparison is not used as the canonical event source.

## ORDERING_AND_DEDUPE
Canonical order:
1. `occurred_at`
2. `game_number`
3. phase rank: `pre_game < in_game < post_game < off_day < lifecycle`
4. source-local ordinal
5. deterministic `event_id`

After sorting:
- first occurrence of each deterministic `dedupe_key` is retained;
- `sequence` is reassigned contiguously `0..N-1`;
- `source_command` is fixed to `next_game`, `week`, or `month` for that mutation.

Persistent career events reuse existing source-history logical/dedupe identities. Transient gameplay IDs derive from deterministic season/game/phase/ordinal/type coordinates.

## TRANSIENT_VS_PERSISTENT
Transient response-only:
- gameplay notable markers
- current form-change presentation fact

Persistent source histories:
- career_history: roster promotion/demotion, debut, recovery and existing early-career spine
- event_history: v0.4 event resolution, including represented rating/Trait/injury effects
- injury_history: game-origin injury starts

Transient DTOs are never appended to persistent histories solely for presentation.
No Neon/event table/schema was added.

## FARM_SEMANTICS
FARM timeline events describe only authoritative roster state transitions.
They do not claim or imply a newly implemented full second-team league simulation.

## VALIDATION
New `tests/test_event_timeline_v1.py` covers:
- empty/no-event canonical list
- deterministic same-day ordering
- duplicate suppression
- dense sequence assignment
- FARM -> FIRST -> FARM retaining both transitions
- deterministic transient gameplay identity
- recovery persistent exactly-once
- recovery save/load persistence
- same-seed + same-actions byte-stable canonical event facts
- WEEK/MONTH dense ordered sequences and correct `source_command`
- partial period near season end stops at committed final game

Existing suites retained and passed:
- WEEK/MONTH exact canonical game composition
- API same-idempotency-key exact response replay
- stale revision 409 before committed mutation
- external SessionStore CAS/idempotency/restart tests
- career spine history/dedupe/save-load tests
- existing v0.4 event tests

Final validation: workflow #765 (`34582277850`) = PASS across all jobs/steps.

## TRANSACTIONAL_BEHAVIOR
No FastAPI/store code changed.
Existing transactional semantics remain authoritative:
- stale revision -> mutator is not committed, so no new history/timeline commit;
- success -> state/history and response are generated in one existing mutation transaction;
- same idempotency key/fingerprint -> stored response replay, no simulation rerun and no duplicate persistent history;
- save/load preserves persistent histories and RNG state.

## 07_HANDOFF
PR #53 supplies the domain/source event contract that 07 status was blocking on.
After merge, 07 should:
- treat `mutation.result.notable_events` as CanonicalEventDTO v1 dictionaries;
- preserve backend array order/sequence exactly;
- update typed HTTP/frontend transport DTO definitions from legacy `{date,kind,message}` to the additive canonical shape;
- keep timeline generation inside the existing transactional mutator;
- make no new Neon table/event store;
- retain current idempotency and revision semantics.

07 must not re-detect roster/injury/form/event semantics from final snapshots.

## 06_HANDOFF
06 should consume `mutation.result.notable_events: CanonicalEventDTO[]` after 07 transport typing is updated.
UI requirements:
- backend order/`sequence` is authoritative;
- support empty, single and multi-event results;
- multiple events on one game/date are valid;
- never collapse to the last event or one event per category;
- `importance` / `presentation_priority` control visual emphasis only, not semantic filtering;
- display FARM promotion/demotion as roster-state movement only, not full minor-league simulation;
- do not infer narrative triggers from final Dashboard/Season state.

04 does not implement UI.

## UNSUPPORTED_OR_OPEN_EVENT_CATEGORIES
No placeholder production events were fabricated for absent semantics.
Still OPEN:
- off-day event source channel
- lineup/role-change canonical career semantics
- rivalry
- milestone / record
- award timeline during explicit season finalization
- contract / FA / transfer
- retirement timeline
- manager-specific interactions
- complete intra-game source-fact emission for every possible intermediate form state; v1 emits deterministic postgame form delta plus any causal v0.4 event result
- subsystem-wide RNG stream isolation outside the already RNG-free observational/template layer

## RELATED_PRS
- #39 — early-career observational spine (merged before this task)
- #50 — P1 Growth/Career production advance breadth (merged)
- #52 — P1 UI/backend mutation contract expansion (merged)
- #53 — P1 Canonical Progression Event Timeline v1 (current implementation)

## NEXT_ACTION
- Merge/integrate PR #53 through 07.
- 07 updates transport typings to CanonicalEventDTO v1 without changing transaction semantics.
- 06 then exposes week/month controls and renders ordered event timelines.
- Next 04 narrative-domain batch after P1 integration: Award / Milestone timeline only after authoritative lifecycle semantics are defined.

## GATES
- P1_CANONICAL_EVENT_DTO_V1 = PASS
- P1_EVENT_ID_DETERMINISM = PASS
- P1_COMPOSITE_EVENT_RETENTION = PASS
- P1_ORDERING_AND_DEDUPE = PASS
- P1_TRANSIENT_PERSISTENT_POLICY = PASS
- P1_RECOVERY_PERSISTENCE = PASS
- P1_SAVE_LOAD_HISTORY = PASS
- P1_SAME_SEED_TIMELINE_DETERMINISM = PASS
- P1_TRANSACTIONAL_EVENT_SAFETY = PASS_INHERITED_AND_REGRESSION_GREEN
- P1_FASTAPI_CHANGE_REQUIRED = NO
- P1_NEON_SCHEMA_CHANGE_REQUIRED = NO
- P1_UI_IMPLEMENTATION = NOT_04_SCOPE
- P1_EVENT_TIMELINE_PRODUCTION_CONTRACT = PASS
- P1_UNSUPPORTED_EVENT_CATEGORIES = OPEN
