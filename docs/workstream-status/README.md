# Workstream Status Protocol

This directory is the cross-chat coordination layer for Baseball Player Career Simulator.

Each specialist chat owns exactly one status file and must keep it current. `00 - Game Design HQ` reads these files plus current GitHub PR/CI state to reconstruct project status without relying on chat-local memory.

## Allowed STATE values

- `IDLE`
- `ACTIVE`
- `BLOCKED`
- `REVIEW`
- `DONE`

## Allowed gate/result values

- `PASS`
- `FAIL`
- `OPEN`
- `NOT_RUN`

## Required update rules

1. Read the latest `main` and your own status file before starting work.
2. Use the current production `main` as implementation source of truth unless the task explicitly defines another validation target.
3. Update only your own workstream file unless the task explicitly assigns coordination-document ownership.
4. Record the exact source-of-truth SHA used for conclusions.
5. Record PRs, branches, blockers, dependencies, gates, and the next action.
6. Do not hide failed or unresolved findings; use `FAIL` or `OPEN`.
7. When a PR is merged, replace stale branch-based status with the resulting `main` SHA on the next update.
8. Keep this file current-state oriented. Put long history in PRs/reports and link/reference them instead of growing the status file indefinitely.
9. Bundle status updates with meaningful work where possible; do not create CI noise solely for cosmetic status edits.
10. Before ending a task, update the workstream file even if the task only produced audit/research conclusions.

## Standard fields

Every workstream file should preserve this structure:

- `WORKSTREAM`
- `UPDATED_AT`
- `SOURCE_OF_TRUTH`
- `STATE`
- `CURRENT_TASK`
- `RESULT`
- `LAST_COMPLETED`
- `CURRENT_FINDINGS`
- `BLOCKERS`
- `OPEN_ITEMS`
- `DEPENDENCIES`
- `NEXT_ACTION`
- `RELATED_PRS`
- `RELATED_BRANCHES`
- `GATES`

## Ownership

- `00-hq.md` — 00 - Game Design HQ
- `01-gameplay.md` — 01 - Gameplay Engine
- `02-ratings-generation.md` — 02 - Player Ratings & Generation
- `03-growth-career.md` — 03 - Growth & Career
- `04-events-story.md` — 04 - Events & Story
- `05-balance-lab.md` — 05 - Balance Lab
- `06-web-ui.md` — 06 - Web UI
- `07-integration-github.md` — 07 - Integration & GitHub
- `08-data-research.md` — 08 - Baseball Data & Research
