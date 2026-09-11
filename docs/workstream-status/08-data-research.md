# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@105ef5ef3716f262e732939a97f6cc465d5a58c2
STATE: ACTIVE
CURRENT_TASK: Phase 2D catch probability and defensive-range reference research
RESULT: VERIFIED_FOR_ARCHITECTURE_PARTIAL_FOR_KBO_CALIBRATION

## LAST_COMPLETED
- Public data provenance/usage policy remains in place.
- `docs/phase2c-kbo-stadium-wall-geometry-reference.md` remains the Phase 2C stadium/wall reference.
- Added `docs/phase2d-catch-probability-defense-reference.md` for Statcast Catch Probability/OAA concepts, outfield/infield reduced difficulty variables, fixed responsibility mapping, defender-rating monotonicity, error separation, and Phase 2D validation targets.

## CURRENT_FINDINGS
- Official MLB Statcast outfield Catch Probability is based on distance needed, opportunity time, movement direction, and wall proximity. Distance needed is shortest/optimal distance rather than actual route distance, which strongly supports an O(1) reduced difficulty model without simulating fielder paths.
- Statcast public difficulty bands: 5 Star 0-25%, 4 Star 30-50%, 3 Star 55-75%, 2 Star 80-90%, 1 Star 95%; >95% is easier than the one-star bucket. Public values are reported in 5-point bands because 1-point precision overstates certainty.
- Outfield OAA accumulates actual catch result relative to baseline Catch Probability, so baseline BIP difficulty and defender skill should be architecturally separable.
- Statcast opportunity time starts at pitch release, not bat contact. Project Phase 2D hang time is therefore a strong proxy but not definition-identical; any pre-contact read allowance is future calibration, not fixed by 08.
- MLB standard outfield positioning under neutral conditions provides useful nominal start zones: LF roughly 260-320 ft / -33 to -21 deg, CF 280-350 ft / -8 to +7 deg, RF 260-320 ft / +21 to +33 deg. This supports fixed nominal start anchors and one Euclidean required-distance proxy rather than dynamic starting-position simulation.
- Direction matters at equal distance/time. Statcast explicitly penalizes going back on the ball, and wall context can materially change difficulty. A published wall-update example changed an opportunity from ~49% under the old model to ~6% with wall context.
- Statcast Jump decomposes outfield range into reaction, burst, and route. Seasonal leaderboards show several feet of spread above/below MLB average, supporting a meaningful defender-rating effect on borderline plays while not justifying a direct feet-to-rating mapping.
- MLB infield OAA uses a distinct model: distance to intercept point, time available, distance from intercept to target base, and runner speed on force plays. Therefore ground-ball/infield conversion should not reuse the outfield fly-catch surface.
- Official KBO Defense Award methodology confirms that KBO uses range-adjusted UZR/KUZR-type metrics plus official records/errors. Public KBO basic defense exposes E/PO/A/DP/FPCT, but no play-level Catch Probability surface was recovered.
- Recommended Phase 2D runtime model: fixed responsibility lookup -> reduced physical difficulty -> average-defender baseline probability surface -> defender-rating adjustment in log-odds/logistic space -> one RNG roll. No movement simulation/search loop is required.
- Outfield recommended reduced inputs: hang time, landing x/y, fixed nominal OF start, derived required-distance proxy, direction class, wall context, defender rating. EV/LA should be secondary once trajectory outputs already encode them.
- Infield/ground recommended reduced inputs: direction/spray sector, EV or ground-speed class, first-impact depth, fixed IF role, defender rating; optional batter speed can be added later if throw-to-first timing is modeled.
- Position ownership should use fixed location buckets with predeclared adjacent blends at LF/CF, CF/RF, 3B/SS, SS/2B, 2B/1B boundaries. No nearest-player pathfinding is necessary.
- Defender effect requirements: same BIP + higher rating => non-decreasing out probability; largest practical effect around intermediate difficulty; impossible/easy extremes remain near 0/1. Exact rating-point -> probability shift remains OPEN.
- Error/misplay probability should ultimately remain separate from range/catch difficulty. Phase 2D V1 may combine reach+attempt success, but should preserve interfaces to split ROE/error later.

## SOURCE / DEFINITION QUALITY
- VERIFIED MLB: Catch Probability inputs and star bands; OAA accounting; standard OF positioning zones; Jump reaction/burst/route concept; infield OAA input structure.
- PARTIAL KBO: official KBO UZR/KUZR use and public basic defense outcomes support the existence of range and error components but not a public probability surface.
- OPEN KBO: catch rate by hang time/distance, starting-position distribution, landing-zone conversion surface, ground-out probability by EV/direction, raw KUZR calibration, error by opportunity difficulty.

## MODEL POLICY
- Preferred model = small average-defender probability surface + defender-rating logit shift.
- Secondary model = single monotonic logistic function if implementation needs an initial minimal form.
- Do not use a full dynamic movement model, route simulation, search loop, or per-BIP nearest-player search.
- Maintain separate `base_catch_probability`, `defender_adjusted_probability`, `responsible_position`, `difficulty_bucket`, and optional `error_probability` observables.

## OWNER HANDOFF
- 01 Gameplay Engine: implement separate OF and IF difficulty paths. OF: landing/hang + fixed nominal OF start -> required-distance proxy + direction/wall -> baseline probability -> rating shift -> one RNG. IF: spray/impact sector + EV/speed + impact depth + fixed IF role -> baseline probability -> rating shift -> one RNG. Use fixed ownership tables and predeclared adjacent blends only. Do not bind current project rating scale numerically from this research.
- 05 Balance Lab: validate catch/out rate by BIP type, hang-time, distance/depth, direction, wall context, position, and defender-rating bucket; IF ground-out rate by EV/direction/depth; monotonic sweeps; model calibration curve; BABIP/hit-type impact; error/ROE if separated.
- 00 Game Design HQ: no coefficient decision required from 08. If necessary, decide whether V1 uses the recommended baseline-surface+logit architecture or a minimal single-logistic scaffold.

## SANITY / VALIDATION POLICY
- same BIP, higher defender rating must not lower P(out).
- same OF state except more hang/opportunity time must not lower P(catch).
- same time except larger required distance must not increase P(catch).
- same time/distance: going back should not be easier than forward unless a separately justified condition exists.
- wall-proximity difficulty must not accidentally improve otherwise identical opportunities.
- all probabilities finite and clamped/bounded [0,1].
- gap-sector responsibility should be continuous and deterministic.
- MLB star bands are difficulty labels/sanity references only, not KBO target shares.

## BLOCKERS / DATA_GAPS
- KBO play-level catch-probability/time-distance surface.
- KBO nominal OF/IF positioning by game state.
- KBO BIP conversion by landing zone/spray/depth.
- KBO ground-out probability by EV/direction.
- transparent KUZR/UZR probability calibration details.
- KBO error probability conditioned on opportunity difficulty.
- machine-readable MLB time x distance catch-rate surface suitable for a provisional derived baseline under usage constraints.

## NEXT_ACTION
- Phase 2D is research-unblocked at the architecture level. Highest-value next data is a KBO or MLB-derived reduced catch surface that can calibrate the baseline average-defender probabilities without changing the runtime contract.

## RELATED_DOCS
- `docs/phase2d-catch-probability-defense-reference.md`
- `docs/phase2c-kbo-stadium-wall-geometry-reference.md`
- `docs/phase2b-lightweight-trajectory-reference.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- MLB_OUTFIELD_CATCH_PROBABILITY_STRUCTURE = VERIFIED
- MLB_CATCH_DIFFICULTY_BANDS = VERIFIED
- MLB_OUTFIELD_OAA_STRUCTURE = VERIFIED
- MLB_INFIELD_OAA_STRUCTURE = VERIFIED
- KBO_RANGE_METRIC_EXISTENCE = VERIFIED_PARTIAL
- KBO_CATCH_PROBABILITY_SURFACE = OPEN
- FIXED_NOMINAL_POSITION_PROXY = RECOMMENDED
- OF_IF_MODEL_SEPARATION = RECOMMENDED
- FIXED_POSITION_RESPONSIBILITY = RECOMMENDED
- DEFENDER_RATING_MONOTONICITY = REQUIRED
- BASELINE_SURFACE_PLUS_LOGIT_ADJUSTMENT = RECOMMENDED
- ERROR_RANGE_SEPARATION = RECOMMENDED
- O1_ONE_RNG_RUNTIME_CONTRACT = SATISFIABLE
- PHASE2D_VALIDATION_METRIC_PACK = PASS
- PHASE2D_CATCH_PROBABILITY_REFERENCE = VERIFIED_FOR_ARCHITECTURE_PARTIAL_FOR_KBO_CALIBRATION
