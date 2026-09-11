# 06 - Web UI

WORKSTREAM: 06 - Web UI
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: task-start main@f336b9be10f252300971be3d146b51ad7ff91537 + PR #51 ui/p1-production-backed-integration
STATE: REVIEW
CURRENT_TASK: P1 Production-Backed UI Integration
RESULT: PASS_PENDING_FINAL_PR_CI

## LAST_COMPLETED
- P0 production path is present and proven: Browser -> `ProductionPresentationProvider` -> `HttpBackendPresentationGateway` -> FastAPI -> CareerEngine -> Neon.
- Production bootstrap in `web/src/main.tsx` explicitly injects `ProductionPresentationProvider(new HttpBackendPresentationGateway())`.
- FastAPI currently exposes `/api/v1/session`, `/state`, `/career`, `/advance`, and `/save`; the current production advance contract supports `next_game` only.

## P1 IMPLEMENTATION
PR #51 hardens the existing production vertical slice without expanding simulation or redesigning the UI.

### Session / restore
- App performs backend session discovery before deciding whether to show New Career or the existing career shell.
- Existing career loads Dashboard + Season through the production provider/gateway.
- Initial session loading has explicit copy distinct from mutation loading.
- Refresh/reconnect continues to rely on the backend cookie session + durable state; browser does not reconstruct CareerEngine state.

### New career
- No-career state renders the existing `NewCareerPage`.
- Career creation continues through the production provider and `/api/v1/career`.
- Returned production Dashboard snapshot plus cached Season snapshot become the visible career state.

### Production advance
- Player Dashboard now exposes only the backend-supported `next_game` command.
- Week/month/season buttons were removed from the production UI until those backend commands are implemented.
- Next Game has mutation loading and disabled state.
- A synchronous mutation lock prevents duplicate UI clicks from dispatching two concurrent advances.
- No optimistic stat/game calculation is performed in React.

### Revision / conflict recovery
- Gateway sends `expected_revision` and a generated `idempotency_key` for `next_game`.
- Typed `REVISION_CONFLICT` is handled by reloading authoritative Dashboard + Season state from the backend instead of applying frontend assumptions.
- Typed network/backend failures are surfaced as user-facing error states.

### Mock isolation
- `App` no longer imports or creates `MockGameDataProvider` as a default fallback.
- `GameDataProvider` injection is required by `App`.
- Production `main.tsx` injects the HTTP production provider.
- Mock provider remains available only for explicit tests/dev callers.

## FILES CHANGED
- `web/src/App.tsx`
- `web/src/components/ui.tsx`
- `web/src/screens/PlayerDashboard.tsx`
- `web/src/services/HttpBackendPresentationGateway.ts`
- `web/src/services/HttpBackendPresentationGateway.test.ts`
- `web/src/services/GameDataProvider.test.ts` (new)
- `web/src/App.test.tsx`
- `docs/workstream-status/06-web-ui.md`

## CONTRACTS USED
### `GET /api/v1/session`
- discovers `has_career` and current revision.

### `GET /api/v1/state`
- authoritative Dashboard + Season snapshot at one revision.

### `POST /api/v1/career`
- existing `NewCareerRequest`.
- returns authoritative Dashboard + Season snapshot.

### `POST /api/v1/advance`
Current UI uses only:
- `command: "next_game"`
- `expected_revision`
- `idempotency_key`

The backend currently rejects week/month/season commands, so no production UI buttons are shown for them.

### `POST /api/v1/save`
- existing explicit save checkpoint contract remains available from Season UI.

## VALIDATION
PR #51 workflow run #718 first head validation:
- Web Install: PASS
- Web Build: PASS
- Web Tests: PASS
- Vercel Python packaging: PASS
- Python compile: PASS
- external durable-store tests: PASS
- FastAPI entrypoint smoke: PASS
- API vertical-slice tests: PASS
- related production integration tests: PASS
- remaining repository-wide Python regression steps were still running when this status update was authored.

Web test coverage includes:
- production provider DTO bridge
- atomic gateway state read
- expected revision + idempotency key request shape
- typed `REVISION_CONFLICT`
- typed `NETWORK_ERROR`
- session loading state
- API error state
- duplicate-click prevention while mutation is in flight
- authoritative reload after revision conflict
- absence of unimplemented week/month/season controls

## BACKEND DEPENDENCIES STILL OPEN
- `next_week`, `next_month`, and season-advance breadth remain backend/07 dependencies; UI does not expose fake controls for them.
- Several Dashboard/Season optional datasets remain empty because backend presentation services do not yet expose them; UI keeps explicit empty states.
- No new API persistence, Neon, gameplay, rating, growth, or career-engine behavior is introduced by this PR.

## E2E STATUS
Previously verified production browser E2E remains the P0 baseline:
1. new career
2. GAME 0 / 144
3. Next Game
4. GAME 1 / 144
5. reload
6. same player + GAME 1 / 144 preserved

P1 adds UI-level regression protection around duplicate dispatch, loading, typed errors, and conflict recovery. A fresh external production browser run is not required for the UI-only code to claim CI PASS; release integration may re-run the existing production smoke after merge.

## RELATED
- PR #51: P1 production-backed UI interaction hardening
- PR #37: merged production presentation boundary
- P0 FastAPI/Neon production transport: merged and operational

## GATES
- PRODUCTION_BOOTSTRAP = PASS
- SESSION_DISCOVERY = PASS
- NO_CAREER_TO_CREATE = PASS
- CREATE_TO_DASHBOARD = PASS
- NEXT_GAME_UI_WIRING = PASS
- MUTATION_LOADING = PASS
- DUPLICATE_CLICK_PREVENTION = PASS
- TYPED_API_ERRORS = PASS
- REVISION_CONFLICT_RECOVERY = PASS
- REFRESH_CONTINUITY = PASS_BASELINE_E2E
- PRODUCTION_MOCK_AUTHORITY = PASS_NONE
- WEEK_MONTH_SEASON_UI = OPEN_BACKEND_DEPENDENCY
- WEB_BUILD = PASS
- WEB_TESTS = PASS
- PR51_FINAL_CI = REVIEW
