# 06 - Web UI

WORKSTREAM: 06 - Web UI
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@590c1860b010a9735a7a1ca09910942614ae1b69
STATE: IDLE
CURRENT_TASK: P1 UI post-PR51 integration wait
RESULT: PASS — PR #51 merged after full latest-head CI GREEN; no new UI breadth until 03/07 production contracts land

## LAST_COMPLETED
- PR #51 `Web UI: production-backed career interaction hardening` merged to main as `590c1860b010a9735a7a1ca09910942614ae1b69`.
- Latest PR head `d482d03db95bb1e495d915301939b3cf76a152b7` workflow run #723 completed SUCCESS.
- `web-tests` PASS: install, build, tests.
- `unit-tests` PASS: Vercel Python packaging, compile, external durable-store tests, FastAPI entrypoint smoke, API vertical-slice tests, related production integration tests, full unit suite, auto-career smoke, balance smoke, and high-school/draft calibration gate.
- PR #51 was mergeable and was squash-merged after CI completion.

## PRESERVED PRODUCTION UI CONTRACT
- `App` requires an injected `GameDataProvider`; there is no production mock fallback.
- Production bootstrap remains `ProductionPresentationProvider(new HttpBackendPresentationGateway())`.
- `HttpBackendPresentationGateway` remains the production transport authority.
- UI exposes only the currently implemented production `next_game` mutation.
- Mutation lock prevents duplicate dispatch while an advance is in flight.
- Gateway mutation requests preserve `expected_revision` and `idempotency_key`.
- `REVISION_CONFLICT` triggers authoritative backend state reload.
- Transport/network failures retain typed `BackendTransportError`, including `NETWORK_ERROR`.
- Browser does not simulate, reconstruct, or optimistically mutate CareerEngine/domain state.

## CURRENT WAIT CONDITION
Do not add `next_week`, `next_month`, or season-advance controls until both conditions are satisfied:
1. 03 finalizes the corresponding career progression semantics on production main.
2. 07 exposes the merged semantics through the existing production API contract.

When those contracts land, extend the existing `HttpBackendPresentationGateway` / `ProductionPresentationProvider` path. Do not create a parallel frontend transport or simulation path.

## ALLOWED WORK WHILE WAITING
- regression fixes for the merged PR #51 production-backed path;
- test fixes that preserve the same backend-authoritative contract;
- compatibility updates required by merged backend DTO/API changes.

No new UI feature/design breadth is scheduled in this state.

## BACKEND DEPENDENCIES OPEN
- next-week progression API: OPEN
- next-month progression API: OPEN
- season-advance API: OPEN
- additional production presentation datasets remain backend-owned and must not be fabricated by Web UI.

## GATES
- PR51_LATEST_HEAD_FULL_CI = PASS
- PR51_MERGEABLE = PASS
- PR51_MERGED = PASS
- PRODUCTION_PROVIDER_REQUIRED = PASS
- HTTP_GATEWAY_AUTHORITY = PASS
- MUTATION_LOCK = PASS
- EXPECTED_REVISION = PASS
- IDEMPOTENCY_KEY = PASS
- REVISION_CONFLICT_RELOAD = PASS
- TYPED_NETWORK_ERROR = PASS
- PRODUCTION_MOCK_FALLBACK = PASS_NONE
- NEXT_WEEK_UI = OPEN_BACKEND_DEPENDENCY
- NEXT_MONTH_UI = OPEN_BACKEND_DEPENDENCY
- SEASON_ADVANCE_UI = OPEN_BACKEND_DEPENDENCY

## NEXT_ACTION
Wait for merged 03 progression semantics and the corresponding 07 production API breadth. Until then, accept only regression/compatibility work on the existing PR #51 production path.
