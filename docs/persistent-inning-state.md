# Persistent Inning / Base-State Orchestration

## Source

- Repository: `ogw07222-tech/baseball-player-sim`
- Base main SHA: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- Branch: `feature/persistent-inning-state`
- Probability layer: production H3.2.1 in `src/hitting/`

## Scope

This branch adds orchestration only. It does **not** change H3.2.1 hitting, defense, steal, advancement, or double-play formulas.

The new `src/inning.py` layer maintains runner identity, base occupancy, outs, scores, batting-order positions, half-inning transitions, extra innings, and game-over state across teammate plate appearances.

## State model

`RunnerState` keeps the canonical `Player` reference plus team side and lineup slot.

`InningState` keeps:

- inning / half
- outs
- home / away score
- first / second / third runner identity
- home / away batting-order index
- current batter
- current pitcher
- game-over flag

Each state transition validates non-negative scores, legal outs, unique base-runner identity, and batting-team ownership of occupied bases.

## Reused production APIs

No probability is reimplemented. The orchestration layer calls:

- `simulate_plate_appearance_outcome()`
- `apply_steal_to_state()`
- `apply_first_to_third_to_state()`
- `apply_second_to_home_to_state()`
- `apply_double_play_to_state()`

H3.2.1 formula files remain unchanged.

## Runner advancement policy

- Walk / HBP: forced advancement only.
- ROE: forced advancement only; no RBI is awarded by the fallback.
- Single: runner on third scores; runner on second uses validated 2B->Home; runner on first uses validated 1B->3B when third is available. Failed extra-base attempts fall back to the next safe base.
- Double: runners on second/third score; runner on first advances deterministically to third because no validated 1B->Home-on-double formula exists.
- Triple: all existing runners score; batter occupies third.
- Home run: all runners plus batter score.
- Strikeout: one out, runners unchanged.
- Ground-ball out with runner on first and fewer than two outs: validated DP adapter is used. On an avoided DP, the lead runner is retired and the batter occupies first as a fielder's choice.
- Non-ground out: one out; no sac-fly logic is invented.

## Steal timing

Steal evaluation occurs between completed plate appearances. It uses actual base occupancy, inning, outs, and score differential through the existing H3.2.1 `GameState` adapter. A caught-stealing third out switches the half-inning without advancing the batting order.

## Half-inning and game flow

- Three outs clear the bases and switch sides.
- Each team keeps its own batting-order index across innings.
- After the top of the ninth or later, the game ends if the home team already leads.
- After the bottom of the ninth or later, a non-tie ends the game.
- A home lead created in the bottom of the ninth or later ends the game immediately.
- Ties continue into extra innings; no new extra-inning limit or runner rule is invented.

## Stats

The engine reuses `BattingLine` for PA/AB/H/2B/3B/HR/BB/SO/R/RBI/SB/CS/GDP/ROE and H3.2.1 baserunning diagnostics. No duplicate stat schema is introduced.

## Explicit limitations

This pass does not implement:

- sac fly / sac bunt / squeeze / hit-and-run
- manager tactics AI
- catcher-specific running defense
- pitcher fatigue or substitution
- starter/reliever orchestration
- 1B->Home probability on a double
- detailed multi-force ground-ball logic with runners on multiple bases
- UI/application routing for the new full-team game engine

The current pitcher is a stable `PitcherProfile` reference supplied to the game engine. Pitcher Foundation / calibration formulas are not modified.

## Determinism

All random decisions consume the caller-provided `RNG`. The orchestration layer does not instantiate `random.Random()` internally.

## Conflict risk

The branch adds `src/inning.py`, tests, and this document only. It does not touch `src/hitting/*`, `src/pitching/*`, `src/growth.py`, `src/stats.py`, `src/config.py`, or `src/player.py`, minimizing conflict with pitcher calibration work.

## Gate

`PERSISTENT_INNING_ENGINE_READY` is granted only after the full repository CI passes and the formula-file diff remains empty.
