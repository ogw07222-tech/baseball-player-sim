# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-12
SOURCE_OF_TRUTH: main@5b3312009bd6f2d87483e4a02b3f701725775f2a
STATE: ACTIVE
CURRENT_TASK: Phase 2A priority research for EV / Launch Angle / Timing / Spray / Fair-Foul
RESULT: PARTIAL_WITH_STRONG_STRUCTURAL_EVIDENCE_AND_OPEN_KBO_DISTRIBUTIONS

## LAST_COMPLETED
- Public data provenance/usage policy and dataset provenance matrix remain in place.
- `docs/phase2-batted-ball-physics-reference.md` remains the broader Phase 2 physics/park/defense reference.
- Added `docs/phase2a-ev-la-timing-spray-fair-foul-reference.md` as the implementation-priority Phase 2A pack for EV, launch angle, timing, spray and fair/foul.

## CURRENT_FINDINGS
- No modern public completed-season KBO league EV percentile distribution was recovered. Historical KBO/Sports2i tracking provides partial anchors: early-season 2019/2020 league mean batted-ball speed ~135.3/135.6 km/h; player-level TrackMan samples include Kim Ha-seong 2020 mean EV 90.1 mph (~145.0 km/h), LA 13 deg, 95+ mph 50.4%, max 108.9 mph, and Lee Jung-hoo 2022 mean EV 88.7 mph (~142.7 km/h), LA 12.3 deg, 95+ mph 37.7%, max 107 mph. These are not league calibration distributions.
- Official MLB Baseball Savant 2025 provides a high-quality sanity reference only: 124,888 BBE, mean EV 89.4 mph (~143.9 km/h), mean LA 13.5 deg, Hard-Hit% 40.9%, official hard-hit threshold >=95 mph (~152.9 km/h), and 2025 max EV 122.9 mph. These must not be relabeled as KBO targets.
- Historical KBO TrackMan reporting gives mean in-play LA ~11.92 deg and mean HR LA ~28.07 deg in 2017. KBO/Sports2i individual HR samples show very high-EV HRs can occur below 20 deg, supporting EVxLA interaction instead of fixed HR-angle rules.
- MLB Statcast 2025 BBE profile is useful for Phase 2A sanity: GB 42.4%, FB 26.6%, LD 23.9%, PU 7.1%, Pull 39.2%, Straight/Center 36.4%, Oppo 24.5%. No matching modern KBO league spray aggregate was recovered.
- Peer-reviewed 2019 optical-motion work with 26 baseball players measured acceptable timing error at about +/-7.9 ms for fastballs and +/-10.7 ms for curve/slow pitches; outside-pitch optimal impact was ~10 ms later than inside. This is strong structural evidence but not a KBO-pro scalar coefficient.
- A 2017 high-speed-camera college study independently found inside pitches were contacted farther toward the pitcher and outside pitches farther toward the catcher. Combined evidence supports timing + pitch location + handedness as spray inputs.
- Statcast Attack Direction and public MLB analysis also support out-front/early contact -> pull pressure and deeper/later contact -> opposite-field pressure; exact ms->spray-degree and ms->EV mappings remain OPEN.
- No reliable compact KBO league foul/contact, foul/swing, two-strike foul, or foul-EV distribution was recovered. MLB Statcast exposes reproducible pitch-result categories, so those aggregates are derivable later. Fair/foul should therefore be implemented geometrically and measured before being hard-calibrated.
- High-EV foul contact must remain possible; no evidence supports making foul synonymous with weak contact.

## SOURCE / DEFINITION QUALITY
- VERIFIED MLB-only: Baseball Savant 2025 league aggregate EV/LA/Hard-Hit and BBE/spray profile; official hard-hit and EV/LA definitions; observed 122.9 mph 2025 extreme.
- PARTIAL KBO: Sports2i historical league EV mean, older KBO TrackMan LA mean/HR LA, player-level KBO TrackMan EV/LA samples.
- VERIFIED STRUCTURAL: peer-reviewed timing error scale and inside/outside optimal-contact shift; contact timing affects horizontal batted-ball direction.
- OPEN KBO: modern EV mean/SD/percentiles, EV by BBE type/outcome, LA histogram, spray by handedness/hitter type, foul rates/EV.

## SANITY POLICY
- MLB EV/LA/spray figures are `SANITY/WATCH` references only; they do not define KBO PASS/FAIL central values.
- 95 mph hard-hit is an `MLB_HARD_HIT_REFERENCE`, not a KBO threshold.
- EV materially above the known MLB Statcast extreme (~123 mph) at non-negligible frequency should trigger WATCH/FAIL investigation.
- Use roughly 8-11 ms as a timing-order-of-magnitude test vector, not a production coefficient target.
- Use MLB spray composition only as a broad smoke-check; KBO-specific spray calibration remains OPEN.
- Fair/foul has structural invariants now, no hard league percentage gate yet.

## OWNER HANDOFF
- 01 Gameplay Engine — implementation prior: preserve continuous EV/LA/spray; make spray responsive to timing + pitch location + handedness; mirror handedness geometry; allow hard fouls; resolve fair/foul geometrically; do not choose 1B/2B/HR before physical/field resolution. Provisional only: MLB Statcast LA buckets and hard-hit label for debugging. Future calibration: KBO EV/LA/spray/foul distributions.
- 05 Balance Lab — Phase 2A measurement pack: EV mean/SD/P10/P25/P50/P75/P90/P95/P99/max; LA distribution and GB/LD/FB/PU debug buckets; EVxLA surface; timing-error histogram; spray by handedness/pitch-location/timing bucket; foul/swing, foul/contact, two-strike foul, foul EV distribution; fair/foul by timing and spray.
- 00 Game Design HQ — no coefficient decision requested. Only resolve design-level questions if Phase 2A needs a fixed bootstrap distribution policy before KBO data becomes available.

## BLOCKERS
- No authoritative modern KBO league EV/LA distribution with percentiles.
- No KBO league pull/center/oppo split with clear denominator/handedness split.
- No KBO compact foul/contact or two-strike foul aggregate.
- No professional/KBO timing-error-to-spray or timing-error-to-EV scalar transfer function.

## OPEN_ITEMS
- Seek Sports2i/official team/TrackMan public modern KBO EV/LA aggregate with sample and denominator metadata.
- Seek or derive KBO spray distribution by batter handedness and BBE type under permitted public-use conditions.
- Derive MLB foul distributions only if needed for structural sanity, keeping them separately namespaced from KBO calibration.
- Seek professional-level biomechanical work for timing error vs EV/contact quality and exact horizontal direction response.

## NEXT_ACTION
- Highest-value next research gap is a modern KBO EV/LA tracking export or published aggregate. Second is KBO spray distribution; third is KBO foul-rate/foul-EV evidence. Phase 2A implementation can proceed meanwhile using the structural evidence and MLB references strictly as provisional/sanity inputs.

## RELATED_DOCS
- `docs/phase2a-ev-la-timing-spray-fair-foul-reference.md`
- `docs/phase2-batted-ball-physics-reference.md`
- `docs/kbo-pitch-batted-ball-run-conversion-reference.md`

## GATES
- PUBLIC_DATA_POLICY = PASS
- KBO_MODERN_EV_DISTRIBUTION = OPEN
- KBO_EV_HISTORICAL_ANCHORS = PARTIAL
- KBO_MODERN_LA_DISTRIBUTION = OPEN
- KBO_LA_HISTORICAL_ANCHORS = PARTIAL
- MLB_STATCAST_EV_LA_SANITY = VERIFIED_MLB_ONLY
- TIMING_ORDER_OF_MAGNITUDE = VERIFIED_STRUCTURAL
- INSIDE_OUTSIDE_CONTACT_SHIFT = VERIFIED_STRUCTURAL
- TIMING_TO_SPRAY_DIRECTION = QUALITATIVE_STRONG
- EXACT_TIMING_TO_SPRAY_COEFFICIENT = OPEN
- KBO_SPRAY_DISTRIBUTION = OPEN
- MLB_SPRAY_SANITY = VERIFIED_MLB_ONLY
- KBO_FAIR_FOUL_REFERENCE = OPEN
- FAIR_FOUL_GEOMETRIC_CONTRACT = PASS
- PHASE2A_VALIDATION_METRIC_PACK = PASS
- PHASE2A_EV_LA_TIMING_SPRAY_FAIR_FOUL_REFERENCE = PARTIAL_WITH_STRONG_STRUCTURAL_EVIDENCE_AND_OPEN_KBO_DISTRIBUTIONS
