# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@c390c788ca8e459942f45f37b0fdc0c85db7fa14
STATE: REVIEW
CURRENT_TASK: P0 Web ↔ Python Production Vertical Slice
RESULT: PASS for local/CI vertical slice and main integration; production deployment remains OPEN pending external transactional durable storage and deployment wiring

## LAST_COMPLETED
- Implemented the P0 browser-to-authoritative-Python vertical slice on `feature/p0-web-python-vertical-slice`.
- Extracted canonical `serialize_game(engine)` / `deserialize_game(payload)` boundaries from path-oriented persistence without changing save schema semantics.
- Added FastAPI `/api/v1/session`, `/api/v1/career`, `/api/v1/state`, `/api/v1/advance`, and `/api/v1/save` routes.
- Added transactional SQLite local/CI session storage with revision compare-and-swap and idempotency replay records.
- Added `HttpBackendPresentationGateway` and switched the production web entrypoint to `ProductionPresentationProvider`; `MockGameDataProvider` is no longer production bootstrap authority.
- Added Vite `/api` proxy for localhost:5173 -> FastAPI localhost:8000 development topology.
- Initial feature run #634 completed GREEN.
- Updated the branch onto latest pre-merge main `67f752a375a708d9d9834f09c6954aced4b950f9` with no P0 file conflicts; integrated head `062cf30ae4c964268187bb13df2206ccc61f7734` passed PR run #641 GREEN.
- PR #42 was marked ready and merged as `c390c788ca8e459942f45f37b0fdc0c85db7fa14`.
- Post-merge main run #642 completed GREEN across API vertical-slice tests, related production integration tests, full Python suite, Auto career smoke, Balance smoke, draft calibration gate, web build, and web tests.

## CURRENT_FINDINGS
- Authoritative flow is React -> GameDataProvider -> ProductionPresentationProvider -> HttpBackendPresentationGateway -> FastAPI -> CareerEngine -> ProductionAdvanceService -> canonical serialized save -> transactional store -> Dashboard + Season DTO -> React.
- `POST /api/v1/career` reuses canonical `CareerEngine.evaluate_draft()` for the initial playable PRO transition rather than inventing HTTP-layer roster/draft semantics.
- `POST /api/v1/advance` P0 scope accepts `command=next_game` only; week/month/season breadth is intentionally deferred.
- Mutation transaction checks idempotency before execution, compares expected revision, runs simulation at most once per committed idempotency key, atomically persists revision+1, and returns DTOs for the committed revision.
- Same idempotency key + same request replays the stored response without a second game. Reusing a key with a different request returns `SIMULATION_CONFLICT`. Stale revision returns `REVISION_CONFLICT` 409.
- API integration tests verify create -> state, refresh/restart recovery from the same SQLite file, consistent state reads, next_game revision 1 -> 2, persisted `CareerEngine.current_session.games_completed == 1`, idempotent replay, stale-revision rejection, deterministic save/load resume, and manual-save revision checks.
- SQLite is explicitly local/CI only. Under Vercel/production mode without an external durable adapter, the API fails closed with `SAVE_FAILED` rather than treating function-local filesystem as authority.
- No gameplay, rating, growth, event, catcher, KBO-rule, or probability formula was changed by PR #42.

## BLOCKERS
- Production/serverless deployment requires a real external transactional durable-store adapter/configuration. Function-local SQLite/filesystem is intentionally rejected as production authority.
- Same-origin Vercel FastAPI routing/root deployment layout has not yet been production-validated.

## OPEN_ITEMS
- Select and implement the external transactional durable store while preserving the `SessionStore` revision/idempotency contract.
- Wire/validate FastAPI in the final deployment topology and use secure production cookie settings.
- Run real browser process E2E against Vite :5173 + FastAPI :8000 when a local/Codespaces checkout is available; current evidence is GitHub Actions FastAPI TestClient + web gateway/build tests.
- Extend advance breadth to week/month/season only after `next_game` deployment correctness is established.

## DEPENDENCIES
- 06: frontend may treat `/api/v1` and `HttpBackendPresentationGateway` as the production transport boundary; no frontend domain simulation should be added.
- 05: production balance remains unchanged; no retuning is required from this transport milestone.
- Deployment infrastructure: external transactional durable storage is required before Vercel production authority can be enabled.

## NEXT_ACTION
- Implement the external durable `SessionStore` adapter and same-origin FastAPI deployment wiring, then run deployed next_game idempotency/revision smoke validation before enabling broader advance commands.

## RELATED_PRS
- #42 merged: P0 Web ↔ Python production vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- feature/p0-web-python-vertical-slice

## GATES
- SERIALIZATION_BOUNDARY = PASS
- SESSION_DISCOVERY = PASS
- CREATE_CAREER = PASS
- ATOMIC_STATE_SNAPSHOT = PASS
- NEXT_GAME_E2E = PASS
- REVISION_CAS = PASS
- IDEMPOTENCY_REPLAY = PASS
- STALE_REVISION_409 = PASS
- REFRESH_RESTORE = PASS
- BACKEND_RESTART_PERSISTENCE = PASS
- DETERMINISTIC_RESUME = PASS
- MOCK_NOT_PRODUCTION_AUTHORITY = PASS
- API_INTEGRATION_TESTS = PASS
- RELATED_PRODUCTION_TESTS = PASS
- PYTHON_UNIT_SUITE = PASS
- AUTO_CAREER_SMOKE = PASS
- BALANCE_SMOKE = PASS
- DRAFT_CALIBRATION_GATE = PASS
- WEB_BUILD = PASS
- WEB_TESTS = PASS
- PR42_LATEST_MAIN_REVALIDATION = PASS
- PR42_MERGED = PASS
- MAIN_CI_GREEN = PASS
- EXTERNAL_DURABLE_STORE = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
