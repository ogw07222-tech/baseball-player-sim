# 06 - Web UI

WORKSTREAM: 06 - Web UI
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@9aa458735721570581f4968060590acf3fc9c957 + PR #37@812a0f8b34fa34c03a4787cf218bd74fc8febfaa
STATE: DESIGN_READY
CURRENT_TASK: Production backend transport contract
RESULT: PASS

## LAST_COMPLETED
- PR #37 implements production-safe frontend DTO types, `BackendPresentationGateway`, `ProductionPresentationProvider`, Dashboard/Season hardening, nullable handling, and adapter tests.
- PR #37 Web build/tests are green.
- PR #36 resolved the former `game_calling` CLI smoke blocker; latest main has moved ahead and 07 owns PR #37 rebase/integration.

## CURRENT_FINDINGS
- Frontend boundary is already correct: React screens consume `GameDataProvider`; production mode should inject `ProductionPresentationProvider`, which consumes `BackendPresentationGateway` and adapts Python presentation DTOs.
- Python `GameService` is a read-only presentation facade. Simulation mutation/state ownership remains in `CareerEngine` / production advance pipeline, not in presentation adapters.
- Current persistence serializes Player + CareerEngine + RNG state and optional production advance/pitcher-usage state. Deterministic resume therefore requires the backend to persist the complete authoritative save snapshot; the browser must not reconstruct engine state.
- Current Vercel project is a Vite-only `web/` deployment and `web/vercel.json` has Git deployment disabled. No concrete Python HTTP transport exists yet.

## SELECTED_TRANSPORT_ARCHITECTURE
Use a lightweight FastAPI HTTP bridge implemented as stateless/serverless-compatible request handlers, with durable per-session save snapshots in transactional storage.

Runtime rule:
1. request identifies an opaque backend session/save slot;
2. backend loads the complete persisted save snapshot;
3. backend reconstructs the authoritative `CareerEngine`, including RNG/advance state;
4. application/advance service executes the requested read or mutation;
5. mutation is persisted atomically with an incremented revision;
6. presentation DTO is built from the authoritative post-mutation engine state and returned;
7. browser stores presentation state only, never simulation state.

Do not rely on Python process memory or Vercel function filesystem for authoritative career state.

## TRANSPORT OPTIONS
### A. Lightweight Python HTTP API + durable store — SELECTED
- Complexity: medium-low
- Vercel compatibility: high via FastAPI/Python runtime
- Save persistence: high when backed by transactional durable storage
- Latency: low/moderate; snapshot load + simulation + write per mutation
- Cost: low for current scale
- Determinism: high if full RNG/save state and revision are persisted
- Operational model: stateless HTTP compute, stateful durable save record

### B. Persistent backend process
- Complexity: medium
- Vercel compatibility: low/indirect for an always-resident in-memory process
- Save persistence: requires separate volume/database anyway
- Latency: potentially lowest while warm
- Cost: higher baseline
- Determinism: high if process/session lifecycle is controlled, but restart recovery still requires durable saves
- Not selected because it introduces infrastructure and lifecycle coupling before the project needs it.

### C. Pure serverless bridge with browser-carried serialized backend state
- Complexity: superficially low
- Vercel compatibility: high
- Save persistence: poor/security-sensitive
- Latency: payload grows with career state
- Cost: low
- Determinism: technically possible but browser becomes de-facto state carrier
- REJECTED because authoritative backend state must not be reconstructed or trusted from the browser.

### D. Serverless bridge using function-local memory/filesystem
- Complexity: low
- Vercel compatibility: deployment works, state semantics do not
- Save persistence: unacceptable across instance replacement/concurrency
- Determinism: unsafe
- REJECTED.

## EXACT HTTP CONTRACT V1
Base path: `/api/v1`
Content-Type: `application/json`
Session identity: opaque server-issued session id in an HttpOnly, SameSite=Lax cookie. The browser does not serialize engine state. Authentication can later replace/augment this without changing presentation DTOs.

### Session/career
- `GET /api/v1/session`
  - 200: `{ "has_career": boolean, "revision": integer | null }`
- `POST /api/v1/career`
  - request: existing `NewCareerRequest` JSON shape
  - creates/replaces the career for the current session according to explicit product policy
  - 201: `{ "data": BackendDashboardDto, "meta": { "revision": integer } }`

### Read presentation
- `GET /api/v1/dashboard`
  - 200: `{ "data": BackendDashboardDto, "meta": { "revision": integer } }`
- `GET /api/v1/season`
  - 200: `{ "data": BackendSeasonDto, "meta": { "revision": integer } }`
- Reads are side-effect free and must use `GameService` / presentation services only.

### Advance mutations
- `POST /api/v1/advance`
  - request: `{ "command": "next_game" | "week" | "month" | "season", "expected_revision": integer, "idempotency_key": string }`
  - backend performs load -> revision check -> production advance -> atomic save -> build DTO
  - 200: `{ "data": BackendDashboardDto, "meta": { "revision": integer } }`
  - same `idempotency_key` for the same session must never execute the simulation twice.

### Explicit save
- `POST /api/v1/save`
  - request: `{ "expected_revision": integer }`
  - 204 if current authoritative state is durably stored
  - initial implementation may make this an idempotent durability confirmation because successful mutations already auto-persist.

### Optional future load/save-slot endpoints
Do not add until multi-slot UX is designed. V1 has one active career per opaque session.

## ERROR CONTRACT
All non-2xx JSON errors:
`{ "error": { "code": string, "message": string, "retryable": boolean, "details": object | null }, "meta": { "revision": integer | null } }`

Required codes:
- `NO_CAREER` -> 404
- `REVISION_CONFLICT` -> 409; frontend must refresh authoritative dashboard/season before retrying
- `INVALID_REQUEST` -> 400/422
- `SIMULATION_CONFLICT` -> 409 for domain/session state that cannot accept the requested advance
- `SAVE_FAILED` -> 503, retryable only when commit is known not to have executed
- `INTERNAL_ERROR` -> 500 with no domain internals/traceback exposed

Never automatically retry an advance after an ambiguous network/server failure unless idempotency-key lookup proves whether the mutation executed.

## LOADING / FRONTEND CONTRACT
- Initial session/dashboard/season fetch uses existing page loading state.
- Advance/save commands expose mutation-loading separately from initial loading.
- While an advance is in flight, disable all advance controls to prevent concurrent mutations.
- After successful advance, use returned Dashboard DTO immediately, then fetch Season DTO at the returned revision.
- On `REVISION_CONFLICT`, discard optimistic assumptions and reload both presentation DTOs.
- Mock provider remains tests/dev-only and is never production truth.

## SAVE / SESSION / DETERMINISM OWNERSHIP
Authoritative state: backend only.
Persisted snapshot must include the same semantic payload currently required by `src/persistence.py`: player, career engine state, RNG state, production advance state when present, pitcher usage state when present, and save version.

Durable record minimum fields:
- `session_id` / save-slot key
- serialized save payload
- `revision`
- `save_version`
- `updated_at`
- optional last idempotency result/key for mutation replay protection

Mutation commit must be atomic on `(session_id, expected_revision)` so two browser requests cannot both advance from the same RNG state.

## LOCAL DEVELOPMENT PATH
Recommended developer topology after implementation:
- FastAPI runs locally against an in-memory/temp durable-store adapter for tests or local SQLite/file adapter only for local development.
- Vite dev server proxies `/api` to the Python dev server, or `vercel dev` serves frontend/API together once repository deployment layout is integrated.
- Frontend uses relative `/api/v1/...` URLs; no environment-specific simulation logic.

## PRODUCTION DEPLOYMENT PATH
Preferred target: same-origin Vercel deployment with Vite frontend + FastAPI/Python API bridge and an external transactional durable store.

Because current Vercel configuration is rooted under `web/`, 07 must choose the minimal repository/deployment layout that makes both `web` build output and Python `src` importable by the API. Do not duplicate `src` under `web/`.

If same-project monorepo layout proves awkward, acceptable fallback is a separate Python API deployment with an explicit API base URL and strict CORS; the HTTP contract remains identical.

## FRONTEND / BACKEND AUTHORITY
Backend authoritative for:
- career existence
- player/career/domain state
- RNG state
- current session/season progress
- all advance outcomes
- save revision/version
- presentation DTO contents

Frontend authoritative only for:
- current navigation/tab state
- temporary loading/error UI state
- display formatting
- non-domain UI preferences

## OWNERSHIP SPLIT
### 06 - Web UI
- define/maintain `BackendPresentationGateway` contract
- implement `HttpBackendPresentationGateway` after 07 exposes the API
- map transport errors to typed frontend errors/loading states
- inject `ProductionPresentationProvider` in production bootstrap
- add gateway/component integration tests
- do not implement simulation/session persistence logic

### 07 - Integration & GitHub
- rebase/revalidate/merge PR #37
- establish FastAPI/API entrypoint and repository deployment layout
- wire `CareerEngine`/production advance/application presentation services behind the API without changing gameplay formulas
- implement durable session/save repository and revision/idempotency transaction
- configure local/prod environment, Vercel routing/deployment, CI smoke tests
- coordinate any backend contract change with 00 before broadening scope

## RISKS
- Serverless concurrent mutation can duplicate advances without revision + idempotency enforcement: BLOCKING design requirement.
- File-based production saves are not a valid serverless persistence strategy: BLOCKING deployment requirement.
- Current `save_game(path, engine)` is path-oriented; transport integration may need a small persistence serialization boundary so storage adapters can persist bytes/dicts without temporary-file authority. This should be owned by 07 and preserve existing save semantics/tests.
- No authentication/multi-save-slot contract exists yet. V1 opaque cookie session is acceptable for the first single-user production milestone but is not a final account system.
- Long `advanceSeason` execution time must be measured against deployed function limits before release; keep the HTTP contract stable even if execution strategy later changes.

## BLOCKERS
- PR #37 must be rebased/revalidated by 07 before merge.
- Concrete durable storage provider and deployment layout are not yet implemented.

## OPEN_ITEMS
- Select the durable transactional store during 07 implementation (database/managed store), with atomic revision compare-and-swap support.
- Measure production `advanceSeason` latency and function duration.
- Define authentication and multi-save-slot UX in a later 00/06 contract if needed.

## NEXT_ACTION
07: integrate PR #37 onto latest main, then implement the smallest FastAPI transport vertical slice: session -> dashboard/season read -> one `next_game` mutation -> durable revisioned save -> production provider wiring. Do not implement all endpoints before this slice passes determinism/concurrency tests.

## RELATED_PRS
- #37 open draft, Web production presentation bridge
- #36 merged, former CLI smoke blocker resolved

## RELATED_BRANCHES
- ui/production-presentation-milestone
- main

## GATES
- WEB_BUILD = PASS
- WEB_TESTS = PASS
- PRODUCTION_PRESENTATION_MILESTONE = PASS_PENDING_07_INTEGRATION
- TRANSPORT_ARCHITECTURE = PASS
- DIRECT_BACKEND_TRANSPORT = OPEN
- DURABLE_SESSION_PERSISTENCE = OPEN
- END_TO_END_PRODUCTION_PROVIDER = OPEN
