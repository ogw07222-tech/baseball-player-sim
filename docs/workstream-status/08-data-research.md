# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-11
SOURCE_OF_TRUTH: main@ddf5f81389c37a50994dca1e0936e314b503e738
STATE: ACTIVE
CURRENT_TASK: KBO/MLB batted-ball physics and field-position reference pack for Phase 2
RESULT: PARTIAL_WITH_VERIFIED_PHYSICS_AND_KBO_OUTCOME_TARGETS

## LAST_COMPLETED
- Public data provenance/usage policy and detailed dataset provenance matrix remain in place.
- `docs/kbo-shared-evidence-baseline.md` provides common 02/03/04/05 references.
- `docs/kbo-pitch-batted-ball-run-conversion-reference.md` provides Phase-1 pitch/outcome/run-conversion references.
- Added `docs/phase2-batted-ball-physics-reference.md` for Phase 2 physical batted-ball calibration, stadium geometry, MLB Statcast structural references, defensive reach, and post-implementation validation targets.

## CURRENT_FINDINGS
- No completed-season public KBO league aggregate was recovered for batted-ball EV mean/SD/percentiles, hard-hit rate, launch-angle distribution, EVxLA hit surface, or spray distribution. These remain OPEN and MLB values must not be used as KBO calibration truth.
- Official MLB Baseball Savant provides strong structural sanity references: 2025 MLB 124,888 batted balls, average EV 89.4 mph (~143.9 km/h), average LA 13.5 deg, Hard-Hit% 40.9%, Barrel% 8.6%; 2024 average EV 88.8 mph, LA 13.3 deg, Hard-Hit% 38.9%, Barrel% 7.8%.
- Statcast hard-hit threshold is EV >=95 mph (~152.9 km/h); launch-angle sweet spot is 8-32 deg. Common Statcast contact-angle buckets are GB <10 deg, LD 10-25 deg, FB 25-50 deg, popup >50 deg. These are MLB definitions/structural references only.
- Peer-reviewed batting-timing evidence supports a spray model influenced by contact timing and pitch location, with acceptable timing windows on the order of milliseconds and outside-pitch optimal contact later than inside-pitch contact. No KBO league-wide spray target was recovered.
- Fair/foul KBO league rate, two-strike foul rate, and foul-EV distribution remain OPEN. MLB pitch-level public data make them derivable, but no compact verified league aggregate was retained in this pass.
- Baseball-flight literature supports gravity + quadratic aerodynamic drag + spin/Magnus lift as the material lightweight force structure. A representative published 100 mph / 29 deg / 2500 rpm example travels about 397 ft with aerodynamics versus about 571 ft in vacuum, demonstrating that no-drag projectile motion has unacceptable carry bias for wall-cross modeling.
- Research recommendation only: drag + approximate lift is the strongest lightweight V1 physical model candidate; empirical EV/LA->distance regression is useful as a cross-check but transfers poorly from MLB to KBO parks/weather. Production formula choice remains 01/00-owned.
- KBO stadium geometry is only partially public. Stronger official dimensions were recovered for Jamsil, Gocheok, Gwangju, and major Daejeon features; Suwon/Daegu/Changwon/Sajik/Incheon detailed geometry relies more on secondary sources. Exact wall polygons, many sector wall heights, and stadium elevations remain OPEN.
- Jamsil line/CF dimensions are 100/125/100 m with published wall height roughly 2.6-2.7 m. Gocheok is 99/122/99 m with 4 m wall and dome roof. Gwangju is 99/121/99 m and open-air. Daejeon is asymmetric with LF 99 m, RF 95 m and an 8 m Monster Wall sector; exact internal radial geometry should be represented as polygon/wall segments rather than forced scalar LC/RC distances.
- MLB Statcast defensive structure is usable as architecture evidence only: Sprint Speed average competitive-play context ~27 ft/s; Jump decomposes early movement into reaction/burst/route components; Catch Probability uses opportunity time, distance, direction and wall context. No equivalent public KBO defensive-tracking distribution was recovered.
- Recent completed KBO outcome gates remain directly usable for Phase 2 validation: 2B/PA ~4.02%, 3B/PA ~0.38%, HR/PA ~2.06%, XBH/H ~27.71%, plus the broader run-environment baselines. Current pre-Phase-2 simulation has 2B near target, 3B low, HR high, and HR resolution before defense/no park geometry, making wall-cross/landing-sector validation a high priority.

## SOURCE / DEFINITION QUALITY
- VERIFIED KBO: recent completed 2B/3B/HR/XBH outcome totals; selected official stadium line/CF dimensions and major wall features.
- PARTIAL KBO: park geometry beyond official published dimensions; PBP-derived GB/FB trend shares; event-specific park factors.
- OPEN KBO: league EV distribution, LA distribution, EVxLA outcome surface, spray distribution, foul/contact rates, batted-ball spin, Statcast-like defensive reach/catch probability.
- VERIFIED MLB-only: Statcast EV/LA/Hard-Hit/Barrel definitions and league aggregates; Sprint Speed/Jump/Catch Probability architecture.
- VERIFIED physics structure: gravity, quadratic drag and spin lift/Magnus terms; exact coefficients remain model/condition dependent and are not chosen by 08.

## OWNER HANDOFF
- 01 Gameplay Engine: architect Phase 2 around continuous EV/LA/spray -> trajectory -> fair/foul/park-wall -> defense -> hit outcome. Preserve observable wall crossing, landing position, hang time and catchability. Avoid predeclaring HR before park/defense resolution. Support piecewise/asymmetric stadium wall geometry. Coefficients remain 01/00-owned.
- 05 Balance Lab: after implementation, validate EV/LA/spray/distance/hang-time distributions, wall-cross rates, fair/foul, GB/LD/FB/PU, 1B/2B/3B/HR, HR/PA, HR/BIP, 3B/PA, XBH/H, BABIP, runs/game, catchable/catch-conversion buckets, and park-sector HR distributions. Keep MLB sanity metrics separate from KBO pass/fail gates.
- 02 Ratings & Generation: no direct Phase 2 coefficient action from this pack; later rating-to-EV/LA/speed mappings should be validated against KBO data when public tracking distributions become available.
- 00 Game Design HQ: decide whether Phase 2 V1 adopts physical drag+lift, a staged drag-only intermediate, and when real-park/weather complexity enters production. 08 recommends drag+approximate lift from a research perspective only.

## BLOCKERS
- No authoritative/public completed-season KBO EV/LA percentile dataset was recovered.
- No KBO league-wide spray/pull/opposite distribution with explicit denominator was recovered.
- No compact KBO fair/foul or two-strike foul distribution was recovered.
- No KBO player-tracking defensive reach/catch-probability dataset was recovered.
- Full current wall polygons/heights/elevations are not publicly verified for every KBO park.

## OPEN_ITEMS
- Seek Sports2i/official-team/TrackMan-public batted-ball EV/LA aggregate with explicit sample/season/units.
- Seek or derive KBO spray and fair/foul aggregate under permitted public-use conditions.
- Build a source-versioned park geometry dataset with wall segments rather than only five radial distances.
- Recover stadium elevation/weather metadata if Phase 2 adds atmospheric park states.
- If legal/public-use conditions permit, derive compact KBO EV/LA or defense outcome surfaces without committing restricted raw tracking/PBP feeds.

## NEXT_ACTION
- Highest-value research gap: a KBO batted-ball tracking aggregate for EV/LA/spray. In parallel, Phase 2 implementation can proceed using KBO hit-type outcome gates and MLB/peer-reviewed physics strictly as structural sanity references, with generic stadium geometry if needed.

## RELATED_DOCS
- `docs/phase2-batted-ball-physics-reference.md`
- `docs/kbo-pitch-batted-ball-run-conversion-reference.md`
- `docs/kbo-simulation-realism-comparison-2026-09-11.md`
- `docs/kbo-shared-evidence-baseline.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- KBO_PHASE2_HIT_TYPE_TARGETS = VERIFIED
- KBO_EV_DISTRIBUTION = OPEN
- KBO_LA_DISTRIBUTION = OPEN
- KBO_SPRAY_DISTRIBUTION = OPEN
- KBO_FAIR_FOUL_REFERENCE = OPEN
- MLB_STATCAST_EV_LA_REFERENCE = VERIFIED_MLB_ONLY
- BALL_FLIGHT_FORCE_STRUCTURE = VERIFIED
- NO_DRAG_PROJECTILE_FOR_WALL_CARRY = NOT_RECOMMENDED
- DRAG_PLUS_APPROX_LIFT_RESEARCH_MODEL = RECOMMENDED
- KBO_STADIUM_GEOMETRY = PARTIAL
- KBO_DEFENSIVE_TRACKING = OPEN
- MLB_DEFENSE_ARCHITECTURE_REFERENCE = VERIFIED_MLB_ONLY
- PHASE2_VALIDATION_METRIC_PACK = PASS
- PHASE2_BATTED_BALL_PHYSICS_REFERENCE_PACK = PARTIAL_WITH_VERIFIED_PHYSICS_AND_KBO_OUTCOME_TARGETS
