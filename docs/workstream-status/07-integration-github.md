# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@e642fa2545bdc05ad8cc2b363b7bd199173409b1
STATE: REVIEW
CURRENT_TASK: PR #36 completed; main CI green; PR #37 integration revalidation/unblock
RESULT: PASS for PR #36 and MAIN_CI_GREEN; PR #37 OPEN pending stale-base update and fresh integration CI

## LAST_COMPLETED
- PR #36 merged to main with the minimal `game_calling` CLI presentation label fix.
- Main workflow run #566 completed GREEN on `e642fa2545bdc05ad8cc2b363b7bd199173409b1`.
- Python full unit suite, exact Auto career smoke, Balance smoke, draft calibration gate, web build, and web tests all passed on that main SHA.
- PR #37 repository-wide smoke blocker was cleared and its PR description was updated with the current integration state.

## CURRENT_FINDINGS
- PR #36 changed only `src/main.py` presentation mapping; gameplay, ratings, growth, events, catcher gameplay, tests, and workflow logic were not changed.
- MAIN_CI_GREEN is confirmed on the post-#36 production main SHA.
- PR #37 is open, draft, and GitHub reports it mergeable, but its head `812a0f8b34fa34c03a4787cf218bd74fc8febfaa` is 5 commits behind latest validated main and 12 commits ahead of the merge base.
- PR #37's previous web build/tests and Python unit suite were green; its prior repository-wide failure was the now-fixed Auto career smoke blocker.

## BLOCKERS
- PR #37 requires update/rebase onto latest main and one fresh integration CI run before merge recommendation is upgraded to PASS.

## OPEN_ITEMS
- Update/rebase `ui/production-presentation-milestone` onto latest main without unrelated changes.
- Run one fresh PR integration CI cycle.
- If green, mark PR #37 ready for review and proceed with merge review.

## DEPENDENCIES
- 06: repository-wide blocker is cleared; PR #37 is unblocked for revalidation, but not yet final-merge PASS until fresh CI on latest main.
- 05: production validation remains an independent readiness input.

## NEXT_ACTION
- Rebase/update PR #37 onto latest main, avoid any extra feature changes, and use a single fresh Actions run as final integration evidence.

## RELATED_PRS
- #36 merged
- #37 open/draft, mergeable, revalidation required

## RELATED_BRANCHES
- main
- feature/fix-game-calling-cli-label
- ui/production-presentation-milestone

## GATES
- RUNNER_EXECUTION = PASS
- PR36_FIX = PASS
- PYTHON_UNIT_SUITE = PASS
- WEB_TESTS = PASS
- AUTO_CAREER_SMOKE = PASS
- MAIN_CI_GREEN = PASS
- PR37_REPOSITORY_BLOCKER_CLEARED = PASS
- PR37_LATEST_MAIN_REVALIDATION = OPEN
- PR37_MERGE_READY = OPEN
