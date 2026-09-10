# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: `main@b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc` for deployed code; this status update does not change application code
STATE: BLOCKED
CURRENT_TASK: Diagnose Production 503 on /api/v1/session
RESULT: FIRST GATE BLOCKED — CURRENT READY DEPLOYMENT REACHES FASTAPI, BUT PRODUCTION RUNTIME DOES NOT SEE AN EXTERNAL DATABASE URL

## CURRENT_FINDINGS
- Current Production deployment: `dpl_zeqW4tEs1FBs95cKeZABrXSEPcCU`.
- Deployment state: `READY`.
- Deployed Git SHA: `b3ca2fe9cd6c84f400d7d301a2c30176bf0978cc`.
- Deployed SHA contains PR #49 merge `13c7976fdae227b10f20d7130f6f7e176eb579e3`; PR #49 is later than and contains PR #48 and PR #45 in ancestry.
- `GET /api/v1/session` on the Production alias returns HTTP 503 with actual FastAPI JSON: `error.code = SAVE_FAILED`, message `external transactional durable store is required in production`, `retryable = false`.
- Therefore the previous `FUNCTION_INVOCATION_FAILED` circular-import crash is resolved on the deployed code. The request reaches FastAPI and the application's fail-closed production store path.
- Exact current root cause classification: Production runtime does not see any supported external database URL environment variable (`BASEBALL_SIM_DATABASE_URL`, `DATABASE_URL`, or `POSTGRES_URL`), so `_default_store()` selects `DisabledProductionStore`.
- This response is not a Neon hostname/SSL/pooled-endpoint/schema error. The Postgres adapter is not being selected yet.
- Runtime logs show handled HTTP 503 requests for `/api/v1/session`; no current function-crash/runtime exception cluster is required to explain the response.
- The currently exposed Vercel connector does not provide environment-variable list/edit actions, so `DATABASE_URL` Production-scope configuration cannot be inspected or corrected from this tooling session.
- No application code change is justified. `git.deploymentEnabled=false` remains preserved.

## FIRST GATES
- NEW_PRODUCTION_DEPLOYMENT_AFTER_HISTORICAL_STALE = PASS
- VERCEL_CURRENT_MAIN_BUILD = PASS
- VERCEL_DEPLOYED_SHA_VERIFIED = PASS
- PR45_INCLUDED = PASS
- PR48_INCLUDED = PASS
- PR49_INCLUDED = PASS
- PRODUCTION_API_ROUTE_REACHED = PASS
- PRODUCTION_API_SESSION_ROUTE = FAIL (HTTP 503 handled FastAPI JSON)
- PRODUCTION_DATABASE_URL_VISIBLE = FAIL on current deployment
- FULL_PRODUCTION_SMOKE = NOT RUN

## ROOT CAUSE
Production external durable-store environment configuration is not visible to the currently deployed serverless runtime. The exact application response is the fail-closed branch used when no supported database URL variable is present. This establishes an environment/deployment configuration blocker, not an application import/build blocker and not yet a Neon connection blocker.

## REQUIRED NEXT ACTION
- In Vercel project `baseball-player-sim`, verify an environment variable named exactly `DATABASE_URL` exists under Settings → Environment Variables.
- Verify its environment scope includes Production.
- Verify the stored value is the intended Neon pooled Production PostgreSQL connection string without exposing the secret.
- Save the variable configuration.
- Create one new Production deployment from latest main while keeping Git auto-deploy disabled.
- Re-test only `GET /api/v1/session` first.

## NEXT-RESULT CLASSIFICATION
- HTTP 200 FastAPI JSON: FIRST GATE passes; then continue full production smoke.
- HTTP 503 with `external durable store is unavailable`: the database URL is now visible and the Postgres adapter is selected; inspect Neon connection/SSL/pooled endpoint/credentials/schema runtime evidence before any fix.
- HTTP 503 with the same `external transactional durable store is required in production`: the environment variable is still not reaching that deployment; continue Vercel environment/scope/deployment diagnosis without changing application code.

## DO NOT RUN YET
Do not run career create, GET state, `next_game`, revision CAS, idempotency, reconnect persistence, Neon session/idempotency-row verification, cold-start persistence, browser E2E, or MockGameDataProvider production-authority checks until `/api/v1/session` returns HTTP 200.

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
- PRODUCTION_DATABASE_URL_VISIBLE = FAIL
- VERCEL_PRODUCTION_WIRING = FAIL
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
