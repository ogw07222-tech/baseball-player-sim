# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
TASK_START_MAIN: `b4e836eb747aea42a5782fed71c39fcb3a982f17`
LATEST_P1_HTTP_BASE: PR #52 merge `559ee4cb3a61fa80e949e70dff1c4f7f65118fc7`
STATE: P1_CANONICAL_EVENT_HTTP_BLOCKED_ON_SOURCE_FACTS
CURRENT_TASK: P1 Canonical Event Timeline HTTP Integration
RESULT: OPEN / IMPLEMENTATION DEFERRED — 04 CanonicalEventDTO v1 is design-ready, but the 03-owned authoritative per-transition/per-game source-fact emission required for lossless week/month timelines is not yet implemented. 07 must not reconstruct or invent those domain facts from final snapshots.

## P0 / EXISTING P1 BASELINE
Already merged and preserved:
- FastAPI production runtime
- Neon production persistence
- create career / state
- `next_game`, `week`, `month`
- revision CAS / stale 409
- idempotency replay
- same-key retry transport behavior
- authoritative mutation result
- production HTTP provider authority
- Vercel Git auto-deploy OFF
- strict forced cold-start evidence remains OPEN but non-blocking

Current `/api/v1/advance` transaction shape remains correct:
- deserialize one canonical save payload inside `SessionStore.mutate()`;
- run exactly one authoritative `ProductionAdvanceService` command;
- serialize authoritative state;
- build response inside the same mutator;
- commit state + revision + idempotency response atomically;
- replay returns stored response without rerunning simulation.

## CONSUMED 03 CONTRACT
Authoritative progression contract consumed from merged PR #50 / current 03 status:
- `next_game` -> `ProductionAdvanceService.advance_one_game()`
- `week` -> `ProductionAdvanceService.advance_one_week()`
- `month` -> `ProductionAdvanceService.advance_one_month()`
- WEEK/MONTH are exact compositions of scheduled canonical games.
- state/RNG/stat/roster/injury/fatigue/pitcher-usage effects remain 03/01-owned.
- completed season rejects with `SeasonCompleteError` before mutation.
- automatic season transition remains OPEN.

03 event-timeline dependency still missing:
- no published production contract currently returns the ordered authoritative transition facts emitted during each internal game;
- no explicit per-transition coordinates `(season, game_number, phase, local ordinal)` are exposed by 03;
- therefore 07 cannot losslessly preserve FARM -> FIRST -> FARM or other intermediate transitions by looking only at final period state.

## CONSUMED 04 CONTRACT
Canonical contract consumed from `docs/workstream-status/04-events-story.md` as of main commit `b4e836eb747aea42a5782fed71c39fcb3a982f17`.

CanonicalEventDTO v1 fields:
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
- `player_id` (04 contract includes it; nullable)
- `team_id` (04 contract includes it; nullable)
- `related_entity_ids` (04 contract includes it)
- `state_effects`
- `rating_changes`
- `injury_effect`
- `trait_changes`
- `source_command`
- `presentation_priority`
- `persistence`
- `dedupe_key`

Required ordering:
1. occurred_at / simulated date
2. game_number
3. phase rank `pre_game < in_game < post_game < off_day < lifecycle`
4. source-local ordinal
5. deterministic event_id tie-breaker

`sequence` is contiguous after canonical ordering.

Persistence policy:
- persistent career facts reuse canonical save-payload history such as `player.career_history`;
- transient markers are response-only;
- no second durable HTTP/event truth and no new Neon table for v1.

## CURRENT GAP IN PRODUCTION CODE
`src/time_advance.py` still uses `CareerEventSummary {date, kind, message}`.

Current `AdvanceOrchestrator._advance_dates()`:
- runs each scheduled game;
- appends only `GamePerformance.notable_events` as simple game markers;
- samples roster only before and after the entire period;
- therefore cannot preserve intermediate roster transitions when end state equals start state.

Current `AdvanceResultViewModel.notable_events` serializes that simple `CareerEventSummary` list directly.

Current frontend type is correspondingly only:
- `date`
- `kind`
- `message`

Existing durable `player.career_history` already contains deterministic draft/entry/callup/debut/demotion facts, but it is a career-level history channel, not a per-mutation ordered source-fact stream. 07 must not infer which entries belong to each internal game by comparing only period-final snapshots.

## WHY NO PRODUCTION PR WAS CREATED
The requested invariants cannot all be proven with current source facts:
- `next_game` canonical event list: only simple gameplay markers are currently available.
- `week`/`month`: internal canonical career transitions are not emitted as per-game timeline facts.
- FARM -> FIRST -> FARM: current period before/after roster sampling can collapse this to no change.
- multiple same-day transitions: no authoritative phase/local ordinal contract is emitted.

Implementing CanonicalEventDTO construction in 07 now would require one of the prohibited behaviors:
- infer domain transitions from final snapshots;
- duplicate 03 transition detection;
- invent event semantics/ordering coordinates;
- treat HTTP response generation as a second event source of truth.

Therefore production code remains unchanged until the 03/04 source contract is implemented.

## EXACT 03 HANDOFF REQUIRED BEFORE 07 IMPLEMENTATION
03/04 should provide one authoritative per-command event source contract consumed by `ProductionAdvanceService` / `AdvanceSummary`.

Minimum acceptable shape before HTTP adaptation:
- every internal game returns/emits its canonical event facts before the composite orchestrator advances to the next game;
- persistent career events reuse the actual append performed by the domain/history layer, not a reconstructed copy;
- transient game markers may be adapted to canonical transient events;
- each event has deterministic ordering coordinates or is already returned in authoritative canonical order;
- FARM -> FIRST -> FARM in one composite command yields two distinct events;
- same-day/multi-event order is deterministic;
- no category collapse / last-event-wins;
- no random UUIDs;
- no separate durable event table.

Preferred integration point:
- replace or supersede `CareerEventSummary` / `AdvanceSummary.major_events` with 04 CanonicalEventDTO v1, OR expose a typed equivalent that `AdvanceResultViewModel` can pass through without semantic reconstruction.

For composites:
- each `CareerGameAdvanceProvider.advance_game()` iteration must surface the complete canonical event list generated by that game/postgame transition;
- `AdvanceOrchestrator._advance_dates()` must append every internal game list in order;
- canonical sort/dedupe/sequence assignment must occur deterministically before returning the summary;
- final-snapshot roster comparison must not be used as the canonical event source.

## PLANNED 07 HTTP PATCH AFTER SOURCE CONTRACT MERGES
Bounded 07 changes only:
1. `AdvanceResultViewModel.notable_events` passes canonical DTO dictionaries unchanged / losslessly.
2. `/api/v1/advance` keeps timeline generation inside existing `SessionStore.mutate()`.
3. no new DB schema/table.
4. frontend `BackendAdvanceEventDto` expands to CanonicalEventDTO v1 with nullable compatibility.
5. legacy `{date, kind, message}` game markers are accepted only if 04 supplies/approves a deterministic transient canonical adapter.
6. no UI layout changes.

Transaction behavior will remain:
- stale revision: mutator does not run -> no state mutation, history append, event response, or idempotency insertion;
- success: canonical state/history + response timeline commit atomically;
- same idempotency key: exact stored response replay, no simulation rerun, no duplicate history;
- retryable network retry: same request body/key -> same committed response/timeline.

## REQUIRED TEST MATRIX FOR FUTURE INTEGRATION PR
Must PASS on the final composed 03 + 04 + 07 tree:
- next_game canonical timeline
- week canonical timeline
- month canonical timeline
- no-event list `[]`
- multiple events same game/day preserve deterministic `sequence`
- FARM -> FIRST -> FARM preserved as two ordered events
- WEEK timeline equals concatenated canonical NEXT_GAME timelines from equivalent save/seed
- MONTH timeline equals concatenated canonical NEXT_GAME timelines from equivalent save/seed
- stale revision leaves serialized state/history unchanged
- same idempotency key returns byte-equivalent JSON response and no duplicate history
- same key + different fingerprint -> `SIMULATION_CONFLICT`
- persistence restart preserves persistent history
- save/load preserves persistent history and deterministic future sequence
- transient events are not persisted accidentally
- partial composite near season end contains only actually committed game events
- web TypeScript build/tests
- production provider compatibility
- full related Python integration/store suite

## EXACT 06 HANDOFF
06 should eventually receive `mutation.result.notable_events: CanonicalEventDTO[]` and treat backend order as authoritative.

UI contract:
- display next_game / week / month lists without deriving triggers;
- support empty list;
- support multiple events on same date/game;
- do not group-collapse categories;
- do not keep only the last event;
- use `importance` / `presentation_priority` only for emphasis/order presentation, never semantic filtering;
- display both persistent and transient response events;
- do not infer injury/recovery/callup/demotion from final Dashboard/Season state.

No 06 production type change should merge before the canonical source-event contract is available unless it is purely additive and backward compatible.

## IMPLEMENTATION / PR STATUS
- 07 production implementation PR: NOT CREATED
- Reason: authoritative 03 transition/source-fact contract is not yet available in production code.
- 04 CanonicalEventDTO v1: DESIGN_READY, production implementation not present on latest main.
- No production deployment performed.
- No Neon schema change performed.
- No Vercel configuration changed.

## MERGE ORDER RECOMMENDATION
1. 03 — authoritative transition/source-fact emission and composite preservation
2. 04 — CanonicalEventDTO v1 implementation + deterministic adapter/order/dedupe contract
3. 07 — one coherent HTTP/DTO/transaction integration PR
4. 06 — event timeline rendering / controls consuming the published DTO

If 03+04 are delivered in one coordinated PR, 07 may branch directly from that merged main and produce one HTTP integration PR.

## PASS / FAIL / OPEN
PASS:
- existing transaction/CAS/idempotency foundation
- state + response atomic mutation architecture
- exact idempotency replay architecture
- retryable same-key transport behavior
- existing canonical save-payload persistence
- no-new-Neon-table design
- 04 CanonicalEventDTO v1 design contract consumed

FAIL / NOT YET IMPLEMENTED:
- CanonicalEventDTO production object/path
- complete per-game authoritative career transition emission
- composite FARM -> FIRST -> FARM retention
- canonical event sequence on production HTTP response

OPEN / BLOCKING 07 CODE:
- 03 source facts / transition coordinates
- 04 production DTO + approved legacy transient adapter

OPEN / NON-BLOCKING EXISTING P1:
- automatic season advance
- forced cold-start evidence

## NEXT_ACTION
Wait for the coordinated 03/04 production source contract. Once merged, immediately implement the bounded 07 pass-through inside the existing `/api/v1/advance` SessionStore mutation, run the full transactional/composition matrix above, and create one coherent integration PR. Do not deploy production solely for this contract integration unless an explicit release/deploy task requests it.
