# 07 - Integration & GitHub

WORKSTREAM: 07 - Integration & GitHub
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@4b90f565ea9f846e9450340bf0ade77eff0c44d8
STATE: DONE
CURRENT_TASK: PR #38 / #39 sequential production integration
RESULT: PASS — PR #38 merged first; PR #39 reconciled onto post-#38 main, revalidated, and merged; production integration regression GREEN

## LAST_COMPLETED
- Validated PR #38 `feature/production-season-lifecycle-v1@fcffdba5670e4322d4542967fcd24d51a046271b` and merged it first as `4aba1adcd60acb98558145e42dca2cfc45423388`.
- Post-#38 main workflow run #619 completed SUCCESS.
- Rechecked PR #39 after #38 merge; GitHub reported the expected conflict in shared `src/career.py`.
- Resolved #39 against post-#38 main with merge-resolution head `f8ad51e8ff44f8079ad3bd57b23311c2e84b67e5`, preserving #38 lifecycle finalization and adding only #39 observational hooks.
- Fresh PR #39 workflow run #621 completed SUCCESS: full Python unit suite, Auto career smoke, Balance smoke, draft calibration gate, web build, and web tests all passed.
- PR #39 merged as `b97a4aca7ebc339de71e178f88a75faa68df7764`.
- Post-#39 main workflow run #622 completed SUCCESS across both test jobs and all required gates.
- Subsequent main changes through `4b90f565ea9f846e9450340bf0ade77eff0c44d8` are unrelated CI/docs integration changes; merged #38/#39 code remains present.

## CURRENT_FINDINGS
- Integration order #38 -> #39 was retained because #38 owns Growth/Career lifecycle finalization while #39 observes authoritative draft/roster/appearance transitions.
- The only direct changed-file overlap between #38 and #39 was `src/career.py`.
- Conflict resolution preserved `SeasonFinalizationResult`, `finalize_completed_pro_season()`, and #38 `finish_pro_season()` semantics.
- #39 observational hooks for draft/pro entry, call-up, first-team debut, demotion, and roster transitions were layered without changing roster probabilities or lifecycle RNG semantics.
- Append-only `career_history`, save/load compatibility, deterministic RNG-free narrative rendering, and dedupe tests are present on current main.
- No gameplay probability, rating scale, growth coefficient, event effect, fatigue/injury/form formula, or test threshold was retuned.
- Code integration main `b97a4aca7ebc339de71e178f88a75faa68df7764` passed run #622; current main `4b90f565ea9f846e9450340bf0ade77eff0c44d8` still contains the same #38/#39 code tree for affected files.

## BLOCKERS
- None for PR #38 / #39 production integration.

## OPEN_ITEMS
- 05 long-run lifecycle equivalence/distribution validation remains an independent non-blocking validation item from PR #38.
- Future contract/FA/trade/posting/service-time systems remain outside these PR scopes.
- Career-history presentation in Web UI remains a future 06-facing integration task if exposed to players.

## DEPENDENCIES
- 03: Production Season Lifecycle Bridge v1 is merged and is the lifecycle production contract.
- 04: Career Spine v1 is merged as an observational layer over authoritative 03 transitions.
- 05: may run long-run lifecycle/career-history regression validation without retuning production semantics.
- 06: may consume career-history data later; no frontend change was required for these backend integrations.

## NEXT_ACTION
- Treat current main as the integration baseline for subsequent CareerEngine/lifecycle work; run 05 long-run validation separately if prioritized.

## RELATED_PRS
- #38 merged
- #39 merged

## RELATED_BRANCHES
- main
- feature/production-season-lifecycle-v1
- feature/career-spine-v1

## GATES
- PR38_TARGETED_LIFECYCLE = PASS
- PR38_SAVE_LOAD_BOUNDARY = PASS
- PR38_HEADLESS_EQUIVALENCE = PASS
- PR38_FULL_PYTHON_SUITE = PASS
- PR38_MAIN_CI = PASS
- PR39_CONFLICT_RESOLUTION = PASS
- PR39_APPEND_ONLY_HISTORY = PASS
- PR39_DEDUPE = PASS
- PR39_SAVE_LOAD = PASS
- PR39_RNG_FREE_NARRATIVE = PASS
- PR39_ZERO_SIMULATION_MUTATION = PASS
- PR39_FULL_PYTHON_SUITE = PASS
- WEB_BUILD_TESTS = PASS
- AUTO_CAREER_SMOKE = PASS
- BALANCE_SMOKE = PASS
- DRAFT_CALIBRATION_GATE = PASS
- MAIN_CI_GREEN = PASS
