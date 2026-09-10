# 06 - Web UI

WORKSTREAM: 06 - Web UI
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@2f9a0c7a3c14ca462e4be3d95db3ad4a28635d56 + merged PR #37@1cbddd67df717b8f4800189c87f168fcf0c4e127
STATE: DESIGN_READY
CURRENT_TASK: Production backend transport contract
RESULT: PASS

## LAST_COMPLETED
- PR #37 is merged into main. The production-safe frontend DTO types, `BackendPresentationGateway`, `ProductionPresentationProvider`, Dashboard/Season nullable handling, fake-condition removal, and adapter tests are now production-main code.
- PR #37 Web build/tests were green before merge.
- Current `App.tsx` still falls back to `MockGameDataProvider` when no provider is injected; concrete production transport/bootstrap remains the next UI integration gap.

## CURRENT_FINDINGS
- Frontend boundary is correct: React screens -> `GameDataProvider` -> `ProductionPresentationProvider` -> `BackendPresentationGateway` -> backend presentation DTOs.
- `GameService` remains a read-only presentation facade; HTTP must not move gameplay formulas or simulation logic into the transport layer.
- `src/persistence.py` persists Player, CareerEngine state, RNG state, and optional advance/pitcher-usage state. Backend storage must preserve the complete snapshot so deterministic resume does not depend on browser state.
- Current Vercel config is still under `web/` and only disables Git deployment. No concrete Python HTTP transport is present.
- Separate Dashboard and Season reads can observe different revisions around a concurrent mutation. Production transport should therefore prefer one atomic presentation snapshot containing both DTOs.

## SELECTED_TRANSPORT_ARCHITECTURE
Use a lightweight FastAPI HTTP bridge with stateless/serverless-compatible request handlers and a transactional durable save store.

Authoritative runtime rule:
1. request identifies an opaque backend session/save slot;
2. backend loads the complete persisted save snapshot;
3. backend reconstructs the authoritative CareerEngine including RNG/advance state;
4. read requests build presentation DTOs only; mutation requests run the existing production advance path;
5. mutation persists atomically using expected revision + idempotency key;
6. response is built from the authoritative post-mutation state;
7. browser stores only presentation/UI state, never reconstructable engine state.

Do not use function memory, Vercel function filesystem, localStorage, or browser-carried save JSON as production authority.

## TRANSPORT OPTIONS
### A. FastAPI HTTP API + transactional durable store — SELECTED
- Complexity: medium-low
- Deployment compatibility: high
- Save persistence: high
- Latency: low/moderate; one snapshot load and write per mutation
- Cost: low at current scale
- Determinism: high with complete persisted RNG/state + revision/CAS
- Vercel compatibility: high via Python/FastAPI runtime

### B. Persistent backend process
- Complexity: medium
- Deployment compatibility: requires separate always-on backend infrastructure
- Save persistence: still needs durable storage
- Latency: potentially lower while warm
- Cost: higher baseline
- Determinism: high if lifecycle is controlled
- Vercel compatibility: poor fit for in-memory authority
- Not selected because it adds infrastructure before it is needed.

### C. Serverless bridge with browser-carried backend state
- Complexity: superficially low
- Deployment compatibility: high
- Save persistence/security: poor
- Latency: grows with payload size
- Cost: low
- Determinism: technically possible but browser becomes de-facto authority
- REJECTED.

### D. Function-local memory/filesystem authority
- Complexity: low
- Deployment compatibility: code can run, state semantics are unsafe
- Save persistence: unacceptable across instance replacement/concurrency
- Latency/cost: low
- Determinism: unsafe
- REJECTED.

## EXACT HTTP CONTRACT V1
Base path: `/api/v1`
Content-Type: `application/json`
Session identity: opaque server-issued id in an HttpOnly, SameSite=Lax cookie. Authentication/multi-slot support may later replace or augment this without changing presentation DTOs.

### Canonical presentation snapshot
`GET /api/v1/state`

200:
`{ "data": { "dashboard": BackendDashboardDto, "season": BackendSeasonDto }, "meta": { "revision": integer } }`

404 when no career exists. Dashboard and Season must be built from the same loaded authoritative snapshot and same revision.

### Session
`GET /api/v1/session`

200:
`{ "has_career": boolean, "revision": integer | null }`

This endpoint is lightweight discovery only. The frontend should use `/state` for actual presentation loading after `has_career=true`.

### Career creation
`POST /api/v1/career`

Request: existing `NewCareerRequest` JSON shape.

201:
`{ "data": { "dashboard": BackendDashboardDto, "season": BackendSeasonDto }, "meta": { "revision": 1 } }`

Creation produces and persists one complete authoritative career snapshot before responding.

### Advance mutation
`POST /api/v1/advance`

Request:
`{ "command": "next_game" | "week" | "month" | "season", "expected_revision": integer, "idempotency_key": string }`

200:
`{ "data": { "dashboard": BackendDashboardDto, "season": BackendSeasonDto }, "meta": { "revision": integer } }`

Rules:
- load -> revision check -> existing production advance -> atomic durable save -> build both DTOs;
- same `(session, idempotency_key)` must never execute simulation twice;
- two requests from the same `expected_revision` cannot both commit;
- response DTOs always represent the committed revision.

### Explicit manual save
`POST /api/v1/save`

Request:
`{ "expected_revision": integer }`

204 when the current revision is already durable or a manual checkpoint is confirmed. V1 advance/create mutations already persist atomically, so this endpoint must not create a second divergent state.

### Optional diagnostic/read endpoints
`GET /api/v1/dashboard` and `GET /api/v1/season` may exist for diagnostics/backward compatibility, but production bootstrap should prefer `/state` so UI data is revision-consistent.

## ERROR CONTRACT
All non-2xx JSON errors use:
`{ "error": { "code": string, "message": string, "retryable": boolean, "details": object | null }, "meta": { "revision": integer | null } }`

Required codes:
- `NO_CAREER` -> 404
- `INVALID_REQUEST` -> 400/422
- `REVISION_CONFLICT` -> 409
- `SIMULATION_CONFLICT` -> 409
- `SAVE_FAILED` -> 503 only when durable commit is known not to have completed
- `INTERNAL_ERROR` -> 500 with no traceback/domain internals exposed

Frontend must not blindly retry an ambiguous advance failure. Reuse the same idempotency key and/or reload `/state` before any new mutation.

## LOADING CONTRACT
- initial session/state loading is distinct from mutation loading;
- while an advance is in flight, disable all advance controls;
- no optimistic simulation/stat mutation in the browser;
- successful create/advance replaces Dashboard + Season from the returned atomic snapshot;
- `REVISION_CONFLICT` triggers authoritative `/state` reload;
- mock provider remains tests/dev-only and never production truth.

## SAVE / SESSION / DETERMINISM OWNERSHIP
Backend is authoritative for career existence, Player/CareerEngine state, RNG, advance/session state, stats, injuries/events/growth outcomes, save version/revision, and presentation DTO content.

Frontend is authoritative only for navigation, loading/error UI, display formatting, and non-domain preferences.

Durable record minimum:
- session/save-slot key
- serialized full save payload
- revision
- save_version
- updated_at
- idempotency replay record/result as needed

Mutation commit must provide atomic compare-and-swap/transaction semantics on `(session_id, expected_revision)`.

## PERSISTENCE BOUNDARY REQUIRED BY 07
Current `save_game(path, engine)` / `load_game(path)` are path-oriented. 07 may extract a small serialization boundary such as `serialize_game(engine)` and `deserialize_game(payload)` while preserving the exact current save semantics and tests. HTTP/API code must not duplicate save-format logic.

## LOCAL DEVELOPMENT PATH
Preferred first slice:
- FastAPI on localhost:8000;
- Vite on localhost:5173;
- Vite `/api` proxy to FastAPI;
- local repository adapter may use temp SQLite/file storage strictly for development/tests;
- frontend uses relative `/api/v1/...` URLs.

After repository deployment integration, `vercel dev` may serve the combined frontend/API topology for final local verification.

## PRODUCTION DEPLOYMENT PATH
Preferred target: same-origin Vercel project with frontend + FastAPI/Python API and an external transactional durable store.

07 owns the minimal repository/root-layout change needed to make both the Vite build and root `src/` Python package available to the deployment. Do not copy Python domain code under `web/`.

Fallback: separate Python API deployment with explicit API base URL + strict CORS if same-project layout causes disproportionate build/deployment complexity. The HTTP contract remains unchanged.

## OWNERSHIP SPLIT
### 06 - Web UI
- maintain frontend gateway contract;
- implement `HttpBackendPresentationGateway` after backend API exists;
- add typed transport/error types;
- change production bootstrap from default mock to `ProductionPresentationProvider` while retaining explicit mock injection for tests;
- add initial/mutation loading UX and gateway integration tests;
- do not implement simulation or persistence logic.

### 07 - Integration & GitHub
- PR #37 integration is complete; maintain merged production state;
- add FastAPI entrypoint/routes and deployment layout;
- wire session -> durable repository -> CareerEngine restore -> production advance -> persistence -> GameService presentation;
- implement revision/idempotency transaction semantics;
- extract reusable persistence serialization boundary if required;
- configure local/prod routing, durable-store environment, CI and Vercel smoke validation.

## RISKS
- Duplicate/concurrent advances without revision + idempotency enforcement: BLOCKING.
- Persisting only partial engine state breaks deterministic resume: BLOCKING.
- Function-local filesystem/memory as authority: BLOCKING.
- Current App production bootstrap still defaults to mock provider until transport wiring lands: OPEN.
- `advanceSeason` duration must be measured against deployed function limits before release: OPEN.
- Authentication and multiple save slots are intentionally deferred from V1: OPEN, non-blocking for the first single-session milestone.

## BLOCKERS
- Concrete FastAPI transport and durable transactional repository are not implemented.
- Production Web bootstrap is not yet wired to an HTTP gateway.

## OPEN_ITEMS
- Select durable transactional store in 07 implementation.
- Measure `next_game`, week/month, and especially season mutation latency in deployed runtime.
- Later define account authentication and multi-save-slot UX with 00/06 if required.

## NEXT_ACTION
Implement one vertical slice only: session -> atomic `/state` read -> one `next_game` mutation -> durable revisioned save/idempotency -> `HttpBackendPresentationGateway` -> production provider bootstrap. Validate this before adding week/month/season breadth.

## RELATED_PRS
- #37 merged: Web production presentation bridge
- #36 merged: former CLI smoke blocker resolved

## RELATED_BRANCHES
- main

## GATES
- PR37_INTEGRATION = PASS
- WEB_BUILD = PASS
- WEB_TESTS = PASS
- PRODUCTION_PRESENTATION_MILESTONE = PASS
- TRANSPORT_ARCHITECTURE = PASS
- TRANSPORT_CONTRACT_V1 = PASS
- DIRECT_BACKEND_TRANSPORT = OPEN
- DURABLE_SESSION_PERSISTENCE = OPEN
- END_TO_END_PRODUCTION_PROVIDER = OPEN
