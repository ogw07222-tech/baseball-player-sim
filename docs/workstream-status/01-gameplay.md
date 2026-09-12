# 01 - Gameplay Engine

WORKSTREAM: 01 - Gameplay Engine
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: task-start main@081c45ed9382d16c3569398d1ada1dbc842d6cf2; PR #68 code/test checkpoint@f6053039f25310378922df6030f832c67cc5f4c9
STATE: READY_FOR_05_PHASE2E_A_VALIDATION
CURRENT_TASK: Phase 2E-A Ground Travel / Final Location Shadow
RESULT: PASS_IMPLEMENTATION / 05_VALIDATION_OPEN

## SOURCE_STATE
- Actual latest main at task start: `081c45ed9382d16c3569398d1ada1dbc842d6cf2`.
- Phase2A/B/C/D were already integrated; the latest main additionally contained the 08 Phase2E-A research/status documentation.
- No open Phase2D/Phase2E gameplay PR existed at task start.
- Branch: `feature/phase2e-a-ground-travel-shadow`.
- PR: #68 `Gameplay: Phase 2E-A ground travel final-location shadow`.
- Code/test checkpoint validated by CI: `f6053039f25310378922df6030f832c67cc5f4c9`.
- CI run: `34669261305`; merge-ref tested against task-start main.

## PRODUCTION FLOW / AUTHORITY
Production physical metadata flow is now:
`Phase1 contact -> Phase2A BattedBallState -> Phase2B first-ground trajectory -> Phase2C WallInteraction -> Phase2E-A GroundTravelState -> Phase2D DefensiveOpportunity/Resolution shadow -> existing legacy result resolver`.

Phase2E-A is metadata/shadow only.
Still authoritative and unchanged:
- `PlateAppearanceOutcome.result`;
- legacy HR resolver;
- legacy defense / error path;
- legacy 1B/2B/3B resolver;
- runner advancement;
- Phase1 fair/foul semantics;
- Phase2D defensive shadow authority remains non-canonical.

## GROUND_TRAVEL_SCHEMA
New immutable `GroundTravelState` fields:
- `valid`
- `surface_class`
- `impact_horizontal_speed_fps`
- `post_impact_horizontal_speed_fps`
- `bounce_distance_ft`
- `rollout_start_speed_fps`
- `rollout_distance_ft`
- `ground_travel_distance_ft`
- `first_impact_x_ft`, `first_impact_y_ft`
- `final_x_ft`, `final_y_ft`
- `final_radial_distance_ft`
- `wall_ground_contact`
- `ground_model_version`
- `invalid_reason`

All numeric fields are finite. Speeds/distances are non-negative. `BattedBallState` now has optional `ground_travel` metadata.

## IMPACT_SPEED_MODEL
Research contract followed:
`impact_horizontal_speed = first_ground_impact_distance / hang_time * class_correction`.

The source of truth remains Phase2B realized trajectory; no independent flight model is created.
Engineering baseline corrections:
- ground_like `0.96`
- line_drive `0.90`
- fly_ball `0.84`
- popup `0.72`

Impact-speed proxy is bounded to 220 ft/s for numerical safety. These are engineering baselines, not KBO-measured coefficients.

## BOUNCE_MODEL
Exactly one representative bounce is modeled:
- `post_impact_speed = impact_speed * class_retention`
- `bounce_distance = post_impact_speed * fixed_class_time_proxy`
- `rollout_start_speed = post_impact_speed * class_rollout_retention`

No repeated bounce loop, timestep, frame stepping, numerical integration, or collision iteration exists.
The Pennbounce total surface-pace values were not copied directly into horizontal retention coefficients.

## ROLLOUT_MODEL
Neutral V1 rollout uses constant effective deceleration:
`d_roll = v_roll^2 / (2 * a_roll)`.

Default engineering baseline:
- `a_roll = 35 ft/s^2`.
- must be finite and >0.
- zero rollout-start speed returns exactly zero rollout distance.

`rollout_distance_ft()` is exposed as a deterministic helper so 05 can test speed/resistance monotonicity directly.

## SURFACE_MODEL
`surface_class = "neutral"` only.
No grass/dirt/synthetic map or radial pseudo-classification was added.
Schema/model version are explicit so later trustworthy surface geometry can extend the contract without replacing the state type.

## FINAL_POSITION / MIRROR
First impact uses Phase2B canonical landing coordinate.
Post-impact travel stays on the same Phase2A spray ray:
- `unit_x = sin(spray)`
- `unit_y = cos(spray)`
- final radial position = first-impact radial distance + realized ground travel, subject to wall clamp.

Thus mirrored +/- spray produces equal scalar travel / radial distance, mirrored X, and equal Y.
No lateral spin drift is modeled in V1.

## WALL_STOP_MODEL
Phase2C `WallInteraction.wall_radius_ft` is reused; no new stadium geometry exists.
If unconstrained final ground radius reaches/passes the wall:
- final radius is clamped exactly to wall radius;
- final x/y are recomputed at that radial wall point on the same spray ray;
- `wall_ground_contact=True`;
- no rebound/carom velocity is retained.

If the airborne Phase2B trajectory already reaches the wall before first ground impact, Phase2E-A returns invalid `air_wall_precedes_ground` rather than inventing a post-impact path.

## RNG / DETERMINISM
Phase2E-A RNG usage = ZERO.
- no parent RNG read is required for ground travel;
- no new child RNG namespace is created;
- Phase2D child RNG contract remains unchanged.

Dedicated tests compare Phase2E-A enabled vs test-only disabled and verify exact equality of:
- final PA result sequence;
- canonical parent RNG state;
- Phase2A state;
- Phase2B trajectory;
- Phase2C wall interaction;
- Phase2D defensive opportunity/resolution.

## INVALID / FAIL-SAFE
Explicit invalid states cover:
- missing trajectory;
- invalid trajectory;
- unsupported trajectory class;
- missing wall context;
- non-finite input;
- invalid/near-zero hang time;
- invalid wall radius;
- non-positive/non-finite rollout deceleration;
- airborne wall interaction before first-ground travel;
- non-finite derived or final geometry.

Invalid GroundTravelState has finite safe zero travel and never creates any physical hit/out authority.

## CHANGED FILES
Production:
- new `src/hitting/ground_travel.py` — blob `cae9d2e8c979d83781dd39c4a579856f7b56ad4c`.
- new `src/hitting/ground_travel_parameters.py` — blob `dd69d779eed5645c2d2d2d254fc2ff0cebec1f33`.
- modified `src/hitting/physical.py` — blob `2d5242375ed35775a261d51a96c62880015ad368`.

Tests:
- new `tests/test_phase2e_a_ground_travel.py`.

No changes to `src/hitting/model.py`, legacy `src/hitting/defense.py`, baserunning, Phase1 parameters, trajectory coefficients, or stadium geometry.

## TESTS / CI
GitHub Actions run `34669261305` on code/test checkpoint `f6053039f25310378922df6030f832c67cc5f4c9`:
- web build/tests PASS;
- Python dependency/compile PASS;
- durable-store/API PASS;
- related production integration 31/31 PASS;
- Phase1 regression PASS;
- Phase2A regression PASS;
- Phase2B regression PASS;
- Phase2C regression PASS;
- Phase2D regression PASS;
- Phase2E-A targeted 13/13 PASS.

Phase2E-A targeted PASS:
- finite/non-negative state;
- impact-speed distance monotonicity;
- rollout speed monotonicity;
- resistance monotonicity;
- zero-speed rollout;
- trajectory-class structural behavior;
- LF/RF mirror;
- deterministic wall clamp;
- no-wall path;
- invalid trajectory / air-wall / invalid-deceleration fail-safe;
- exact deterministic replay;
- production metadata attachment + parent RNG purity;
- enabled/disabled legacy outcome + upstream Phase2A/B/C/D metadata exact invariance;
- 50k fixed-cost ground-state guard.

Full Python discover: 466 tests, 465 PASS, 1 FAIL.
Sole failure remains pre-existing/out-of-scope `test_balance_v04.BalanceV04Tests.test_draft_distribution_not_extreme`: undrafted `0.056666...`, historical assertion requires `>0.10`. Phase2E-A does not touch generation/draft balance.

Phase1 fixed-seed sanity remained unchanged (40k): BB 9.4625%, K 17.6475%, HBP 1.285%, HR/PA 2.835%, Swing 48.0969%, Chase 20.9709%.

## PERFORMANCE
Architecture is O(1) fixed cost per eligible BIP:
- one division for impact-speed proxy;
- fixed class lookups;
- one-bounce algebra;
- one `v^2/(2a)` rollout calculation;
- one radial wall comparison/clamp;
- no runtime loops in production ground model.

Direct 50,000 GroundTravelState generation guard PASS (<5 s loose CI guard).
No coefficient/performance tuning was performed in this PR.
05 should perform the requested paired 50k+ PA and 500+ game incremental/cumulative Phase2 benchmark because Phase2D already carries cumulative performance WATCH.

## KNOWN_LIMITATIONS
- coefficients are neutral engineering baselines; KBO calibration remains OPEN;
- surface is neutral only;
- no explicit impact velocity from Phase2B yet; distance/hang proxy is used;
- one representative bounce only;
- no spin-resolved ground impact;
- no wall rebound/carom;
- no ground defender assignment, retrieval, pickup, throw, physical 1B/2B/3B authority, runner timing, or advancement changes;
- ground travel is metadata only and cannot change gameplay outcome.

## HANDOFF TO 05
Independent target:
- PR #68 `Gameplay: Phase 2E-A ground travel final-location shadow`.
- Validate exact final PR HEAD reported after this status-only commit; production code identity remains code/test checkpoint `f6053039f25310378922df6030f832c67cc5f4c9`.

Required 05 validation:
1. source/blob identity;
2. valid/invalid GroundTravelState distribution by trajectory class;
3. impact/post-impact/bounce/rollout/final-distance distributions and bound pileup;
4. monotonic sweeps for distance, speed, deceleration and class effects;
5. LF/RF mirror and wall-stop invariants;
6. exact Phase1/2A/2B/2C/2D/final-result/RNG regression;
7. 50k+ PA and 500+ game paired benchmark with us/PA, ms/game, incremental delta and cumulative Phase2 cost;
8. no tuning or authority migration during validation.

## GATES
- GROUND_TRAVEL_SCHEMA = PASS
- IMPACT_SPEED_MODEL = PASS_STRUCTURAL
- REPRESENTATIVE_BOUNCE = PASS_STRUCTURAL
- ROLLOUT_MODEL = PASS
- SURFACE_MODEL = NEUTRAL_V1
- WALL_GROUND_STOP = PASS
- MIRROR = PASS
- INVALID_STATE_FAIL_SAFE = PASS
- RNG_USAGE = ZERO
- LEGACY_RESULT_INVARIANCE = PASS
- PHASE2D_REGRESSION = PASS
- PHASE2C_REGRESSION = PASS
- PHASE2B_REGRESSION = PASS
- PHASE2A_REGRESSION = PASS
- PHASE1_REGRESSION = PASS
- PRODUCTION_INTEGRATION = PASS
- PERFORMANCE_ARCHITECTURE = PASS_O1
- FULL_PYTHON_SUITE = BLOCKED_ONLY_BY_OUT_OF_SCOPE_DRAFT_GATE_465_OF_466_PASS
- PHASE2E_A_IMPLEMENTATION = PASS
- PHASE2E_A_05_VALIDATION = OPEN
- READY_FOR_05 = YES
