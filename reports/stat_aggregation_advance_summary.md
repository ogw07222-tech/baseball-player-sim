# Stat Aggregation / Advance Foundation Summary

## 1. Branch

`feature/stat-aggregation-advance-foundation`

## 2. Base SHA

`44b4bbb9113e351ceb35aac75f02a8ee6eab3723`

The branch was created directly from latest `main`, not from any calibration,
pitcher, normalization, or persistent-inning branch.

## 3. Implementation HEAD

`92725bc242db37fa0ca9f465804b162cf7139451`

This is the complete five-file implementation/report HEAD used by Draft PR #26 and CI run #416 attempts 1-2 before the CI-status amendment commit.

## 4. Changed files

Foundation-only diff:

- `src/stat_aggregation.py`
- `src/time_advance.py`
- `tests/test_stat_aggregation_advance.py`
- `docs/stat-aggregation-and-advance.md`
- `reports/stat_aggregation_advance_summary.md`

No gameplay formula module is part of this diff.

## 5. Untouched calibration/gameplay files

Protected at the base Git blob level by tests:

- `src/simulation.py`
- `src/hitting/model.py`
- `src/hitting/parameters.py`
- `src/hitting/baserunning.py`
- `src/hitting/defense.py`
- `src/growth.py`
- `src/config.py`
- `src/stats.py`
- all existing `src/pitching/*` files

No KBO target, tolerance, calibration report, real-player inference, generation,
normalization, or H3.2.1 formula is changed.

## 6. Hitter stat coverage

Counting:

G, PA, AB, R, H, 1B, 2B, 3B, HR, RBI, BB, HBP, SO, SB, CS, GDP, SF.

Derived centrally from totals:

AVG, OBP, SLG, OPS, ISO, BABIP, BB%, K%, HR%.

Current production `BattingLine` maps directly; SF remains zero/unsupported
until a provider emits it.

## 7. Pitcher stat coverage

Container coverage:

G, GS, BF, OUTS_PITCHED, H, R, ER, HR, BB, HBP, SO, W, L, SV, HLD.

Derived:

IP/IP display, ERA, WHIP, K%, BB%, HR%, K/9, BB/9, HR/9.

Current production `PitchingLine` adapter safely supplies the subset available
on main. Missing official decisions/scoring fields are not inferred.

## 8. Unsupported stats / providers

Current explicit limitations:

- `TEAM_GAME_RESULT_PROVIDER_NOT_READY`
- `PITCHER_FULL_GAME_RESULT_PROVIDER_NOT_READY`
- persistent `src/inning.py` not present on current main
- official pitcher W/L/SV/HLD ownership unavailable
- pitcher HBP/R unavailable in the current `PitchingLine`
- hitter SF absent from current main `BattingLine`

These limitations do not block the aggregation foundation because adapters
carry zero/default/unsupported state rather than inventing results.

## 9. Aggregation invariants

Hitter:

- H = 1B + 2B + 3B + HR
- AB >= H
- PA >= AB
- non-negative counting stats
- derived rates recomputed from cumulative totals

Pitcher:

- outs pitched >= 0
- GS <= G
- HR <= H
- non-negative counting stats
- IP derived from exact outs

Period/season/career aggregates sum counting stats exactly. Game/season rates
are never averaged.

## 10. Advance contracts

Added provider-oriented contracts:

- one game = exactly one scheduled game provider call
- one week = all scheduled games in next seven calendar days, sequentially
- one month = all scheduled games through the same day next calendar month,
  sequentially
- period summaries aggregate exact game outputs
- same deterministic game sequence yields exact counting-stat equivalence
  between bulk period advance and repeated game advance

No random weekly/monthly stat generation is present.

## 11. Save compatibility

`AdvancePipelineState` has independent `as_dict()/from_dict()` serialization.

Missing state keys load as zero/default values, preserving compatibility with
old saves. Recent game history is capped (default 64).

The existing `src/persistence.py` payload is intentionally untouched until a
canonical production game provider is connected; no save version bump is
required for this foundation branch.

## 12. Tests

Local foundation suite before GitHub publication:

- 19 tests executed
- 17 PASS
- 2 protected-file tests skipped only because the local scratch directory has
  no `.git` metadata
- Python compile PASS

CI checkout contains Git metadata, so the two protected-file hash tests are
expected to execute there.

Coverage includes:

- hitter game aggregation and hit decomposition
- hitter derived stats from cumulative totals
- pitcher outs -> IP, ERA, WHIP
- weekly/monthly/season/career aggregation
- weekly/monthly compositional equivalence
- backward-compatible stat-state serialization
- raw-rating-only UI view model
- protected gameplay/pitcher file blob checks

## 13. CI

Draft PR #26 triggered workflow `tests` run #416 at implementation HEAD
`92725bc242db37fa0ca9f465804b162cf7139451`.

- attempt 1: unit-tests FAIL before checkout, web-tests FAIL before checkout
- attempt 2 (manual rerun): same result
- both job attempts reported `steps=[]` and `runner_id=0`; no job log blob was created
- an unrelated concurrent repository PR (#25, run #418) also failed immediately at workflow start

This is classified as `CI_INFRASTRUCTURE_BLOCKED`, not a code-test failure. The
repository-wide CI PASS gate cannot be claimed until GitHub Actions runners
execute the workflow.

Local foundation validation remains:
- 19 tests executed
- 17 PASS
- 2 Git-hash safety tests SKIP only because the scratch workspace has no `.git`
- Python compile PASS

## 14. Known limitations

1. Current main has no `src/inning.py`; PR #18 owns that work independently.
2. Team score/W-L is provider-owned and unsupported by current player-centric
   simulation.
3. Pitcher official decisions are not yet available from the stable FastSim
   line.
4. Recent-history monthly summaries are only guaranteed inside the retained
   history window.
5. The foundation state is serialization-ready but not yet embedded into the
   existing career save payload.

## 15. Next recommended integration

After a canonical team game/inning provider lands, implement a thin
`GameAdvanceProvider` adapter that converts that provider's real game outputs to
`GamePerformance`. Do not modify aggregation formulas.

Gate status:

`STAT_AGGREGATION_ADVANCE_FOUNDATION_NOT_READY`

Reason: all foundation implementation gates checked locally and the GitHub diff
guard pass, but the explicit repository-wide CI PASS requirement is blocked by
GitHub Actions infrastructure before any step runs. No main merge is recommended
until a normal runner execution passes.
