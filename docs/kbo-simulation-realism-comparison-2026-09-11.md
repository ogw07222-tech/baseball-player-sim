# Simulation Statistics vs Real KBO — Realism Audit

Access date: 2026-09-11 (Asia/Seoul)

Role: `08 - Baseball Data & Research`

Purpose: independent research comparison of the current canonical simulation-distribution baseline against recent real KBO league environments. This report does **not** modify gameplay/rating constants.

## 1. Simulation source used

Repository latest-main audit head at research start: `main@0aafcbc6106474e96a35dae0fceeb4d9c0b5acbf`.

`docs/workstream-status/05-balance-lab.md` identifies the canonical representative full-game distribution as GitHub Actions run `34488552895`, simulation SHA `7112ce550e0933a80b0c75701de46fbd03047077`, seed `20260906`, 10,000 games. The artifact `heavy-validation-34488552895-7112ce550e0933a80b0c75701de46fbd03047077` was re-opened during this audit.

The artifact reports:
- runs/game: 8.1360; P10/P50/P90/P95/P99 = 3/8/14/16/20; max 31
- runs/team-game: 4.0680; P10/P50/P90/P95/P99 = 1/4/8/10/13; max 29
- PA/game: 77.3202; P10/P50/P90/P95/P99 = 68/77/87/91/99; max 112
- hits/team-game: 9.1905 -> hits/game 18.3810
- HR/game: 2.0976
- BB/game: 6.2906
- K/game: 16.5189
- innings/game: 9.1653; 9-inning 89.50%, 10-inning 4.47%, 11-inning 6.03%
- extra innings: 10.50%
- draws: 3.49%
- walk-offs: 7.31%
- 20+ total-run games: 112/10,000 = 1.12%
- 15+ run team-games: 81/20,000 = 0.405%
- 100+ PA games: 84/10,000 = 0.84%
- 12+ innings: 0
- completion 100%; safety-cap hits 0; invariant violations 0

A compare from the 05 baseline head to the current audit head changed production/career-integration files but not the full-game simulation core modules, so the canonical distribution remains the comparison target by code identity.

## 2. Real KBO sources and period

Primary period: completed regular seasons **2022, 2023, 2024, 2025** (10 teams, nominally 720 games/season). This avoids overfitting to one season.

Sources:
- KBO official current/team records: `https://www.koreabaseball.com/Record/Team/`
- KBO official 2025 rule change: `https://www.koreabaseball.com/Kbo/League/GameManage2025.aspx`
- KBO official 2025 Board notice confirming regular-season extra innings reduced from 12 to 11 and documenting 59 extra-inning games in 2024: `https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=11353`
- Yagoonara completed-season team batting/pitching tables for 2022-2025, which state `Data Source: koreabaseball.com`.
- Baseball-Reference / published standings for tie counts when a compact completed-season KBO standings aggregate was needed.
- MyKBO Stats walk-off season summaries for 2022-2025; this is secondary and used only for the walk-off comparison.

Redistribution posture: this report stores compact aggregates/derived comparisons only; no restricted bulk source table is copied.

### 2.1 Recent KBO league environment derived from completed team totals

| Season | Runs/game | Hits/game | HR/game | BB/game | K/game | HBP/game | PA/game | AVG | OBP | SLG | OPS | ISO | BABIP | BB% | K% | HR% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 9.060 | 17.779 | 1.507 | 6.847 | 14.540 | 1.001 | 77.726 | .260 | .333 | .379 | .713 | .119 | .307 | 8.81% | 18.71% | 1.94% |
| 2023 | 9.197 | 18.013 | 1.283 | 7.139 | 13.847 | 0.967 | 78.099 | .263 | .339 | .374 | .712 | .110 | .310 | 9.14% | 17.73% | 1.64% |
| 2024 | 10.750 | 19.346 | 1.997 | 7.313 | 15.036 | 1.088 | 79.535 | .277 | .352 | .420 | .772 | .143 | .325 | 9.19% | 18.91% | 2.51% |
| 2025 | 9.463 | 17.811 | 1.654 | 7.115 | 15.311 | 1.119 | 77.772 | .262 | .339 | .389 | .727 | .127 | .312 | 9.15% | 19.69% | 2.13% |
| 2022-25 mean | **9.617** | **18.237** | **1.610** | **7.103** | **14.684** | **1.044** | **78.283** | **.266** | **.341** | **.390** | **.731** | **.125** | **.314** | **9.07%** | **18.76%** | **2.06%** |

2026 is still incomplete and is not used as a calibration target. As an official KBO in-season cross-check on the access date, the current team batting aggregate was again a higher-scoring environment than the simulation; this strengthens rather than reverses the completed-season conclusion.

### 2.2 Recent KBO pitching environment

Weighted league aggregates from the same completed seasons:

| Season | ERA | WHIP | K/9 | BB/9 | HR/9 |
|---|---:|---:|---:|---:|---:|
| 2022 | 4.06 | 1.38 | 7.33 | 3.45 | 0.76 |
| 2023 | 4.14 | 1.41 | 6.99 | 3.61 | 0.65 |
| 2024 | 4.91 | 1.50 | 7.62 | 3.71 | 1.01 |
| 2025 | 4.31 | 1.41 | 7.77 | 3.61 | 0.84 |

The canonical 10k full-game artifact does not emit simulation ERA/WHIP/K9/BB9/HR9 with denominator definitions suitable for direct comparison, so those direct pitching rows are `OPEN` rather than reverse-engineered from incomplete fields.

## 3. Definition alignment

- `runs/game`, `hits/game`, `HR/game`, `BB/game`, `K/game`: both teams combined per played game.
- `runs/team-game`: one team side of one game; KBO reference is league runs divided by 2 x games.
- `PA/game`: both teams combined. The simulation artifact's `average_pa_per_team_game=38.6601`, therefore 77.3202 combined PA/game.
- Simulation-derived event rates below use the same simulation PA denominator: `event/game / PA/game`.
- KBO BB%, K%, HR% use league BB/SO/HR divided by league PA.
- AVG/OBP/SLG/OPS/ISO/BABIP are **not** reconstructed for simulation because the canonical artifact does not emit all AB/HBP/SF/TB/1B/2B/3B inputs.
- 2025 KBO regular season max inning is 11; 2022-2024 used the prior 12-inning cap. Frequency comparisons involving extras therefore require rule context.

## 4. Primary comparison table

| Metric | Simulation | KBO reference | Reference period | Difference | Difference % | Status | Comment |
|---|---:|---:|---|---:|---:|---|---|
| Runs/game | 8.136 | 9.617 mean; 9.060-10.750 range | 2022-25 | -1.481 | -15.4% | **FAIL** | Below every completed recent season. |
| Runs/team-game | 4.068 | 4.809 mean; 4.530-5.375 range | 2022-25 | -0.741 | -15.4% | **FAIL** | Equivalent to only ~586 runs/team over 144 games vs recent league-average ~652-774. |
| Hits/game | 18.381 | 18.237 mean; 17.779-19.346 | 2022-25 | +0.144 | +0.8% | **PASS** | Hit volume is realistic despite low scoring. |
| HR/game | 2.098 | 1.610 mean; 1.283-1.997 | 2022-25 | +0.487 | +30.3% | **FAIL** | Above even the 2024 high-HR environment. |
| BB/game | 6.291 | 7.103 mean; 6.847-7.313 | 2022-25 | -0.813 | -11.4% | **FAIL** | Below every recent completed season. |
| K/game | 16.519 | 14.684 mean; 13.847-15.311 | 2022-25 | +1.835 | +12.5% | **FAIL** | Above every recent completed season. |
| PA/game | 77.320 | 78.283 mean; 77.726-79.535 | 2022-25 | -0.963 | -1.2% | **WATCH** | Close, but slightly below the recent range. |
| H/PA | 23.77% | 23.29% mean; 22.87-24.32% | 2022-25 | +0.48 pp | +2.1% | **PASS** | Contact-result volume broadly plausible. |
| BB/PA | 8.14% | 9.07% mean; 8.81-9.19% | 2022-25 | -0.93 pp | -10.3% | **FAIL** | Systematic low-walk environment. |
| K/PA | 21.36% | 18.76% mean; 17.73-19.69% | 2022-25 | +2.60 pp | +13.9% | **FAIL** | Systematic high-strikeout environment. |
| HR/PA | 2.71% | 2.06% mean; 1.64-2.51% | 2022-25 | +0.65 pp | +31.7% | **FAIL** | Home-run probability is outside recent completed-season range. |
| AVG | not emitted | .260-.277 | 2022-25 | - | - | **OPEN** | Need AB from same simulation sample. |
| OBP | not emitted | .333-.352 | 2022-25 | - | - | **OPEN** | Need H/BB/HBP/AB/SF. |
| SLG / OPS / ISO | not emitted | SLG .374-.420; OPS .712-.772; ISO .110-.143 | 2022-25 | - | - | **OPEN** | Need total bases and extra-base-hit breakdown. |
| BABIP | not emitted | .307-.325 | 2022-25 | - | - | **OPEN** | Need AB, SO, HR, SF. |
| Draw frequency | 3.49% | 3.06% (22/720) | 2025, 11-inning rule | +0.43 pp | +14.2% | **WATCH** | Correct rule cap; frequency modestly high vs first full 11-inning season. |
| Extra-inning frequency | 10.50% | 8.19% (59/720) | 2024, 12-inning rule | +2.31 pp | +28.2% | **WATCH** | Reference is pre-2025 rule; exact completed-2025 extra-inning count still needed. |
| Walk-off frequency | 7.31% | 6.56% 4-year mean; 5.69-7.08% | 2022-25 | +0.75 pp | +11.4% | **WATCH** | Slightly above recent range; secondary source. |
| Mean innings/game | 9.165 | no directly aligned compact aggregate | - | - | - | **OPEN** | Do not derive from total pitching IP because walk-offs change denominator geometry. |
| 20+ total-run games | 1.12% | no verified recent aggregate yet | - | - | - | **OPEN** | Need game-log aggregation. |
| 15+ run team-games | 0.405% | no verified recent aggregate yet | - | - | - | **OPEN** | Need game-log aggregation. |
| 100+ PA games | 0.84% | no verified recent aggregate yet | - | - | - | **OPEN** | Need game-log aggregation under same PA definition. |
| HBP/game | not emitted | 0.967-1.119 | 2022-25 | - | - | **OPEN** | Required for OBP/run-conversion audit. |
| Errors/game | not emitted | not aggregated in this pass | - | - | - | **OPEN** | Need simulation and KBO same-definition field. |
| Shutout frequency | not emitted | not aggregated in this pass | - | - | - | **OPEN** | Need game-level outcome counters. |
| Team win% spread / parity | not emitted in canonical game artifact | recent standings available | 2022-25 | - | - | **OPEN** | Needs season-level Monte Carlo output, not independent games only. |

## 5. Key structural finding

The strongest signal is **not** simply that offense is too weak.

The simulation produces a realistic number of hits and almost-realistic PA volume, but simultaneously produces:
- materially fewer walks,
- materially more strikeouts,
- materially more home runs,
- and materially fewer runs.

That combination means the realism gap must be decomposed before changing constants. Plausible causes include more than one subsystem:
1. PA outcome mix (`BB/K/contact/HR`) in gameplay probability logic;
2. extra-base-hit mix beyond HR (2B/3B absent from the canonical artifact);
3. sequencing / advancement / run-conversion behavior;
4. baserunning and runner advancement;
5. double-play frequency;
6. defense/errors and unearned-run pathways;
7. lineup/rating distribution if production player quality changes event probabilities;
8. pitcher/bullpen usage and fatigue if later-innings scoring is suppressed.

A direct formula change cannot be justified from the current evidence alone.

## 6. Realism summary

| Area | Status | Audit finding |
|---|---|---|
| Overall run environment | **FAIL** | Runs/game is ~15% below 2022-25 mean and below every completed season in the reference window. |
| Contact environment | **WATCH** | Hits and H/PA are realistic, but the surrounding K/BB mix is not. |
| K/BB environment | **FAIL** | K is high and BB is low, both outside recent completed-season ranges. |
| Power environment | **FAIL** | HR/game and HR/PA are above recent KBO range despite the low total run environment. |
| Pitching environment | **OPEN/WATCH** | Direct ERA/WHIP outputs are absent; indirect event mix is too K/HR-heavy and BB-light. |
| Extra innings / draws | **WATCH** | 11-inning cap is correct; draw rate is somewhat high vs 2025 and extras are high vs 2024 pre-rule reference. |
| Game-length / PA environment | **WATCH** | PA/game is close but slightly low; mean inning alignment lacks exact real counterpart. |
| Distribution variance | **OPEN/WATCH** | Simulation run/PA percentiles exist, but matched real game-level quantiles were not yet aggregated. |
| Extreme tails | **OPEN** | Simulation tails are measurable; real KBO frequencies need game-log aggregation. |
| Team parity | **OPEN** | Canonical artifact has no team-season standings distribution. |

## 7. Strongest realism matches

1. **Hits/game and H/PA**: very close to the recent KBO environment.
2. **PA/game**: only ~1.2% below the 2022-25 mean.
3. **Rule semantics**: no 12+ inning regular-season games, consistent with the 2025 11-inning limit.
4. **Simulation stability**: 100% completion, no cap hits, no invariant violations, deterministic replay.

These are important: the engine is not globally broken or distribution-collapsed. The realism issue is concentrated in the statistical composition and scoring conversion.

## 8. Biggest realism gaps

Priority by evidence strength and gameplay impact:

1. **Run environment too low — FAIL** (`01 + 05`, possible `02` contribution).
2. **Strikeout rate too high — FAIL** (`01`, with `02` distribution isolation needed).
3. **Walk rate too low — FAIL** (`01`, with `02` distribution isolation needed).
4. **Home-run rate too high — FAIL** (`01`, with power-rating distribution check in `02`).
5. **The combination of realistic hits + excess HR + deficient runs requires run-conversion decomposition — high priority WATCH/FAIL investigation**, not a one-knob tuning response.
6. Draw/extra-inning/walk-off frequencies are secondary **WATCH** items.

## 9. Calibration priority routing

### Priority 1 — 05 Balance Lab
Run a measurement-only decomposition before tuning.

Exact request:
- rerun the canonical 10k seed or a larger fixed-seed sample and emit league totals for `PA, AB, R, H, 1B, 2B, 3B, HR, TB, BB, IBB, HBP, SO, SF, SAC, GDP, E, ER`;
- report AVG/OBP/SLG/OPS/ISO/BABIP, BB%, K%, HR%, HBP%, GDP/PA;
- report per-game P10/P25/P50/P75/P90/P95/P99 for runs, hits, HR, BB, K, HBP, PA;
- add counters for shutouts, 15+ team-run games, 20+ total-run games, 100+ PA games, walk-offs, draws, and extra innings;
- do **not** change any production constants in this run.

### Priority 2 — 01 Gameplay Engine
Observed bias: event mix has too few BB, too many K and too many HR relative to recent KBO.

Exact request after 05 decomposition:
- sensitivity-only sweeps around BB/K/contact/HR pathways;
- identify which probability stage creates the bias;
- separately audit non-HR extra-base-hit generation and runner advancement/run conversion;
- inspect GDP, errors, baserunning, sacrifice and sequencing before proposing production changes.

### Priority 3 — 02 Ratings & Generation
Observed bias may be formula-level or population-level.

Exact request:
- run the same gameplay engine against (a) fixed neutral ratings and (b) current generated production rating distribution;
- compare BB%, K%, HR%, H/PA and runs/PA;
- determine how much of each bias is caused by player distribution rather than core gameplay probabilities;
- inspect power/contact/discipline distribution tails without changing rating scales yet.

### Priority 4 — 05 + 03 pitcher/role isolation
If scoring suppression is concentrated late in games, bullpen usage/fatigue may contribute.

Exact request:
- split scoring/event rates by innings 1-3, 4-6, 7-9, extras;
- emit starter vs reliever BF, IP, K%, BB%, HR% and runs allowed when those stats are available;
- compare with the 08 starter/reliever workload baseline before changing role logic.

### Priority 5 — 08 Data & Research
Remaining reference gaps:
- completed-2025 extra-inning game count;
- game-log-derived real KBO run/PA/event quantiles and extreme-tail frequencies;
- shutout/error frequencies under matched definitions;
- real team-season win%/run-differential distributions for parity audit.

### Priority 6 — 00 Game Design HQ
A cross-system decision is needed only after sensitivity evidence if the project must choose between:
- multi-year recent KBO environment calibration, or
- explicit season-target calibration such as completed 2025.

Do not choose this target implicitly by tuning to one anomalous season.

## 10. Final gate

- `RECENT_KBO_MULTIYEAR_REFERENCE = PASS`
- `RUN_ENVIRONMENT_REALISM = FAIL`
- `HIT_VOLUME_REALISM = PASS`
- `BB_ENVIRONMENT_REALISM = FAIL`
- `K_ENVIRONMENT_REALISM = FAIL`
- `HR_ENVIRONMENT_REALISM = FAIL`
- `PA_ENVIRONMENT_REALISM = WATCH`
- `EXTRA_INNING_DRAW_REALISM = WATCH`
- `WALKOFF_REALISM = WATCH`
- `BATTING_RATE_STAT_COMPARISON = OPEN` (simulation denominator fields incomplete)
- `PITCHING_RATE_STAT_COMPARISON = OPEN` (simulation ERA/WHIP/K9 fields incomplete)
- `REAL_GAME_TAIL_DISTRIBUTION = OPEN`
- `TEAM_PARITY_COMPARISON = OPEN`
- `OVERALL_KBO_STATISTICAL_REALISM = FAIL_WITH_STRONG_LOCAL_MATCHES`

The engine has strong structural/stability evidence and realistic hit/PA volume, but the current full-game statistical composition is not yet a realistic recent-KBO environment.