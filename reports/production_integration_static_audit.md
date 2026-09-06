# Production Integration Consolidation — Static Audit

## Scope

Repository: `ogw07222-tech/baseball-player-sim`

Base: `main@1477fc3aecf9224d1b34f77a5d755880c9c88bfe`

Consolidation branch: `feature/production-integration-consolidation`

This audit is intentionally separate from runtime validation. GitHub Actions has repeatedly failed before runner allocation (`runner_id=0`, `steps=[]`), so no consolidation-specific test command has executed yet.

## Canonical foundations

- PR #11 H3.2.1 production port is already merged into `main` and is not replayed.
- PR #18 PersistentInningEngine is already merged into `main` and is not replayed.
- The consolidation diff contains no changes to `src/hitting/model.py`, `src/hitting/parameters.py`, `src/hitting/baserunning.py`, `src/hitting/defense.py`, `src/pitching/`, or `web/`.

## Finding 1 — inherited-run pitcher R attribution

Status: **FIXED IN CONSOLIDATION**

The dynamic pitcher provider can change pitchers during an inning. The original stacked implementation credited `event.runs_scored` to whichever pitcher was active when the run scored. That is incorrect for inherited runners.

The consolidation now tracks run responsibility by runner identity. Scoring identities are recovered from exact `BattingLine.R` deltas around each event, and a runner is charged to the pitcher who allowed that runner to reach base. A batter who scores without a prior on-base responsibility entry (for example, the batter on a home run) is charged to the current pitcher.

This changes stat accounting only. It does not change H3.2.1, pitching outcome probability, pitcher raw ratings, or inning/base-running probability math.

Regression helpers were added for:

- scoring-runner identity recovery from run deltas;
- inherited runner charged to original pitcher while the current batter/run is charged to the reliever.

Runtime execution is still pending.

## Finding 2 — bases-loaded fielder's-choice lead-force mismatch

Status: **OPEN / BLOCKING NATURAL-EVENT READY**

PR #21 documentation says multi-force ground-ball states use the available lead force. Under bases loaded, the lead force is at home.

The currently consolidated `BaseStateResolver.fielders_choice()` instead scores the runner from third when first, second, and third are occupied with fewer than two outs. That behavior does not match the documented lead-force contract.

Expected minimal lead-force behavior for bases loaded:

- runner from third is retired at home;
- runner from second advances to third;
- runner from first advances to second;
- batter reaches first;
- one out is recorded;
- no run scores on that force play.

This should be fixed with a targeted partial patch and a deterministic regression test before `NATURAL_EVENTS_INTEGRATION_READY` can be marked READY.

No H3 probability retuning is required.

## Finding 3 — persistent team W/L/T missing from advance state

Status: **OPEN / BLOCKING COMPOSITIONAL ADVANCE READY**

`ProductionGameResult` provides an exact final score and exact per-game W/L/T. `AdvanceSummary` also reports period win/loss/tie deltas.

However, `AdvancePipelineState` does not currently persist cumulative team W/L/T. It persists player season/career stats and a capped recent-game history only.

Therefore the required persistent-state equivalence contract cannot yet prove or preserve:

- cumulative team wins;
- cumulative team losses;
- cumulative team ties;

across repeated one-game advance versus one week/month advance, especially after recent history is truncated.

A production-level team-record state (or equivalent canonical persistent field) is required. It must be optional/backward-compatible for old saves and included in compositional equality tests.

## Finding 4 — ER / ERA validity metadata is incomplete

Status: **OPEN / NON-FABRICATION REVIEW REQUIRED**

The full-game provider correctly marks `ER`, `W`, `L`, `SV`, and `HLD` unsupported where exact provenance/rules are unavailable.

The generic aggregation container nevertheless stores `ER=0` by default and exposes an `ERA` property whenever outs exist. Generic `unsupported_pitcher_fields()` also does not currently include `ER` when the source lacks it.

This creates a risk that an unsupported ER/ERA could be presented as a real zero rather than “not supported / not valid”.

Before production UI/provider promotion, the aggregate contract should carry explicit validity/support metadata for ER-derived outputs or omit ERA where ER provenance is unavailable. Do not invent ER from runs.

## GitHub Actions execution status

Current classification:

`GITHUB_ACTIONS_EXECUTION = NOT_RUN_INFRASTRUCTURE_LIMIT`

Observed behavior on consolidation runs:

- `runner_id=0`
- `steps=[]`
- no runner name
- no test/import/build command executed

This is infrastructure non-execution, not a code assertion failure.

## Current static gate impact

- `H32_CANONICAL_BEHAVIOR_PRESERVED = READY` — protected H3 files remain byte-identical to latest main.
- `PERSISTENT_INNING_CANONICAL_PRESERVED = READY_STATIC / NOT_RUN_RUNTIME`.
- `NATURAL_EVENTS_INTEGRATION_READY = NOT_READY` — bases-loaded FC lead-force mismatch remains.
- `STAT_AGGREGATION_INTEGRATION_READY = NOT_READY` — ER/ERA validity contract still needs explicit resolution and runtime regression.
- `TIME_ADVANCE_INTEGRATION_READY = NOT_READY` — cumulative team W/L/T is not persistent.
- `FULL_GAME_PROVIDER_INTEGRATION_READY = NOT_READY` — runtime sanity unavailable; inherited-run R fix is unexecuted.
- `PITCHER_DYNAMIC_ROLE_READY = READY_STATIC / SOURCE_VALIDATED`.
- `PITCHER_ROTATION_READY = READY_STATIC / SOURCE_VALIDATED`.
- `PITCHER_CONSECUTIVE_FATIGUE_READY = READY_STATIC / SOURCE_VALIDATED`.
- `PITCHER_BULLPEN_USAGE_READY = NOT_READY` — consolidated full-game runtime unavailable.
- `CATCHER_ABILITY_SCHEMA_READY = READY_STATIC`.
- `CATCHER_GENERATION_READY = NOT_READY` — consolidation generation regression unavailable.
- `CATCHER_GROWTH_FOUNDATION_READY = NOT_READY` — consolidation regression unavailable.
- `CATCHER_SAVE_COMPATIBILITY_READY = NOT_READY` — consolidation save regression unavailable.
- `SAVE_COMPATIBILITY_READY = NOT_READY` — runtime regression unavailable.
- `COMPOSITIONAL_ADVANCE_READY = NOT_READY` — team record missing from persistent state and runtime regression unavailable.
- `FULL_REGRESSION_READY = NOT_READY`.
- `PRODUCTION_INTEGRATION_CONSOLIDATION_READY = NOT_READY`.

## Required next execution

Once a Codespaces/local runner is available, run:

```bash
bash tools/run_production_integration_checks.sh
```

Before marking the consolidation READY, also add targeted tests for:

1. bases-loaded fielder's-choice lead force;
2. inherited-run pitcher responsibility in an actual mid-inning substitution scenario;
3. cumulative team W/L/T persistence and week/month compositional equivalence;
4. ER/ERA unsupported-state propagation.
