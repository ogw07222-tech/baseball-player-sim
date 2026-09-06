# Stat Aggregation and Advance Foundation

## Scope and source

Branch: `feature/stat-aggregation-advance-foundation`

Base: `main@44b4bbb9113e351ceb35aac75f02a8ee6eab3723`

This foundation owns **counting-stat transport, aggregation, date-window
composition, serialization, and UI-ready summaries only**. It does not own or
change any hitting, pitching, normalization, growth, event, injury, or
calibration probability.

At the base SHA, `src/inning.py` is not present on `main`; the persistent inning
engine exists in a separate PR. This foundation therefore depends on provider
interfaces instead of importing that branch.

## Stat ownership

Gameplay owns events and outcomes.

Aggregation owns:

`game result -> exact counting stats -> period totals -> season totals -> career totals`

Derived rates are always recalculated from cumulative counting totals. Per-game
AVG/OBP/SLG/ERA values are never averaged.

### Hitter counting stats

Supported by the foundation container:

- G, PA, AB, R, H, 1B, 2B, 3B, HR, RBI
- BB, HBP, SO, SB, CS, GDP, SF

The current production `BattingLine` supplies all except SF at the base SHA.
The adapter reads SF when a future provider exposes it and otherwise uses zero
while marking it unsupported at the game-adapter boundary.

### Hitter derived stats

Centralized in `HitterCountingStats`:

- AVG = H / AB
- OBP = (H + BB + HBP) / (AB + BB + HBP + SF)
- SLG from total bases / AB
- OPS = OBP + SLG
- ISO = SLG - AVG
- BABIP = (H - HR) / (AB - SO - HR + SF)
- BB%, K%, HR% use PA as denominator

### Pitcher counting stats

Foundation container:

- G, GS, BF, OUTS_PITCHED
- H, R, ER, HR, BB, HBP, SO
- W, L, SV, HLD

The current production `PitchingLine` safely provides G, BF, outs, H, ER, HR,
BB, and SO. GS can be supplied by caller context. R, HBP, W/L/SV/HLD are not
invented; absent fields remain zero and are reported as unsupported.

### Pitcher derived stats

- IP is derived from outs; `IP_display` uses baseball notation such as 3.1
- ERA = ER * 27 / outs
- WHIP = (H + BB) * 3 / outs
- K%, BB%, HR% use BF
- K/9, BB/9, HR/9 use outs

FIP is intentionally not part of this foundation.

## Containers

`src/stat_aggregation.py` provides:

- `HitterCountingStats`
- `PitcherCountingStats`
- `GameStatLine`
- `PeriodStatLine`
- `SeasonStatLine`
- `CareerStatLine`
- `GamePerformance`

`GamePerformance` also carries date, level (`FIRST`/`FARM`), optional opponent,
optional team result/score, notable events, and unsupported-stat metadata.

First-team and farm counting totals are stored separately. An `overall` view is
derived by adding the two counting lines.

## Adapter boundary

Adapters consume existing production objects by their output contract:

- `hitter_stats_from_result()`
- `pitcher_stats_from_result()`
- `game_performance_from_results()`
- `season_stats_from_record()`
- `career_stats_from_records()`

No gameplay module imports this foundation to calculate a probability. The
dependency direction is one-way: aggregation consumes gameplay output.

## Advance contract

`src/time_advance.py` defines:

- `ScheduleProvider`
- `GameAdvanceProvider`
- `AdvancePipelineState`
- `AdvanceSummary`
- `AdvanceResultViewModel`
- `AdvanceOrchestrator`

The date contract treats `current_date` as the last completed calendar date.
A provider returns scheduled dates satisfying:

`current_date < game_date <= requested_end_date`

### advance_one_game

Find the next scheduled date and invoke exactly one `GameAdvanceProvider`
operation.

### advance_one_week

Advance the calendar seven days and invoke the game provider once for every
scheduled date in that interval.

### advance_one_month

Advance to the same day in the next calendar month (clamped to the month's last
day) and invoke the provider once for every scheduled date in the interval.

A week/month is never synthesized as one random aggregate result.

## Compositional equivalence

Given the same starting state, schedule, deterministic game provider, and
results:

- one weekly advance produces the same counting totals as repeatedly advancing
  the same scheduled games individually;
- one monthly advance produces the same counting totals as the same individual
  game sequence.

Only the final calendar cursor differs naturally: a period advance moves to the
period end, while repeated one-game advance stops on the final game date.

## Period summaries

`get_weekly_summary()` uses the rolling seven-day window ending at the current
date.

`get_monthly_summary(year, month)` filters the capped recent-history buffer.

The default recent-history cap is 64 game records, enough for last-10 plus
current/previous-month UI use in ordinary schedules while preventing unbounded
save growth. Historical month queries outside the retained window are not
guaranteed.

## Team result support

Team W/L/T is aggregated only when the `GamePerformance` provider supplies a
team result. The current player-centric main simulation does not expose a
canonical team game result, so the contract supports `team_result = None`.
No score or win/loss formula is invented here.

Limitation flag:

`TEAM_GAME_RESULT_PROVIDER_NOT_READY`

## Pitcher game result support

The current FastSim pitching line does not own official decisions or all
scoring fields. Those fields remain explicit zero/default/unsupported values
until a canonical game-result provider supplies them.

Limitation flag:

`PITCHER_FULL_GAME_RESULT_PROVIDER_NOT_READY`

## Event and rating extension points

`AdvanceSummary` can carry:

- roster changes detected by an injected roster-state provider
- notable events already emitted by a game provider
- raw/display rating before/after snapshots and deltas

It does not run growth, roster, event, or injury formulas itself.

`AdvanceResultViewModel` rejects rating keys containing normalized/gameplay/
effective prefixes, so normalized internal gameplay ratings are not exposed
through this stat/UI boundary.

## Persistence policy

`AdvancePipelineState` is JSON-serializable with:

- current date
- current season aggregate
- career aggregate
- completed season aggregates
- capped recent game history
- history limit

`from_dict()` treats missing state as a zero/default structure. Existing saves
are therefore not invalidated by this foundation.

The current `save_game()` payload is deliberately not modified in this branch:
there is no canonical production `GameAdvanceProvider` on main yet. A future
integration may store the state under one optional save key without changing
the container contract.

## Parallel-work safety

This branch is based directly on `main`, not on calibration or persistent-inning
branches.

Protected files are not modified:

- `src/simulation.py`
- `src/hitting/*`
- `src/pitching/*`
- `src/growth.py`
- `src/config.py`
- `src/stats.py`
- calibration tools/reports/data

Regression tests also compare protected production file Git blob hashes against
the base SHA so accidental formula edits fail CI.

## Known limitations

- `src/inning.py` is not on main at the branch base, so inning-state integration
  is intentionally deferred to an adapter.
- No canonical team W/L provider exists in current main.
- Current pitching FastSim does not provide official W/L/SV/HLD or HBP/R
  ownership.
- Monthly history queries depend on the retained history cap.
- This foundation does not change existing `SeasonRecord` persistence; it
  provides independent backward-compatible serialization ready for later
  optional embedding.
