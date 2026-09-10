# Shared KBO evidence baseline pack

Access date: 2026-09-10 (Asia/Seoul)

Purpose: minimal, public-repository-safe reference pack for workstreams 02/03/04/05. This document does not modify gameplay or rating formulas and does not reproduce paywalled or bulk third-party datasets.

Status labels:
- **ACTUAL**: directly reported by the cited source or exactly reproducible from cited/stored factual totals.
- **INFERRED**: derived from factual totals using a stated formula.
- **ESTIMATED**: approximate or model-based value.
- **OPEN**: insufficient evidence for a reliable baseline.

## Source policy and matched-season policy

For calibration, prefer a completed regular season. The primary matched-condition statistical baseline in this pack is therefore **2025 KBO regular season**. Current 2026 official pages are useful for rules, roster-state and in-season checks but should not be mixed into a 2025 calibration target.

Primary sources checked:
- KBO official records/statistics: https://www.koreabaseball.com/Record/
- KBO English team statistics: https://eng.koreabaseball.com/Stats/TeamStats.aspx
- KBO league operation: https://m.koreabaseball.com/About/GameManage.aspx
- KBO 2026 rules changes: https://www.koreabaseball.com/Kbo/League/GameManage2026.aspx
- KBO awards: https://www.koreabaseball.com/Player/Awards/
- KBO official notices / roster and FA announcements: https://www.koreabaseball.com/MediaNews/Notice/

Secondary cross-check used for completed 2025 team totals:
- Yagoonara 2025 team batting/pitching pages, which identify KBO/koreabaseball.com as source: https://www.yagoonara.com/en/team-stats/detail/2025/hitter and https://www.yagoonara.com/en/team-stats/detail/2025/pitcher

Redistribution note: KBO pages and notices carry copyright/republication restrictions. This repository stores only compact factual summaries and source references here; it does not copy the source tables or attachments in bulk. Redistribution permission for historical copied datasets remains governed by `data/PROVENANCE.md` and may be OPEN.

---

## A. Rating / Generation evidence

| Metric | Value | Season / sample | Source/provider | Type | Reliability | Simulation use |
|---|---:|---|---|---|---|---|
| League roster age lower observed bound | 18y 1m 19d | 2026 registered-player snapshot, Jan 31 cutoff | KBO official 2026 roster/annual salary notice | ACTUAL | High | Hard plausibility bound only; not an age distribution |
| League roster age upper observed bound | 42y 1m 15d | 2026 registered-player snapshot, Jan 31 cutoff | KBO official 2026 roster/annual salary notice | ACTUAL | High | Hard plausibility bound only |
| 2025 roster age lower observed bound | 18y 1m 19d | 2025 registered-player snapshot, Jan 31 cutoff | KBO official 2025 roster/annual salary notice | ACTUAL | High | Historical bound |
| 2025 roster age upper observed bound | 42y 6m 16d | 2025 registered-player snapshot, Jan 31 cutoff | KBO official 2025 roster/annual salary notice | ACTUAL | High | Historical bound |
| 2025 players registered during season | 597 | all players registered in 2025 KBO League, as referenced in 2026 retained-player notice | KBO official | ACTUAL | High | Approximate universe size; not opening-day roster size |
| 2026 retained players | 568 | after 29 exclusions from the 597 players registered during 2025 | KBO official retained-player notice | ACTUAL | High | Off-season roster-state anchor |
| 2024 league average fastball velocity | 144.2 km/h | KBO regular season, fastball average; reported in 2025 news article | Newsis report | ACTUAL claim from secondary source | Medium | Provisional league-center velocity reference; do not label official until primary table is recovered |
| 2025 early-season elite reliever fastball average | 154 km/h (Kim Seo-hyeon) | through Apr 20/22, 2025 | Yonhap, explicitly attributing figures to KBO | ACTUAL snapshot | Medium-High | Elite velocity anchor, not full-season distribution |
| 2025 early-season elite starter fastball average | 153 km/h (Cody Ponce) | through Apr 20/22, 2025 | Yonhap, explicitly attributing figures to KBO | ACTUAL snapshot | Medium-High | Elite starter velocity anchor |
| 2025 early-season slower established starter example | 140.4 km/h (Lim Chan-gyu) | Apr 2025 snapshot | NewsPim | ACTUAL snapshot | Medium | Lower-velocity viable-starter example, not distribution percentile |
| Current position distribution | OPEN | modern full KBO registered-player sample | KBO annual roster attachment exists, but compact verified counts were not recovered in this pass | OPEN | - | Do not calibrate generator position shares yet |
| Full age distribution | OPEN | modern KBO roster | no verified aggregate age histogram recovered | OPEN | - | Do not infer normal distribution from min/max |
| Hitter/pitcher usage spectrum | OPEN | completed matched season | requires player-level PA/IP/G/GS aggregation | OPEN | - | Needs reproducible summary extraction |
| Starter/reliever role distribution | OPEN | completed matched season | no stable official role label distribution recovered | OPEN | - | Use GS/G/IP only after aggregation |
| Low/middle/elite player performance spectrum | OPEN | matched player sample | requires qualified/all-player percentile definition | OPEN | - | Define percentile sample before tuning ratings |

### A interpretation

The current pack is enough to constrain impossible ages and establish provisional physical fastball anchors, but **not** enough to approve a complete player-generation distribution. Workstream 02 should treat position shares, age histogram, usage percentiles and low/middle/elite performance percentiles as OPEN.

---

## B. Growth / Career evidence

| Metric / rule | Value | Season / scope | Source/provider | Type | Reliability | Simulation use |
|---|---|---|---|---|---|---|
| Standard KBO regular-season schedule | 144 games/team; 16 games against each other club; 720 league games | current KBO league operation | KBO official | ACTUAL | High | Season/career workload contract |
| 2026 FA-qualified players announced | 30 total: A 7, B 13, C 10 | 2026 FA class announced Nov 5, 2025 | KBO official | ACTUAL | High | Useful annual FA market-size anchor; not a long-term average |
| 2026 FA approved players | 21 | approved Nov 8, 2025 | KBO official | ACTUAL | High | Annual transaction-volume example |
| External FA signings allowed per club in 2026 class | up to 3 | because 21 FA-approved players; KBO cites Rule 173 | KBO official | ACTUAL | High | Transaction-rule contract for that class |
| Historical FA service-season threshold | 145 active-roster days = one season; generally 9 seasons, 8 for qualifying four-year university graduates | KBO official FA notices; applies to players first registered after 2006 under registration-day method | KBO official historical notices | ACTUAL historical rule statement | Medium-High | Useful service-time model reference; current full rulebook should be checked before locking production rules |
| Debut-age distribution | OPEN | KBO careers | no verified league-wide debut-age aggregate recovered | OPEN | - | Requires player debut-date aggregation |
| Age-performance curve | OPEN | KBO careers | no matched, provenance-safe longitudinal aggregate recovered | OPEN | - | Do not tune aging curve from anecdotes |
| Career-length distribution | OPEN | retired/completed careers | no verified distribution recovered | OPEN | - | Needs cohort definition and censoring handling |
| Peak-age distribution | OPEN | multi-year player careers | no verified league-wide peak-age study recovered | OPEN | - | Must define metric (WAR/OPS/ERA-/playing time) first |
| 1st-team / Futures movement frequency | OPEN | player transactions | no compact official aggregate recovered | OPEN | - | Requires transaction-log aggregation or public summary source |

### B interpretation

Workstream 03 can immediately use the 144-game season contract and the FA/roster-day rules as structural references. It should **not** treat debut age, peak age, career length, or promotion/demotion frequency as calibrated yet.

---

## C. Events / Story evidence

| Event / criterion | Value | Season / scope | Source/provider | Type | Reliability | Simulation use |
|---|---|---|---|---|---|---|
| KBO MVP | titleholders plus other outstanding players are eligible; media vote | current award framework | KBO official awards page | ACTUAL | High | Award event eligibility/context |
| KBO Rookie Award | current-year signees and players signed within prior 5 years whose prior cumulative record does not exceed 30 IP (pitcher) or 60 PA (hitter); overseas-pro experience excluded | current award framework | KBO official awards page / 2025 notice | ACTUAL | High | Rookie-event eligibility contract |
| Golden Glove pitcher candidate | qualified IP OR 10+ wins OR 30+ saves OR 30+ holds | current framework | KBO official | ACTUAL | High | Award candidate gate |
| Golden Glove fielder/catcher candidate | at least 720 defensive innings at position, subject to titleholder exceptions | current framework | KBO official | ACTUAL | High | Award candidate gate |
| KBO Fielding Award pitcher candidate | at least 48 IP (one third of 144 games) | current framework | KBO official | ACTUAL | High | Defensive-award event gate |
| KBO Fielding Award catcher candidate | at least 72 games | current framework | KBO official | ACTUAL | High | Defensive-award event gate |
| KBO Fielding Award IF/OF candidate | at least 720 defensive innings at position | current framework | KBO official | ACTUAL | High | Defensive-award event gate |
| 2025 MVP / Rookie winners | Cody Ponce / Ahn Hyun-min | 2025 regular season | KBO official awards page | ACTUAL | High | Historical narrative reference only |
| 2025 Golden Gloves | 10 awards across pitcher, catcher, 1B, 2B, 3B, SS, 3 OF, DH | 2025 | KBO official | ACTUAL | High | Annual award-count contract |
| 2025 Fielding Awards | 9 positional winners | 2025 | KBO official | ACTUAL | High | Annual award-count contract |
| Injury-event frequency | OPEN | KBO player-seasons | no provenance-safe league-wide injury incidence dataset recovered | OPEN | - | Do not set injury probability from this pack |
| Milestone incidence rates | OPEN | career/season milestones | official record pages exist, but no compact rate distribution produced | OPEN | - | Use milestone definitions later, not frequencies yet |

### C interpretation

Workstream 04 has enough evidence to implement **award eligibility and annual award structure** without inventing thresholds. Injury/random-event frequencies remain OPEN.

---

## D. Balance evidence — primary completed-season pack

Primary sample: **2025 KBO regular season, all 10 teams**. Hitting totals were already frozen in `tools/pitcher_calibration/targets.py`; completed-season team tables were cross-checked against a secondary KBO-derived provider. Pitching aggregate values below use the same completed season.

### D1. Hitting league baseline

| Metric | Value | Sample | Source/provider | Type | Reliability |
|---|---:|---|---|---|---|
| PA | 55,996 | all 10 teams, 2025 regular season | repository frozen totals; source lineage identifies KBO/koreabaseball.com | ACTUAL | High for value; historical ingestion URL OPEN |
| AB | 49,021 | same | same | ACTUAL | High |
| H | 12,824 | same | same | ACTUAL | High |
| HR | 1,191 | same | same | ACTUAL | High |
| BB | 5,123 | same | same | ACTUAL | High |
| SO | 11,024 | same | same | ACTUAL | High |
| AVG | .2616 | same | H / AB | INFERRED | High |
| OBP | .3385 | same | standard OBP formula from stored H, BB, HBP, AB, SF | INFERRED | High |
| SLG | .3887 | same | total bases / AB from stored 1B/2B/3B/HR | INFERRED | High |
| OPS | .7272 | same | OBP + SLG | INFERRED | High |
| BB% | 9.149% | BB / PA | stored totals | INFERRED | High |
| K% | 19.687% | SO / PA | stored totals | INFERRED | High |
| HR% | 2.127% | HR / PA | stored totals | INFERRED | High |
| BABIP | .3122 | standard BABIP formula | stored totals | INFERRED | High |

### D2. Pitching league baseline

| Metric | Value | Sample | Source/provider | Type | Reliability |
|---|---:|---|---|---|---|
| IP | 12,771.0 | all 10 teams, 2025 regular season | Yagoonara completed-season aggregate, sourced from KBO | ACTUAL secondary aggregation | Medium-High |
| ERA | 4.31 | same | same | ACTUAL secondary aggregation | Medium-High |
| WHIP | 1.41 | same | same | ACTUAL secondary aggregation | Medium-High |
| SO | 11,024 | same | matches batting SO total | ACTUAL | High |
| BB | 5,123 | same | matches batting BB total | ACTUAL | High |
| HR | 1,191 | same | matches batting HR total | ACTUAL | High |
| K/9 | 7.769 | 11,024 SO / 12,771 IP * 9 | derived from totals | INFERRED | High |
| BB/9 | 3.610 | 5,123 BB / 12,771 IP * 9 | derived from totals | INFERRED | High |
| HR/9 | 0.839 | 1,191 HR / 12,771 IP * 9 | derived from totals | INFERRED | High |
| H+BB per IP | 1.405 | (12,824 H + 5,123 BB) / 12,771 IP | derived approximation to WHIP excluding other definitions not involved | INFERRED | High |
| QS | 562 league total | all teams, 2025 | Yagoonara KBO-derived team aggregation | ACTUAL secondary aggregation | Medium-High |

### D3. Season-volume anchors

- 144 games per team, 720 league games: **ACTUAL, KBO official**.
- Therefore there are 1,440 team-start opportunities in a complete regular season: **INFERRED** from two starting teams per game.
- Starter IP/start league-wide: **OPEN**. Total pitching IP cannot be separated into starter and reliever IP without a GS/IP aggregation.
- Bullpen workload distribution: **OPEN**. Holds/saves totals alone are insufficient for reliever innings and appearance workload.

### D usage rule

Workstream 05 may use the 2025 hitting and pitching values above as the **matched completed-season league baseline**. Do not combine them with current 2026 in-season numbers in one calibration objective.

---

## Usable evidence by workstream

### 02 - Player Ratings & Generation
Usable now:
- roster age hard bounds (2025/2026 snapshots);
- roster-universe anchors (597 registered in 2025; 568 retained for 2026);
- provisional fastball center/elite/slow-starter anchors with explicit source quality.

Still OPEN:
- modern position distribution;
- full age histogram;
- PA/IP usage percentiles;
- starter/reliever population share;
- low/middle/elite performance percentiles.

### 03 - Growth & Career
Usable now:
- 144-game season structure;
- 145-day historical service-season rule reference;
- 2026 FA market-size example (30 qualified, 21 approved);
- observed KBO roster age bounds.

Still OPEN:
- debut-age distribution;
- age-performance curve;
- career length;
- peak age;
- first-team/Futures movement frequency.

### 04 - Events & Story
Usable now:
- MVP/Rookie eligibility framework;
- Golden Glove thresholds;
- Fielding Award thresholds;
- annual award counts and 2025 winners as historical examples;
- FA approval/transaction event timing examples.

Still OPEN:
- injury incidence;
- slump/breakout empirical frequency;
- milestone incidence rates.

### 05 - Balance Lab
Usable now:
- completed 2025 league AVG/OBP/SLG/OPS, BB%, K%, HR%, BABIP;
- completed 2025 ERA/WHIP and derived K/9, BB/9, HR/9;
- 144 games/team / 720 league games;
- 2025 QS total as workload-quality context.

Still OPEN:
- starter IP/start;
- reliever IP/appearance and bullpen workload percentiles;
- role-split ERA/FIP/rate baselines.

---

## Next research priorities

1. **Modern roster distribution extraction**: recover compact counts from the official 2025/2026 KBO player-registration attachment (position and average service/age fields) without committing the bulk attachment.
2. **Starter/reliever workload pack**: aggregate 2025 player G/GS/IP to produce starter IP/start, reliever IP/app, appearances/team and role percentiles.
3. **Career longitudinal pack**: define cohorts and calculate debut age, career length and peak-age distributions with censoring rules documented.
4. **Performance spectrum pack**: produce 2025 hitter/pitcher percentile bands under explicit PA/IP thresholds for low/middle/elite calibration.
5. **Velocity distribution**: locate a primary or clearly licensed KBO pitch-tracking aggregate; until then keep 144.2 km/h league center as secondary/provisional.
6. **Injury/event frequency**: search for KBO or peer-reviewed public aggregate data; do not infer injury probabilities from news counts.

## Gate

**SHARED_KBO_EVIDENCE_LANE = OPEN (usable partial baseline pack)**

Reason: completed-season league balance baselines and several official structural/award rules are usable now, but the distributional inputs most important to player generation and long-term career calibration remain incomplete.