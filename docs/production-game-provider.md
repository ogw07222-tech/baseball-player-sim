# Production Full-Game Provider Integration

## Responsibility boundaries

This integration is orchestration only. It stacks the persistent inning engine and natural-baseball-events work on top of the frozen H3.2.1 production gameplay math, then connects the independent stat aggregation/date-advance foundation.

Probability ownership remains:

- `src/hitting/model.py`: H3 hitting / batted-ball outcome math
- `src/hitting/defense.py`: validated defense resolution
- `src/hitting/baserunning.py`: validated steal / XBT / DP math
- `src/natural_events.py`: natural event interpretation
- `src/pitching/*`: existing pitcher gameplay/fatigue contracts

The full-game provider does not duplicate or retune those formulas.

## Dependency stack

Integration base:

1. `feature/persistent-inning-state` / PR #18
2. `feature/natural-baseball-events` / PR #21
3. the five independent files from PR #26 (`stat_aggregation` / `time_advance`)
4. this provider integration

Calibration branches, hitter-normalization experiments, Velocity work and Pitcher Joint calibration are deliberately not in the base.

## Full-game flow

`GameFixture` → `LineupProvider` → `PitcherGameplayProvider` → `PersistentInningEngine` → actual PA/base-state events → `ProductionGameResult` → career user's `GamePerformance` → `AdvanceOrchestrator` → period/season/career aggregates.

Every scheduled game runs the same persistent H3 engine. Week/month advance is composition of individual games; there is no aggregate FastSim formula.

## Lineup contract

`LineupProvider.lineup(team, level)` must return exactly nine distinct `Player` objects in batting order.

The included `DeterministicNeutralLineupProvider` is an integration fallback, not manager AI. It supplies stable neutral NPCs. The career player replaces the canonical slot for his position only when the existing CareerEngine participation decision says he starts.

A future roster/manager layer can replace the provider without changing gameplay math.

## Pitcher contract

`PitcherGameplayProvider.plan()` supplies a `TeamPitchingPlan` containing a starter and bullpen gameplay `PitcherProfile`.

The temporary provider uses the repository's existing `PitcherProfile.from_level()` adapter for both slots. It adds no Stuff/Control/Breaking/Velocity coefficient.

Because the current full-game engine has no substitution manager, the integration fallback changes from starter to generic bullpen only between the sixth and seventh innings. This is an orchestration safety policy to avoid a nine-inning starter default, not a pitcher-quality or fatigue formula.

Future Joint-v4/rotation work can implement `PitcherGameplayProvider` without editing the full-game provider.

## Pitcher stat extraction

Per active pitcher the provider records directly from game events:

- G / GS
- BF
- outs pitched
- H
- R
- HR
- BB
- HBP
- SO

The fallback changes pitchers between innings, so inherited-run ownership is not ambiguous and R is exact for this policy.

ER and official W/L/SV/HLD are explicitly unsupported. Error provenance and official substitution/decision state are not sufficient to calculate them without inventing rules.

## Team result

`ProductionGameResult` derives W/L/T only from the persistent engine final score. No separate team-result probability exists.

## Career participation

`CareerGameAdvanceProvider` reuses the existing CareerEngine rules:

- current FIRST/FARM level
- injury availability
- `_play_probability()`
- fatigue update
- injury check
- form update
- roster reconsideration
- career-event scheduling

No new appearance probability is introduced.

A non-started career player can have zero personal PA while the full team game still runs and contributes an exact team result.

## Date advance

`ProductionAdvanceService` composes PR #26's `AdvanceOrchestrator` with the full-game provider.

Supported operations:

- `advance_one_game()`
- `advance_one_week()`
- `advance_one_month()`

Week/month execution iterates each scheduled date and runs a fresh full game.

`CareerSeasonScheduleProvider` is temporary deterministic date plumbing for the existing 144-game season. It is not a new KBO scheduler: it places games on non-Mondays from April 1 until a canonical schedule provider is available.

## Aggregation

The career user's exact game `BattingLine` is copied from his actual lineup slot. It is then:

1. added to the current `SeasonRecord`,
2. converted through `hitter_stats_from_result`,
3. added to `AdvancePipelineState`,
4. accumulated into period, season and career totals.

Team W/L/T comes from final score and is available to `AdvanceSummary`.

## Save integration

`AdvancePipelineState` is an optional top-level save key named `advance_state`.

Old saves that omit it load exactly as before. No `SAVE_VERSION` bump is required because the new key is optional and zero/default reconstruction is supported.

The capped recent `GamePerformance` history is enough for last-10, weekly/monthly backend summaries without retaining every pitch or PA event.

## Event retention

The provider does not store full event logs by default. It retains only a small capped notable-event list (HR, SB/CS, walkoff, high-K) plus exact final stat lines and score.

## Determinism

The provider uses the caller's existing `RNG`. With identical seed, fixture, lineups, ratings and initial state it produces identical score and stat lines.

## Limitations / future hooks

- deterministic neutral NPC lineup fallback until a canonical roster provider exists
- deterministic date adapter until a real league schedule provider exists
- no pinch-hitting / defensive replacements
- no pitcher manager/role AI
- generic bullpen slot after six completed innings
- ER unsupported
- W/L/SV/HLD unsupported
- user-pitcher career path is interface-ready but not yet wired to a pitcher roster
- WP/PB remain disabled by the natural-events contract
- current advance service does not replace existing season-finalization/growth logic

These are integration/provider limitations. They must not be fixed by retuning H3, pitcher calibration, normalization, or growth formulas.
