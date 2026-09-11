# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-11
TASK_START_MAIN: `eb169941bf6f7c96ddb271ac430bffc06292e703`
DEPENDENCY_PR: #54 `Growth/Career: P1 canonical career transition source facts`
DEPENDENCY_PRODUCTION_HEAD: `9f93842cb2e86ebfe6fd76a7c4068f0e8a66c25d`
DEPENDENCY_MERGE_SHA: `38aea3b5f1cc525bb0d1107d3bb8d77db51cb107`
IMPLEMENTATION_BRANCH: `feature/p1-canonical-eventdto-source-facts`
IMPLEMENTATION_PR: #56 `P1: CanonicalEventDTO v1 from 03 source facts`
VALIDATED_CODE_HEAD: `516e8ca64d59009d054633339642bbb2c7a8c423`
STATE: ACTIVE
CURRENT_TASK: P1 CanonicalEventDTO v1 Implementation from 03 Source Facts
RESULT: PASS_WITH_OPEN_UNSUPPORTED_CATEGORIES

## AUTHORITATIVE_INPUT
04 consumes transition semantics only from the merged 03 contract:
- `AdvanceSummary.source_facts` for `next_game`, `week`, `month`.
- `SeasonFinalizationResult.source_facts` for explicit season finalization.

No roster/injury/form/Trait/rating/growth/lifecycle transition is reconstructed from period-final snapshots.
No 03 emission logic is duplicated in 04.

## CANONICAL_EVENT_DTO_V1
Implemented in `src/event_timeline.py`:
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
- `player_id`
- `team_id`
- `related_entity_ids`
- `state_effects`
- `rating_changes`
- `injury_effect`
- `trait_changes`
- `source_command`
- `presentation_priority`
- `persistence`
- `dedupe_key`

Internal deterministic ordering metadata remains `phase` + `source_ordinal`; it is not required as a transport field.
Rendering/normalization consumes no RNG and mutates no simulation state.

## NORMALIZATION_MAPPING
Current production 03 fact types map as follows:
- `roster_promotion` -> category `roster`, title `1군 등록`.
- `roster_demotion` -> `roster`, title `1군 말소`.
- `first_team_debut` -> `roster`, title `1군 데뷔`, major.
- `injury_created` -> `injury`, source injury state only.
- `injury_recovery_completed` -> `injury`, title `회복 완료`.
- event-driven `injury_cleared` / `injury_changed` -> `injury`.
- `form_transition` -> `form`, exact source before/after state.
- `trait_gained` / `trait_lost` -> `trait`, exact Trait key/action.
- `event_rating_change` -> `development`, exact `rating_deltas`.
- `season_growth` -> `development`, exact growth rating deltas / ability state.
- `season_finalized` -> `lifecycle`.

No production event is invented for unsupported semantics.
FARM-facing roster text uses `비1군/개발군` wording and does not imply a fully simulated Futures/minor league.

## IDENTITY_AND_DEDUPE
Random UUIDs are prohibited and not used.

Persistent facts with existing durable identity:
- `existing_history_kind` + `existing_dedupe_key` form the event-id basis.
- `dedupe_key` preserves the existing durable dedupe key.
- `fact_type` remains part of canonical event identity/dedupe so one `event_history` resolution may safely expose multiple distinct authoritative changes (for example injury + rating) without category collapse.

Facts without durable identity:
- deterministic coordinates form identity:
  `season:game_number:simulated_date:phase:local_ordinal:fact_type`.

Same save + seed + action sequence therefore produces identical canonical identity/order.

## ORDERING
Canonical sort uses the 03 coordinates as primary authority:
1. `simulated_date`
2. `game_number`
3. phase rank: `pre_game < in_game < post_game < off_day < lifecycle < system`
4. `local_ordinal`
5. deterministic `event_id`

After sorting/dedupe, `sequence` is reassigned contiguously from 0.
No last-event-wins or same-category collapse exists.
FARM -> FIRST -> FARM source facts remain two distinct ordered DTOs.

## RETENTION_POLICY
04 creates no durable event/history store and appends no history.

When 03 provides `existing_history_kind`, DTO `persistence` reflects the existing authority:
- `career_history`
- `injury_history`
- `event_history`
- `trait_history`
- `growth_history`

Without an existing durable history identity, DTO retention is `transient`.

### Recovery decision
`injury_recovery_completed` = **A. transient only** for v1.

Reason:
- 03 emits an authoritative recovery-completion source fact at the exact mutation point.
- ordinary recovery currently has no compatible durable recovery history row.
- appending a new `injury_history` completion row or `career_history` story row in 04 would create a second/new durable truth and violate ownership.
- durable injury state/history remains 03-owned; the recovery completion is still losslessly available in the successful mutation response.

If 03 later defines a durable recovery identity, 04 can project that identity without changing normalization semantics.

## GAMEPLAY_NOTABLE_ADAPTER
Existing `CareerEventSummary` / `GamePerformance.notable_events` remains supported as category `gameplay`:
- deterministic transient id from season/date/game coordinate when available + ordinal + kind.
- no persistent write.
- no overlap with 03 career source-fact types.
- title/summary are deterministic; no flavor RNG.

`AdvanceResultViewModel.from_summary()` now combines:
- 03 `source_facts`
- existing gameplay notable markers
into one CanonicalEventDTO timeline.
FastAPI itself is unchanged.

## SOURCE_COMMAND
Advance result mapping:
- `GAME` -> `next_game`
- `WEEK` -> `week`
- `MONTH` -> `month`

Lifecycle source facts are normalized with `source_command=lifecycle` via `canonical_timeline_from_source_facts()` when lifecycle transport consumes them.

## VALIDATION
PR #56 production-code HEAD: `516e8ca64d59009d054633339642bbb2c7a8c423`
Workflow: tests #785 (`34590163877`)
RESULT: SUCCESS

PASS:
- Vercel Python packaging
- Python compile
- external PostgreSQL durable-store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice tests
- related production integration tests
- full Python unit suite
- auto-career smoke
- balance smoke
- high-school/draft calibration gate + artifact
- web build/tests

Targeted CanonicalEventDTO tests cover:
1. no source facts -> `[]`
2. single roster promotion
3. FARM -> FIRST -> FARM retained
4. first-team debut
5. injury_created
6. injury_recovery_completed
7. form transition
8. Trait gain/loss
9. event rating change
10. season_growth
11. season_finalized
12. same date/game deterministic sequence
13. same seed/actions byte-stable DTO list
14. existing durable dedupe identity reuse
15. projection appends no persistent history / is repeatable
16. gameplay event is transient
17. save/load durable truth remains stable
18. near-season-end partial period projects only actual committed source facts

## BACKWARD / TRANSACTIONAL COMPATIBILITY
- no save schema change
- no Neon schema/table
- no FastAPI route/request change
- no gameplay formula change
- no rating/growth formula change
- no roster decision change
- no new FARM simulation
- projection is pure and does not alter existing durable history
- existing SessionStore stale-revision/idempotency replay semantics remain unchanged; successful response timeline is produced inside the already-existing mutation result path.

## EXACT_07_HANDOFF
After PR #56 merges:
- treat `mutation.result.notable_events` as `CanonicalEventDTO[]`.
- transport backend order and fields unchanged; do not reconstruct semantics.
- do not derive roster/injury/form/Trait/rating/growth events from final snapshot.
- do not collapse by category or retain only last event.
- idempotency replay must return stored CanonicalEventDTO response unchanged.
- stale revision remains no-mutator/no-event-commit through existing SessionStore contract.
- no new DB/event table is needed.

For future explicit lifecycle transport:
- normalize `SeasonFinalizationResult.source_facts` with `source_command=lifecycle` and transport the resulting DTO list unchanged.

## EXACT_06_HANDOFF
06 should consume backend `CanonicalEventDTO[]` only:
- `sequence` / backend array order is authoritative.
- support empty, single and multiple events.
- multiple same-date/game events must remain visible.
- `importance` and `presentation_priority` control emphasis, not semantic filtering.
- category is display metadata; frontend must not infer transition semantics from category/final snapshot.
- `persistence` may distinguish durable-history-backed facts from response-only notices.
- FARM wording must remain roster-state/development-state wording; never claim a fully simulated Futures league.

## UNSUPPORTED / OPEN
Do not fabricate until authoritative production semantics exist:
- off-day event facts
- lineup/role career transitions
- coach/manager source-fact timeline not provided by current 03 contract
- rivalry
- milestone / record
- award-specific timeline source fact
- contract / salary / service time
- FA / posting
- transfer / trade / release
- retirement event timeline
- full Futures/minor-league game simulation

## PR_HISTORY
- PR #53 closed as superseded by the authoritative source-fact implementation.
- PR #54 merged: 03 authoritative CareerSourceFact dependency.
- PR #56 open: current 04 CanonicalEventDTO implementation.

## GATES
- P1_03_SOURCE_FACT_DEPENDENCY = PASS
- P1_CANONICAL_EVENT_DTO_V1 = PASS
- P1_SOURCE_FACT_NORMALIZATION = PASS
- P1_EVENT_ID_DETERMINISM = PASS
- P1_COMPOSITE_EVENT_RETENTION = PASS
- P1_NO_DUPLICATE_DURABLE_TRUTH = PASS
- P1_RECOVERY_RETENTION_POLICY = PASS_TRANSIENT_V1
- P1_GAMEPLAY_NOTABLE_ADAPTER = PASS
- P1_ADVANCE_RESULT_PROJECTION = PASS
- P1_FINAL_CI = PASS
- P1_07_TRANSPORT_TYPING = OPEN
- P1_06_TIMELINE_PRESENTATION = OPEN
