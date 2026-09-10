# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@b52b339d175c51d6ca1d9c2d6e99ab17e770a746
STATE: ACTIVE
CURRENT_TASK: Restore Auto career smoke and fully green main CI
RESULT: OPEN

## LAST_COMPLETED
- Public repository conversion restored GitHub-hosted runner execution.
- Root cause of current smoke failure identified as missing `game_calling` CLI display label.
- PR #36 created with minimal presentation-layer fix.

## CURRENT_FINDINGS
- Python full unit suite passes 253 tests on post-#33 main sequence.
- Web tests pass.
- Current blocker is presentation-only and does not indicate gameplay formula failure.

## BLOCKERS
- PR #36 still requires final validation/merge and resulting main CI confirmation.

## OPEN_ITEMS
- Validate exact Auto career smoke on PR #36.
- Merge PR #36 if green.
- Confirm latest main repository workflow is fully green.
- Then coordinate PR #37 revalidation/merge readiness.

## DEPENDENCIES
- 06: PR #37 waits on this blocker.
- 05: production validation runs independently but final readiness should include both results.

## NEXT_ACTION
- Finish PR #36 with minimal push/CI cycle, merge if green, and report resulting main SHA + CI status.

## RELATED_PRS
- #36 open
- #37 dependent

## RELATED_BRANCHES
- feature/fix-game-calling-cli-label
- main

## GATES
- RUNNER_EXECUTION = PASS
- PYTHON_UNIT_SUITE = PASS
- WEB_TESTS = PASS
- AUTO_CAREER_SMOKE = OPEN
- MAIN_CI_GREEN = OPEN
