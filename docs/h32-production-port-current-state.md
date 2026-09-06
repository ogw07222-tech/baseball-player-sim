# H3.2.1 Production Port — Current State Review

## Canonical state
- Current main: `1477fc3aecf9224d1b34f77a5d755880c9c88bfe`
- Validated Balance-Lab source: `test/h31-balance-lab-integration@b7b8aafde0a50e687310dbe03b872087a569e08c`
- Original production port PR: #11
- Persistent inning/base-state PR: #18
- Latest pitcher-calibration merge: #19

## Formula freeze
The H3.2.1 gameplay formulas remain frozen. Current production still uses the validated constants for:
- Contact / Power / Discipline / Speed sensitivity
- H3.1 batted-ball construction
- difficulty-tier defense catch curves
- damage suppression
- error rules
- stretch-double downgrade / single-to-double / triple conversion
- H3.2.1 steal attempt gate
- H3.2 steal success curve
- 1B -> 3B advancement
- 2B -> Home advancement
- double-play completion / avoidance

No current production file imports `tools.balance_lab` at runtime.

## Production architecture now present
- `src/hitting/parameters.py`: frozen H3.2.1 constants
- `src/hitting/model.py`: production pitch -> swing -> contact -> batted-ball pipeline
- `src/hitting/defense.py`: catch probability and damage suppression
- `src/hitting/baserunning.py`: steal / advancement / DP probability layer and state adapters
- `src/simulation.py`: backward-compatible PA/game adapter
- `src/inning.py`: persistent runner identity, bases, outs, score, batting order, actual state-sensitive baserunning
- `src/records.py`: backward-compatible ROE/GDP/SB/XBT diagnostics

## Persistent inning status
The limitation documented in the original PR #11 report is now resolved by PR #18.

Production now owns real runner/base state across teammate plate appearances and directly calls the frozen H3.2.1 APIs for:
- 1B -> 3B on singles
- 2B -> Home on singles
- ground-ball double-play completion / avoidance
- 1B -> 2B steal attempts between plate appearances

Runner identity is preserved and Speed is read from the canonical `Player` object.

## Backward compatibility
Legacy public APIs remain available:
- `simulate_plate_appearance(...) -> str`
- `simulate_player_game(...)`

The persistent game engine is additive. Existing player-centric career calls remain supported.

Old saves remain compatible because new `BattingLine` fields default to zero during `from_dict()`.

## Regression evidence
Original production port PR #11 recorded:
- exact same-seed neutral event parity against Balance Lab
- neutral baseline inside the validated H3.1/H3.2.1 band
- Contact/Power/Discipline/Speed/Defense monotonicity
- steal suppression / success / diminishing-return checks
- advancement and DP monotonicity
- deterministic seed behavior
- save compatibility
- full repository CI green at the validated PR candidate

Persistent inning PR #18 recorded workflow run #259 with:
- Python compile: PASS
- full unit tests: PASS
- auto-career smoke: PASS
- balance smoke: PASS
- high-school / draft calibration gate: PASS
- web build/tests: PASS

Pitcher calibration PR #19 explicitly reports:
- `src/hitting/*` diff: NONE
- `src/simulation.py` diff: NONE
- persistent inning changes: NONE

Its final PR head `5de811fced124971b97b30f4e6f4934521f4ff22` had the repository `tests` workflow complete successfully.

## Current main CI note
The post-merge push workflow associated with current main `1477fc3a...` ended in failure before normal job steps were exposed. Because the immediately preceding PR #19 test workflow was green and PR #19 did not change H3.2.1 production files, this is not evidence of an H3 gameplay regression. It should be treated as a separate CI/infrastructure signal until a normal runner execution is observed.

## Remaining H3.2.1 risks / out of scope
- existing real-player ratings have not been refit to H3.2.1 production outputs
- `steal_sense` remains intentionally outside the frozen steal formulas
- catcher-specific running defense is not yet represented by individual catcher/pitcher ratings
- UI/provider wiring is separate from the gameplay port
- later natural-baseball-event work may extend runner decisions, but must not retune frozen H3.2.1 formulas without Balance-Lab validation

## Gate
`PRODUCTION_PORT_READY`

The validated H3.2.1 math is already in production architecture and the actual persistent base-state engine now consumes the validated baserunning APIs. No additional formula port is required at this stage.
