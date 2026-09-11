# KBO pitch / batted-ball / run-conversion reference pack

Access date: 2026-09-11 (Asia/Seoul)

Purpose: empirical KBO reference package for `01 - Gameplay Engine`, `02 - Ratings & Generation`, `05 - Balance Lab`, and `00 - Game Design HQ`. This is research/validation only. No production probability or rating constant is changed here.

Simulation source: `docs/workstream-status/05-balance-lab.md`, expanded offense/pitch diagnostic run `34580783735`, checkout `21a7621763a85268a4e2fb68cad9194854c4c601`, seed `20260906`.

Status labels:
- **PASS**: definition-aligned and inside a plausible recent KBO range.
- **WATCH**: directionally plausible but materially offset, source/sample weaker, or definition only approximately aligned.
- **FAIL**: definition-aligned and materially inconsistent with recent KBO evidence.
- **OPEN**: no sufficiently definition-aligned KBO reference was recovered.

## 1. Source hierarchy and limitations

Primary KBO sources were checked first. KBO official pages are strong for league totals, rules, and measurement-system changes, but a reusable completed-season league aggregate for Zone%, O-Swing%, Z-Swing%, Contact%, Z-Contact%, O-Contact%, CStr%, CSW%, F-Strike%, or count-reach rates was not recovered.

Secondary sources used where needed:
- Yagoonara completed-season league/team totals; pages identify `koreabaseball.com` as their data source.
- Yagoonara pitch-tracking pages for the current 2026 KBO swing/chase/contact environment. These are useful but are an in-progress sample and may represent an average across qualified hitters rather than a pitch-weighted league aggregate.
- FanGraphs/Sports Info Solutions pages were checked for definitions and individual KBO plate-discipline fields, but no robust 2022-2025 league-average row was recovered for the requested full plate-discipline set.
- Media reports citing KBO/Statiz were used only where no stronger compact aggregate was public.

No raw third-party table is copied into the repository. Only compact factual summaries, derivations, definitions, and source paths are retained.

## 2. Pitch-tracking comparison

### 2.1 Best currently available KBO pitch reference

Yagoonara's 2026 KBO pitch-tracking view reports 207,795 tracked pitches and a league hitter zone-swing profile. It reports an out-of-zone chase rate of about 27%, states that hitters miss on about 40% of those out-of-zone swings, and the current qualified-hitter summary gives approximately Swing% 44.8, O-Swing% 26.7, Z-Swing% 64.3, Whiff/swing 21.0, and Z-Contact% 86.9. This is a **2026 in-progress secondary reference**, not a completed-season official league aggregate.

| Metric | Simulation neutral | KBO reference | Period | Definition | Difference | Confidence | Status |
|---|---:|---:|---|---|---:|---|---|
| Zone% | 55.15% | direct league Zone% not recovered; implied roughly 48% from current Swing/O-Swing/Z-Swing averages | 2026 live | pitches in zone / pitches; KBO figure is only algebraically implied from separately published averages | about +7 pp vs implied value | Low | **OPEN/WATCH** |
| Swing% | 47.47% | ~44.8% | 2026 live | swings / all tracked pitches | +2.67 pp, +6.0% | Medium-Low | **WATCH** |
| O-Swing / Chase% | 21.25% | ~26.7-27.0% | 2026 live | swings at out-of-zone pitches / out-of-zone pitches | -5.45 pp, -20.4% | Medium | **WATCH** |
| Generated-prospect Chase% | 33.57% | ~26.7-27.0% | 2026 live | same denominator | +6.87 pp, +25.7% | Medium | **FAIL** |
| Z-Swing% | 68.80% | ~64.3% | 2026 live | swings at in-zone pitches / in-zone pitches | +4.50 pp | Medium-Low | **WATCH** |
| Whiff/swing | 27.39% | ~21.0% | 2026 live | misses / swings | +6.39 pp, +30.4% | Medium-Low | **FAIL/WATCH** |
| Generated-prospect Whiff/swing | 30.80% | ~21.0% | 2026 live | misses / swings | +9.80 pp, +46.7% | Medium-Low | **FAIL** |
| Contact/swing | 72.62% | about 79% (=1-whiff) | 2026 live | contacted swings / swings | -6.38 pp | Medium-Low | **FAIL/WATCH** |
| Z-Contact% | 74.64% | ~86.9% | 2026 live | contact on in-zone swings / in-zone swings | -12.26 pp | Medium-Low | **FAIL** |
| O-Contact% | 64.54% | ~60% inferred from 40% miss on out-of-zone swings | 2026 live | contact on out-of-zone swings / out-of-zone swings | +4.5 pp | Low-Medium | **WATCH** |
| SwStr% | 13.00%/pitch | matched KBO league aggregate not recovered | recent KBO | swinging strikes / all pitches | n/a | - | **OPEN** |
| Called strike% | 17.21%/pitch | matched league aggregate not recovered | recent KBO | called strikes / all pitches | n/a | - | **OPEN** |
| CSW% | 30.21%/pitch (= called + swinging strikes) | matched league aggregate not recovered | recent KBO | called + swinging strikes / all pitches | n/a | - | **OPEN** |
| First-pitch strike% | simulation direct strike result not yet exposed; first-pitch in-zone 55.10% is not the same statistic | no matched aggregate recovered | recent KBO | first pitch resulting in a strike, not merely located in zone | n/a | - | **OPEN** |
| 0-2 reached | 18.30% | no matched KBO league aggregate recovered | recent KBO | PA reaching 0-2 | n/a | - | **OPEN** |
| 3-0 reached | 4.56% | no matched KBO league aggregate recovered | recent KBO | PA reaching 3-0 | n/a | - | **OPEN** |
| 3-2 reached | 9.27% | no matched KBO league aggregate recovered | recent KBO | PA reaching 3-2 | n/a | - | **OPEN** |

### 2.2 Looking vs swinging strikeouts

No final recent league-wide KBO swinging/looking strikeout split was recovered. A 2025 KBO-attributed report through Sep. 22 gives KIA 1,128 strikeouts: 822 swinging and 306 looking. KIA's 306 looking strikeouts were **the most in the league** at that snapshot, yet the looking share was only 27.1%.

Simulation neutral strikeouts are 54.43% looking and 45.57% swinging. Even compared with a team that led the league in looking strikeouts, simulation looking-share is roughly double. Older league reporting (2014-2017) also placed looking-strikeout share around the mid-20% range. Therefore the exact contemporary league mean is still OPEN, but **54.4% looking is not supported by the evidence and is a strong FAIL signal**.

## 3. Batted-ball / power structure

Primary factual season totals use completed 2022-2025 KBO regular seasons. PA/AB/TB/SF and hit-type totals are aggregated across all 10 teams. Derived rates use the same league totals rather than averaging player rates.

### 3.1 Recent completed-season derived references

| Metric | 2022 | 2023 | 2024 | 2025 | 2022-25 arithmetic mean |
|---|---:|---:|---:|---:|---:|
| 2B/PA | 3.97% | 3.95% | 4.16% | 4.01% | **4.02%** |
| 3B/PA | 0.36% | 0.39% | 0.40% | 0.37% | **0.38%** |
| HR/PA | 1.94% | 1.64% | 2.51% | 2.13% | **2.06%** |
| XBH/H | 27.40% | 25.96% | 29.06% | 28.40% | **27.71%** |
| TB/H | 1.459 | 1.419 | 1.514 | 1.486 | **1.470** |
| ISO | .119 | .110 | .143 | .127 | **.125** |
| 2B share among non-HR hits | 18.95% | 18.44% | 19.06% | 19.28% | **18.93%** |
| 3B share among non-HR hits | 1.73% | 1.84% | 1.83% | 1.79% | **1.80%** |
| Approx HR/BIP* | 2.84% | 2.38% | 3.74% | 3.20% | **3.04%** |

`*` Approximate KBO HR/BIP uses `HR / (AB - SO - HR + SF)`. Use only when the simulation BIP denominator is confirmed identical.

### 3.2 Simulation comparison

| Metric | Simulation | KBO ref | Difference | Confidence | Status | Comment |
|---|---:|---:|---:|---|---|---|
| 2B/PA | 3.892% | 4.02% | -0.13 pp / -3.2% | High | **PASS** | doubles frequency is close |
| 3B/PA | 0.193% | 0.38% | -0.19 pp / -49.2% | High | **FAIL** | clear triples shortage |
| HR/PA | 2.713% | 2.06% | +0.65 pp / +31.7% | High | **FAIL** | direct denominator match |
| XBH/H | 28.593% | 27.71% | +0.88 pp / +3.2% | High | **PASS** | total XBH share is close despite composition mismatch |
| TB/H | 1.522 | 1.470 | +3.6% | High | **WATCH** | hit value skewed upward by HR mix |
| ISO | .1354 | .1248 | +8.5% | High | **WATCH** | recent KBO range includes 2024 .143, but simulation is power-heavy relative to four-year center |
| HR/BIP | 3.872% | ~3.04% | ~+27% if denominator is identical | Medium | **WATCH/FAIL** | confirm BIP definition before locking comparison |

### 3.3 Deep-air-ball to HR conversion

The simulation reports `eligible deep air ball -> HR = 26.663%`. No KBO public metric with the same eligibility rule was recovered. KBO play-by-play derived fly-ball rates cannot be used directly: their type classifier covers only roughly 70-74% of balls in play, is strongly out-heavy, and classifies essentially none of the doubles/triples. Therefore direct comparison is **OPEN**.

Closest measurable proxies are:
- league HR/PA, which is materially high in simulation;
- approximately defined HR/BIP, also directionally high;
- stadium-specific HR park factors, which show large venue variance but do not define the engine's deep-air eligibility state.

The play-by-play trend source reports completed-season approximate GB/FB shares of 51.4/44.8 (2022), 49.4/47.2 (2023), 48.2/48.3 (2024), and 50.9/46.1 (2025). These are useful for trend context only, not launch-angle-quality calibration.

## 4. HBP / GDP / SF / errors

Recent league aggregates are much stronger here.

| Metric | Simulation | KBO 2022-25 mean | Definition | Difference | Confidence | Status |
|---|---:|---:|---|---:|---|---|
| HBP/game | **0.000** | **1.044** | total both teams per actual game | -100% | High | **FAIL** |
| HBP/PA | **0.000%** | **1.33%** | HBP / league PA | -1.33 pp | High | **FAIL** |
| GDP/game | **1.029** | **1.426** | GDP by both teams per game | -27.8% | High | **FAIL/WATCH** |
| GDP/PA | ~1.33% | **1.82%** | GDP / PA | about -27% | High | **FAIL/WATCH** |
| SF/game | **0.135** | **0.655** | sacrifice flies by both teams per game | -79.4% | High | **FAIL** |
| SF/PA | ~0.175% | **0.84%** | SF / PA | about -79% | High | **FAIL** |
| Errors/game | not exposed by 05 diagnostic | **1.529** | fielding errors by both teams per game | n/a | High KBO / no sim | **OPEN** |
| Errors/team-game | not exposed | **0.764** | errors / team-game | n/a | High KBO / no sim | **OPEN** |
| ROE | not exposed | no compact league aggregate recovered | reached on error / PA or BIP | n/a | - | **OPEN** |

The KBO HBP reference is especially robust: 2022-2025 completed seasons recorded 721, 696, 783, and 806 HBP respectively. Production currently generates zero HBP despite counting-stat support.

## 5. Run conversion / runner advancement

### 5.1 Direct measurable conversion

| Metric | Simulation | KBO 2022-25 mean | Difference | Status |
|---|---:|---:|---:|---|
| R/H | 0.4426 | **0.5268** | -16.0% | **FAIL** |
| R/PA | 0.1052 | **0.1228** | -14.3% | **FAIL** |

HBP absence removes roughly **1.04 baserunners per game** relative to the recent KBO environment and about **1.33% of PA**. That is structurally meaningful, but no KBO-specific run value per HBP was adopted here, so the exact runs/game share of the deficit remains OPEN. The total R/PA gap corresponds to roughly 1.36 runs per simulation game at the simulation's 77.32 PA/game; HBP alone should not be assumed to explain that entire gap without a run-expectancy or sensitivity study.

### 5.2 Advancement metrics

No sufficiently reliable recent public KBO league aggregate was recovered for:
- first-to-third on a single;
- second-to-home on a single;
- first-to-home on a double;
- extra-base-taken rate;
- advancement on outs;
- sacrifice-fly opportunity conversion;
- league LOB/team-game under a definition aligned to the simulation.

KBO-derived public baserunning pages provide SB/SBA/CS and some derived baserunning-run measures, but not the exact base-state transition probabilities required to explain the current R/H deficit. Therefore attribution of the remaining run-conversion gap to baserunning is **OPEN**.

Recommended next 08 path: if public-use conditions permit, parse KBO play-by-play into aggregate transition probabilities only, then store the compact aggregate with source/access-date and not the raw event feed.

## 6. Park-effect evidence

KBO parks materially change scoring and home-run outcomes. A current KBO-derived run park-factor page shows a wide scoring spread, for example Daejeon around 1.206 versus Jamsil around 0.888 on a 1.000-neutral scale. Statiz-derived historical HR factors are even more variable; published 2024 references place Daegu around 1.522 and Jamsil around 0.732 for HR factor, while Statiz itself warns that event-specific single-season park factors such as HR are intrinsically unstable in a 10-team league and should be interpreted conservatively.

This means park omission is important for **team/player distributions, home-road splits, and HR tails**. It does **not** plausibly explain a +31.7% league-average HR/PA bias by itself if the simulation's no-park environment is intended to represent a neutral league average. Schedule-weighted park effects redistribute outcomes around the league mean; they do not automatically raise the league aggregate by 30% unless the base environment is anchored to a non-neutral park or the normalization itself is wrong.

## 7. Answers to the ten diagnostic questions

1. **Zone% 55.15: high?** Direct matched KBO league Zone% is unavailable. A rough value implied by the current 2026 Swing/O-Swing/Z-Swing summary is around 48%, so 55.15% looks high, but because the implied value mixes separately averaged rates this remains **OPEN/WATCH**, not a hard FAIL.
2. **Swing% 47.47: high?** Against the 2026 tracked qualified-hitter reference ~44.8%, yes, moderately high: about +2.7 pp. **WATCH**.
3. **Chase% 21.25: high or low?** Low versus current KBO ~26.7-27%. Neutral is about -5.5 pp; generated prospect 33.57% is instead too high. **Neutral WATCH; generated FAIL**.
4. **Whiff/swing 27.39 realistic?** It appears too high versus current KBO ~21%, about +30%. **FAIL/WATCH** because the KBO reference is live/secondary.
5. **Looking-K share 54.4 realistic?** No supporting evidence. A 2025 team that led KBO in looking strikeouts had only 27.1% of its strikeouts looking at the cited snapshot. Simulation is roughly double. **FAIL**.
6. **HR/PA 2.71 suggests what imbalance?** The league has almost-correct 2B rate and total XBH/H, but too few triples and too many HR. TB/H and ISO are elevated. The most defensible diagnosis is **XBH composition skewed toward HR**, not a generic shortage of doubles/triples. Direct deep-air conversion calibration remains OPEN because no definition-matched KBO metric exists.
7. **How much can HBP=0 structurally affect scoring?** Recent KBO supplies about 1.04 HBP/game and 1.33% of PA; simulation supplies none. That is a meaningful missing on-base pathway. Exact runs lost are OPEN, and HBP alone should not be claimed to explain the full ~1.36 runs/game implied R/PA gap.
8. **GDP/SF frequency match?** No. GDP is ~28% low; SF is ~79% low versus the 2022-25 league mean. **GDP FAIL/WATCH; SF FAIL**.
9. **Can park omission explain HR +30%?** **No, not as the sole league-average explanation.** Parks matter greatly for distribution and tails, but a properly normalized league schedule averages park effects around the league environment. The base HR/contact-quality path remains the higher-priority aggregate-bias suspect.
10. **Is there a KBO baserunning reference that explains run conversion?** Direct R/H and R/PA prove the conversion gap. A public, recent, definition-aligned league aggregate for first-to-third/second-to-home/XBT/advancement-on-outs was not recovered. Attribution to baserunning therefore remains **OPEN** pending play-by-play transition aggregation.

## 8. Exact handoff package

### 01 - Gameplay Engine
Evidence to review, no tuning yet:
- HBP production path is structurally absent versus KBO ~1.33% HBP/PA.
- Neutral Z-Contact 74.6% is materially below the current tracked KBO reference ~86.9%.
- Neutral looking-K share 54.4% is unsupported and far above available KBO evidence.
- HR/PA +31.7%, 3B/PA -49%, GDP about -28%, SF about -79%.
- HR is resolved before defense and without a park factor; park omission does not by itself explain the league-average HR excess.
Request: instrument PA termination and base-state transitions before changing probabilities; specifically expose first/second/third-state before/after each event, LOB, ROE, HBP, SF opportunity/conversion, GDP opportunity/conversion, and HR eligible-air-ball denominator.

### 02 - Ratings & Generation
Evidence:
- Neutral chase is low versus current KBO (~21.3 vs ~26.7), while generated prospects are high (~33.6).
- Neutral whiff is already high; generated prospects worsen it further.
Request: compare mature production-roster discipline/contact distributions, not raw prospects, against the same pitch diagnostics. Preserve engine and rating effects as separate experiments.

### 05 - Balance Lab
Request a follow-up measurement run without tuning:
- publish direct `CSW%`, true first-pitch-strike outcome%, called-strike% on takes, and whiff/swing with explicit denominators;
- expose HBP, ROE, error, LOB and base-state advancement counters;
- output GDP opportunities and SF opportunities, not only realized counts;
- separate HR decision candidates into deep-air eligible count, park-adjusted/not-adjusted state, and resolved HR;
- rerun neutral and mature-roster populations under the same seed/sample.

### 00 - Game Design HQ
No immediate constant decision is required. Cross-system decision becomes necessary only if the project chooses to add explicit park identities/effects to production or chooses a single reference target (e.g. 2025 KBO vs recent multi-year environment) for calibration.

## 9. Gate summary

- `KBO_PITCH_TRACKING_REFERENCE = PARTIAL / OPEN` — useful 2026 live secondary reference, no completed official league table recovered.
- `NEUTRAL_ZONE_RATE = OPEN_WATCH`
- `NEUTRAL_SWING_RATE = WATCH`
- `NEUTRAL_CHASE_RATE = WATCH_LOW`
- `GENERATED_CHASE_RATE = FAIL_HIGH`
- `NEUTRAL_WHIFF_RATE = FAIL_WATCH_HIGH`
- `LOOKING_K_SHARE = FAIL_HIGH`
- `KBO_XBH_STRUCTURE_REFERENCE = PASS`
- `SIM_2B_RATE = PASS`
- `SIM_3B_RATE = FAIL_LOW`
- `SIM_HR_RATE = FAIL_HIGH`
- `SIM_HBP = FAIL_MISSING`
- `SIM_GDP = FAIL_WATCH_LOW`
- `SIM_SF = FAIL_LOW`
- `RUN_CONVERSION = FAIL_LOW`
- `RUNNER_ADVANCEMENT_ATTRIBUTION = OPEN`
- `PARK_EFFECT_IMPORTANCE = PASS_FOR_DISTRIBUTION`
- `PARK_OMISSION_EXPLAINS_HR_PLUS_30 = NO`

Overall: **FAIL/WATCH with strong definition-specific findings and important OPEN tracking/runner-state gaps**.
