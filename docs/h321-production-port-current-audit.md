# H3.2.1 Production Port — Current Audit

## Source of truth

- Repository: `ogw07222-tech/baseball-player-sim`
- Audited `main`: `1477fc3aecf9224d1b34f77a5d755880c9c88bfe`
- Validated Balance-Lab source: `test/h31-balance-lab-integration`
- Validated H3.2.1 source commit: `b7b8aafde0a50e687310dbe03b872087a569e08c`
- Original production port: PR #11, merged as `d114c3d05e5afd7012b32c27213f240f3a256137`
- Persistent inning/base-state integration: PR #18, merged as `adb0dcbd07e3b2b57ee14712016b47381475cf6f`
- Current audit/hardening branch: `feature/h321-production-port`

## Result

The validated H3.2.1 gameplay model is already present in production `src/` on current `main`.
This audit therefore does not re-port or retune gameplay code. It verifies the existing port and adds a formula-contract regression test only.

**Gameplay formula changes in this audit: NONE.**

## Current production architecture

- `src/hitting/parameters.py`
  - frozen H3.1 / H3.2 / H3.2.1 gameplay constants
  - explicitly references Balance-Lab source commit `b7b8aafd...`
- `src/hitting/model.py`
  - pitch -> swing -> contact -> contact quality -> exit quality -> batted-ball type/direction/depth -> defense -> hit/out/error -> speed resolution
- `src/hitting/defense.py`
  - difficulty-tier catch model
  - damage suppression
- `src/hitting/baserunning.py`
  - H3.2.1 steal attempt/success
  - 1B->3B and 2B->Home advancement
  - DP completion/avoidance
  - real `GameState` mutation adapters
- `src/simulation.py`
  - preserves legacy `simulate_plate_appearance()` and `simulate_player_game()` APIs
  - adapts Player traits/form/fatigue into the production H3 engine
  - legacy player-only career loop uses an isolated deterministic steal context rather than fabricating teammate base state
- `src/inning.py`
  - persistent runner identity and base occupancy
  - actual inning/outs/score context
  - batting-order persistence
  - actual-base steal timing
  - H3.2.1 1B->3B, 2B->Home and DP state adapters
- `src/records.py`
  - backward-compatible optional H3.2.1 diagnostics (`ROE`, `GDP`, `SB_attempts`, `DP_avoided`, `XBT`, `XBT_attempts`, `first_to_third`, `second_to_home`)

Production runtime code does not import `tools.balance_lab`.

## Formula parity audit

The production constants and functions were checked against Balance-Lab commit `b7b8aafde0a50e687310dbe03b872087a569e08c`.

Preserved contracts include:

- Contact scale `0.0055`, positive softness `70.0`
- Power scale `0.0108`, positive softness `85.0`
- Discipline zone/chase weights `0.0015 / 0.0045`
- two-strike protection `0.0065`, cap `0.25`
- H3.1 difficulty-tier base catch/leverage/bounds
- Routine/Easy error rates `0.985 / 0.86`
- damage suppression constants
- slow stretch-double downgrade
- single->double upgrade
- triple conversion
- infield-hit race
- H3.2 steal-success curve
- H3.2.1 gated steal-attempt curve (`77.5 / 5.8`, max `0.205`, core `108 / 17`)
- first-to-third curve (`0.20..0.72`, center `95`, scale `28`)
- second-to-home curve (`0.26..0.80`, center `92`, scale `26`)
- DP completion curve (`0.16..0.68`, center `92`, scale `24`)

No production formula retuning was required.

## Production game-state status

The historical PR #11 document predates the persistent inning engine and therefore describes teammate-driven advancement/DP as a future integration point.
That limitation has since been resolved by PR #18.

Current `src/inning.py` now supplies actual:

- runner identity
- first/second/third-base occupancy
- inning and half inning
- outs
- score differential
- batting order

and delegates probability decisions to the frozen H3.2.1 adapters rather than reimplementing probabilities.

The legacy player-only career simulation remains supported separately for compatibility.

## Save compatibility

No PlayerStats migration is performed by this port.
Legacy visible stats such as throwing/stamina/durability/mentality remain in the schema.

New batting/baserunning record fields use zero defaults in `BattingLine.from_dict()`, so old saves remain readable without a save-version bump.

## Regression evidence already in repository

### H3.2.1 production port

PR #11 recorded:

- Python compile: PASS
- full unit suite: 79/79 PASS
- auto-career smoke: PASS
- balance smoke: PASS
- deterministic draft calibration: PASS
- web build/tests: PASS
- neutral production-vs-Balance-Lab event parity: PASS

Neutral production baseline at 100,000 PA / seed 20260905:

- AVG `0.261151`
- OBP `0.320370`
- SLG `0.398793`
- OPS `0.719163`
- HR/PA `0.027700`
- BB/PA `0.080150`
- K/PA `0.213480`

### Persistent inning integration

PR #18 final candidate reported a full green workflow and verifies:

- persistent runner/base state
- forced advancement
- single/double/triple/HR state changes
- H3.2.1 first-to-third and second-to-home delegation
- H3.2.1 DP delegation
- actual-base steal mutation
- batting-order persistence
- full-game invariants
- same-seed deterministic replay

### Latest pitcher calibration coexistence

PR #19 explicitly reports no `src/hitting/*` or `src/simulation.py` formula changes and its pull-request workflow passed before merge.
The pitcher calibration work therefore does not retune H3.2.1 hitter math.

## Added hardening test

`tests/test_h321_formula_contract.py` adds explicit regression locks for:

- core Contact/Power/Discipline constants
- defense constants and representative catch probabilities
- H3.1 Speed outcome constants
- all key H3.2.1 baserunning constants
- representative steal/advancement/DP probability snapshots
- actual steal base-state eligibility
- prohibition on production runtime imports from `tools.balance_lab`

This is test-only hardening. No gameplay source file is changed on the audit branch.

## Current GitHub Actions infrastructure note

At current main run #490 and audit-branch run #503, both `unit-tests` and `web-tests` terminate before any workflow step starts (`steps=[]`, `runner_id=0`).
This is not a Python/unit-test assertion failure and provides no code-level failure evidence; the jobs never receive a runner.

The most recent relevant executable evidence remains the green PR #18 persistent-inning workflow and the green PR #19 pull-request workflow. The new contract test should still be allowed to execute once Actions runners are available before merging this audit-only branch.

## Remaining issues / out of scope

- Existing real-player ratings have not been refit to H3.2.1.
- The legacy player-only career loop cannot represent teammate runner identities; full base-state play uses `PersistentInningEngine`.
- 1B->Home on a double still uses the documented deterministic fallback because no validated probability formula exists.
- sac fly / bunt / squeeze / hit-and-run and manager tactics remain outside H3.2.1.
- `steal_sense` is intentionally not stacked onto the frozen steal math.
- Full 7-stat migration (Resilience, removal of legacy visible stats) is a separate task.

## Gate

**PRODUCTION_PORT_READY**

The production H3.2.1 math is already integrated and persistent game-state orchestration is already present on current main. No formula correction is required by this audit.

Main recommendation for the gameplay port itself: **already promoted / keep as-is**.

Recommendation for this audit branch: merge the test/documentation hardening only after GitHub Actions is able to allocate runners and execute the suite; do not use the current pre-runner infrastructure failure as a gameplay regression signal.
