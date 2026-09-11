# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@cc9580fe1e3d866ef69554aa8419aa9e8198df14
STATE: ACTIVE
CURRENT_TASK: Phase 2B lightweight baseball trajectory reference research
RESULT: VERIFIED_FOR_ARCHITECTURE_PARTIAL_FOR_KBO_CALIBRATION

## LAST_COMPLETED
- Public data provenance/usage policy remains in place.
- `docs/phase2a-ev-la-timing-spray-fair-foul-reference.md` remains the Phase 2A source pack.
- Added `docs/phase2b-lightweight-trajectory-reference.md` for Phase 2B trajectory / hang-time / landing-position research under fixed O(1) runtime constraints.

## CURRENT_FINDINGS
- Official baseball specification: mass 5.00-5.25 oz (141.75-148.84 g), circumference 9.00-9.25 in, implying spherical diameter ~72.77-74.79 mm. Any single mass/diameter used by production is an engineering nominal value, not an official exact constant.
- Standard gravity 9.80665 m/s^2 and standard sea-level atmosphere around rho=1.225 kg/m^3, T=15 C, p=101325 Pa are strong reference constants.
- Baseball drag and Magnus/lift are materially important. Experimental literature covers representative baseball speeds ~50-110 mph and spin ~1500-4500 rpm; drag/lift depend on spin/seam state, so a universal fixed Cd/Cl is not empirically exact.
- Vacuum-only trajectory is rejected for air-ball production. Alan Nathan reference: 100 mph, 29 deg, 2500 rpm, 3-ft launch height, sea-level-like 60 F -> ~397 ft with aerodynamics vs ~571 ft in vacuum. Vacuum overpredicts by ~174 ft / ~43.8% relative to the aerodynamic result.
- Derived no-drag 29-deg/3-ft ranges are ~368/465/572/691 ft at 80/90/100/110 mph respectively. Only the 100-mph case has the aligned verified aerodynamic comparison; the same attenuation factor must not be extrapolated blindly to other speeds.
- Real baseball maximum carry occurs broadly around high-20s/~30 deg rather than vacuum 45 deg. A 100-mph non-spinning Nathan-calculator series gives hang times 2.1/3.1/3.9/4.5/5.6/6.3/6.6 s at 5/10/15/20/30/40/45 deg.
- Actual Statcast high-fly anchor: 105.2 mph, 50 deg, 6.8 s hang, 172-ft apex. Compact league apex distributions remain OPEN.
- Recommended primary runtime architecture: high-fidelity drag/lift trajectories generated OFFLINE -> EVxLA grid -> runtime bilinear interpolation for carry/hang/apex. This satisfies fixed O(1), no loops, no root solve, no frame stepping.
- Recommended secondary architecture: exact vacuum analytical base + jointly fitted correction surfaces for distance/hang/apex. Also O(1), but cross-output consistency must be controlled.
- For sharply negative/near-zero LA, exact analytical first-ground intersection is defensible for Phase 2B V1 because flight is short. At 90 mph from 3 ft, no-drag first-impact examples: -15 deg ~11 ft/0.084 s, -10 deg ~16 ft/0.121 s, -5 deg ~27 ft/0.203 s, 0 deg ~57 ft/0.432 s. These are DERIVED engineering references, not empirical league values.
- Fixed standard atmosphere is acceptable for generic Phase 2B V1 if explicitly labeled neutral-air/no-wind. Nathan/Statcast analysis shows temperature, altitude and especially wind alter carry; wind can shift a ~400-ft fly by tens of feet, so omission is a simplification, not evidence of insignificance.
- Nathan atmospheric sensitivity reference around a 401-ft fly: +10 temperature units in the source's U.S.-unit context ~+3.3 ft; +1000 ft elevation ~+5.9 ft; +50 percentage-point RH ~+0.9 ft; 5 mph out wind ~+18.8 ft. Separate 100/29 case: ~413 ft with 5 mph out wind vs ~380 ft with 5 mph in wind.

## MODEL DECISION SUPPORT
- A vacuum projectile: O(1), stable, but realism FAIL due severe over-carry and wrong optimum angle.
- B simple empirical attenuation: O(1), good runtime, moderate realism; weak if distance/time/apex are corrected independently.
- C constant effective drag: only suitable if reduced to a pre-fit algebraic surrogate; exact 2D quadratic-drag landing is not naturally a simple no-root closed-form production solution.
- D EVxLA carry/hang/apex lookup/surface: O(1), stable, high fidelity within calibrated domain, RECOMMENDED.
- E simplified drag+lift closed-form surrogate: viable O(1) if pre-fit, but calibration is harder than D.

## STANDARD_ATMOSPHERE_POLICY
- Phase2B V1 fixed neutral atmosphere = ACCEPTABLE.
- Humidity omission = ACCEPTABLE for V1 generic trajectory.
- Temperature omission = ACCEPTABLE with documented standard state.
- Altitude omission = ACCEPTABLE for generic KBO-neutral V1, not park-specific realism.
- Stadium-specific air density = DEFER.
- Wind omission = ACCEPTABLE only as an explicit no-wind assumption; wind is materially important and should not be described as negligible.

## OWNER HANDOFF
- 01 Gameplay Engine: use one deterministic O(1) canonical trajectory engine. Preferred runtime path is offline drag/lift EVxLA surface + bilinear interpolation. Return carry distance, ground-flight time, apex, landing x/y. Preserve mirror spray symmetry. Negative/near-zero LA can use analytic first-impact kinematics. Do not use vacuum-only air-ball carry, per-BIP integration, timestep loops, or iterative root finding.
- 05 Balance Lab: validate distance/hang/apex distributions and EVxLA grids; fixed-EV angle sweeps; 100 mph / 29 deg ~397-ft aerodynamic anchor vs ~571-ft vacuum anchor; low-LA impact grids; high-LA hang/apex tails; mirror-coordinate invariants; min/max EV/LA stability.
- 00 Game Design HQ: no coefficient tuning decision required from 08. If Phase 2B needs a policy decision, choose between offline physical-surface lookup and analytic+correction surrogate; 08 recommends the former.

## SANITY POLICY
- 100 mph / high-20s LA should be order-of-magnitude ~400 ft under neutral realistic-air conditions, not ~570+ ft.
- distance maximum near 45 deg = FAIL; broad high-20s/low-30s optimum = PASS/WATCH.
- recurring 600+ ft realistic-air carry = FAIL.
- broad hang sanity: low line/near-ground <~3 s, LD ~2-4.5 s, ordinary fly ~4-6 s, high fly/popup ~5-8 s; recurring >9 s = WATCH/FAIL.
- broad apex sanity: low liner <~30 ft, LD ~10-60 ft, ordinary fly ~40-130 ft, high fly/popup ~100-200+ ft. These are LOW_CONFIDENCE overlapping sanity bands, not KBO targets.
- all outputs must remain finite/nonnegative and mirror-consistent.

## BLOCKERS / DATA_GAPS
- No public modern KBO distance/hang/apex distribution.
- No KBO batted-ball spin distribution / spin-vs-EV-LA mapping.
- No KBO-vs-MLB baseball drag/COR comparison suitable for direct trajectory calibration.
- No KBO park/weather air-state pack integrated with trajectory reference.
- No KBO empirical EVxLA->distance grid.

## NEXT_ACTION
- Phase 2B implementation is research-unblocked at the architecture level. Highest-value future data is KBO EVxLA-distance/spin tracking, but 01 can implement the O(1) trajectory contract now and 05 can validate against the verified physics anchors and broad sanity ranges.

## RELATED_DOCS
- `docs/phase2b-lightweight-trajectory-reference.md`
- `docs/phase2a-ev-la-timing-spray-fair-foul-reference.md`
- `docs/phase2-batted-ball-physics-reference.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- BASEBALL_PHYSICAL_CONSTANTS = VERIFIED
- STANDARD_GRAVITY_ATMOSPHERE = VERIFIED
- DRAG_IMPORTANCE = VERIFIED
- SPIN_LIFT_STRUCTURE = VERIFIED
- VACUUM_ONLY_AIRBALL_MODEL = FAIL_REJECTED
- O1_RUNTIME_CONSTRAINT = SATISFIED_BY_RECOMMENDED_MODELS
- OFFLINE_PHYSICS_RUNTIME_LOOKUP = RECOMMENDED
- VACUUM_PLUS_CORRECTION_SURROGATE = RECOMMENDED_SECONDARY
- STANDARD_ATMOSPHERE_V1 = ACCEPTABLE
- KBO_TRAJECTORY_DISTRIBUTION = OPEN
- PHASE2B_VALIDATION_METRIC_PACK = PASS
- PHASE2B_LIGHTWEIGHT_TRAJECTORY_REFERENCE = VERIFIED_FOR_ARCHITECTURE_PARTIAL_FOR_KBO_CALIBRATION
