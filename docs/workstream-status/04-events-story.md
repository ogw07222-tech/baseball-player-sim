# 04 - Events & Story

WORKSTREAM: 04 - Events & Story
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@b52b339d175c51d6ca1d9c2d6e99ab17e770a746
STATE: ACTIVE
CURRENT_TASK: Events/Traits/Career Story next-contract audit
RESULT: OPEN

## LAST_COMPLETED
- Existing midseason event scheduler, choice flow, cooldown/once-per-season controls, and save continuity are present in production prototype.

## CURRENT_FINDINGS
- Full career narrative coverage and explicit cross-system event contracts require audit before expansion.

## BLOCKERS
- None recorded yet.

## OPEN_ITEMS
- Map event scheduler/traits/injury/news/history integration.
- Identify missing career-stage event categories and state-transition contracts.
- Define first implementation batch without gameplay-formula coupling.

## DEPENDENCIES
- 03: career and injury-development state.
- 06: narrative presentation needs.
- 00: event priority.

## NEXT_ACTION
- Finish audit and propose a bounded production-ready event contract and implementation order.

## RELATED_PRS
- None assigned for current task.

## RELATED_BRANCHES
- main

## GATES
- EVENT_SYSTEM_AUDIT = OPEN
- NEXT_EVENT_CONTRACT = OPEN
