# Production Game Provider Integration Summary

## 1. Branch

- Integration branch: `feature/production-game-provider-integration`
- Draft PR: #28 `Production full-game provider and advance integration`
- PR target: `feature/natural-baseball-events`
- Canonical main at task start: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- Natural-events dependency: `feature/natural-baseball-events@82192e6545ecc59e96112e1df2383d70e204c916`
- Stat aggregation/advance foundation was stacked from PR #26 without gameplay formula changes.

## 2. Source PR dependencies

Required integration order remains:

1. PR #18 — persistent inning/base-state engine
2. PR #21 — natural baseball events, stacked on PR #18
3. PR #26 foundation content — exact stat aggregation and compositional date advance
4. PR #28 — production full-game provider orchestration

Calibration branches PR #19–#27 are not used as the integration base. In
particular, no Pitcher Joint search coefficient, hitter normalization candidate,
real-player inference output, or broad-spectrum calibration result is hardcoded
in this provider.

## 3. Changed files owned by this integration

Provider integration adds/changes:

- `src/game_result.py`
- `src/game_provider.py`
- `src/production_advance.py`
- `src/persistence.py` (optional `advance_state` only)
- `tests/test_production_game_provider.py`
- `tests/test_production_game_provider_contracts.py`
- `tools/production_game_provider_sanity.py`
- `.github/workflows/production-game-provider-sanity.yml`
- `docs/production-game-provider.md`
- this report

The PR also contains the five PR #26 foundation files because that PR is still
independent/unmerged.

## 4. Formula files unchanged

Relative to the PR #21 dependency base, this integration makes no changes to:

- `src/simulation.py`
- `src/hitting/model.py`
- `src/hitting/parameters.py`
- `src/hitting/baserunning.py`
- `src/hitting/defense.py`
- `src/natural_events.py`
- `src/pitching/model.py`
- `src/pitching/parameters.py`
- `src/pitching/growth.py`
- `src/growth.py`
- `src/config.py`
- `src/stats.py`

`tests/test_production_game_provider.py` contains Git blob guards for the frozen
formula/growth files so a real CI checkout will fail if an integration commit
changes them.

## 5. Full-game architecture

Production path:

`GameFixture`
→ 9-player `LineupProvider`
→ `PitcherGameplayProvider`
→ `PersistentInningEngine`
→ H3.2.1 PA outcomes
→ persistent bases/outs/score
→ natural XBT / tag-up / SF / ground advancement / DP / steals
→ final score and per-lineup `BattingLine`
→ `ProductionGameResult`
→ user `GamePerformance`
→ exact stat aggregation
→ `AdvancePipelineState`
→ `AdvanceSummary`.

No separate FastSim probability formula is introduced. The batch sanity runner
uses the same `ProductionGameProvider` and only reduces retained notable-event
volume.

## 6. Lineup / participation contract

A full game always contains two nine-player batting orders. The default lineup
provider is a stable deterministic neutral fixture and is explicitly temporary;
it is not manager AI.

`CareerGameAdvanceProvider` does not invent a new participation formula. It
reuses the current CareerEngine state and existing `_play_probability`, injury,
FIRST/FARM, fatigue, form, roster reconsideration, and career-event paths.
The user is inserted into their real lineup slot only when that existing
participation decision says they play. Otherwise the full team game still runs
and the user receives a zero-appearance `GamePerformance` with participation
metadata.

## 7. Player stat coverage

Hitter full-game extraction supports:

- G
- PA / AB
- R
- H / 1B / 2B / 3B / HR
- RBI
- BB / HBP / SO
- SB / CS
- GDP
- SF

The exact `BattingLine` emitted by the persistent engine is converted by the PR
#26 aggregation adapter and is also added to the existing career season record.

## 8. Pitcher stat coverage

The integration can count from the actual full-game event stream:

- G
- GS
- BF
- outs pitched
- H
- R
- HR
- BB
- HBP
- SO

A temporary deterministic handoff replaces the starter after six completed
innings with one generic bullpen slot built from the same existing
`PitcherProfile`/team-level contract. It adds no bullpen quality coefficient and
prevents a permanent 9-IP-starter production default.

Official scoring fields remain deliberately unsupported:

- ER
- W / L
- SV / HLD

No approximation is invented. A later pitching-usage/scoring provider can
replace the fallback without changing the game-provider orchestration.

## 9. Team result support

Team W/L/T is derived directly from the final persistent-engine score.
There is no random or independent team-result sampler in the production advance
path.

This resolves the architectural blocker named
`TEAM_GAME_RESULT_PROVIDER_NOT_READY` in PR #26, subject to executable regression
validation.

## 10. Advance support

`ProductionAdvanceService` exposes:

- `advance_one_game()`
- `advance_one_week()`
- `advance_one_month()`

Week and month operations are chronological compositions of the same full-game
provider. No weekly/monthly aggregate stat roll is generated.

The temporary `CareerSeasonScheduleProvider` only assigns dates to the existing
144-game career contract and skips Mondays. It is not presented as a canonical
KBO scheduling model and can be replaced behind the existing `ScheduleProvider`
interface.

## 11. Determinism / compositional equivalence

The implementation includes tests for:

- same seed -> same full score, batting lines, pitcher lines and event counts
- one-week result == repeated one-game results on the same schedule
- one-month result == repeated one-game results on the same schedule
- season/career counting totals == exact sum of emitted game performances

These tests are committed but have not yet received executable CI evidence in
the current repository runner state; see section 17.

## 12. Persistent runner-state coverage

Required contracts are covered by the stacked PR #18/#21 tests and explicit
provider-integration contract tests:

- batting-order persistence
- bases cleared between half innings
- walkoff termination
- extra-inning termination
- steal mutates real first/second-base state
- 1B -> 3B
- 2B -> Home
- DP mutates outs and bases
- sacrifice fly scores the real runner

These tests call the existing persistent inning/natural-event APIs rather than
reimplementing their probabilities.

## 13. Save compatibility

The existing save version is not bumped.

When a `ProductionAdvanceService` is active, `src.persistence` stores its
`AdvancePipelineState` under optional top-level `advance_state`.

- new save: state round-trips
- old save: missing key remains valid
- Player/Season serialization remains unchanged
- RNG seed/state serialization remains unchanged

## 14. Recent history / backend view model

The PR #26 foundation retains a capped recent `GamePerformance` history and
supports last-10, weekly and monthly aggregation. `AdvanceResultViewModel`
provides raw backend contracts for period hitting/pitching, team record, season
totals, rating delta and notable events. No `web/` file is modified.

## 15. Monte Carlo sanity plan

Committed runner:

`python tools/production_game_provider_sanity.py --games 10000 --seed 20260906`

It measures without tuning:

- runs / team / game
- hits / team / game
- HR / game
- BB / game
- K / game
- extra-inning percentage
- walkoff percentage
- average innings
- PA / team / game and lineup-slot PA distribution
- safety-cap hit rate
- runtime / games per second

It also benchmarks 1 game, a 6-game week, a 26-game month and 144 games.

**Current result: NOT EXECUTED.** No distribution number is published because
GitHub-hosted jobs were not allocated a runner.

## 16. Performance result

**NOT EXECUTED.** The benchmark exists, but this report intentionally does not
invent latency numbers in the absence of an executed runner.

## 17. Tests / CI status

At integration code HEAD `a3adb78fdb9fa79e6be14cdc52a62da893975e1b`,
GitHub created both workflows but allocated no executable steps:

- repository `tests` run: `34018630189`
- production full-game sanity run: `34018630195`

The `unit-tests`, `web-tests`, and `full-game-sanity` job objects completed with
zero steps. This matches the repository-level runner-allocation issue seen on
recent calibration branches.

Therefore:

- those workflow conclusions are **not evidence of a code/test failure**;
- they are also **not PASS evidence**;
- READY gates that require executed tests/Monte Carlo remain blocked.

The branch now also includes explicit required-contract tests and the workflow
runs full repository unit discovery before the 10k sanity whenever a runner is
available.

## 18. Known limitations

1. Canonical roster/lineup selection is not yet available; the deterministic
   neutral lineup is an integration fallback.
2. The career adapter reuses the existing user participation probability rather
   than implementing bench/substitution manager AI.
3. Pitcher usage is a minimal starter-to-one-bullpen fallback. It is not a
   rotation/bullpen manager.
4. ER and official pitching decisions remain unsupported.
5. Canonical KBO schedule generation is not part of this task.
6. Wild pitch/passed-ball generation remains disabled until its own approved
   probability layer exists.
7. Pitcher calibration/Joint-v4 output can later replace the pitcher gameplay
   adapter without changing this orchestration code.
8. Web UI/provider wiring remains separate.

## 19. Gate table

Because executable CI/Monte Carlo evidence is currently unavailable, structural
implementation is complete but promotion gates remain conservative:

| Gate | Status | Reason |
| --- | --- | --- |
| `PRODUCTION_FULL_GAME_PROVIDER_READY` | **NOT_READY** | implementation complete; executable full suite + 10k sanity not yet run |
| `TEAM_GAME_RESULT_PROVIDER_READY` | **NOT_READY** | final-score path implemented; executable integration validation pending |
| `PITCHER_FULL_GAME_RESULT_PROVIDER_READY` | **PARTIAL** | BF/outs/H/R/HR/BB/HBP/SO implemented; ER and official decisions intentionally unsupported |
| `ADVANCE_FULL_GAME_INTEGRATION_READY` | **NOT_READY** | compositional implementation/tests committed; executable validation pending |
| `SAVE_GAME_PIPELINE_READY` | **NOT_READY** | backward-compatible optional state implemented/tests committed; executable validation pending |

## 20. Merge recommendation

**Do not merge to main yet. Keep PR #28 Draft.**

Recommended order:

1. land/retarget PR #18;
2. land/retarget PR #21 and rerun its existing validation;
3. reconcile PR #26 foundation ownership;
4. rerun PR #28 provider tests + full repository suite + 10k full-game sanity on
   an actual GitHub runner;
5. inspect structural failures as integration/provider/scoring/performance bugs,
   never by retuning H3, hitter normalization, Velocity, S/C/B or growth;
6. only then promote the READY gates and retarget PR #28 to current `main`.
