# Production Integration Consolidation — Blocking-Fix Static Audit

## Scope

Repository: `ogw07222-tech/baseball-player-sim`

Base: `main@1477fc3aecf9224d1b34f77a5d755880c9c88bfe`

Branch: `feature/production-integration-consolidation`

PR: `#33`

This report distinguishes static/code-review completion from runtime validation. GitHub Actions continues to fail before runner allocation (`runner_id=0`, `steps=[]`), and the current ChatGPT execution container cannot reach GitHub over the network to clone the repository. Runtime gates therefore remain NOT_READY until the checked-in local runner is executed in Codespaces/local.

## Canonical foundations / protected behavior

- PR #11 H3.2.1 production port remains canonical.
- PR #18 PersistentInningEngine remains canonical.
- No PR #33 changes exist under `src/hitting/model.py`, `src/hitting/parameters.py`, `src/hitting/baserunning.py`, `src/hitting/defense.py`, `src/pitching/`, or `web/`.
- Existing `src/growth.py` / `src/stats.py` changes are catcher-foundation plumbing only: Game Calling storage/growth is added while current-ability weighting and H3 gameplay formulas are unchanged.

## Blocker A — bases-loaded fielder's-choice lead force

Status: **STATIC FIXED / RUNTIME PENDING**

`BaseStateResolver.fielders_choice()` now has a targeted bases-loaded, outs<2 path:

- runner from third is retired at home;
- runner from second advances to third;
- runner from first advances to second;
- batter reaches first;
- one out is added;
- no run is scored;
- runner identities remain unique.

The existing two-out branch is preserved rather than forcing the same state mutation contract onto an inning-ending play.

Deterministic regression coverage now includes:

- bases loaded / 0 outs;
- bases loaded / 1 out;
- bases loaded / 2 outs;
- runner on first;
- runners first/second;
- runners first/third;
- runners second/third;
- identity uniqueness / base-state validation.

`NATURAL_EVENTS_INTEGRATION_READY` remains NOT_READY until the targeted tests and natural-event regression execute successfully.

## Blocker B — persistent cumulative team W/L/T

Status: **STATIC FIXED / RUNTIME PENDING**

`ProductionAdvancePipelineState` persists:

- `team_wins`;
- `team_losses`;
- `team_ties`;
- `team_record_supported`.

Serialization uses an explicit `team_record` payload. Old advance payloads without that field load as `0-0-0` with `supported=False` rather than fabricating a known historical record.

For new exact production games, the cumulative result is derived from exact final score. A contradictory supplied `team_result` raises rather than silently corrupting the record. Recent-history truncation is independent of cumulative W/L/T.

Regression coverage includes W/L/T, cumulative updates, save/load continuation, old-state compatibility, history truncation, and week/month composition tests already present in the consolidation suite.

`TIME_ADVANCE_INTEGRATION_READY` and `COMPOSITIONAL_ADVANCE_READY` remain NOT_READY until runtime execution proves state equivalence.

## Blocker C — ER / ERA support validity

Status: **STATIC FIXED / RUNTIME PENDING**

`PitcherCountingStats` now carries explicit support metadata for:

- ER / ERA;
- W;
- L;
- SV;
- HLD.

Semantics:

- supported ER=0 remains a real zero and can derive ERA=0.00;
- unsupported ER serializes as `None` and ERA is `None`;
- support flags are serialized explicitly;
- aggregation combines support conservatively, so any unsupported ER source makes aggregate ER/ERA unsupported;
- legacy payloads with an ER count but no provenance metadata retain the internal count but default to unsupported;
- production pitcher game lines mark ER/W/L/SV/HLD unsupported when the provider lacks exact official provenance.

No earned-run scoring logic was invented.

`STAT_AGGREGATION_INTEGRATION_READY` remains NOT_READY until the regression suite executes.

## Inherited-run responsibility

Status: **STATIC FIXED / RUNTIME PENDING**

The dynamic pitcher provider retains identity-based run responsibility:

- an inherited runner who reached against Pitcher A remains charged to Pitcher A after Pitcher B enters;
- a new runner allowed by Pitcher B is charged to Pitcher B if that runner later scores.

The implementation adjusts pitcher R accounting only and does not alter gameplay outcome probabilities.

## Test discovery / runner

Canonical runner:

```bash
bash tools/run_production_integration_checks.sh
```

The runner now includes `tests.test_pr33_blocking_fixes` in the targeted phase and then executes full unittest discovery plus the existing heavy sanity scripts and web test/build.

Planned runtime coverage:

1. compile/import;
2. persistent inning;
3. natural events / FC blocker;
4. stat aggregation / ER validity;
5. full-game provider;
6. inherited-run responsibility;
7. dynamic pitcher usage;
8. catcher foundation;
9. team-record persistence / save compatibility;
10. deterministic composition;
11. full Python suite;
12. 100k+ natural-event sanity;
13. 10k full-game sanity;
14. 500-season pitcher-usage sanity;
15. 200k catcher-generation sanity;
16. web tests;
17. web build.

## GitHub Actions status

`GITHUB_ACTIONS_EXECUTION = NOT_RUN_INFRASTRUCTURE_LIMIT`

Latest observed PR #33 workflow still has:

- `runner_id=0`;
- empty runner name;
- `steps=[]`;
- no Python, sanity, web test, or build command executed.

This is infrastructure non-execution, not assertion evidence.

## Current gates

| Gate | Status |
|---|---|
| H32_CANONICAL_BEHAVIOR_PRESERVED | READY_STATIC |
| PERSISTENT_INNING_CANONICAL_PRESERVED | READY_STATIC / NOT_RUN_RUNTIME |
| NATURAL_EVENTS_INTEGRATION_READY | NOT_READY — static blocker fixed, runtime pending |
| STAT_AGGREGATION_INTEGRATION_READY | NOT_READY — static blocker fixed, runtime pending |
| TIME_ADVANCE_INTEGRATION_READY | NOT_READY — static blocker fixed, runtime pending |
| FULL_GAME_PROVIDER_INTEGRATION_READY | NOT_READY — runtime pending |
| PITCHER_DYNAMIC_ROLE_READY | READY_STATIC / SOURCE_VALIDATED |
| PITCHER_ROTATION_READY | READY_STATIC / SOURCE_VALIDATED |
| PITCHER_CONSECUTIVE_FATIGUE_READY | READY_STATIC / SOURCE_VALIDATED |
| PITCHER_BULLPEN_USAGE_READY | NOT_READY — consolidated runtime pending |
| CATCHER_ABILITY_SCHEMA_READY | READY_STATIC |
| CATCHER_GENERATION_READY | NOT_READY — consolidation runtime pending |
| CATCHER_GROWTH_FOUNDATION_READY | NOT_READY — consolidation runtime pending |
| CATCHER_SAVE_COMPATIBILITY_READY | NOT_READY — consolidation runtime pending |
| TEAM_RECORD_PERSISTENCE_READY | NOT_READY — static fixed, runtime pending |
| ER_ERA_VALIDITY_READY | NOT_READY — static fixed, runtime pending |
| SAVE_COMPATIBILITY_READY | NOT_READY — runtime pending |
| COMPOSITIONAL_ADVANCE_READY | NOT_READY — static fixed, runtime pending |
| FULL_REGRESSION_READY | NOT_READY |
| PRODUCTION_INTEGRATION_CONSOLIDATION_READY | NOT_READY |

`CATCHER_GAMEPLAY_INTEGRATION = NOT_RUN`.

`PITCHER_GAMEPLAY_FATIGUE_EFFECT = NOT_RUN`.

## Merge recommendation

Keep PR #33 as Draft. The three static blockers are now represented in code/tests, but the consolidation must not be promoted to merge-ready until `bash tools/run_production_integration_checks.sh` executes successfully in Codespaces/local and the runtime-dependent gates are updated from evidence.
