# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@8884a8cf174a37995c1c9d60de7fe475722ce3cf
STATE: ACTIVE
CURRENT_TASK: Phase 2E-A ground travel / bounce / rollout research
RESULT: READY_FOR_IMPLEMENTATION_ARCHITECTURE_KBO_CALIBRATION_OPEN

## LAST_COMPLETED
- Public data provenance/usage policy remains in place.
- Phase 2A EV/LA/timing/spray, Phase 2B trajectory, Phase 2C stadium-wall, and Phase 2D catch-probability reference packs remain active upstream references.
- Added `docs/phase2e-ground-travel-reference.md` for first-ground-impact -> representative bounce -> analytical rollout -> final-location research under strict O(1) runtime constraints.

## CURRENT_FINDINGS
- Penn State baseball-field surface research directly supports large first-impact speed loss and strong surface dependence. Reported outbound/inbound surface-pace values span roughly natural turf ~0.38-0.48 and skinned dirt ~0.56-0.60 under representative controlled conditions; synthetic systems are generally intermediate/faster than natural grass. These are total post/pre impact speed ratios, not pure horizontal restitution coefficients.
- Impact angle materially affects surface pace. Wet-grass baseball research also shows horizontal-speed loss depends on incident angle and friction regime, so a single universal horizontal-retention constant is not physically exact.
- Exact baseball-ground decomposition into normal restitution, tangential retention, and spin coupling is not available as a public KBO calibration surface. Topspin/backspin effects remain qualitative for Phase 2E-A.
- Recommended impact-horizontal-speed proxy is `first_impact_distance / hang_time` multiplied by a small calibratable class/LA correction. This reuses the canonical Phase 2B realized trajectory and avoids a second independent flight model. A future direct Phase 2B impact-velocity output should supersede the proxy.
- Recommended bounce architecture is one representative bounce only: incoming proxy -> retained horizontal speed -> fixed/algebraic bounce distance -> rollout-start speed. No repeated bounce loop.
- Recommended rollout architecture is constant effective deceleration with `d_roll = v0^2 / (2*a_roll)`. It is O(1), monotonic, stable, interpretable, and easy to recalibrate later. No trustworthy universal baseball `a_roll` value was recovered; numeric KBO calibration remains OPEN.
- Same first-impact location should not imply identical ground travel: hard grounder, soft grounder, line-drive first bounce, fly-ball landing, and popup landing can have materially different incoming horizontal speed/angle.
- Phase 2E-A should reuse Phase 2B first-impact distance, time/hang time, EV/LA, trajectory class, and spray. EV alone or first-impact distance alone is insufficient.
- Surface class matters physically, but current stadium data does not provide reliable grass/dirt polygons. A radial-depth-only grass/dirt guess would create false precision. `SURFACE_MODEL = NEUTRAL_V1` is recommended with a future surface-class interface reserved.
- Recommended ground-wall interaction is deterministic wall-stop: if unconstrained ground travel crosses the Phase 2C wall radius, clamp final location to the wall, set `wall_ground_contact=true`, and do not simulate rebound in V1.
- Architecture preserves strict O(1): fixed algebra, tiny lookup/branch, no frame stepping, no integration loop, no collision iteration, no mesh traversal.

## SOURCE / DEFINITION QUALITY
- VERIFIED/PARTIAL: Penn State `Pennbounce` baseball-field surface-pace experiments and field surveys; surface and impact-angle effects; grass/dirt ordering.
- QUALITATIVE STRONG: friction/incident-angle/spin regime effects on horizontal ground-bounce behavior.
- OPEN: KBO-specific surface pace, horizontal retained-speed coefficient, rolling deceleration, stop-distance distribution, spin-resolved ground-impact surface, wall-carom coefficient.
- Important definition warning: Pennbounce `COR`/surface pace is outbound total speed divided by inbound total speed for a field impact. It must not be copied directly as Phase 2E horizontal-speed retention.

## MODEL POLICY
- `RECOMMENDED_IMPACT_SPEED_MODEL = FIRST_IMPACT_DISTANCE_DIV_HANG_TIME_WITH_SMALL_CALIBRATABLE_CORRECTION`
- `RECOMMENDED_BOUNCE_MODEL = ONE_REPRESENTATIVE_BOUNCE_FIXED_ALGEBRA_OR_SMALL_LOOKUP`
- `RECOMMENDED_ROLLOUT_MODEL = CONSTANT_EFFECTIVE_DECELERATION_V2_OVER_2A`
- `SURFACE_MODEL = NEUTRAL_V1`
- `WALL_GROUND_INTERACTION = DETERMINISTIC_WALL_STOP_AT_PHASE2C_RADIUS`
- `KBO_CALIBRATION = OPEN`

## MONOTONICITY / VALIDATION POLICY
- higher impact-horizontal-speed proxy -> non-decreasing ground travel;
- higher retained-speed parameter -> non-decreasing ground travel;
- higher effective rolling resistance/deceleration -> non-increasing rollout;
- mirror spray -> equal scalar travel and mirrored X;
- invalid/no first-ground-impact state -> no valid ground-travel state;
- all distances finite and >=0;
- absent wall interaction, final radial distance >= first-impact radial distance;
- wall-stop may cap final radius at the stadium wall;
- zero rollout-start speed -> zero rollout distance.

## OWNER HANDOFF
- 01 Gameplay Engine: Phase 2E-A implementation is research-ready. Use the canonical Phase 2B first-impact position/time as the impact-speed proxy basis, one representative bounce, analytical constant-deceleration rollout, neutral-surface V1, and deterministic wall-stop. Preserve diagnostics for impact-speed proxy, post-impact speed, bounce distance, rollout distance, total ground travel, final x/y, wall contact, and model version. Do not import Pennbounce surface-pace numbers directly as horizontal coefficients.
- 05 Balance Lab: validate impact-speed, retained-speed, bounce/roll/total-travel distributions by trajectory class; monotonic parameter sweeps; mirror invariants; zero/extreme-state stability; wall clamp; wall-ground-contact rate. If later grass/dirt fixtures are added, dirt-like should play faster than natural-grass-like under otherwise matched conditions, but do not call this KBO calibration.
- 00 Physical Batted-Ball Engine HQ: no coefficient decision requested from 08. Architecture handoff is YES; KBO numeric calibration remains OPEN.

## BLOCKERS / DATA_GAPS
- KBO-specific baseball-ground surface pace / rebound measurements.
- KBO grass/dirt/artificial-turf ground-ball pace.
- Modern game-level post-impact horizontal-speed distributions.
- Baseball rolling deceleration / stop-distance distribution under professional field conditions.
- Spin-resolved ground-impact reference.
- Reliable field-surface polygons for KBO parks.
- Wall-carom restitution by wall type/stadium.

## NEXT_ACTION
- Phase 2E-A is research-ready for 01 implementation. Highest-value future research is professional/KBO ground-ball post-impact speed and stop-distance data, followed by reliable grass/dirt field mapping and wall-carom references for Phase 2E-B or later refinement.

## RELATED_DOCS
- `docs/phase2e-ground-travel-reference.md`
- `docs/phase2d-catch-probability-defense-reference.md`
- `docs/phase2c-kbo-stadium-wall-geometry-reference.md`
- `docs/phase2b-lightweight-trajectory-reference.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- BASEBALL_SURFACE_PACE_STRUCTURE = VERIFIED_PARTIAL
- GRASS_DIRT_PACE_ORDERING = VERIFIED
- EXACT_HORIZONTAL_RESTITUTION = OPEN
- SPIN_GROUND_EFFECT = QUALITATIVE
- IMPACT_SPEED_PROXY_B = RECOMMENDED
- ONE_BOUNCE_SURROGATE = RECOMMENDED
- CONSTANT_DECELERATION_ROLLOUT = RECOMMENDED
- NEUTRAL_SURFACE_V1 = RECOMMENDED
- DETERMINISTIC_WALL_STOP = RECOMMENDED
- O1_GROUND_TRAVEL_CONTRACT = SATISFIABLE
- KBO_GROUND_TRAVEL_CALIBRATION = OPEN
- PHASE2E_A_VALIDATION_METRIC_PACK = PASS
- PHASE2E_A_RESEARCH = READY
- IMPLEMENTATION_HANDOFF_TO_01 = YES
