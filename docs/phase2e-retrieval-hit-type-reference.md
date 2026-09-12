# Phase 2E-B Retrieval / Physical Hit-Type Research

Access date: 2026-09-12 (Asia/Seoul)

Purpose: research/reference pack for `01 - Gameplay Engine` Phase 2E-B defensive retrieval, throw timing, batter-runner timing, and physical 1B/2B/3B shadow resolution. Research only; no production gameplay formula or coefficient is changed here.

Parent HQ: `00 - Physical Batted-Ball Engine HQ`

Task-start source of truth: `main@a207c6a0ee6cee73a1840fdf85648649610f180b` (Phase 2E-A merged).

Upstream physical state assumed available from Phase 2E-A:
- first impact / bounce / rollout;
- `final_x`, `final_y`;
- final radial distance;
- `wall_ground_contact`.

Runtime contract assumed by this research:
- O(1) per BIP;
- no fielder path simulation;
- no timestep;
- no dynamic nearest-player loop;
- no relay-chain loop;
- no mesh/pathfinding;
- fixed anchor lookup, fixed branches, sqrt distance, fixed algebra, tiny lookup allowed.

Status labels:
- **VERIFIED**: official/high-authority definition or current measured reference.
- **PARTIAL**: useful measured reference, but league/role/definition transfer is incomplete.
- **QUALITATIVE**: directional/structural evidence only.
- **OPEN**: no suitable public calibration recovered.

## REFERENCE_STATUS

| Lane | Status | Summary |
|---|---|---|
| MLB nominal fielder positioning | VERIFIED | Statcast publishes standard IF/OF positioning zones under neutral conditions |
| MLB running-speed magnitude | VERIFIED | Statcast Sprint Speed average ~27 ft/s; competitive range roughly 23-30 ft/s |
| MLB home-to-first / 90-ft timing | VERIFIED/PARTIAL | official Statcast definitions and current leaderboards provide elite references; league-average exact Phase2E baseline not fixed here |
| MLB fielder arm-strength magnitude | VERIFIED | 2025 position-group league averages available from Statcast Arm Strength leaderboard |
| General fielder exchange/transfer time | PARTIAL | Statcast defines Exchange; older tracked IF/OF examples exist, but no clean current universal pickup+transfer baseline |
| Relay timing | PARTIAL/QUALITATIVE | tracked relay examples exist; no compact universal relay model recovered |
| KBO retrieval / throw / runner tracking calibration | OPEN | no public play-level tracking surface sufficient for direct KBO timing calibration recovered |
| O(1) retrieval architecture | RESEARCH-READY | fixed responsibility zones + nominal anchors + deterministic timing comparison is physically coherent |

---

## RETRIEVER_OWNERSHIP

### Candidate assessment

A. **Fixed Voronoi-like regions**
- runtime: O(1) if pre-authored as fixed zones;
- strength: naturally approximates nearest nominal defender;
- weakness: hard polygon maintenance and team/handedness shifts can create discontinuities.

B. **Radial depth + spray sectors**
- runtime: trivial O(1);
- strength: directly matches available Phase 2E-A `final_x/y` and field geometry;
- weakness: gap balls near responsibility boundaries require overlap handling.

C. **Primary owner + adjacent fallback**
- runtime: O(1) with a fixed secondary role;
- strength: handles gaps without scanning all defenders;
- weakness: must define deterministic blend/selection policy.

D. **Nearest nominal anchor**
- physically intuitive, but a generic implementation that loops over all 9 defenders violates the requested runtime style. It is acceptable only if compiled into fixed small branches, not a runtime roster search.

### Recommendation

**RECOMMENDED_OWNERSHIP_MODEL = RADIAL_DEPTH_PLUS_SPRAY_SECTORS_WITH_PRIMARY_OWNER_AND_ONE_ADJACENT_FALLBACK**

Suggested fixed conceptual zones:

- very shallow home-plate region -> C / P;
- mound/central dribbler -> P / middle infielder fallback;
- left infield line -> 3B;
- left infield gap -> 3B / SS;
- middle-left -> SS;
- middle-right -> 2B;
- right infield gap -> 2B / 1B;
- right infield line -> 1B;
- shallow/deep LF sector -> LF, CF fallback near gap;
- center sector -> CF;
- shallow/deep RF sector -> RF, CF fallback near gap.

The second defender should be selected only from a predeclared adjacent pair. No dynamic nearest-player search is necessary.

For Phase 2E-B V1, the `primary owner` can be authoritative for timing; the adjacent owner may be retained as an observable/future refinement without evaluating a second retrieval path. This preserves one deterministic retrieval-time evaluation per BIP.

---

## NOMINAL_DEFENDER_POSITIONS

Official MLB Statcast `standard` positioning zones are defined from neutral situations (first-eighth inning, no runners) and are suitable architecture priors.

Angles use `-45 deg = 3B line`, `0 deg = straight CF`, `+45 deg = 1B line`.

### Infield standard zones

Versus LHH:
- 1B: 85-130 ft, +31 to +42 deg
- 2B: 130-160 ft, +9 to +31 deg
- SS: 130-160 ft, -18 to 0 deg
- 3B: 80-130 ft, -37 to -17 deg

Versus RHH:
- 1B: 85-130 ft, +23 to +38 deg
- 2B: 130-160 ft, 0 to +18 deg
- SS: 130-160 ft, -28 to -8 deg
- 3B: 80-130 ft, -42 to -30 deg

### Outfield standard zones
- LF: 260-320 ft, -33 to -21 deg
- CF: 280-350 ft, -8 to +7 deg
- RF: 260-320 ft, +21 to +33 deg

These zones are **VERIFIED MLB architecture references**, not KBO exact positions.

### Engineering nominal anchors

If 01 needs one fixed start point per role, midpoint anchors may be derived from the above ranges. These are explicitly `DERIVED_ENGINEERING_BASELINE`, not official averages:

- LF ~290 ft / -27 deg
- CF ~315 ft / 0 deg
- RF ~290 ft / +27 deg

Handedness-specific midpoint anchors can likewise be derived for IF from the official ranges. Do not label these derived midpoints as measured KBO/MLB means.

P and C should use simple field-geometry anchors rather than invented Statcast averages:
- pitcher near mound center / pitching rubber region;
- catcher at home-plate region.

Their exact retrieval responsibility zones are an engineering model decision, not a sourced league distribution.

---

## RETRIEVAL_TIME

### Evidence structure

Statcast fielding concepts explicitly track:
- fielder first step;
- max speed;
- acceleration;
- total distance;
- route efficiency;
- exchange time.

Statcast Sprint Speed gives a useful human movement scale:
- MLB average competitive sprint speed: ~27 ft/s;
- rough competitive range: ~23 ft/s poor to ~30 ft/s elite;
- 30+ ft/s is a `Bolt`.

This is a runner top-speed metric, not a direct fielder retrieval-speed coefficient. A fielder starts from rest/read state and typically cannot sustain top sprint speed across short retrievals.

### Recommended model

`retrieval_time = reaction_delay + retrieval_distance / effective_fielder_speed + pickup_transfer_delay`

Status: **RECOMMENDED STRUCTURE / numeric coefficients OPEN**.

Why it works:
- distance term preserves obvious monotonicity;
- reaction term captures read/start cost;
- fixed effective speed compresses acceleration/route into one bounded quantity;
- pickup/transfer isolates the ball-control cost from movement.

Do not use raw 27 ft/s as the effective retrieval speed. Treat it as a physical upper/magnitude reference; the effective value must be calibrated lower or folded through a distance-dependent small lookup if needed.

### Pickup / exchange references

Statcast defines `Exchange` as time from fielder receiving the ball to release of throw. Public examples show this is a meaningful fraction of a second to >1 second:
- historical MLB catcher average exchange ~0.74 s in a 2016 analysis;
- second-base assist exchange average ~1.2 s in the same period, with a top value near 1.02 s and slower values above 1.4 s;
- an outfield example around 1.0 s has been published.

These are **PARTIAL historical context**, not one universal pickup-transfer constant. Ground-ball pickup while moving and clean catch-to-throw exchange differ materially.

Recommended V1 policy:
- one bounded `pickup_transfer_delay` by role class (`IF`, `OF`, optionally `P/C`);
- no stochastic bobble/error in this layer;
- exact values remain calibration parameters owned outside 08.

---

## DEFENDER_RATING_EFFECT

Rating must alter retrieval time monotonically but remain bounded.

### Candidate mechanisms

1. movement-speed adjustment only
- easy and interpretable;
- misses first-step and pickup skill.

2. reaction-delay adjustment only
- strong for short plays;
- weak for deep retrievals.

3. pickup-delay adjustment only
- too narrow to represent range.

4. bounded combined adjustment
- adjusts effective movement speed and reaction delay, optionally tiny pickup adjustment;
- best general structure.

### Recommendation

**RECOMMENDED_DEFENDER_RATING_EFFECT = BOUNDED_COMBINED_REACTION_AND_EFFECTIVE_SPEED_ADJUSTMENT**

Required properties:
- higher range/defense -> non-increasing retrieval time;
- effect is bounded;
- rating must not reduce reaction to negative time or make movement exceed a plausible physical ceiling;
- pickup adjustment, if present, should be secondary to range/reaction.

Exact project-rating-point mapping is **OPEN** and should not be chosen by 08.

---

## THROW_MODEL

### Official Statcast arm-strength reference

Statcast Arm Strength is maximum release velocity on a play, with leaderboard values based on a top fraction of max-effort throws. 2025 league-average leaderboard values:

| Position | 2025 Arm Strength |
|---|---:|
| 1B | 78.3 mph |
| 2B | 79.3 mph |
| 3B | 85.6 mph |
| SS | 85.7 mph |
| LF | 87.1 mph |
| CF | 89.6 mph |
| RF | 90.5 mph |

Status: **VERIFIED MLB-only**.

Critical limitation: these are not mean velocities of every competitive throw. 1B uses top 1%, 2B/3B/SS top 5%, OF top 10%. They provide arm-strength scale/ordering, not direct `effective_throw_speed` coefficients.

### Recommended direct-throw surrogate

`throw_time = transfer_release_delay + throw_distance / effective_throw_speed`

This is physically reasonable and O(1).

`effective_throw_speed` should be lower than or otherwise calibrated from Statcast max-effort Arm Strength because real throws have trajectories, accuracy constraints, bounces/cutoffs, and are not all max effort.

### Relay

Real deep throws frequently use relays/cutoffs. A documented Statcast-era inside-the-park play included an ~180-ft OF throw with ~0.87-s exchange followed by a ~160-ft relay and ~0.63-s exchange.

Options:
- ignore relay: simplest, but can make very deep OF throws unrealistically fast;
- fixed relay penalty: O(1), stable;
- threshold relay penalty: apply a fixed penalty only when direct throw distance exceeds a calibrated threshold.

**Recommendation: DISTANCE_THRESHOLD_PLUS_FIXED_RELAY_PENALTY**.

No relay chain loop. The threshold and penalty magnitude remain **OPEN calibration parameters**.

---

## BATTER_RUNNER_TIME

### Official timing/geometry references

- MLB base paths form a 90-ft square.
- Statcast Home-to-First is contact to first-base touch.
- Statcast 90-foot splits standardize running over a 90-ft distance and remove some L/R batter-box geometry effects.
- MLB competitive Sprint Speed average is ~27 ft/s, with rough 23-30 ft/s competitive range.
- Current elite 2025 home-to-first values are roughly low-4-second territory, with the fastest current examples around 3.97-4.13 s.
- 2025 elite standardized 90-ft split examples are ~3.67-3.75 s.
- Tracked extreme extra-base running shows first-to-second around 3.2-3.3 s is possible for elite runners already moving at speed.

### Left/right-handed batter effect

Official Statcast notes that left-handed batters physically start closer to first base and are generally favored in raw Home-to-First times. The standardized 90-ft split exists partly to normalize that difference.

V1 recommendation:
- use one standardized speed-rating timing model initially;
- do **not** require a handedness bonus in V1 unless the project explicitly wants raw-contact-to-first realism;
- if added later, handedness should only affect the home-to-first start term, not 1B->2B or 2B->3B.

### Recommended runner model

A single `reference_time * speed_multiplier` is possible, but a slightly more physical O(1) decomposition is better:

`time_to_1B = batter_start_delay + first_leg_time(speed_rating)`

`time_1B_to_2B = base_leg_time(speed_rating) + turn_penalty`

`time_2B_to_3B = base_leg_time(speed_rating) + turn_penalty`

Cumulative:
- `runner_time_1b = time_to_1B`
- `runner_time_2b = time_to_1B + time_1B_to_2B`
- `runner_time_3b = time_to_1B + time_1B_to_2B + time_2B_to_3B`

Each leg is fixed algebra / tiny lookup, O(1).

**RECOMMENDED_RUNNER_TIME_MODEL = STANDARDIZED_BASE_LEG_TIMES_WITH_HOME_TO_FIRST_START_TERM_AND_BOUNDED_SPEED_MULTIPLIER**

Exact KBO central times and speed-rating mapping remain OPEN.

---

## PHYSICAL_HIT_TYPE_LOGIC

Final radial distance alone must not determine 1B/2B/3B.

Recommended deterministic timing race:

1. if upstream Phase 2D physical catch shadow is true -> `physical_result_shadow = OUT`, retrieval not applicable;
2. otherwise obtain Phase 2E-A final ball location;
3. select fixed primary retriever;
4. compute retrieval time;
5. compute defense-control time at the ball;
6. compute throw-arrival time to 1B/2B/3B using fixed base coordinates;
7. compare against cumulative batter-runner arrival times.

### Conceptual resolution

- if defense can control/throw to 1B before runner arrival -> OUT;
- else runner safely reaches 1B;
- evaluate 2B only if 1B is safe and the defensive timing to 2B beats/does not beat runner timing;
- evaluate 3B only if 2B is safe;
- maximum Phase 2E-B V1 result = 3B;
- HR remains Phase 2C wall-clearance authority and is not created by retrieval logic.

This naturally permits:
- routine grounder -> OUT;
- slow/chopped/infield-remote ball -> 1B;
- deep gap/wall-stop ball -> 2B/3B depending retrieval + throw + runner speed.

### Important simplification

Do not simulate a sequence of actual throws. For each candidate base, compute a hypothetical deterministic defense-arrival time from the one retrieved-ball state.

This preserves O(1): at most three fixed base timing evaluations.

**RECOMMENDED_HIT_RESOLUTION_MODEL = DETERMINISTIC_RETRIEVAL_PLUS_HYPOTHETICAL_BASE_ARRIVAL_TIME_RACES**

---

## AIRBORNE_BALL_INTERFACE

Recommended integration contract:

A. `Phase2D physical_out_shadow == true`
- physical result is OUT;
- retrieval/hit-type state marked not-applicable/invalid;
- no extra RNG.

B. airborne BIP not caught
- use the same Phase 2E-A final-location state as ground-like BIPs;
- retrieval begins from final ball location;
- same Phase 2E-B timing machinery may be used.

This unifies ground balls and uncaught air balls after `FinalBallLocation`, which is desirable. Their different physical behavior has already been encoded upstream in trajectory + ground travel + final location.

Potential future refinements such as a rolling ball being intercepted before final rest are explicitly outside V1. Phase 2E-B V1 retrieves from final location, not along the moving-ball path.

---

## THROW_TARGETS

Official base geometry is fixed:
- home, first, second, third form a 90-ft square;
- home-to-second diagonal ~127 ft 3 3/8 in.

Therefore 1B/2B/3B target coordinates can be constants in the project's field coordinate system.

Phase 2E-B V1 only resolves batter-runner `OUT / 1B / 2B / 3B` shadow. Existing runner advancement remains untouched.

No baserunner leads, force-state graph, cutoff positioning, or trailing-runner logic is required in this phase.

---

## REQUIRED_STATE_CONTRACT

Recommended typed contract:

```text
RetrievalState
- valid: bool
- applicable: bool
- model_version
- defender_position: P | C | 1B | 2B | SS | 3B | LF | CF | RF
- adjacent_position: optional
- defender_start_x
- defender_start_y
- ball_x
- ball_y
- retrieval_distance
- reaction_time
- effective_fielder_speed
- travel_time
- pickup_transfer_time
- total_retrieval_time
- wall_ground_contact
```

```text
ThrowState
- valid: bool
- target_base: 1B | 2B | 3B
- origin_x
- origin_y
- target_x
- target_y
- throw_distance
- arm_reference_mph
- effective_throw_speed
- transfer_release_time
- relay_applied: bool
- relay_penalty_time
- total_throw_time
- defense_arrival_time
```

```text
RunnerTimingState
- valid: bool
- speed_reference
- speed_multiplier
- start_delay
- leg_time_h1
- leg_time_12
- leg_time_23
- arrival_time_1b
- arrival_time_2b
- arrival_time_3b
- batter_side: optional
```

```text
PhysicalHitResolution
- valid: bool
- applicable: bool
- upstream_physical_catch: bool
- retrieval_state
- defense_time_1b
- defense_time_2b
- defense_time_3b
- runner_time_1b
- runner_time_2b
- runner_time_3b
- margin_1b = defense_time_1b - runner_time_1b
- margin_2b
- margin_3b
- physical_result_shadow: OUT | 1B | 2B | 3B | NOT_APPLICABLE
- model_version
```

The time margins are important validation observables and future boundary-RNG hooks.

---

## RNG_MODEL

Phase 2E-B V1 can and should be **deterministic**.

Reasoning:
- retrieval/range uncertainty is already represented structurally through defender ratings and fixed timing parameters;
- Phase 2D owns airborne catch probability/RNG;
- errors/bobbles should remain a later separate layer;
- adding boundary RNG now makes calibration less identifiable.

Near-tie plays can simply use a deterministic tie rule in shadow mode, while recording time margin.

Future extension:
- only after timing calibration, an optional one-boundary-RNG layer could map small absolute timing margins to probability;
- not recommended for initial Phase 2E-B.

**RNG_MODEL = DETERMINISTIC**

---

## VALIDATION_TARGETS

### Hard monotonicities
- farther retrieval distance -> retrieval time non-decreasing;
- higher range rating -> retrieval time non-increasing;
- farther throw distance -> throw time non-decreasing;
- higher arm rating/effective throw speed -> throw time non-increasing;
- higher runner speed -> base arrival times non-increasing;
- mirrored LF/RF states with mirrored ratings/anchors -> symmetric scalar timings;
- invalid GroundTravelState -> invalid retrieval state;
- Phase 2D physical catch -> no retrieval/hit resolution;
- all times finite and >=0;
- OUT/1B/2B/3B resolution must be deterministic under same input.

### Distribution diagnostics
- retriever share by position;
- retrieval-distance and retrieval-time distributions by role;
- pickup/transfer component share;
- throw distance/time by role and target base;
- relay-applied rate if relay penalty enabled;
- runner arrival-time distributions by speed-rating bucket;
- time-margin distributions at 1B/2B/3B;
- physical OUT/1B/2B/3B share;
- result by final depth and spray sector;
- result by `wall_ground_contact`;
- result by defender range/arm and runner speed buckets;
- physical hit-type impact on BABIP / 2B / 3B composition once shadow comparison is enabled.

### Scenario matrix

At minimum 05 should test:
1. routine IF ground location + average defender + average runner -> often/structurally OUT-compatible;
2. same ball, faster runner -> result no worse for runner;
3. same ball, better defender -> result no better for runner;
4. deep OF gap final location -> longer retrieval, extra bases become physically possible;
5. wall-stop state -> deep retrieval and 2B/3B timing pressure;
6. mirrored LF/RF cases -> equal timing under symmetric ratings;
7. extreme coordinates / zero distances -> finite stable outputs.

No MLB/KBO outcome share is authorized as a hard Phase 2E-B target by this pack.

---

## DATA_QUALITY

### VERIFIED MLB
- official 90-ft field/base geometry;
- Sprint Speed definition and ~27 ft/s MLB average competitive speed / ~23-30 ft/s broad range;
- official Home-to-First and 90-ft split definitions;
- standard neutral IF/OF positioning zones;
- Statcast Arm Strength definition and 2025 position-group league-average leaderboard values;
- Exchange definition.

### PARTIAL
- historical IF/OF exchange-time magnitudes;
- elite base-to-base timing examples;
- tracked relay examples;
- using Sprint Speed magnitude as a fielder movement ceiling/prior.

### QUALITATIVE
- relay/cutoff necessity rises for deeper throws;
- defender ratings should affect both first-step/reaction and effective movement speed;
- runner handedness primarily affects home-to-first start geometry, not later base legs.

### OPEN
- current league-average generic non-catcher pickup/transfer delay;
- exact effective fielder pursuit speed by position;
- exact direct-throw effective velocity reduction vs Arm Strength;
- generic relay threshold/penalty;
- KBO runner home-to-first and base-to-base distributions;
- KBO position-by-position arm strength;
- KBO retrieval and exchange timings;
- project rating -> reaction/speed/arm multipliers.

---

## KBO_CALIBRATION

`KBO_CALIBRATION = OPEN`

No KBO-specific coefficient is created by this document. MLB tracking is used as an architecture/magnitude reference only.

---

## SOURCES

Primary/reference sources used:
- MLB Statcast Sprint Speed glossary and Baseball Savant Sprint Speed leaderboard.
- MLB Statcast Fielding Alignments / Shifts glossary for standard IF/OF positioning zones.
- MLB Statcast Arm Strength glossary and Baseball Savant 2025 Arm Strength leaderboard.
- MLB Statcast Home-to-First and 90-Foot Running Splits glossaries.
- MLB Statcast/OAA definitions for distance/time/runner-speed defensive timing concepts.
- MLB Official Baseball Rules / field geometry for 90-ft base paths.
- MLB Statcast glossary for Exchange, fielder max speed, first step, acceleration, route efficiency.
- Historical Statcast examples for IF/OF exchange and relay timing magnitude.

No restricted raw dataset is committed.

---

## FINAL_DECISION

`PHASE2E_B_RESEARCH = READY`

`RECOMMENDED_OWNERSHIP_MODEL = RADIAL_DEPTH_PLUS_SPRAY_SECTORS_WITH_PRIMARY_OWNER_AND_ONE_ADJACENT_FALLBACK`

`RECOMMENDED_RETRIEVAL_TIME_MODEL = REACTION_DELAY_PLUS_DISTANCE_OVER_BOUNDED_EFFECTIVE_SPEED_PLUS_PICKUP_TRANSFER_DELAY`

`RECOMMENDED_DEFENDER_RATING_EFFECT = BOUNDED_COMBINED_REACTION_AND_EFFECTIVE_SPEED_ADJUSTMENT`

`RECOMMENDED_THROW_MODEL = DIRECT_DISTANCE_OVER_EFFECTIVE_THROW_SPEED_PLUS_TRANSFER_RELEASE_WITH_DISTANCE_THRESHOLD_FIXED_RELAY_PENALTY`

`RECOMMENDED_RUNNER_TIME_MODEL = STANDARDIZED_BASE_LEG_TIMES_WITH_HOME_TO_FIRST_START_TERM_AND_BOUNDED_SPEED_MULTIPLIER`

`RECOMMENDED_HIT_RESOLUTION_MODEL = DETERMINISTIC_RETRIEVAL_PLUS_HYPOTHETICAL_BASE_ARRIVAL_TIME_RACES`

`RNG_MODEL = DETERMINISTIC`

`KBO_CALIBRATION = OPEN`

`IMPLEMENTATION_HANDOFF_TO_01 = YES`
