# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@21a7621763a85268a4e2fb68cad9194854c4c601
STATE: ACTIVE
CURRENT_TASK: P1 Progression Event Timeline Contract audit/design
RESULT: FAIL_CONTRACT_GAP_DESIGN_READY

## TASK_START_SOURCE
- Task-start latest main: `21a7621763a85268a4e2fb68cad9194854c4c601`.
- Audited production advance, time aggregation, HTTP transactional mutation, event scheduler/resolution, injury/form/roster flow, career_history, save/load and current tests.

## CURRENT_ARCHITECTURE
- `next_game`, `week`, and `month` all flow through `ProductionAdvanceService` / `AdvanceOrchestrator`.
- WEEK/MONTH iterate scheduled games and append only each `GamePerformance.notable_events` into `AdvanceSummary.major_events`.
- Current `CareerEventSummary` is only `{date, kind, message}`.
- `AdvanceResultViewModel.notable_events` serializes `AdvanceSummary.major_events` directly.
- Production game `notable_events` are gameplay-result strings such as game/pitcher markers; they are not the general career-event bus.
- Roster is sampled only before and after the whole period for `roster_changes`; intermediate FARM/FIRST transitions can disappear if the final level returns to the starting level.
- v0.4 choice events resolve into `player.event_history` and `last_event_resolutions`; `last_event_resolutions` is not a durable timeline contract.
- Draft/entry/callup/debut/demotion observational facts persist in append-only `player.career_history`.
- Injury creation persists in `injury_history`, but generic recovery completion is currently state clearing rather than a canonical persistent event.
- Form/slump/hot changes, rating deltas, coach changes, awards and growth are represented in separate state/history channels rather than one ordered advance timeline.

## P1_FINDING
Current `mutation.result.notable_events` is insufficient as a canonical progression-event timeline.

Main failure modes:
1. Only `GamePerformance.notable_events` are accumulated per internal game.
2. Career events resolved in `_postgame()` are not automatically added to `AdvanceSummary.major_events`.
3. Injury/recovery/form/trait/growth/coach/award state changes are not normalized into the same timeline.
4. Period-level before/after roster comparison loses intermediate transitions such as FARM->FIRST->FARM.
5. Current event items lack stable logical ids, sequence, category, effects and retention metadata.
6. `last_event_resolutions` is process state, not serialized durable history.
7. A no-game/off-day event channel does not exist in the current week/month orchestrator.

## CANONICAL_EVENT_DTO_V1
Recommended transport/domain DTO:
- `event_id: str` — stable logical event id, not presentation text.
- `event_type: str`
- `category: str`
- `occurred_at: str | null` — ISO date when known.
- `season: int | null`
- `game_number: int | null`
- `sequence: int` — deterministic order within one advance mutation.
- `title: str`
- `summary: str`
- `importance: info | normal | major | critical`
- `player_id: str | null`
- `team_id: str | null`
- `related_entity_ids: list[str]`
- `state_effects: dict | null`
- `rating_changes: dict[str,int] | null`
- `injury_effect: dict | null`
- `trait_changes: list[dict] | null`
- `source_command: next_game | week | month | lifecycle | system`
- `presentation_priority: int`
- `persistence: transient | career_history`
- `dedupe_key: str`

Nullable fields are allowed; consumers must not infer missing simulation semantics.

## EVENT_ID_AND_DEDUPE
- Persistent career events should reuse their stable `career_history` dedupe key/logical identity.
- Transient game events should derive identity from committed mutation context plus deterministic event coordinates, e.g. `season:game_number:phase:ordinal:type`.
- Never use random UUID generation inside simulation/event rendering.
- Replay of the same committed idempotency key must return the stored response unchanged; it must not regenerate ids or append history again.
- Different commands producing the same already-persisted career event must expose the same persistent logical event id/dedupe key.

## ORDERING_POLICY
Canonical ordering for one mutation response:
1. `occurred_at` / simulated date
2. `game_number` (`null` off-day/lifecycle events ordered by explicit phase)
3. phase rank: `pre_game < in_game < post_game < off_day < lifecycle`
4. source-local ordinal
5. deterministic `event_id` tie-breaker

`sequence` is assigned only after canonical sort and is contiguous from 0.
Same save + same seed + same actions must produce byte-equivalent ordered event facts, excluding explicitly noncanonical presentation metadata.

## COMPOSITE_ADVANCE_SEMANTICS
- `next_game` returns all canonical events emitted by that game advance.
- `week` / `month` must compose the canonical timelines from every internal game plus any explicit off-day/lifecycle event hooks in the period.
- Aggregation is append + canonical sort + dedupe, never last-event-wins.
- Intermediate state transitions must be retained even when final state equals initial state.
- Near season end, the timeline contains only events from games actually advanced before the boundary; no fabricated future events.
- No-event periods return `notable_events: []`.

## TRANSIENT_VS_PERSISTENT_POLICY
Transient-only by default:
- low-level game notable markers
- routine lineup/role flavor when no durable career meaning exists
- low-importance temporary presentation notices

Persistent career history required when production semantics exist and the event matters after the response:
- draft / pro entry / first-team debut
- roster promotion/demotion
- major injury and recovery completion once a recovery event is defined
- Trait gain/loss
- major award / record / milestone once implemented
- team transfer / contract / retirement once 03 exposes authoritative state

Do not persist every transient marker. Persistent history must remain append-only and deduped; mutation timeline may include both transient and newly persisted events.

## CURRENT_EVENT_CLASS_STATUS
- injury: PARTIAL — creation state/history exists; not in canonical advance timeline.
- recovery: MISSING timeline contract; generic recovery completion is not persistently emitted.
- slump/hot: PARTIAL — form state exists; no canonical event timeline.
- breakout: PARTIAL — v0.4 breakthrough events exist but ownership/model cleanup remains separate.
- development/growth: PARTIAL — state changes exist; no ordered advance event contract.
- rating change: PARTIAL — period net delta exists; intermediate changes are not eventized.
- trait gain/loss: PARTIAL — history exists; no timeline integration.
- coach interaction/change: PARTIAL — event/coach history exists; no unified timeline.
- roster promotion/demotion: PERSISTENT FACT EXISTS; composite mutation aggregation missing.
- lineup/role change: MISSING canonical career semantics.
- rivalry: MISSING production semantics.
- milestone/record: MISSING production semantics.
- award: PARTIAL — award state exists; timeline/news integration missing.
- team/career news: PARTIAL — deterministic career news exists for early-career spine only.
- draft/pro entry/pro debut: PERSISTENT FACT EXISTS; mutation timeline integration missing.
- season lifecycle: PARTIAL — lifecycle state exists; canonical timeline integration not complete.

## OWNERSHIP_AND_REQUIRED_CHANGES
03 Growth & Career:
- Emit/return authoritative state-transition facts for injury recovery, form transitions, roster/lifecycle and future contract/team/retirement states rather than requiring 04 to infer them from final snapshots.
- Keep gameplay/growth/roster formulas owned by 03/01; event DTO construction must not change those formulas.
- Provide explicit event coordinates (season/game/phase/local ordinal) at transition time.

04 Events & Story:
- Normalize source facts into CanonicalEventDTO v1.
- Define retention, importance, deterministic title/summary and dedupe contracts.
- Reuse `career_history` for durable story facts rather than introducing duplicate persistent truth.

07 Integration & GitHub:
- Preserve `mutation.result.notable_events` as an ordered list in the HTTP contract.
- Aggregate per-game timeline events for WEEK/MONTH; do not derive them from final snapshots.
- Keep aggregation inside the transactional mutator so stale revision failures commit no state/events.
- Idempotency replay must return the previously committed response/timeline unchanged.
- No Neon schema change is required for v1 if durable events continue to live inside canonical save payload (`career_history` / existing histories).

06 Web UI:
- Treat backend order/sequence as authoritative.
- Render all returned events for week/month; never collapse by category or keep only the last event.
- Importance controls emphasis only, not retention.
- UI must not infer injury/recovery/callup/milestone triggers from final state.
- Support empty, single and multi-event timelines and multiple events on the same game/date.

## TRANSACTIONAL_SAFETY
Current store CAS/idempotency architecture is reusable:
- stale revision is rejected before the mutator executes/commits;
- failed mutation rolls back;
- successful response is stored with the idempotency record;
- replay returns stored response without re-running simulation.
Timeline generation must remain inside this existing transaction boundary.

## REQUIRED_TESTS
Must add contract tests for:
- no-event week -> empty ordered list
- one-event week
- multiple-event week
- multiple events same game/day with deterministic sequence
- month with many games/events and no loss
- WEEK/MONTH timeline equals concatenated canonical NEXT_GAME timelines from equivalent seed/save
- FARM->FIRST->FARM within one composite period preserves both transitions
- same idempotency key returns byte-equivalent timeline and no duplicate persistent history
- stale revision creates no event/history side effect
- save/load preserves persistent career history and deterministic future event sequence
- partial week/month near season end returns only committed events
- persistent event side effect/history append occurs exactly once
- transient events are not accidentally persisted

## DESIGN_DECISION
Do not overload current `CareerEventSummary {date,kind,message}` further as the long-term contract. Introduce a typed canonical progression-event DTO and make `AdvanceSummary.major_events` / `AdvanceResultViewModel.notable_events` carry that shape. Existing simple gameplay notable strings can be adapted into transient canonical events for backward-compatible presentation.

No production code was changed in this audit because source event emission hooks span 03 and 07 ownership and require coordinated implementation to avoid duplicate state/history writes.

## PASS_FAIL_OPEN
PASS:
- next_game/week/month canonical state advancement composition
- transaction/CAS/idempotency foundation
- idempotency response replay
- stale revision no-commit semantics
- persistent early-career `career_history` dedupe model

FAIL:
- canonical progression event DTO in production
- complete week/month career-event aggregation
- intermediate roster transition preservation in mutation result
- unified injury/recovery/form/trait/growth/coach timeline
- stable event identity/sequence contract for `notable_events`

OPEN:
- off-day event production semantics
- lineup/role canonical semantics
- rivalry/milestone/record production semantics
- award timeline integration
- future contract/FA/transfer/retirement timeline hooks from 03
- subsystem-wide RNG isolation beyond the RNG-free observational news layer

## NEXT_ACTION
Coordinate a bounded P1 implementation batch across 03/04/07:
1. add CanonicalEventDTO v1 + deterministic ordering/dedupe helpers;
2. capture per-game before/after source facts at transition time;
3. aggregate every internal game timeline for WEEK/MONTH;
4. bridge existing `career_history` callup/demotion/debut facts into mutation timeline without double-persisting;
5. add transactional/idempotency/composition tests;
6. hand ordered DTOs to 06 for week/month presentation.

## GATES
- P1_EVENT_TIMELINE_AUDIT = PASS
- P1_EVENT_TIMELINE_PRODUCTION_CONTRACT = FAIL
- P1_COMPOSITE_EVENT_RETENTION = FAIL
- P1_TRANSACTIONAL_EVENT_SAFETY_FOUNDATION = PASS
- P1_EVENT_ID_DETERMINISM = DESIGN_READY
- P1_TRANSIENT_PERSISTENT_POLICY = DESIGN_READY
- P1_UI_HANDOFF_CONTRACT = DESIGN_READY
