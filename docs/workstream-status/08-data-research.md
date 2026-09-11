# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@0e2d00afa399e319110b337e65cc412a97984c69
STATE: ACTIVE
CURRENT_TASK: Phase 2C KBO stadium geometry and wall-reference research
RESULT: PARTIAL_BUT_IMPLEMENTATION_READY_WITH_QUALITY_FLAGS

## LAST_COMPLETED
- Public data provenance/usage policy remains in place.
- `docs/phase2b-lightweight-trajectory-reference.md` remains the Phase 2B trajectory reference.
- Added `docs/phase2c-kbo-stadium-wall-geometry-reference.md` for 2026 KBO stadium use, wall-radius/height evidence, O(1) radial model design support, generic fallback, wall-intersection contract, and Phase 2C validation targets.

## CURRENT_FINDINGS
- KBO 2026 schedule/current game pages confirm the active primary venue set: Jamsil, Gocheok, Incheon SSG Landers Field, Suwon KT Wiz Park, Daejeon Hanwha Life Ballpark, Daegu Samsung Lions Park, Gwangju-KIA Champions Field, Sajik, Changwon NC Park. LG/Doosan share Jamsil; 2026 is the current Jamsil stadium's final regular-season year before the planned 2027 temporary transition.
- Strong primary distance evidence: Jamsil LF/RF 100 m and CF 125 m; Gocheok LF/RF 99 m and CF 122 m with 4 m wall; Gwangju LF/RF 99 m and CF 121 m; Daejeon LF 99 m, RF 95 m, ordinary wall ~2.4 m plus an 8 m right-side Monster Wall.
- Daejeon full five-anchor geometry is widely reported as 99/115/122/112/95 m; endpoints/wall heights are primary-verified but LC/CF/RC remain PARTIAL until an official plan/drawing is recovered.
- Incheon 95/115/120/115/95 m with ~2.8 m wall, Suwon 98/115/120/115/98 m with ~4 m wall, Daegu LF/RF ~99.5 m and CF ~122.5 m with ~3.6 m wall, Sajik ~95.8/113/121/113/95.8 m with ~6 m wall, and Changwon LF/RF ~101.2 m / CF 122 m with ~3.3 m wall are usable APPROXIMATED references but are not uniformly primary-verified.
- Jamsil wall height is CONFLICTING: older Seoul official comparison material gives 2.7 m while 2026 Yonhap reports 2.6 m. Do not silently collapse this to one VERIFIED value.
- Daegu detailed LC/RC geometry is definition-sensitive because of its polygonal wall; secondary references expose conflicting-looking ~107 m vs ~123.4 m sector labels. Do not force a five-scalar model as authoritative.
- No authoritative stadium-altitude pack was recovered. Keep altitude UNAVAILABLE and Phase 2B neutral-air assumption separate.
- Recommended runtime stadium representation: fixed angular anchors with piecewise-linear interpolation. Five anchors are sufficient for simple/generic parks; support ~7-9 fixed anchors for Daejeon/Daegu/Changwon and variable wall height. Precompute sector dispatch so each BIP remains O(1) without an anchor scan.
- `carry_distance > wall_radius` alone is not a valid HR test. Phase 2C needs trajectory height at wall radius. Phase 2B should expose fixed-size O(1) height-at-horizontal-distance coefficients or an equivalent lookup descriptor.
- Generic fallback is explicitly `GENERIC_ENGINEERING_BASELINE`, not a claimed KBO average: 100/115/122/115/100 m with 3.0 m wall.
- Geometry and empirical park factor remain separate layers. Implement physical wall distance/height first; later park-factor correction requires a double-counting audit.

## SOURCE / DEFINITION QUALITY
- VERIFIED: 2026 KBO venue use; Jamsil LF/RF/CF; Gocheok LF/RF/CF/wall; Gwangju LF/RF/CF; Daejeon LF/RF and 2.4/8 m wall structure.
- APPROXIMATED: Incheon/Suwon detailed anchors, Daegu detailed wall polygon, Sajik detailed geometry, Changwon sector detail, several wall heights.
- CONFLICTING: Jamsil wall 2.6 vs 2.7 m; Daegu LC/RC scalar conventions.
- UNAVAILABLE: reliable current power-alley values for Jamsil/Gocheok/Gwangju, stadium elevation pack, exact Daejeon Monster Wall angular boundaries, full sector wall-height maps.

## GENERIC / MODEL POLICY
- Generic neutral V1 = 100/115/122/115/100 m, wall 3.0 m, open-air; metadata must say `GENERIC_ENGINEERING_BASELINE`, `is_real_stadium=false`.
- Standard wall model = `wall_anchor(theta, radius, height, source_status)` + fixed-sector linear interpolation.
- Simple parks: 5 anchors at -45/-22.5/0/+22.5/+45 deg.
- Complex parks: fixed 7-9 anchor schema with extra polygon/height-transition vertices.
- No runtime loops or per-BIP anchor scanning are required.

## OWNER HANDOFF
- 01 Gameplay Engine: use season-versioned stadium objects; fixed-anchor O(1) radial wall model; separate wall radius/height; require O(1) `height_at_horizontal_distance(r)` from trajectory; physical HR requires wall reach + wall clearance. Do not merge empirical park factor into the initial physical wall gate. Stadium fair-line coordinates may be exposed, but Phase 2A fair/foul authority migration remains a separate integration decision.
- 05 Balance Lab: validate generic neutral, Jamsil-like, and Daejeon-asymmetric fixtures using identical deterministic BIP corpus. Measure wall reached/clear/contact, HR by sector, clearance margin, near-wall non-HR, park-to-park ratios, wall-height/radius sensitivity, mirror invariants, and impossible-HR count. Geometry-only park ratios are not empirical park factors.
- 00 Game Design HQ: no gameplay coefficient decision requested. If necessary, approve stadium versioning/fallback policy and timing of physical fair/foul authority migration.

## BLOCKERS / DATA_GAPS
- Primary full wall polygons for Incheon/Suwon/Daegu/Sajik/Changwon.
- Official LC/RC for Jamsil/Gocheok/Gwangju.
- Exact Daejeon Monster Wall angular extent.
- Sector-specific wall-height maps.
- Stadium altitudes and season-version history for renovations.
- Foul-pole heights/ground-rule-specific geometry.

## NEXT_ACTION
- Phase 2C is research-unblocked for architecture and generic/asymmetric fixture implementation. Highest-value follow-up is a primary-source full-wall drawing for Daejeon/Daegu and current detailed geometry for the remaining secondary-only parks.

## RELATED_DOCS
- `docs/phase2c-kbo-stadium-wall-geometry-reference.md`
- `docs/phase2b-lightweight-trajectory-reference.md`
- `docs/phase2a-ev-la-timing-spray-fair-foul-reference.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- KBO_2026_STADIUM_SET = VERIFIED
- PRIMARY_LF_RF_CF_COVERAGE = PARTIAL_STRONG
- PRIMARY_POWER_ALLEY_COVERAGE = PARTIAL
- WALL_HEIGHT_COVERAGE = PARTIAL_CONFLICTING
- STADIUM_ALTITUDE_PACK = OPEN
- GENERIC_ENGINEERING_STADIUM = READY
- FIXED_ANCHOR_RADIAL_MODEL = RECOMMENDED
- O1_STADIUM_LOOKUP = SATISFIABLE
- TRAJECTORY_HEIGHT_AT_WALL_CONTRACT = REQUIRED
- GEOMETRY_PARK_FACTOR_SEPARATION = PASS
- FAIR_FOUL_MIGRATION_AUTOMATIC = NO
- PHASE2C_VALIDATION_METRIC_PACK = PASS
- PHASE2C_KBO_STADIUM_GEOMETRY_REFERENCE = PARTIAL_BUT_IMPLEMENTATION_READY_WITH_QUALITY_FLAGS
