# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@d8caf038b0e1cbf9ccc4e4b3859f84799cae3269
STATE: ACTIVE
CURRENT_TASK: Phase 2E-B Retrieval / Physical Hit-Type Research
RESULT: READY_FOR_IMPLEMENTATION_ARCHITECTURE_KBO_CALIBRATION_OPEN

## LAST_COMPLETED
- Public data provenance/usage policy remains in place.
- Phase 2A through Phase 2E-A reference packs remain active upstream references.
- Phase 2E-A is merged on production main as merge commit `a207c6a0ee6cee73a1840fdf85648649610f180b`.
- Added `docs/phase2e-retrieval-hit-type-reference.md` for O(1) retriever ownership, retrieval timing, throw timing, batter-runner timing, and deterministic physical OUT/1B/2B/3B shadow architecture.

## CURRENT_FINDINGS
- Official Statcast standard positioning zones give a defensible basis for fixed nominal defender anchors without pathfinding. Neutral IF zones vary by batter side; OF standard zones are LF 260-320 ft / -33 to -21 deg, CF 280-350 ft / -8 to +7 deg, RF 260-320 ft / +21 to +33 deg.
- Recommended ownership is radial-depth + spray-sector zoning with one primary owner and one predeclared adjacent fallback. Runtime roster scans / nearest-player loops are unnecessary.
- Retrieval timing can be reduced to `reaction_delay + retrieval_distance / effective_fielder_speed + pickup_transfer_delay`. Statcast Sprint Speed provides a human-speed magnitude reference (~27 ft/s MLB average competitive speed; ~23-30 ft/s broad competitive range), but must not be copied directly as fielder effective pursuit speed.
- Statcast Exchange directly supports a pickup/transfer component. Public tracked examples put non-catcher fielding exchange on an order of roughly ~1 s, but a clean current universal IF/OF pickup-transfer calibration was not recovered; numeric coefficient remains OPEN.
- Recommended defender-rating effect is bounded combined adjustment of reaction delay and effective retrieval speed. Same BIP + higher range/defense must never increase retrieval time. Exact project-rating-point mapping is OPEN.
- 2025 official Baseball Savant Arm Strength league-average leaderboard values: 1B 78.3 mph, 2B 79.3, 3B 85.6, SS 85.7, LF 87.1, CF 89.6, RF 90.5. These are position-specific top-fraction max-effort metrics, not average velocity of every throw.
- Recommended throw model is `transfer_release_delay + throw_distance / effective_throw_speed`, with effective speed calibrated below/from the max-effort arm-strength reference. Deep throws may use one fixed relay penalty after a distance threshold; no relay-chain simulation.
- Official MLB base geometry is a 90-ft square. Statcast Home-to-First is contact-to-first touch; standardized 90-ft splits remove part of batter-side geometry. Current elite 2025 90-ft splits are ~3.67-3.75 s; current elite home-to-first examples are ~4.0-4.2 s. Extra-base tracked extremes show ~3.2-3.3 s first-to-second for already-moving elite runners. These are elite references, not KBO central targets.
- Recommended runner timing is a home-to-first start/acceleration term plus standardized 90-ft leg timings under a bounded speed multiplier. Optional handedness effect belongs only in the home-to-first start term; V1 may omit it.
- Physical hit type must not be a final-distance threshold. Recommended resolution is deterministic timing races: retrieval + hypothetical throw arrival to 1B/2B/3B versus cumulative batter-runner arrival times. At most three fixed base evaluations are needed.
- Phase 2D physical catch terminates as OUT with no Phase 2E-B retrieval. Uncaught air balls and ground balls can unify after Phase 2E-A `FinalBallLocation` and use the same retrieval timing machinery.
- V1 RNG is not required. Preserve time margins for future optional boundary-play probability/error layers; initial Phase 2E-B should be deterministic.
- KBO play-level retrieval, throw, runner, exchange, and arm-strength calibration remains OPEN.

## SOURCE / DEFINITION QUALITY
- VERIFIED MLB: base geometry; Sprint Speed definition/magnitude; Home-to-First/90-ft split definitions; standard IF/OF positioning zones; Arm Strength definition and 2025 position-group values; Exchange definition.
- PARTIAL: historical IF/OF exchange magnitudes; elite extra-base timing examples; relay examples; using runner Sprint Speed magnitude as a fielder movement ceiling/prior.
- QUALITATIVE: deeper throws increasingly require cutoff/relay; defender range affects reaction plus effective movement; batter side mainly changes raw home-to-first start geometry.
- OPEN KBO: nominal positions, retrieval time, pickup/exchange time, arm strength, effective throw speeds, runner leg times, relay threshold/penalty, rating multipliers.

## MODEL POLICY
- `RECOMMENDED_OWNERSHIP_MODEL = RADIAL_DEPTH_PLUS_SPRAY_SECTORS_WITH_PRIMARY_OWNER_AND_ONE_ADJACENT_FALLBACK`
- `RECOMMENDED_RETRIEVAL_TIME_MODEL = REACTION_DELAY_PLUS_DISTANCE_OVER_BOUNDED_EFFECTIVE_SPEED_PLUS_PICKUP_TRANSFER_DELAY`
- `RECOMMENDED_DEFENDER_RATING_EFFECT = BOUNDED_COMBINED_REACTION_AND_EFFECTIVE_SPEED_ADJUSTMENT`
- `RECOMMENDED_THROW_MODEL = DIRECT_DISTANCE_OVER_EFFECTIVE_THROW_SPEED_PLUS_TRANSFER_RELEASE_WITH_DISTANCE_THRESHOLD_FIXED_RELAY_PENALTY`
- `RECOMMENDED_RUNNER_TIME_MODEL = STANDARDIZED_BASE_LEG_TIMES_WITH_HOME_TO_FIRST_START_TERM_AND_BOUNDED_SPEED_MULTIPLIER`
- `RECOMMENDED_HIT_RESOLUTION_MODEL = DETERMINISTIC_RETRIEVAL_PLUS_HYPOTHETICAL_BASE_ARRIVAL_TIME_RACES`
- `RNG_MODEL = DETERMINISTIC`
- `KBO_CALIBRATION = OPEN`

## REQUIRED STATE / OBSERVABILITY
- `RetrievalState`: validity/applicability, primary/adjacent defender role, nominal defender start, ball final x/y, retrieval distance, reaction, effective speed, travel, pickup/transfer, total retrieval time, wall-ground-contact.
- `ThrowState`: target base, origin/target coordinates, throw distance, arm reference, effective throw speed, transfer/release, relay flag/penalty, throw time, defense-arrival time.
- `RunnerTimingState`: speed reference/multiplier, home-start delay, H-1 / 1-2 / 2-3 leg times, cumulative 1B/2B/3B arrival times.
- `PhysicalHitResolution`: upstream physical catch, defense vs runner times/margins for 1B/2B/3B, deterministic `OUT | 1B | 2B | 3B | NOT_APPLICABLE` shadow result, model version.

## MONOTONICITY / VALIDATION POLICY
- farther retrieval distance -> retrieval time non-decreasing;
- higher range rating -> retrieval time non-increasing;
- farther throw distance -> throw time non-decreasing;
- higher arm rating/effective throw speed -> throw time non-increasing;
- higher runner speed -> base arrival times non-increasing;
- mirrored LF/RF states with mirrored ratings/anchors -> equal scalar timings;
- invalid GroundTravelState -> invalid retrieval state;
- Phase 2D physical catch -> no Phase 2E-B hit resolution;
- all times finite and >=0;
- same exact input -> deterministic same shadow result.

## OWNER HANDOFF
- 01 Gameplay Engine: Phase 2E-B implementation is research-ready. Use fixed zone ownership, nominal defender anchors, one retrieval-time calculation, up to three fixed hypothetical base throw timings, deterministic runner timings, and no RNG. Do not scan roster defenders or simulate routes/relays. Preserve timing margins and model-version diagnostics. Do not treat Statcast max-effort Arm Strength as direct actual throw speed.
- 05 Balance Lab: validate ownership shares, retrieval/throw/runner timing distributions, monotonic sweeps, mirrored cases, relay threshold behavior, 1B/2B/3B time-margin distributions, physical OUT/1B/2B/3B shadow composition, wall-stop cases, and downstream BABIP/XBH shadow impact. No MLB/KBO result-share gate is authorized yet.
- 00 Physical Batted-Ball Engine HQ: architecture handoff is YES; numeric timing/arm/rating calibration remains OPEN. No authority migration is automatically approved by this research.

## BLOCKERS / DATA_GAPS
- KBO play-level retrieval distance/time and defender start positions.
- KBO fielder pickup/exchange distributions.
- KBO position-by-position arm strength / effective throw velocity.
- KBO home-to-first and base-leg timing distributions.
- KBO relay usage/timing.
- Project rating -> reaction/speed/arm timing multipliers.
- Current universal MLB non-catcher pickup-transfer baseline.

## NEXT_ACTION
- Phase 2E-B is research-ready for 01 shadow implementation. Highest-value future research is KBO runner-time and fielder arm/retrieval tracking. Before any authority cutover, 05 should validate the deterministic timing surfaces and downstream hit-type distributions.

## RELATED_DOCS
- `docs/phase2e-retrieval-hit-type-reference.md`
- `docs/phase2e-ground-travel-reference.md`
- `docs/phase2d-catch-probability-defense-reference.md`
- `docs/phase2c-kbo-stadium-wall-geometry-reference.md`
- `docs/phase2b-lightweight-trajectory-reference.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- MLB_STANDARD_POSITIONING_REFERENCE = VERIFIED
- MLB_SPRINT_SPEED_REFERENCE = VERIFIED
- MLB_ARM_STRENGTH_REFERENCE = VERIFIED
- MLB_RUNNER_TIMING_REFERENCE = VERIFIED_PARTIAL
- GENERIC_NONCATCHER_EXCHANGE = PARTIAL_OPEN
- KBO_RETRIEVAL_TIMING = OPEN
- KBO_ARM_STRENGTH = OPEN
- KBO_RUNNER_TIMING = OPEN
- FIXED_ZONE_RETRIEVER_OWNERSHIP = RECOMMENDED
- O1_RETRIEVAL_TIME = SATISFIABLE
- BOUNDED_DEFENDER_RATING_EFFECT = RECOMMENDED
- O1_THROW_MODEL = SATISFIABLE
- FIXED_RELAY_PENALTY = RECOMMENDED
- DETERMINISTIC_RUNNER_TIMING = RECOMMENDED
- DETERMINISTIC_HIT_TYPE_TIMING_RACE = RECOMMENDED
- RNG_MODEL = DETERMINISTIC
- PHASE2E_B_VALIDATION_METRIC_PACK = PASS
- PHASE2E_B_RESEARCH = READY
- KBO_CALIBRATION = OPEN
- IMPLEMENTATION_HANDOFF_TO_01 = YES
