# Natural Baseball Events Integration

## Source / branch

- Repository: `ogw07222-tech/baseball-player-sim`
- Main at branch creation: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- Persistent inning source: `feature/persistent-inning-state`
- Persistent inning source HEAD: `db2183c53d91af008c2e1daa2a4e63074bc229d3`
- Natural-events branch: `feature/natural-baseball-events`
- Frozen H3.2.1 probability source remains `src/hitting/`.

This layer fills natural runner-advancement interpretation between the frozen
H3.2.1 PA engine and the persistent inning/base-state engine. It does not
retune Contact, Power, Discipline, Speed, defense, steal, validated
first-to-third, validated second-to-home, or DP curves.

## Implemented events

### Runner on first scoring on a double

A double now preserves the existing deterministic scoring of runners from
second/third, but a runner from first may attempt to score when real
`BattedBall` metadata is available.

`first_to_home_on_double_probability()` reuses the validated H3.2.1
`second_to_home_probability(speed, recovery)` curve and applies only a small
batted-ball-depth interpretation:

- shallow: `-0.16`
- medium: `-0.03`
- deep: `+0.08`

The result is bounded to `[0.08, 0.90]`. Direct legacy/test callers that supply
a double without `BattedBall` metadata keep the old conservative first-to-third
fallback.

### Sacrifice fly and tag-up

On a caught fly-ball out with fewer than two outs, runners may tag:

- 3B -> Home
- 2B -> 3B, if third base is available after the lead-runner decision

The underlying speed/recovery shapes reuse the validated H3.2.1 advancement
curves. Depth scales the chance:

- 3B -> Home: shallow `0.12x`, medium `0.72x`, deep `1.12x`
- 2B -> 3B: shallow `0.06x`, medium `0.48x`, deep `0.86x`

A successful 3B -> Home tag records a sacrifice fly:

- PA +1
- AB +0
- SF +1
- RBI +1 per scoring runner under the current single-run SF contract
- scoring runner R +1
- team score +1
- out +1

`SF` is an optional zero-default `BattingLine` field, so older saves that do not
contain it continue to load as `SF=0`.

### Wild pitch / passed ball contract

`PitchMiscEvent` defines:

- `NONE`
- `WILD_PITCH`
- `PASSED_BALL`

The persistent state resolver can consume a supplied WP/PB and advance occupied
runners one base in lead-runner order:

- 3B -> Home
- 2B -> 3B
- 1B -> 2B

No catcher rating or occurrence probability is introduced. The normal
`step()` path does not generate WP/PB, so both remain disabled until a future
catcher/pitch-misc probability layer supplies an event.

### Fielder's choice refinement

Explicit fielder's-choice resolution preserves runner identity and uses a
minimal force hierarchy rather than replacing the runner on first blindly.

For multi-force ground-ball states, the state resolver uses the available lead
force before placing the batter on first. It does not implement fielding
decision AI.

The frozen H3.2.1 DP adapter remains canonical for the simple runner-on-first,
fewer-than-two-outs DP situation.

### Ground-ball advancement

When no force runner occupies first, a generic ground-ball out can produce
conservative:

- 2B -> 3B
- 3B -> Home

advancement. These contracts reuse the H3.2.1 advancement curves at reduced
event multipliers (`0.42x` and `0.28x`) and do not add position-by-position
fielding logic.

## Base occupancy invariants

Every resolver keeps:

- no duplicate runner identity across bases
- at most one runner per base
- scored runners removed from bases
- retired runners removed from bases
- lead-runner decisions resolved before trailing-runner movement
- half-inning base clearing after the third out

The existing `InningState.validate()` invariant checks remain active after every
public event resolution.

## Third-out scoring structure

The resolution contract now carries `third_out_is_force` so force-third-out and
timing-play logic can be distinguished by future rule expansion.

This pass prevents tag-up and generic ground advancement with two outs and does
not score runners on a completed third-out DP/force. A complete timing-play
rulebook (appeals, missed bases, unusual fourth-out cases) remains out of scope.

## Stats / save compatibility

Existing production fields continue to be used:

- R / RBI
- SB / CS
- GDP
- XBT / XBT_attempts
- first_to_third
- second_to_home
- ROE

New field:

- `SF` — optional, zero-default, included in `as_dict()` / `from_dict()`

No save version bump is required because old payloads load the missing field as
zero.

## Determinism

All new stochastic decisions consume the caller-provided `RNG`. No resolver or
probability function instantiates an independent random generator.

Same seed + same lineups + same initial state + same supplied event sequence
therefore remains deterministic.

## Performance

All new state resolvers are O(1). WP/PB is disabled by default. The committed
sanity runner exercises 100,000+ production game events and reports SF, tag-up,
first-to-home-on-double, GDP, XBT, and disabled WP/PB counts.

## Unsupported / future work

Still out of scope:

- catcher blocking/catching/game-calling ratings
- calibrated WP/PB occurrence rates
- bunts / squeeze / hit-and-run
- manager tactical AI
- detailed position-by-position fielding decisions
- full timing-play / appeal / fourth-out rulebook
- pitcher substitution/fatigue/calibration
- H3.2.1 formula retuning

## Formula-freeze guarantee

This branch does not modify:

- `src/hitting/model.py`
- `src/hitting/parameters.py`
- `src/growth.py`
- `src/stats.py`
- `src/config.py`

The new probability contracts live in `src/natural_events.py` and only
interpret already-produced H3.2.1 batted-ball/state information.

## 100k+ event sanity result

CI run #284 (`tests`) executed the deterministic sanity runner with seed
`20260906` and completed `100,061` game events across `1,248` neutral games
(`97,835` plate appearances):

- Sacrifice flies: `179` (`1.098 / 600 PA`)
- Tag-up: `1,784` attempts / `374` successes (`20.96%`)
- 1B -> Home on double: `1,428` attempts / `865` successes (`60.57%`)
- GDP: `1,356` (`8.316 / 600 PA`)
- XBT: `5,847` (`35.858 / 600 PA`)
- Fielder's choice: `3,315`
- Ground-out advancement: `1,098` attempts / `217` successes (`19.76%`)
- Wild pitch: `0`
- Passed ball: `0`

The disabled-by-default WP/PB contract therefore does not leak spontaneous
misc events into normal game simulation. The broad sanity gate rejected neither
an all-runners-score-on-double pathology nor shallow/tag-up explosion.

## CI evidence

PR #21 code HEAD `ffc4c07c1b69b8f0e604b08b3ab34bc5f1d7371e`, workflow run #284:

- Python compile: PASS
- Full unit suite: `119/119 PASS`
- 100k+ natural-event sanity: PASS
- Auto-career smoke: PASS
- Balance smoke: PASS
- High-school / draft calibration gate: PASS
- Draft calibration artifact upload: PASS
- Web build: PASS
- Web tests: PASS

## Gate

**NATURAL_BASEBALL_EVENTS_READY**

P0 natural events are implemented, the WP/PB state contract is present but
disabled until a future catcher/pitch-misc probability layer exists, runner
identity/base invariants and deterministic replay are preserved, H3.2.1 formula
files are unchanged, 100k+ event sanity is non-pathological, and full repository
CI is green.
