# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: `main@b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc`
STATE: BLOCKED
CURRENT_TASK: Diagnose Production 503 on /api/v1/session
RESULT: CURRENT DEPLOYMENT REACHES FASTAPI BUT SESSION ROUTE RETURNS HANDLED 503; DATABASE ENV/STORE PATH NOT YET DISAMBIGUATED

## CURRENT_FINDINGS
- Current Production deployment: `dpl_zeqW4tEs1FBs95cKeZABrXSEPcCU`.
- Deployment state: `READY`.
- Deployed Git SHA: `b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc`.
- Deployed SHA contains PR #49 merge `13c7976fdae227b10f20d7130f6f7e176eb579e3`; PR #49 contains the earlier PR #48 lockfile fix and PR #45 packaging fix in ancestry.
- The previous `FUNCTION_INVOCATION_FAILED` circular-import crash is no longer the current symptom. Runtime telemetry records repeated `GET /api/v1/session` responses with HTTP 503 on this READY deployment and reports no runtime exception cluster for the route.
- `PRODUCTION_API_ROUTE_REACHED = PASS`: the function executes and returns an application-level 503 rather than crashing during import.
- The current application has two relevant handled 503 paths: when production has no external database URL, `_default_store()` selects `DisabledProductionStore`, whose operations raise `ApiProblem(503, "SAVE_FAILED", "external transactional durable store is required in production")`; when a configured Postgres store raises `StoreUnavailable`, the app returns a different handled 503 (`external durable store is unavailable`).
- Exact response body could not be retrieved through the available Vercel connector in this session because direct deployment/alias fetch is intercepted by Vercel SSO and returns HTTP 302 before exposing the application body. Runtime request logs expose the 503 status but not the response body.
- The available Vercel connector does not expose project environment-variable listing, so `DATABASE_URL` presence/scope cannot be asserted from tooling. `PRODUCTION_DATABASE_URL_VISIBLE = OPEN`.
- No code change is justified yet: missing/incorrect Production env scope vs Postgres connection failure cannot be distinguished until the actual 503 JSON body or equivalent runtime evidence is obtained.
- `git.deploymentEnabled=false` remains preserved.

## FIRST GATES
- VERCEL_CURRENT_MAIN_BUILD = PASS
- VERCEL_DEPLOYED_SHA_VERIFIED = PASS
- PR49_INCLUDED = PASS
- PRODUCTION_API_ROUTE_REACHED = PASS
- PRODUCTION_API_SESSION_ROUTE = FAIL (HTTP 503)
- PRODUCTION_DATABASE_URL_VISIBLE = OPEN
- FULL_PRODUCTION_SMOKE = NOT RUN

## ROOT-CAUSE BRANCH
- If the actual response body has `error.code = SAVE_FAILED` and message `external transactional durable store is required in production`, classify as Production external DB URL missing/not visible to this deployment. Fix Vercel Production Environment Variable scope/config only, redeploy once, and retest `/api/v1/session`; do not change application code.
- If the body message is `external durable store is unavailable`, the configured Postgres path is being selected and the next blocker is Neon/Postgres connectivity. Inspect the new runtime traceback/error details before any code or DB change; classify hostname/SSL/pooled endpoint/credentials/schema exactly.

## BLOCKERS
- Exact 503 JSON response body is not observable through the current Vercel connector because the fetch path is intercepted by Vercel SSO.
- Vercel environment-variable names/scopes are not exposed by the current connector, so `DATABASE_URL` Production visibility remains unverified.

## NEXT_ACTION
- Obtain the actual `/api/v1/session` JSON body from the current Production URL (without exposing any secret). If it reports `external transactional durable store is required in production`, verify/add `DATABASE_URL` under Vercel Production scope and create one new Production deployment from current main. If it reports `external durable store is unavailable`, inspect that deployment's runtime DB error before changing anything.
- Do not run career create, next_game, CAS, idempotency, persistence, cold-start, or browser E2E until `/api/v1/session` returns HTTP 200 FastAPI JSON.

## RELATED_PRS
- #49 merged: Vercel direct-module import circularity fix
- #48 merged: web npm lockfile fix
- #45 merged: Vercel Python packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 production persistence wiring
- #42 merged: Web ↔ Python vertical slice

## GATES
- PR45_MERGED = PASS
- PR48_LOCKFILE_FIX_MERGED = PASS
- PR49_RUNTIME_IMPORT_FIX_MERGED = PASS
- VERCEL_GIT_AUTO_DEPLOY = OFF
- VERCEL_CURRENT_MAIN_BUILD = PASS
- VERCEL_DEPLOYED_SHA_VERIFIED = PASS
- PRODUCTION_API_ROUTE_REACHED = PASS
- PRODUCTION_API_SESSION_ROUTE = FAIL
- PRODUCTION_DATABASE_URL_VISIBLE = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
