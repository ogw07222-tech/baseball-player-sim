# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@9f7fc381bde6edc626ef42bb175abff2aa7b151d
STATE: BLOCKED
CURRENT_TASK: One-Time Manual Production Deploy Without Re-enabling Git Auto Deploy
RESULT: BLOCKED — Git auto-deploy has been restored to OFF on current main, but the available Vercel connector deployment action cannot create the requested one-time Production deployment from a Git SHA directly. Its runtime validation requires an explicit `target`, project `name`, and full `files` bundle; the exposed connector schema in this session does not provide a Git-source/redeploy-by-SHA path. No Preview deployment was intentionally created and no new automatic Production deployment was created after auto-deploy was disabled.

## LAST_COMPLETED
- Task-start main: `80209cba45f684e6bf6603ab5f2dec705c4765a9`.
- Confirmed the intended Production project remains Vercel project `baseball-player-sim` (`prj_5m6Qi5Ljj0ebBtZPcWbZjQADj1ZD`).
- Detected that task-start main had root `vercel.json` in schema-only form, meaning Git auto-deploy had been re-enabled by prior PR #46 and did not match the requested OFF state.
- Created and merged PR #47 to restore `git.deploymentEnabled: false` with no net file changes outside root `vercel.json`.
- PR #47 merge SHA: `9f7fc381bde6edc626ef42bb175abff2aa7b151d`.
- Verified root `vercel.json` on main now has `git.deploymentEnabled: false`.
- Verified no Vercel deployment was created after the PR #47 merge timestamp, confirming the OFF configuration suppressed the merge-triggered deployment.
- Attempted exactly one connector manual-deploy action. The action rejected the invocation before deployment creation because the connector requires explicit `target`, `name`, and `files` inputs and does not expose a Git-SHA deployment input in this session.
- No gameplay, UI, DB, ratings, growth, events, SessionStore semantics, or unrelated configuration was changed.

## CURRENT_FINDINGS
- `VERCEL_GIT_AUTO_DEPLOY = OFF` on current main.
- Current main contains PR #45 in ancestry.
- No one-time manual Production deployment was created in this run.
- Historical stale deployment evidence remains historical only and was not reused.
- The most recent current-main Git-triggered deployment remains the earlier PR #46 deployment and is not reused as the requested manual deployment.

## BLOCKERS
- Available Vercel connector does not expose a supported one-time Production deployment from repository Git SHA; its deploy action requires a full file bundle.

## OPEN_ITEMS
- Create exactly one Production deployment of latest main through a Vercel UI/CLI/API path that can target the linked Git project while leaving `git.deploymentEnabled: false` unchanged.
- After a new Production deployment exists, run FIRST GATE: `READY`, deployed SHA contains PR #45 or later main, and `GET /api/v1/session` returns FastAPI JSON.
- Only if all FIRST GATE checks pass, continue the existing full production smoke.

## DEPENDENCIES
- Vercel Production project: `baseball-player-sim`.
- Git auto-deploy: OFF.
- One-time Git-SHA/manual Production deployment capability: BLOCKED in current connector surface.

## NEXT_ACTION
- Trigger exactly one manual Production deployment from current main outside the unavailable connector Git-SHA path (Vercel UI/CLI/API). Keep automatic Git deployments OFF. Once the new deployment appears, verify FIRST GATE before any full smoke.

## RELATED_PRS
- #47 merged: restore Vercel Git auto-deploy OFF
- #46 merged: prior temporary re-enable of Vercel Git deployments
- #45 merged: Vercel Python packaging fix
- #44 merged: Neon production schema + Vercel handoff
- #43 merged: P0 production persistence wiring
- #42 merged: Web ↔ Python vertical slice

## RELATED_BRANCHES
- main
- fix/disable-vercel-auto-deploy

## GATES
- PR45_MERGED = PASS
- VERCEL_CONNECTOR_ACCESS = PASS
- VERCEL_GIT_AUTO_DEPLOY = OFF
- ONE_TIME_MANUAL_PRODUCTION_DEPLOYMENT = BLOCKED
- VERCEL_CURRENT_MAIN_BUILD = OPEN
- VERCEL_DEPLOYED_SHA_VERIFIED = OPEN
- PRODUCTION_API_SESSION_ROUTE = OPEN
- VERCEL_PRODUCTION_WIRING = OPEN
- PRODUCTION_SESSION_PERSISTENCE = OPEN
- PRODUCTION_REVISION_CAS = OPEN
- PRODUCTION_IDEMPOTENCY = OPEN
- DEPLOYED_NEXT_GAME_E2E = OPEN
- DEPLOYED_BROWSER_E2E = OPEN
- COLD_START_PERSISTENCE = OPEN
- MOCK_NOT_PRODUCTION_AUTHORITY = OPEN
- P0_WEB_PYTHON_PRODUCTION_COMPLETE = OPEN
