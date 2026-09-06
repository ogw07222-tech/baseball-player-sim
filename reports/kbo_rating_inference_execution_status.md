# KBO First-Team Population + Real-Player Rating Inference — Execution Status

## Source

- canonical `main` at task start: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- stacked calibration base: `feature/overnight-hitter-pitcher-calibration@c6c69ceefb3c4f2f5fbe88a772b4508f842e58dd`
- work branch: `feature/kbo-first-team-rating-inference`

## Frozen contracts

This branch does not modify:

- `src/hitting/model.py`
- `src/hitting/parameters.py`
- `src/hitting/baserunning.py`
- `src/hitting/normalization.py`
- `src/pitching/physical_velocity.py`
- production S/C/B raw recenter
- frozen KBO objective/tolerances

Velocity remains measured-average-fastball first. H3.2.1 remains frozen.

## Implemented calibration infrastructure

- production `CareerEngine` first-team player-season sampler, retaining only first-team PA > 0;
- first-team PA weighting and weighted means/SD/quantiles;
- multi-seed neutral-H3 offense diagnostic;
- explicit best-available generated pitcher pool with a non-fabricated usage-weight limitation marker;
- 2025 real KBO hitter/pitcher source-table collector with provenance fallback;
- frozen Velocity v2 inverse mapping;
- staged hitter candidate library + local refinement + near-equivalent candidates;
- measured-velocity-first pitcher S/C/B candidate search, conditional on a READY first-team Joint v4;
- generated-vs-real weighted distribution comparison;
- Joint v4 rerun that samples hitters by actual generated first-team PA;
- contract/unit tests and frozen-formula diff guard;
- pilot and full-scale GitHub Actions workflows.

## Current execution blocker

GitHub Actions did not allocate a hosted runner to either the new calibration workflow or the repository's existing `tests` workflow on the same HEAD. Jobs ended with:

- `runner_id = 0`
- no runner name
- zero executed steps

Therefore these failures are not calibration/test failures and no Monte Carlo output from those attempts is treated as evidence.

Until an actual runner executes the pipeline, the new population/inference gates remain NOT_READY/NOT_RUN rather than being inferred from unexecuted code.

## Current gate status

KBO_FIRST_TEAM_POPULATION_CONTRACT_READY = NOT_READY

KBO_REAL_PLAYER_RATING_INFERENCE_READY = NOT_READY

KBO_GENERATED_REAL_RATING_ALIGNMENT_READY = NOT_READY

PITCHER_JOINT_CALIBRATION_V4_READY = NOT_RUN

FULL_HITTER_PITCHER_VALIDATION_READY = NOT_RUN
