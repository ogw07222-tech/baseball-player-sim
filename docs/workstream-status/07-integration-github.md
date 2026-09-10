# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@11fbb451a0e967820ea69db2d315616133cd2023
STATE: BLOCKED
CURRENT_TASK: P0 Manual Production Verification Fallback
RESULT: READY_FOR_MANUAL_EVIDENCE — Vercel connector live access remains blocked, so no current deployment/runtime facts are inferred. Latest API contract and the canonical deployed smoke script were re-read from main. A manual Vercel UI + production-site + Neon verification procedure is prepared so user-provided screenshots/status/HTTP responses can be treated as auditable evidence. All deployed-runtime gates remain OPEN until that evidence is supplied.

## LAST_COMPLETED
- Re-read latest main at task start: `11fbb451a0e967820ea69db2d315616133cd2023`.
- Re-read `src/api/app.py` and confirmed the current P0 API contract: GET `/api/v1/session`, POST `/api/v1/career`, GET `/api/v1/state`, POST `/api/v1/advance`, POST `/api/v1/save`.
- Confirmed production session cookie name `baseball_sim_session`, opaque UUID session ID, HttpOnly, SameSite=Lax, Secure in production, Path=/, one-year max age.
- Confirmed P0 `advance` accepts only `command=next_game`; request requires `expected_revision` and `idempotency_key`.
- Confirmed stale revision error is HTTP 409 with `error.code=REVISION_CONFLICT`; conflicting idempotency reuse is HTTP 409 with `error.code=SIMULATION_CONFLICT`.
- Re-read `tools/deployed_p0_smoke.py`, which already codifies create/state/next_game/revision/idempotency replay/stale-409/new-client persistence/API-error-schema checks.
- Prepared a manual fallback sequence that preserves one browser/curl cookie jar and avoids exposing the session cookie, DATABASE_URL, save payload, idempotency fingerprint, or connection secrets.
- No application, gameplay, ratings, growth, injury, events, KBO rules, stat formulas, UI, advance breadth, persistence logic, DB schema, SessionStore semantics, or deployment configuration was changed.

## CURRENT_FINDINGS
- GitHub/API evidence is sufficient to define exactly what manual runtime responses must look like, but it is not sufficient to mark any deployed gate PASS.
- Intended repository-root production project from prior verified Vercel evidence is `baseball-player-sim`; user must confirm the currently active production project/deployment in Vercel UI because connector evidence is stale/unavailable.
- The production domain must be taken from the active Vercel Production deployment/assigned domain, not guessed from historical aliases.
- The canonical smoke career payload is `{name: "Deployment Smoke", position: "SS", bats: "RIGHT", throws: "RIGHT", traitCount: 1}`.
- Successful career creation must return HTTP 201 with `meta.revision=1`; successful `next_game` must return HTTP 200 with `meta.revision=2` and dashboard progress game/games_completed = 1.
- Repeating the exact same advance request with the same idempotency key must return the same committed response and must not increase game count/revision again.
- A new idempotency key with stale `expected_revision=1` after the first commit must return HTTP 409 with `REVISION_CONFLICT` and current revision 2.
- A fresh HTTP client/browser request that reuses the same `baseball_sim_session` cookie must recover the revision-2 state from durable storage.
- Neon verification should expose only aggregate/latest revision/timestamps, not session IDs, cookie values, save payloads, fingerprints, DATABASE_URL, or passwords.

## BLOCKERS
- Vercel connector live access remains unstable/blocked, so current project/deployment/env/runtime cannot be independently queried by 07.
- Deployed gates require user-supplied Vercel UI screenshots/status and production HTTP/Neon evidence, or later restored connector access.

## OPEN_ITEMS
- User to provide Vercel Production project name, latest deployment status, deployed Git SHA, build-failure status, and production domain from the Vercel UI.
- User to provide production HTTP evidence for session -> career create -> state -> next_game -> same-key replay -> stale revision 409 -> reconnect/state persistence.
- User to provide Neon production evidence showing a session row exists, latest revision advanced to 2, updated_at changed, and at least one idempotency record exists, without sharing secrets or full save payload.
- User to refresh/reopen the production site and provide browser evidence that the same career/state is shown and backend DTOs are being used.
- Once evidence is supplied, 07 will validate deployed SHA, route contract, revision progression, persistence, idempotency, stale-409 behavior, Neon durability, and browser authority before changing gates.

## DEPENDENCIES
- Neon production PostgreSQL/schema: READY and previously validated.
- GitHub main/API contract: `11fbb451a0e967820ea69db2d315616133cd2023` at task start.
- Vercel connector: BLOCKED; manual user evidence is the active fallback path.

## NEXT_ACTION
- User performs the manual verification checklist supplied by 07 and returns screenshots and/or sanitized command outputs. 07 then audits those artifacts against the exact API contract and updates deployed-runtime gates. Do not expose DATABASE_URL, cookies, save payloads, fingerprints, or other secrets.

## RELATED_PRS
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 Vercel production persistence wiring code
- #42 merged: P0 Web ↔ Python local/CI vertical slice
- #37 merged: production presentation contract/provider foundation

## RELATED_BRANCHES
- main
- Neon branch `production`
- Neon branch `p0-validation`

## GATES
- NEON_PRODUCTION_PROJECT = PASS
- NEON_PRODUCTION_DATABASE = PASS
- NEON_PRODUCTION_SCHEMA = PASS
- EXTERNAL_DURABLE_STORE = PASS
- POSTGRES_SESSION_STORE_ADAPTER = PASS
- POSTGRES_MIGRATION_CONTRACT = PASS
- POSTGRES_REAL_SERVICE_TESTS = PASS
- PRODUCTION_FAIL_CLOSED = PASS
- PRODUCTION_SECURE_SESSION_COOKIE = PASS
- MOCK_NOT_PRODUCTION_AUTHORITY_CODE = PASS
- MANUAL_PRODUCTION_VERIFICATION_FALLBACK = PASS
- VERCEL_CONNECTOR_ACCESS = BLOCKED
- VERCEL_CURRENT_MAIN_BUILD = OPEN
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- PRODUCTION_API_SESSION_ROUTE = OPEN
- VERCEL_DATABASE_URL_PRODUCTION_SCOPE_VERIFIED = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
