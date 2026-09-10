# KBO roster / age / pitcher workload baseline pack

Access date: 2026-09-10 (Asia/Seoul)

Purpose: public-repository-safe baseline pack for `02 - Player Ratings & Generation`, `05 - Balance Lab`, and lifecycle-methodology support for `03 - Growth & Career`. This document records compact aggregates and reproducible derivations only; it does not copy KBO bulk tables or attachments.

Status labels:
- **ACTUAL**: directly reported by the identified source.
- **INFERRED**: mathematically derived from reported source values.
- **ESTIMATED**: approximate/model-based and not suitable as a calibration truth.
- **OPEN**: not sufficiently verified for calibration use.

## 1. Modern KBO roster position baseline

Primary source: KBO official notice, `2026 KBO 리그, 소속 선수 621명 등록`, published 2026-02-10.
Source URL: https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11831
Population definition: all 621 players registered by the 10 KBO clubs in the official 2026 club-player list announced Feb. 10, 2026.
Redistribution: KBO notice explicitly states that unauthorized republication/redistribution is prohibited. This repository stores only summary counts/shares and source metadata; the attached roster workbook is not committed.

| Position | Count | Share | Type | Confidence |
|---|---:|---:|---|---|
| Pitcher | 317 | 51.05% | ACTUAL count; INFERRED share | High |
| Catcher | 50 | 8.05% | ACTUAL count; INFERRED share | High |
| Infielder | 138 | 22.22% | ACTUAL count; INFERRED share | High |
| Outfielder | 116 | 18.68% | ACTUAL count; INFERRED share | High |
| Total | 621 | 100% | ACTUAL | High |

2025 comparison from the same KBO notice: Pitcher 50.1%, Infielder 22.6%, Outfielder 18.4%, Catcher 8.9%. With 597 total registered players in 2025, the nearest integer counts consistent with those published shares are 299 pitchers, 135 infielders, 110 outfielders, and 53 catchers; those integer counts are **INFERRED**, not directly quoted.

### Rookie composition

The 2026 notice reports 52 rookies among the 621 registered players.

- Rookie share of registered population: **8.37%** = 52 / 621, INFERRED.
- Rookie pitchers: **28 / 52 = 53.85%**, ACTUAL count / INFERRED share.
- Rookie infielders: **14 / 52 = 26.92%**, ACTUAL count / INFERRED share.
- Rookie outfielders: **8 / 52 = 15.38%**, ACTUAL count / INFERRED share.
- Rookie catchers: **2 / 52 = 3.85%**, ACTUAL count / INFERRED share.

2025 comparison: 48 rookies were registered, according to the KBO 2025 registration notice.

### 02 usage

For generator-level **position share comparison**, the 2026 registered-player distribution above is usable now. It is a club-registration population, not an active 1st-team roster or playing-time-weighted population. Do not use these shares as PA/IP role shares.

## 2. Modern KBO roster age evidence

Primary official age-bound sources:
- 2026 KBO annual roster/salary notice: https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11861
- 2025 KBO annual roster/salary notice: https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11394

Population/cutoff: registered club players, age measured at the Jan. 31 roster-registration cutoff used by KBO in the cited notices.

| Season | Youngest observed | Oldest observed | Type | Confidence |
|---|---|---|---|---|
| 2026 | 18y 1m 19d | 42y 1m 15d | ACTUAL | High |
| 2025 | 18y 1m 19d | 42y 6m 16d | ACTUAL | High |

The 2026 oldest registered player was Choi Hyung-woo and the youngest was Park Jun-seong; the 2025 oldest was Oh Seung-hwan and the youngest was Kim Seo-jun. Names are retained here only to make the published bounds auditable.

### Age-distribution status

The KBO annual roster attachments contain richer club-player registration information, but a verified public aggregate for **mean, median, P10/P25/P75/P90, position-specific age, and young-player age shares** was not recoverable in this pass without bulk-extracting the restricted attachment/player pages. Therefore:

- roster mean age: **OPEN**
- roster median age: **OPEN**
- roster age percentiles: **OPEN**
- position-specific age: **OPEN**
- age <=21 / <=23 shares: **OPEN**

Do not infer a normal distribution from the min/max bounds or treat rookie share as a direct age<=20 share.

## 3. Completed 2025 pitcher workload evidence

Matched-season policy: use completed **2025 KBO regular season** only. Do not mix current 2026 in-season records into 2025 workload calibration.

Primary/secondary sources checked:
- KBO official pitcher record pages expose `G`, `GS`, `TBF`, `IP` and detailed pitching statistics.
- Baseball-Reference 2025 KBO pitching leaderboard provides a compact player-level cross-check with `Age`, `G`, `GS`, `IP`, and `BF`: https://www.baseball-reference.com/register/leader.cgi?id=4e296e3b&type=pitch

Redistribution: no player-level leaderboard dump is committed. Only compact high-workload examples and derived bands are retained.

### League volume anchors

- 10 teams x 144 games/team = 720 league games: **ACTUAL KBO schedule structure**.
- Two team starts per game -> **1,440 team-start opportunities**: INFERRED.
- 2025 league total pitching workload already established in the shared evidence pack: **12,771.0 IP** across all 10 teams, completed regular season.

### High-volume starter tail

Baseball-Reference's completed 2025 leaderboard sorted by GS identifies the following top five by starts:

| Player | G | GS | IP | IP/GS | Type |
|---|---:|---:|---:|---:|---|
| Logan Allen | 32 | 31 | 173.0 | 5.58 | ACTUAL G/GS/IP; INFERRED IP/GS |
| Drew Anderson | 30 | 30 | 171.2 | 5.72 | ACTUAL / INFERRED |
| Yonny Chirinos | 30 | 30 | 177.0 | 5.90 | ACTUAL / INFERRED |
| Enmanuel De Jesus | 32 | 30 | 163.2 | 5.46 | ACTUAL / INFERRED |
| Ariel Jurado | 30 | 30 | 197.1 | 6.58 | ACTUAL / INFERRED |

Interpretation: a **full-season high-volume starter** tail of roughly `30-31 GS` is directly observed, and this tail sample spans about **5.46-6.58 IP/start**. This is **not** a league P90/P95 estimate; it is a high-GS extreme sanity band.

### High-appearance reliever tail

Baseball-Reference's completed 2025 leaderboard sorted by games identifies the following top five appearance totals:

| Player | G | GS | IP | IP/G | Type |
|---|---:|---:|---:|---:|---|
| Jeong Hyeon-su | 82 | 0 | 47.2 | 0.58 | ACTUAL G/GS/IP; INFERRED IP/G |
| Kim Jin-sung | 78 | 0 | 70.2 | 0.91 | ACTUAL / INFERRED |
| Noh Kyung-eun | 77 | 0 | 80.0 | 1.04 | ACTUAL / INFERRED |
| Kim Jin-ho | 76 | 0 | 72.1 | 0.95 | ACTUAL / INFERRED |
| Jeong Cheol-won | 75 | 0 | 70.0 | 0.93 | ACTUAL / INFERRED |

Interpretation: a **full-season extreme reliever-appearance tail** of roughly `75-82 G` is directly observed. Those five zero-start relievers span about **0.58-1.04 IP/appearance**. This is an extreme sanity band, not a league percentile band.

### Workload percentile status

A complete player-level 2025 `G/GS/IP/BF` table was not reproduced into this public repo, and the sources checked did not expose a compact percentile aggregate. Therefore the following remain **OPEN** rather than being guessed:

- all-pitcher G P10/P50/P90/P95
- starter GS P10/P50/P90/P95
- starter IP/start P10/P50/P90/P95
- reliever G P10/P50/P90/P95
- reliever IP/appearance P10/P50/P90/P95
- starter share of total IP
- bullpen share of total IP
- starter/reliever population counts under a single role-classification rule

### Recommended reproducible role classification for next extraction

When a licensed/reproducible player-level table is available, preserve raw `G`, `GS`, `IP`, `BF` and classify with explicit mutually exclusive tags:

1. `starter_primary`: GS/G >= 0.50 and GS >= 10
2. `reliever_primary`: GS == 0 and G >= 10
3. `hybrid`: 0 < GS/G < 0.50 or low-sample mixed usage
4. `small_sample`: G < 10

This is a **project analysis convention**, not an official KBO role definition. Publish both the raw distribution and sensitivity to the classification thresholds before production tuning.

## 4. Velocity evidence update

Primary official system evidence:
- KBO official notice, 2025-03-07: KBO adopted **TrackMan as the official pitch-velocity measurement system for the 2025 season**, with the intention of unifying broadcast and ballpark velocity displays.
- Source: https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11398

This materially improves measurement provenance: 2025 displayed KBO velocities have an identified official measurement system. However, the KBO public pages checked still do not expose a reusable league-wide pitch-level velocity distribution or aggregate mean/percentiles.

### Average vs maximum velocity rule

These must remain separate fields:

- `avg_fastball_velocity_kmh`: mean of fastball pitch velocities over a stated pitch/sample window.
- `max_fastball_velocity_kmh`: maximum observed fastball velocity over that window.

A single-game or player `max` must never be substituted for a league/player `average`.

### Current status

- Official measurement provider/system from 2025 onward: **TrackMan / KBO official — PASS**.
- League-wide 2025 average fastball velocity: **OPEN from primary source**.
- League-wide 2025 velocity SD/percentiles: **OPEN**.
- Existing 2024 `144.2 km/h` league-average fastball anchor remains a **secondary provisional reference**, not upgraded to official by the TrackMan notice.
- Official KBO news can provide auditable player-game examples containing both maximum and average velocity, but those examples are not a league distribution.

## 5. Debut-age / career-length longitudinal methodology

No provenance-safe league-wide completed-career distribution was obtained in this pass. The methodology is therefore fixed before data collection.

### Player cohort

Use KBO player IDs as entity keys. Prefer a retrospective cohort with first KBO regular-season appearance within a fixed entry window (example: 2005-2015) and follow through a fixed observation cutoff. Exclude players whose identity/history cannot be resolved consistently.

### Debut age

`debut_age = date_of_first_KBO_regular_season_appearance - date_of_birth`.

Report mean, median, P10/P25/P75/P90 and position groups. Distinguish KBO debut from professional debut in foreign leagues.

### Career length

Use two measures:

1. `calendar_span`: last KBO regular-season appearance year - first appearance year + 1.
2. `active_seasons`: count of KBO seasons with at least one first-team appearance.

The second measure is preferred for simulation because military service, injury, overseas play, and non-playing gaps can make calendar span misleading.

### Right censoring

Players active at the observation cutoff are **right-censored** and must not be treated as completed careers. Publish:
- completed-career distribution separately;
- censored share;
- Kaplan-Meier career-survival curve when sample size permits.

### Left truncation

Do not build a career-length distribution from players whose KBO careers began before the data window unless full pre-window history is available.

### Peak age

Peak age requires a predeclared metric and playing-time minimum. Report at least separate definitions for:
- hitter rate-performance peak (for example OPS or an era-adjusted metric);
- pitcher rate-performance peak;
- playing-time/workload peak;
- composite-value peak if a defensible value metric is available.

Do not define peak from a single low-PA/IP season.

## 6. Handoff fields

### 02 - Player Ratings & Generation: usable now

- `registered_population_2026 = 621`
- position counts/shares: P `317 / 51.05%`, C `50 / 8.05%`, IF `138 / 22.22%`, OF `116 / 18.68%`
- `rookies_2026 = 52 / 8.37%` of registered population
- rookie position composition: P 53.85%, IF 26.92%, OF 15.38%, C 3.85%
- observed roster age bounds: 18y1m19d to 42y1m15d for 2026
- age mean/median/percentiles: **OPEN**
- velocity: official 2025 measurement system = TrackMan; league distribution = **OPEN**

### 05 - Balance Lab: usable now

- completed-season `team_start_opportunities = 1,440`
- high-volume starter tail: `30-31 GS`, observed `5.46-6.58 IP/GS` among top-five GS leaders
- high-appearance zero-start reliever tail: `75-82 G`, observed `0.58-1.04 IP/G` among top-five appearance leaders
- use these as **extreme workload sanity bands only**, not as P90/P95 central calibration targets
- full starter/reliever percentile bands: **OPEN**

### 03 - Growth & Career: usable now

- longitudinal cohort/censoring methodology above is ready for implementation
- 2025/2026 observed roster age bounds remain usable plausibility constraints
- debut-age and career-length numerical distributions remain **OPEN** pending reproducible cohort extraction

## 7. Source quality and redistribution summary

| Evidence | Provider | Source quality | Redistribution posture |
|---|---|---|---|
| 2026 position/rookie counts | KBO official | High | Summary-only; KBO notice says no unauthorized redistribution |
| 2025/2026 age bounds | KBO official | High | Summary-only |
| 2025 starter/reliever high-workload examples | Baseball-Reference, cross-checkable against KBO record fields | Medium-High | No bulk table committed; minimal examples only |
| 2025 velocity measurement system | KBO official | High | Summary-only |
| League velocity distribution | not recovered | OPEN | no dataset committed |

## 8. Remaining OPEN gaps and next research order

1. Recover or independently calculate modern KBO roster **age mean/median/percentiles** from a source whose extraction/redistribution conditions permit aggregate processing.
2. Obtain a reproducible completed-2025 player-level `G/GS/IP/BF` source and calculate full starter/reliever P10/P50/P90/P95, role shares, IP shares, and tails under the declared role classifier.
3. Find a primary or explicitly licensed TrackMan-derived KBO **league fastball distribution** with average, SD and percentiles; keep maximum velocity separate.
4. Build the debut-age/career-length cohort using the predeclared censoring methodology.

Overall gate for this pack: **PARTIAL PASS / OPEN**. Position distribution and extreme workload sanity anchors are usable; full age and workload distributions remain OPEN.