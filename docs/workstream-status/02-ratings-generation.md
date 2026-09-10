# 02 - Player Ratings & Generation

WORKSTREAM: 02 - Player Ratings & Generation
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@b52b339d175c51d6ca1d9c2d6e99ab17e770a746
STATE: ACTIVE
CURRENT_TASK: Production rating/generation contract re-audit and next calibration experiment definition
RESULT: OPEN

## LAST_COMPLETED
- Historical hitter/pitcher/catcher calibration branches exist as reference material.

## CURRENT_FINDINGS
- Historical calibration branches are not production source of truth.
- Current-main scale consistency must be re-audited before promoting old experimental conclusions.

## BLOCKERS
- None recorded yet.

## OPEN_ITEMS
- Audit hitter/pitcher/catcher raw scales and generation distributions.
- Identify reusable historical findings versus obsolete assumptions.
- Define the next calibration experiment and its validation criteria.

## DEPENDENCIES
- 08: real-world KBO reference data/provenance.
- 05: Monte Carlo validation support.
- 01: gameplay-side contract questions only when needed.

## NEXT_ACTION
- Complete current-main audit and write a bounded next experiment plan without production tuning.

## RELATED_PRS
- Historical calibration PRs #20-#27 are reference-only unless explicitly revalidated.

## RELATED_BRANCHES
- main

## GATES
- PRODUCTION_RATING_CONTRACT_AUDITED = OPEN
- NEXT_CALIBRATION_EXPERIMENT_DEFINED = OPEN
