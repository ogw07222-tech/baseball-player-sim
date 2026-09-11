# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
TASK_START_MAIN: `38aea3b5f1cc525bb0d1107d3bb8d77db51cb107`
INTEGRATION_BASE_AFTER_04: `05a9c0b23eb8da27c4de42e4b4e16c92a559cf6a`
PR57_MERGE_SHA: `aa3dea91f652d157d9dc19f26deeab61cce9488c`
STATE: P1_CANONICAL_EVENT_HTTP_MERGED
CURRENT_TASK: P1 Canonical Event Timeline HTTP Integration
RESULT: PASS_MERGED — CanonicalEventDTO v1 is transported unchanged through the existing transactional advance contract; PR #57 is merged.

## DEPENDENCY RESOLUTION
Current GitHub source of truth superseded the task prompt's stale PR #53 reference:
1. PR #54 — 03 authoritative `CareerSourceFact` emission — merged before task implementation.
2. PR #53 — CLOSED/SUPERSEDED; not consumed because it inferred facts from histories/snapshots.
3. PR #56 — 04 `CanonicalEventDTO` v1 from 03 source facts — CI #785 PASS; merged as `05a9c0b23eb8da27c4de42e4b4e16c92a559cf6a`.
4. PR #57 — 07 HTTP/frontend transport integration — CI #795 PASS; merged as `aa3dea91f652d157d9dc19f26deeab61cce9488c`.
5. 06 — timeline UI rendering remains the next consumer.

No 03/04 event semantics were reimplemented in 07.

## CANONICAL HTTP CONTRACT
`mutation.result.notable_events` is now modeled in frontend transport as `CanonicalEventDTO[]` with:
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

04-internal ordering coordinates remain private. 07 performs no sorting, filtering, collapse, ID generation, sequence recomputation, title/summary rewriting, persistence rewriting, or final-state trigger inference.

Current merged 04 v1 policy remains authoritative: ordinary `injury_recovery_completed` is transient unless a compatible durable source history exists. 07 does not create a separate recovery history.

## TRANSACTION / CAS / IDEMPOTENCY
No FastAPI route redesign or Neon schema change was required.

The existing `/api/v1/advance` path still runs inside `SessionStore.mutate()` and builds the canonical mutation response from the same in-transaction authoritative engine state.

Successful logical mutation commits atomically:
- simulation/state mutation
- canonical save-payload histories
- CanonicalEventDTO response projection
- serialized save payload
- revision +1
- idempotency response record

Stale `expected_revision` rejects before the mutator executes, so there is no state/history/timeline/idempotency commit and no revision change.

Same session + idempotency key + fingerprint returns the stored response without rerunning simulation or event projection. Retryable frontend network retry reuses the same serialized request body and idempotency key. Conflicting fingerprint with the same key retains the existing HTTP 409 conflict behavior.

No new Neon event table was added; durable event truth remains inside the existing canonical save payload histories.

## FRONTEND TRANSPORT
`web/src/types/backendPresentation.ts` explicitly models CanonicalEventDTO v1 instead of legacy `{date, kind, message}` events.

`HttpBackendPresentationGateway` now preserves the complete successful backend mutation result instead of discarding it after extracting the dashboard.

`ProductionPresentationProvider` exposes that result as `advanceResult` while retaining a DashboardViewModel-compatible return shape, so existing UI behavior remains compatible and 06 can consume:
`advanceResult.notable_events`.

No visual/layout file was changed.

## COMMANDS
The same canonical shape is transported for:
- `next_game`
- `week`
- `month`

Composite arrays preserve backend order and sequence exactly. Representative validation covers injury recovery + roster promotion in one game, mixed transient/persistent events, and FARM -> FIRST -> FARM within one month retaining both roster transitions.

Automatic season advance remains unavailable. Lifecycle is a valid canonical `source_command`, but no new lifecycle HTTP mutation was added in this task.

## VALIDATION
PR #57 implementation HEAD validated by Actions: `36540e82ab07bb9a2d7b3826c0742f42efd064c9`
Workflow: tests #795 (`34591503804`)

PASS:
- web install/build/tests
- Python dependency/Vercel packaging contract
- compile
- PostgreSQL external durable-store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice regression
- related production integration regression
- full Python suite: 348 tests / OK
- Auto career smoke
- Balance smoke
- high-school/draft calibration gate
- calibration artifact upload

Dedicated 07 HTTP tests PASS:
- next_game CanonicalEventDTO timeline
- week ordered mixed persistent/transient timeline
- month FARM->FIRST->FARM retention
- multiple same-game sequence retention
- stale revision exact rollback/no idempotency insertion
- byte-equivalent same-key replay
- no duplicate persistent career history
- restart durable-history equality
- same-key different fingerprint conflict

Merged 04 coverage also remains PASS for empty timelines, deterministic same-date ordering, injury/recovery/form/trait/rating/growth/lifecycle projection, deterministic gameplay transient adapters, save/load determinism, and partial near-season-end periods.

## DEPLOYMENT
No Production Vercel deployment was created.
- Vercel Git auto-deploy remains OFF.
- No production deployment quota was consumed for this contract-only integration.
- Batch this merge into the next intentional release.

## EXACT 06 HANDOFF
Production result:
`mutation.result.notable_events: CanonicalEventDTO[]`

ProductionPresentationProvider result:
`advanceResult.notable_events: CanonicalEventDTO[]`

06 rules:
- backend array order and `sequence` are authoritative;
- render every returned event; no category collapse / last-event-wins;
- no trigger inference from dashboard/final state;
- support 0 / 1 / N events;
- support multiple events on the same date/game;
- display persistent and transient events returned in the same timeline;
- `importance` and `presentation_priority` affect emphasis only;
- use backend `title` and `summary` without narrative regeneration;
- preserve `source_command` as `next_game`, `week`, `month`, or `lifecycle`;
- FARM/FIRST events are roster-movement facts only; do not infer broader league simulation semantics.

06 may now render timelines after Next Game / Next Week / Next Month. UI controls/layout remain 06-owned.

## REMAINING OPEN
- 06 timeline rendering and optional Next Week / Next Month controls.
- Automatic season HTTP command.
- Lifecycle HTTP mutation/response exposure beyond current game/week/month route.
- Future event categories without 03/04 production semantics, including later contract/FA/trade/retirement work.
- Strict forced-cold-start production evidence remains OPEN_NON_BLOCKING from earlier deployment validation.

## GATES
- PR54_03_SOURCE_FACTS = PASS_MERGED
- PR56_04_CANONICAL_EVENT_DTO_V1 = PASS_MERGED
- PR57_07_CANONICAL_EVENT_HTTP = PASS_MERGED
- CANONICAL_EVENT_HTTP_DTO = PASS
- NEXT_GAME_TIMELINE = PASS
- WEEK_TIMELINE = PASS
- MONTH_TIMELINE = PASS
- COMPOSITE_EVENT_RETENTION = PASS
- BACKEND_SEQUENCE_PRESERVED = PASS
- CAS_EVENT_ROLLBACK = PASS
- IDEMPOTENCY_TIMELINE_REPLAY = PASS
- PERSISTENT_HISTORY_NON_DUPLICATION = PASS
- PERSISTENCE_RESTART = PASS
- WEB_TYPE_BUILD_COMPATIBILITY = PASS
- PRODUCTION_PROVIDER_COMPATIBILITY = PASS
- NO_NEW_EVENT_TABLE = PASS
- VERCEL_AUTO_DEPLOY = OFF
- PRODUCTION_DEPLOYMENT_THIS_TASK = NOT_RUN_BY_DESIGN
- P1_CANONICAL_EVENT_HTTP_INTEGRATION = PASS_MERGED
- 06_TIMELINE_RENDERING = OPEN
- AUTOMATIC_SEASON_COMMAND = OPEN

## NEXT_ACTION
06 can consume `advanceResult.notable_events` for Next Game / Next Week / Next Month timeline rendering. Keep deployment batched with the next intentional Production release.
