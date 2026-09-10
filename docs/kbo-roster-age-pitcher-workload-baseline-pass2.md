# KBO roster / age / pitcher workload baseline — second-pass verification

Access date: 2026-09-10 (Asia/Seoul)

Purpose: focused second-pass verification against the latest repository state and current authoritative/public sources. This is a delta to `docs/kbo-roster-age-pitcher-workload-baseline.md`; it does not change gameplay or rating formulas and does not copy restricted bulk datasets.

## Source set checked

1. KBO official 2026 registered-player notice, published 2026-02-10: `https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11831`
2. KBO official 2025 registered-player notice, published 2025-02-11: `https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11371`
3. KBO official 2025/2026 roster/salary notices: `bdSe=11394`, `bdSe=11861`
4. KBO official pitcher record pages: `Record/Player/PitcherBasic/Basic1.aspx`, `Basic2.aspx`, `Situation.aspx`
5. KBO official TrackMan notice, published 2025-03-07: `https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11398`
6. Baseball-Reference completed-2025 KBO pitching leaderboard: `https://www.baseball-reference.com/register/leader.cgi?id=4e296e3b&type=pitch`
7. MyKBO Stats used only as an unofficial cross-check where helpful; it explicitly states it is not affiliated with KBO and is not promoted to primary evidence.

Public-repository posture: source tables/attachments are not committed. Only compact factual aggregates, formulas, and source paths are retained. KBO notices explicitly prohibit unauthorized republication/redistribution of their news/site materials, so the attached XLSX files are treated as reference-only unless permission is separately established.

## 1. Modern roster distribution — revalidated

Population: all players registered by the 10 KBO clubs in the 2026 official club-player registration announcement.

| Field | Value | Status | Provider | Sample |
|---|---:|---|---|---|
| registered players | 621 | ACTUAL | KBO official | 2026 registered-player population |
| pitchers | 317 (51.05%) | ACTUAL count / INFERRED share | KBO official | same |
| catchers | 50 (8.05%) | ACTUAL / INFERRED | KBO official | same |
| infielders | 138 (22.22%) | ACTUAL / INFERRED | KBO official | same |
| outfielders | 116 (18.68%) | ACTUAL / INFERRED | KBO official | same |
| rookies | 52 (8.37%) | ACTUAL / INFERRED | KBO official | same |
| rookie pitchers | 28 | ACTUAL | KBO official | 52 rookies |
| rookie infielders | 14 | ACTUAL | KBO official | 52 rookies |
| rookie outfielders | 8 | ACTUAL | KBO official | 52 rookies |
| rookie catchers | 2 | ACTUAL | KBO official | 52 rookies |

KBO also directly reports the 2025 position shares in the 2026 comparison: pitcher 50.1%, infielder 22.6%, outfielder 18.4%, catcher 8.9%. This provides a one-year stability check, but the 2026 registered-player distribution remains the recommended R1 comparison target because its exact counts are directly stated.

### Age status

Official observed bounds remain usable:
- 2026: 18y 1m 19d to 42y 1m 15d — ACTUAL, KBO official.
- 2025: 18y 1m 19d to 42y 6m 16d — ACTUAL, KBO official.

No public compact KBO aggregate for mean, median, percentiles, position-specific age, or <=21/<=23 share was found in this pass. The official annual attachment is richer but is subject to the public-repository redistribution caution above. Therefore all central/percentile age-distribution fields remain OPEN.

02 handoff:
- use 2026 registered-player position shares for generator population comparison;
- use 8.37% rookie share only as a rookie-registration share, not as an age-bin proxy;
- use official min/max ages only as plausibility bounds;
- do not fabricate mean/median/percentiles from the bounds.

## 2. Completed-2025 pitcher workload — second-pass heavy-sanity additions

Matched season: completed 2025 KBO regular season only.

KBO official player record pages directly expose `G`, `IP`, and `TBF`/pitching detail fields. In the public rendered table checked in this pass, `GS` is not consistently exposed together with those fields. Baseball-Reference provides the compact completed-season `G`, `GS`, `IP`, and `BF` combination needed for role-oriented sanity checks. Thus high-tail role evidence below is secondary-source ACTUAL with KBO-field cross-check, not official-KBO-only evidence.

### High-volume starter tail

Top-five completed-2025 GS leaders used in the existing baseline:

| Player | G | GS | IP | BF | IP/GS | BF/GS |
|---|---:|---:|---:|---:|---:|---:|
| Logan Allen | 32 | 31 | 173.0 | 770 | 5.58 | 24.84 |
| Drew Anderson | 30 | 30 | 171 2/3 | 694 | 5.72 | 23.13 |
| Yonny Chirinos | 30 | 30 | 177.0 | 737 | 5.90 | 24.57 |
| Enmanuel De Jesus | 32 | 30 | 163 2/3 | 712 | 5.46 | 23.73 |
| Ariel Jurado | 30 | 30 | 197 1/3 | 786 | 6.58 | 26.20 |

Derived heavy-sanity ranges for this observed extreme group:
- GS: 30–31
- IP/start: 5.46–6.58
- BF/start: 23.13–26.20

These are extreme-tail sanity bands. They are not P90/P95 estimates.

### High-appearance zero-start reliever tail

| Player | G | GS | IP | BF | IP/G | BF/G |
|---|---:|---:|---:|---:|---:|---:|
| Jeong Hyeon-su | 82 | 0 | 47 2/3 | 203 | 0.58 | 2.48 |
| Kim Jin-sung | 78 | 0 | 70 2/3 | 291 | 0.91 | 3.73 |
| Noh Kyung-eun | 77 | 0 | 80.0 | 320 | 1.04 | 4.16 |
| Kim Jin-ho | 76 | 0 | 72 1/3 | 316 | 0.95 | 4.16 |
| Jeong Cheol-won | 75 | 0 | 70.0 | 312 | 0.93 | 4.16 |

Derived heavy-sanity ranges for this observed extreme group:
- appearances: 75–82
- IP/appearance: 0.58–1.04
- BF/appearance: 2.48–4.16

Again, these are observed extreme-tail bands, not league percentiles.

### Why full P10/P50/P90/P95 remains OPEN

A percentile pack requires a complete, stable player-level universe and an explicit classification rule. This pass did not obtain a redistribution-safe complete 2025 `G/GS/IP/BF` table from a primary/licensed aggregate. Accordingly, no percentile was backfilled from leaderboard snippets.

For the eventual extraction, retain raw values and publish sensitivity under the existing project classifier:
- `starter_primary`: GS/G >= 0.50 and GS >= 10
- `reliever_primary`: GS == 0 and G >= 10
- `hybrid`: mixed usage
- `small_sample`: G < 10

This classifier is PROJECT-DERIVED, not a KBO official role definition.

05 handoff now usable:
- 1,440 completed-season team-start opportunities;
- starter extreme sanity: 30–31 GS, 5.46–6.58 IP/start, 23.13–26.20 BF/start;
- zero-start reliever extreme sanity: 75–82 G, 0.58–1.04 IP/app, 2.48–4.16 BF/app;
- full central/percentile targets remain OPEN.

## 3. Velocity provenance — revalidated

KBO officially adopted TrackMan as the official league pitch-velocity measurement system beginning with the 2025 season. This is a high-confidence measurement-system fact.

Required separation:
- `avg_fastball_velocity_kmh`: average over a declared pitch/sample window.
- `max_fastball_velocity_kmh`: maximum observed value over that declared window.

KBO news examples explicitly report both average and maximum values separately, confirming that the two concepts are not interchangeable. However, no primary/licensed league-wide 2025 fastball mean + SD/percentile distribution was recovered.

Status:
- official measurement system = TrackMan: PASS
- player/game average-vs-max semantic separation: PASS
- league-wide primary average: OPEN
- league SD/P10/P50/P90/P95: OPEN
- older 2024 144.2 km/h secondary league-average anchor: remains provisional and must not be labelled official.

## 4. Longitudinal career dataset methodology — retained

The previously declared methodology remains valid and is the production research contract until a numerical cohort is materialized:
- entity key: stable KBO player ID;
- debut: first KBO regular-season appearance, distinct from overseas/pro debut;
- report both calendar span and active-season count;
- active players at observation cutoff are right-censored;
- pre-window careers without complete prior history are left-truncated and excluded from naive career-length estimates;
- career survival should use Kaplan–Meier when appropriate;
- peak age must predeclare metric and PA/IP threshold, with hitter, pitcher, workload and composite-value peaks kept conceptually separate.

03 handoff: methodology PASS; debut-age, career-length and peak-age numerical distributions remain OPEN.

## 5. Confidence / redistribution summary

| Evidence | Confidence | Redistribution status |
|---|---|---|
| 2026 position/rookie distribution | High | summary-only; KBO bulk attachment not committed |
| 2025/2026 age bounds | High | summary-only |
| age central/percentile distribution | OPEN | no aggregate committed |
| 2025 high-tail G/GS/IP/BF examples | Medium-High | secondary compact evidence; no bulk table committed |
| 2025 workload percentiles | OPEN | no complete licensed/reproducible universe obtained |
| TrackMan official measurement-system fact | High | summary-only |
| league velocity distribution | OPEN | no dataset committed |
| career cohort methodology | High as methodology | no player-level cohort committed |

## 6. Gate

- ROSTER_POSITION_DISTRIBUTION_BASELINE = PASS
- ROSTER_ROOKIE_SHARE_BASELINE = PASS
- ROSTER_AGE_BOUNDS = PASS
- ROSTER_AGE_DISTRIBUTION = OPEN
- STARTER_RELIEVER_EXTREME_WORKLOAD_SANITY = PASS
- STARTER_RELIEVER_BF_EXPOSURE_SANITY = PASS
- STARTER_RELIEVER_WORKLOAD_PERCENTILES = OPEN
- VELOCITY_MEASUREMENT_PROVENANCE = PASS
- VELOCITY_AVERAGE_MAX_SEPARATION = PASS
- VELOCITY_DISTRIBUTION_BASELINE = OPEN
- CAREER_LONGITUDINAL_METHODOLOGY = PASS
- CAREER_LONGITUDINAL_NUMERICAL_BASELINE = OPEN

Overall: **PARTIAL PASS / OPEN**.

Next priority: obtain a complete aggregate-permitted 2025 pitcher universe with G/GS/IP/BF; then compute role counts, IP shares and P10/P50/P90/P95. Second priority is an aggregate-permitted roster age distribution. Third is a primary/licensed TrackMan league velocity distribution.