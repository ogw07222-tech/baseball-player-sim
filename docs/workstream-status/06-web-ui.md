# 06 - Web UI

WORKSTREAM: 06 - Web UI
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@774431d9b221407bebeddb02001eeeed6c40bef2 + merged PR #37
STATE: BLOCKED
CURRENT_TASK: Freeze UI expansion; wire real Python transport
RESULT: BLOCKED — required 07 FastAPI backend is not present on current main

## LAST_COMPLETED
- PR #37 is merged. Production-safe backend presentation DTO types, `BackendPresentationGateway`, `ProductionPresentationProvider`, nullable handling, fake-condition removal, and adapter tests are on main.
- The transport contract is frozen around an authoritative backend session, atomic Dashboard+Season state snapshot, revisioned mutations, durable save state, and idempotency.

## CURRENT_FINDINGS
- `web/src/services/GameDataProvider.ts` contains the production presentation boundary but no concrete `HttpBackendPresentationGateway`.
- `web/src/App.tsx` still defaults to `MockGameDataProvider` when no provider is injected; production bootstrap is therefore not connected to Python.
- Current main contains no FastAPI entrypoint or implementation of `/api/v1/session`, `/api/v1/state`, `/api/v1/career`, or `/api/v1/advance`.
- `docs/workstream-status/07-integration-github.md` records PR #38/#39 integration as 07's latest completed task and does not record a FastAPI transport implementation.
- No open PR/branch found in the inspected repository state provides the required production transport.

## P0 CONTRACT ISSUE
GitHub issue #41 tracks the missing backend vertical slice required by 06:
- opaque backend session identity;
- atomic Dashboard+Season `/state` response at one revision;
- career creation;
- `next_game` mutation with `expected_revision` and `idempotency_key`;
- durable authoritative CareerEngine/RNG/advance-state persistence;
- `REVISION_CONFLICT` mapping;
- duplicate/retry protection.

06 will not invent endpoints, move simulation logic into React, reconstruct backend state in the browser, or use the mock provider as production truth.

## REQUIRED 07 API BEFORE 06 IMPLEMENTATION
Frozen expected contract from the prior design milestone:
- `GET /api/v1/session`
- `GET /api/v1/state`
- `POST /api/v1/career`
- `POST /api/v1/advance`

Canonical state/mutation responses must contain both `BackendDashboardDto` and `BackendSeasonDto` plus one authoritative `revision`.

Advance must preserve idempotency and reject stale `expected_revision` with `REVISION_CONFLICT` rather than executing simulation twice.

If 07's actual implementation intentionally differs, 07 must publish the concrete route/request/response/error contract before 06 wiring begins.

## FRONTEND IMPLEMENTATION READY AFTER UNBLOCK
### 06 ownership
- implement `HttpBackendPresentationGateway` against the concrete 07 API;
- typed API success/error envelopes;
- retain authoritative revision returned by backend;
- create career and `next_game` wiring;
- reuse one idempotency key for retry of the same logical mutation;
- on `REVISION_CONFLICT`, reload authoritative `/state`;
- split initial loading from mutation loading and disable advance controls in flight;
- remove default production mock bootstrap;
- allow mock only by explicit injection in tests/dev;
- add gateway/integration/E2E tests.

### Explicit non-scope
- no new screens/design expansion;
- no gameplay/rating/growth/stat calculation in frontend;
- no backend save reconstruction in frontend;
- no Figma work.

## REQUIRED E2E GATE
1. Browser creates career against Python backend.
2. Dashboard and Season show the same backend revision state.
3. Next Game triggers one Python-engine game.
4. Returned state is rendered without frontend simulation logic.
5. Refresh loads the same durable revision.
6. Duplicate click cannot issue a second concurrent advance.
7. Retry with the same idempotency key does not advance twice.
8. Stale revision returns conflict and UI reloads authoritative `/state`.

Current result: NOT RUN — backend transport absent.

## BLOCKERS
- P0: concrete 07 FastAPI backend transport absent from current main.
- P0: durable revision/idempotency implementation unavailable for E2E validation.
- Therefore production bootstrap cannot safely replace the default mock yet.

## NEXT_ACTION
07 / issue #41: land the smallest backend vertical slice (`session -> state -> career -> next_game`, durable revision/idempotency). Then 06 immediately wires `HttpBackendPresentationGateway` and runs the required browser-to-Python E2E without UI expansion.

## RELATED
- PR #37 merged
- Issue #41 open: P0 FastAPI transport required for production Web gateway

## GATES
- PR37_INTEGRATION = PASS
- FRONTEND_PRESENTATION_BOUNDARY = PASS
- UI_EXPANSION_FREEZE = PASS
- REAL_FASTAPI_BACKEND_AVAILABLE = FAIL
- HTTP_GATEWAY_IMPLEMENTATION = OPEN
- PRODUCTION_BOOTSTRAP = OPEN
- REVISION_CONFLICT_HANDLING = OPEN
- IDEMPOTENCY_E2E = OPEN
- BROWSER_TO_PYTHON_E2E = OPEN
