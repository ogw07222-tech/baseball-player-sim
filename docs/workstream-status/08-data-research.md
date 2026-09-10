# 08 - Baseball Data & Research

WORKSTREAM: 08 - Baseball Data & Research
UPDATED_AT: 2026-09-10
SOURCE_OF_TRUTH: main@564518b0e021f3f9b4880fe4ca55946cc0d93179
STATE: ACTIVE
CURRENT_TASK: Shared KBO evidence lane for next development wave
RESULT: OPEN

## LAST_COMPLETED
- Public data provenance/usage policy added under `data/README.md`.
- Detailed KBO dataset provenance matrix added and linked from main.
- Added `docs/kbo-shared-evidence-baseline.md` as a compact, provenance-labelled baseline pack for 02/03/04/05.
- Established 2025 completed regular season as the preferred matched-condition league baseline for Balance work.

## CURRENT_FINDINGS
- 2025 KBO league hitting baseline is usable from frozen aggregate totals: AVG .2616, OBP .3385, SLG .3887, OPS .7272, BB% 9.149%, K% 19.687%, HR% 2.127%, BABIP .3122.
- 2025 pitching aggregate cross-check supports ERA 4.31, WHIP 1.41, 12,771 IP, 11,024 SO, 5,123 BB, 1,191 HR; derived K/9 7.769, BB/9 3.610, HR/9 .839.
- KBO official operation confirms 144 games/team and 720 league games.
- Official award pages provide usable Rookie, Golden Glove and Fielding Award eligibility thresholds.
- Official FA notices provide usable transaction examples and historical 145 active-roster-day service-season reference, but the current full rulebook should be checked before hard-locking production service rules.
- Modern position distribution, full age histogram, starter/reliever workload splits, debut-age/career-length/peak-age curves and injury-event frequency remain OPEN.
- Velocity evidence is only provisional: a secondary report gives a 2024 league fastball average of 144.2 km/h, while 2025 early-season official-attributed reporting provides elite 153-154 km/h anchors. No primary full distribution was recovered.

## BLOCKERS
- No verified compact extraction yet for modern KBO position/age distribution from the official annual registration attachment.
- No completed 2025 player-level GS/IP aggregation yet for starter/reliever workload baselines.
- No provenance-safe longitudinal cohort dataset yet for debut age, peak age or career length.
- Primary/licensed full KBO pitch-velocity distribution not yet recovered.

## OPEN_ITEMS
- Recover compact modern roster position/age/service summaries from official KBO registration material without committing bulk source attachments.
- Build 2025 starter/reliever workload summaries from player G/GS/IP under a reproducible aggregation path.
- Define and build longitudinal career cohorts with censoring rules for debut age, career length and peak age.
- Build explicit-PA/IP percentile packs for low/middle/elite hitter and pitcher spectra.
- Find a primary or clearly licensed KBO pitch-tracking aggregate for velocity distribution.
- Research public aggregate injury/event incidence before any narrative probability calibration.

## DEPENDENCIES
- 02: can use age bounds and provisional velocity anchors; position/age/usage/performance distributions remain OPEN.
- 03: can use season structure and FA/service-time references; longitudinal career distributions remain OPEN.
- 04: can use award eligibility/annual award structure and FA transaction context; injury/event frequencies remain OPEN.
- 05: can use the 2025 matched-season league hitting/pitching baseline immediately; starter/reliever workload split remains OPEN.

## NEXT_ACTION
- Highest priority: modern roster position/age distribution extraction, then completed-2025 starter/reliever workload aggregation.

## RELATED_PRS
- #35 merged

## RELATED_BRANCHES
- main

## GATES
- PUBLIC_DATA_POLICY = PASS
- DATASET_PROVENANCE_MATRIX = PASS
- 2025_MATCHED_LEAGUE_BASELINE = PASS
- AWARD_RULE_BASELINE = PASS
- ROSTER_DISTRIBUTION_BASELINE = OPEN
- CAREER_LONGITUDINAL_BASELINE = OPEN
- VELOCITY_DISTRIBUTION_BASELINE = OPEN
- STARTER_RELIEVER_WORKLOAD_BASELINE = OPEN
- SHARED_KBO_EVIDENCE_LANE = OPEN
