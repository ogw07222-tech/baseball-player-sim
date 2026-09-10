# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@e0ee4e9a12d8bc806c30dcdd58ea2acb88029932
STATE: DONE
CURRENT_TASK: PR #37 latest-main revalidation and production UI integration
RESULT: PASS — PR #37 merged after fresh latest-main validation; post-merge main CI GREEN

## LAST_COMPLETED
- Updated `ui/production-presentation-milestone` onto `main@9aa458735721570581f4968060590acf3fc9c957` with merge commit `1cbddd67df717b8f4800189c87f168fcf0c4e127`.
- Stale-base update preserved the 11 PR #37 `web/src/**` changes without feature additions; no conflicting file paths were found against intervening main changes.
- Fresh PR workflow run #578 completed GREEN: Python full unit suite, exact Auto career smoke, Balance smoke, draft calibration gate, artifact upload, web build, and web tests all passed.
- PR #37 was marked ready for review and merged as `1edad331045f554b03777a6254dab02f024f063b`.
- Latest post-merge main `e0ee4e9a12d8bc806c30dcdd58ea2acb88029932` includes PR #37 plus a subsequent docs-only workstream update; workflow run #586 completed GREEN across both jobs and all required gates.

## CURRENT_FINDINGS
- PR #37 integration introduced only its existing Web UI production-presentation milestone changes; no gameplay, rating, growth, event, catcher gameplay, test, or workflow logic was modified during stale-base resolution.
- Production DTO/type compatibility is validated by the PR web build/tests and adapter coverage on the latest-main-integrated head.
- Main remains repository-wide GREEN after PR #37 integration.
- PR #37 intentionally provides the transport-agnostic `ProductionPresentationProvider` / `BackendPresentationGateway` contract; a concrete browser-to-Python transport remains a separate production-wiring task, not a blocker to PR #37's completed milestone.

## BLOCKERS
- None for PR #37 integration or current main CI.

## OPEN_ITEMS
- Implement and validate a concrete `BackendPresentationGateway` transport before the browser can consume Python presentation DTOs directly in live production.
- Perform Vercel deployment only when that concrete browser integration requires user-visible verification.

## DEPENDENCIES
- 06: PR #37 is merged; Web UI milestone is unblocked and integrated into production main.
- 05: balance/production validation remains an independent readiness input for future simulation changes.
- Future browser-live production wiring depends on a concrete backend transport contract implementation.

## NEXT_ACTION
- Begin the separate concrete browser-to-Python presentation transport integration task, keeping PR #37's merged DTO/provider contracts as the frontend boundary; avoid Vercel deployment until local/integration validation is complete.

## RELATED_PRS
- #36 merged
- #37 merged

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
- BALANCE_SMOKE = PASS
- DRAFT_CALIBRATION_GATE = PASS
- PR37_DTO_TYPE_COMPATIBILITY = PASS
- PR37_LATEST_MAIN_REVALIDATION = PASS
- PR37_MERGE_READY = PASS
- PR37_MERGED = PASS
- MAIN_CI_GREEN = PASS
- PRODUCTION_UI_TRANSPORT = OPEN
