# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
TASK_START_MAIN: `38aea3b5f1cc525bb0d1107d3bb8d77db51cb107`
INTEGRATION_BASE_AFTER_04: `05a9c0b23eb8da27c4de42e4b4e16c92a559cf6a`
STATE: P1_CANONICAL_EVENT_HTTP_VALIDATED
CURRENT_TASK: P1 Canonical Event Timeline HTTP Integration
RESULT: PASS — CanonicalEventDTO v1 is transported unchanged through the existing transactional advance contract; PR #57 validated and ready to merge.

## DEPENDENCY RESOLUTION
The task prompt referenced PR #53 as the 04 implementation, but current GitHub source of truth showed PR #53 already CLOSED/SUPERSEDED because it inferred event facts from histories/snapshots.

Authoritative dependency order used here:
1. PR #54 — 03 authoritative `CareerSourceFact` emission — already merged at task start.
2. PR #56 — 04 `CanonicalEventDTO` v1 from 03 source facts — CI run #785 PASS and merged as `05a9c0b23eb8da27c4de42e4b4e16c92a559cf6a` before 07 implementation.
3. PR #57 — 07 HTTP/frontend transport integration — this task.
4. 06 — UI rendering after #57.

No 03/04 event semantics were reimplemented by 07.

## CONSUMED CANONICAL CONTRACT
Public `CanonicalEventDTO` v1 fields transported by `mutation.result.notable_events`:
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

04-internal phase/source ordinals remain private and are not added to the HTTP DTO.

Current merged 04 v1 policy is authoritative: ordinary `injury_recovery_completed` is currently a transient canonical event unless a compatible durable source history already exists. 07 does not append a separate recovery history or override that persistence policy.

## HTTP / TRANSACTION PATH
No FastAPI route redesign was needed.

Merged 04 already makes `AdvanceResultViewModel.from_summary()` project `AdvanceSummary.source_facts` plus transient gameplay notable markers to the canonical ordered list. Existing FastAPI `/api/v1/advance` calls that view-model inside the existing `SessionStore.mutate()` mutator.

Therefore a successful mutation remains one atomic logical transaction:
- authoritative simulation/state mutation
- existing persistent histories in the canonical save payload
- canonical event response projection
- serialized save payload
- revision +1
- idempotency response record

No Neon event table or schema change was added.

## CAS / IDEMPOTENCY
Existing store semantics are preserved:
- stale `expected_revision` is rejected before the mutator runs;
- stale rejection commits no state/history/timeline/idempotency row and does not advance revision;
- same session + key + fingerprint replays the stored response without rerunning simulation or canonical projection;
- conflicting fingerprint with the same key retains the existing HTTP 409 simulation/idempotency conflict behavior;
- retryable browser transport retry reuses the exact same serialized request body and idempotency key.

Dedicated tests verify byte-equivalent HTTP replay, stable event ids/sequences, no duplicate durable career history, and exactly one idempotency row.

## FRONTEND TRANSPORT CHANGES
`web/src/types/backendPresentation.ts` now explicitly models CanonicalEventDTO v1 and `BackendAdvanceResultDto.notable_events` is `BackendCanonicalEventDto[]` instead of legacy `{date,kind,message}[]`.

`HttpBackendPresentationGateway` now preserves the successful authoritative mutation result instead of discarding it after extracting the dashboard. It performs no event sorting, filtering, category collapse, ID generation, sequence recalculation, title/summary rewriting, or persistence rewriting.

A successful gateway mutation returns:
- authoritative dashboard DTO
- the exact backend `mutation.result`

`ProductionPresentationProvider` adapts the dashboard as before and additionally exposes `advanceResult` to 06. Existing App/dashboard behavior remains compatible because the returned object is still a DashboardViewModel-compatible shape. No UI visual/layout file was changed.

Mock-provider compatibility is retained by making transport metadata optional at the generic `GameDataProvider` level; production HTTP/provider paths always provide the backend mutation result.

## COMMAND BEHAVIOR
The same canonical event shape is used for:
- `next_game`
- `week`
- `month`

07 preserves backend ordering and `sequence` exactly. Composite arrays are not reconstructed from the final dashboard.

Verified representative composite behavior includes:
- injury recovery + roster promotion in the same game timeline;
- mixed transient and persistent events;
- FARM -> FIRST -> FARM in one month retaining both promotion and demotion in order;
- persistent career-history rows surviving replay/restart without duplicate append.

Automatic season advance remains intentionally unavailable. Lifecycle source-command support belongs to the canonical DTO but no automatic season HTTP command was introduced.

## VALIDATION — PR #57
Implementation/code HEAD validated by GitHub Actions: `36540e82ab07bb9a2d7b3826c0742f42efd064c9`
Workflow: tests run #795 (`34591503804`)

PASS:
- web npm install/build/tests
- Python dependency and Vercel packaging contract
- Python compile
- PostgreSQL external durable-store tests
- Vercel FastAPI entrypoint smoke
- API vertical-slice regression
- related production integration regression
- full Python unit suite: 348 tests / OK
- Auto career smoke
- Balance smoke
- high-school/draft calibration gate
- calibration artifact upload

New HTTP timeline tests PASS:
- next_game CanonicalEventDTO shape
- week ordered mixed persistent/transient timeline
- month FARM->FIRST->FARM retention
- same-game event sequence preservation
- stale CAS no state/history/event/idempotency commit
- same-key byte-equivalent replay
- stable persistent history across replay
- restart durable-history equality
- same-key different fingerprint conflict

Merged 04 tests retained and PASS for:
- no-event canonical list
- deterministic same-day ordering
- injury creation/recovery projection
- form/trait/rating/growth/lifecycle canonical mapping
- deterministic transient gameplay adapter
- save/load deterministic future timeline
- partial period near season end

## PR
PR #57 — `P1 integration: transport CanonicalEventDTO timelines`

Change scope is limited to frontend transport/types/provider compatibility, dedicated API transport tests, and this 07 status document. No gameplay/growth/rating/injury/roster/event semantics were changed.

## DEPLOYMENT
No production Vercel deployment was created for this contract-only integration.
- Git auto-deploy remains OFF.
- No production deployment quota was intentionally consumed.
- Batch deployment with the next intentional release.

## EXACT 06 HANDOFF
Production mutation contract:
`mutation.result.notable_events: CanonicalEventDTO[]`

06 consumption rules:
- backend array order and `sequence` are authoritative;
- render all returned events; do not collapse by category or keep only the last event;
- do not infer event triggers from dashboard/final state;
- support 0 / 1 / N events;
- support multiple events on the same date/game;
- mixed persistent/transient timelines are normal and both are displayable;
- `importance` and `presentation_priority` control emphasis only, never retention;
- FARM/FIRST canonical roster events mean roster movement only; UI must not invent extra league simulation implications;
- use backend `title`/`summary`; do not regenerate narrative;
- `source_command` is passed as `next_game`, `week`, `month`, or `lifecycle` unchanged.

`ProductionPresentationProvider` now exposes `advanceResult.notable_events`, so 06 can render the returned timeline after Next Game / Next Week / Next Month without new trigger logic.

## REMAINING OPEN
- Actual 06 timeline UI/rendering and optional Next Week/Next Month controls.
- Automatic season HTTP command remains OPEN.
- Lifecycle HTTP action/response transport beyond current game/week/month advance remains future work.
- Event categories that 03/04 have not given production semantics remain OPEN (for example future contract/FA/trade/retirement and other catalog gaps).
- Strict forced-cold-start production evidence remains OPEN_NON_BLOCKING from the earlier P0/P1 deployment work.

## GATES
- PR54_03_SOURCE_FACTS = PASS_MERGED
- PR56_04_CANONICAL_EVENT_DTO_V1 = PASS_MERGED
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
- P1_CANONICAL_EVENT_HTTP_INTEGRATION = PASS
- 06_TIMELINE_RENDERING = OPEN
- AUTOMATIC_SEASON_COMMAND = OPEN

## NEXT_ACTION
Merge PR #57, then hand `advanceResult.notable_events` to 06 for timeline rendering. Batch this contract with the next intentional Production release rather than creating a deployment only for this transport change.
