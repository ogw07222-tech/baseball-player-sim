# Phase 2A EV / Launch Angle / Timing / Spray / Fair-Foul reference pack

Access date: 2026-09-12 (Asia/Seoul)

Purpose: research/reference pack for `01 - Gameplay Engine` Phase 2A Physical Batted-Ball Engine and `05 - Balance Lab`. Research only; no production gameplay coefficient or rating constant is changed here.

Task-start source of truth: `main@584e5902d6187355631563fd0edb97a6e16483e9`.

Status labels:
- **VERIFIED**: strong source + clear definition; suitable for direct reference use within its league/sample.
- **PARTIAL**: useful evidence exists but league/sample/definition/coverage is incomplete.
- **QUALITATIVE_EVIDENCE**: directional/structural evidence is strong but not suitable as a scalar calibration target.
- **OPEN**: no sufficiently reliable definition-aligned reference recovered.

## REFERENCE_STATUS

| Lane | Status | Summary |
|---|---|---|
| KBO league-wide EV distribution | **OPEN/PARTIAL** | historical Sports2i/KBO tracking gives league mean examples and player-level TrackMan references, but no modern completed-season league percentile pack recovered |
| MLB EV distribution/context | **VERIFIED MLB-only** | official Baseball Savant 2025 league aggregate + hard-hit definition + observed extreme |
| KBO league-wide LA distribution | **OPEN/PARTIAL** | historical KBO tracking mean/HR-angle references exist; no modern completed-season full distribution recovered |
| MLB LA distribution/context | **VERIFIED MLB-only** | official 2025 aggregate and BBE class profile available |
| Timing -> spray | **VERIFIED structural / PARTIAL scalar** | peer-reviewed optical-motion study supports ~10 ms timing windows and later optimal contact on outside pitches |
| Pitch location -> contact point/spray | **VERIFIED structural** | experimental evidence: inside contact farther toward pitcher, outside farther toward catcher; timing and batted-ball direction are coupled |
| League spray composition | **VERIFIED MLB-only / KBO OPEN** | official Baseball Savant 2025 MLB BBE profile gives pull/straight/oppo; no matching KBO league-wide tracking aggregate recovered |
| Fair/foul league rate | **OPEN KBO / PARTIAL MLB** | Statcast exposes foul events and bat-tracking contact structure, but no compact league aggregate retained here |

---

## EV_REFERENCE

### KBO evidence

No modern public completed-season KBO league distribution for EV P10/P25/P50/P75/P90/P95, hit/out EV, GB/LD/FB EV, or HR EV distribution was recovered. Do not fabricate these.

Useful KBO-adjacent tracking evidence:

1. **Sports2i official KBO tracking, early-season league mean**
   - Source: SportsSeoul report citing Sports2i, KBO's official record company and HTS tracking.
   - Sample/context: early 2019 vs early 2020 league-wide comparison; not a full season.
   - Mean batted-ball speed reported: **135.3 km/h (2019 early sample)** and **135.6 km/h (2020 early sample)**.
   - Definition: league average batted-ball speed from Sports2i HTS; exact inclusion criteria are not reproduced in the article.
   - Confidence: **Medium** for existence/magnitude, **Low-Medium** as a modern Phase 2 calibration target.
   - Use: historical KBO plausibility anchor only.

2. **KBO TrackMan player references relayed by The Athletic / Korean media**
   - Kim Ha-seong, final KBO season 2020: mean EV **90.1 mph (~145.0 km/h)**, LA **13°**, 95+ mph share **50.4%**, max EV **108.9 mph (~175.3 km/h)**.
   - Lee Jung-hoo, KBO MVP season 2022: mean EV **88.7 mph (~142.7 km/h)**, LA **12.3°**, 95+ mph share **37.7%**, max EV **107 mph (~172.2 km/h)**.
   - These are player samples, not league averages.
   - Confidence: **Medium**; source chain is TrackMan -> analyst/media, not a direct KBO league export.
   - Use: realistic KBO-player magnitude check only.

### MLB Statcast reference — separate league

Official Baseball Savant 2025 MLB aggregate:

| Metric | 2025 MLB | Definition / sample | Status |
|---|---:|---|---|
| Batted balls | **124,888** | all tracked MLB BBE in league aggregate | VERIFIED MLB-only |
| Mean EV | **89.4 mph = 143.9 km/h** | average Statcast launch speed | VERIFIED MLB-only |
| Hard-Hit% | **40.9%** | BBE with EV >=95 mph | VERIFIED MLB-only |
| Hard-hit threshold | **95 mph = 152.9 km/h** | official Statcast definition | VERIFIED MLB-only |
| Max observed 2025 | **122.9 mph = 197.8 km/h** | Oneil Cruz, Statcast-era record | VERIFIED extreme, not central target |

Official source: Baseball Savant league page / MLB Statcast glossary.

### EV quality bands for Phase 2A sanity

These are **not KBO tuning targets**. They are broad implementation sanity bands derived from MLB Statcast definitions/observed magnitudes plus KBO player examples.

- `<60 mph / <96.6 km/h`: very weak contact region; do not forbid, but it should not dominate normal fair BBE. **LOW_CONFIDENCE numeric band**.
- `60-95 mph / 96.6-152.9 km/h`: broad ordinary-contact region. **LOW_CONFIDENCE as distribution target**.
- `>=95 mph / >=152.9 km/h`: official MLB hard-hit boundary. **VERIFIED MLB definition, PROVISIONAL outside MLB**.
- `100-110 mph / 160.9-177.0 km/h`: strong/elite game contact is common enough to appear regularly among power hitters. **MLB/KBO-player sanity region, not league quantile**.
- `>120 mph / >193 km/h`: extreme MLB tail; should be exceptionally rare. 2025 MLB maximum was 122.9 mph. **VERIFIED MLB extreme**.
- Values materially above ~123 mph should trigger `WATCH/PHYSICS_SANITY` unless future KBO evidence supports them.

No KBO EV percentile target is authorized by this pack.

---

## LA_REFERENCE

### KBO evidence

1. **2017 KBO TrackMan historical league reference**
   - Source: Chosun report citing TrackMan.
   - League mean in-play launch angle: **11.92°**.
   - League mean HR launch angle: **28.07°**.
   - Choi Jeong example: mean in-play LA 25.33°, mean HR LA 30.17°.
   - Sample definition in article is not a modern full tracking export; historical-only.
   - Confidence: **Medium** as historical KBO magnitude, **Low-Medium** for modern calibration.

2. **KBO/Sports2i individual HR examples**
   - Kang Baek-ho 2020: 11 HR sample, mean HR launch angle **27.3°**, mean HR EV **163.1 km/h**.
   - Individual HRs in the cited period include low-angle HRs around 18.8-24.1° at high EV, showing that HR outcome is an EV×LA interaction rather than a fixed LA band.
   - Confidence: **Medium**, player-only.

3. **Korean empirical barrel study, 2018-2020 data**
   - A Korean analysis summarized by Dong-A Science used 2018-2020 KBO outcomes to derive park-specific HR-barrel EV/LA zones.
   - Example home-run-type ranges reported for smaller parks: EV ~147+ km/h around 22.5-35°, with wider acceptable LA as EV increases.
   - Jamsil-like large-park reference requires materially higher EV for the same angle band.
   - Status: **PARTIAL/ANALYTICAL**, not an official KBO definition.
   - Use: strong qualitative evidence that park geometry and EV interact with LA; do not copy its thresholds directly into gameplay constants.

### MLB Statcast reference — separate league

Official Baseball Savant 2025 MLB:
- mean LA: **13.5°** over 124,888 BBE.
- launch-angle sweet spot: **8-32°** (official Statcast definition).
- league batted-ball profile: **GB 42.4%, FB 26.6%, LD 23.9%, PU 7.1%**.

Common Statcast-style class boundaries used for game/debug buckets:
- GB: `<10°`
- LD: `10-25°`
- FB: `25-50°`
- PU: `>50°`

These are MLB/Statcast classification references, not verified KBO taxonomy.

### EV x LA outcome relationship

Baseball Savant publishes hit probability broken down by exit velocity and launch angle and xBA/xwOBA models use EV+LA. This is sufficient evidence that Phase 2A should preserve EV and LA continuously and avoid mapping contact directly to `single/double/HR` before trajectory/field resolution.

Broad Phase 2A LA sanity:
- physical output may extend well below 0° and above 50°; do not clip to only fair-hit classes.
- `-30° to +70°` is a **broad engineering sanity window**, not a measured KBO distribution. **LOW_CONFIDENCE**.
- majority of ordinary competitive BBE should live in a much narrower interior region; use MLB `8-32°` only as a sweet-spot/debug region, not as a target mean.
- HR-capable LA is EV- and park-dependent; KBO evidence includes HR below 20° when EV is very high, while historical KBO mean HR LA is around high-20s.

---

## TIMING_REFERENCE

### Peer-reviewed evidence

Primary study: *Acceptable timing error at ball-bat impact for different pitches and its implications for baseball skills*, Human Movement Science 66 (2019), 26 high-school baseball players, optical 3-D motion capture, pitching machine.

Measured acceptable timing error:
- fastball 123.6 +/- 4.6 km/h: **+/-7.9 ms**.
- curveball 91.3 +/- 3.5 km/h: **+/-10.7 ms**.
- slowball 91.9 +/- 3.3 km/h: **+/-10.7 ms**.
- optimal timing for outside pitches was approximately **10 ms later** than for inside pitches.
- variation in impact location along the bat explained **38.1%** of timing-error variation (`R^2=0.381`).

Interpretation:
- timing errors relevant to directional/contact-quality outcomes are on the order of **single-digit to low-double-digit milliseconds**, not tens/hundreds of milliseconds.
- increasing pitch speed tightens the acceptable timing window.
- timing error and impact point on the bat are coupled.

Limitations:
- high-school players, not KBO/MLB professionals.
- pitching-machine setting.
- the study does **not** provide a production-ready ms->spray-degree transfer function.

Therefore timing scalar mapping is **PARTIAL**, while structural dependency is **VERIFIED**.

### Early/late contact -> spray

The same study states that impact timing strongly influences same-field vs opposite-field batted-ball direction, and outside pitches require later impact. MLB Statcast's `Attack Direction` is also explicitly a horizontal direction of bat sweet-spot travel at contact, expressed pull/oppo relative to center field.

FanGraphs analysis of Statcast bat-tracking reports attack direction vs pull rate correlation around **r=0.60** and describes the expected mechanism: contact farther out front favors pull; being behind/later favors opposite field.

Classification for Phase 2A:
- `early/out-front -> pull tendency`: **QUALITATIVE_EVIDENCE / strong**.
- `late/deeper -> opposite-field tendency`: **QUALITATIVE_EVIDENCE / strong**.
- `timing error -> exact spray degrees`: **OPEN**.
- `timing error -> exact EV penalty`: **OPEN**; the 2019 study supports worse sweet-spot impact with timing error, but not a universal scalar EV penalty.

---

## PITCH_LOCATION_TO_SPRAY

Experimental evidence supports the contact-point shift:
- 2017 college-baseball high-speed-camera study: all batters contacted inside pitches farther toward the pitcher and outside pitches farther toward the catcher.
- 2019 timing study: optimal impact for outside pitch approximately 10 ms later than inside.

This supports the Phase 2A prior:
- inside pitch -> earlier/farther-forward contact -> pull-side pressure.
- outside pitch -> later/deeper contact -> opposite-field pressure.
- handedness should mirror horizontal spray orientation.

Pitch height -> horizontal spray direction: **OPEN**. Height clearly affects bat path/LA mechanics, but no strong scalar Phase 2A horizontal-spray calibration was recovered here.

Do not encode inside=pull or outside=oppo deterministically; hitter swing path and timing can override location.

---

## SPRAY_REFERENCE

### KBO

No modern league-wide KBO TrackMan pull/center/opposite distribution with clear denominator was recovered: **OPEN**.

### MLB Statcast 2025 — sanity only

Official Baseball Savant 2025 league batted-ball profile over **124,888 BBE**:
- Pull: **39.2%**
- Straight/Center: **36.4%**
- Opposite: **24.5%**

Official 2025 BBE-type shares in the same aggregate:
- GB 42.4%
- FB 26.6%
- LD 23.9%
- PU 7.1%

The Baseball Savant batted-ball leaderboard notes that across **2022-2024**, pulled airballs were only **17.5% of all BBE but produced 66% of all HR**, demonstrating that HR spray is substantially more pull-skewed than overall BBE spray.

Use:
- a Phase 2A generator producing near-uniform thirds (~33/33/33) is not automatically absurd, but MLB reality is visibly pull-skewed and oppo-light.
- a broad MLB sanity region such as `pull 30-50%, center 25-45%, oppo 15-35%` is acceptable for implementation smoke checks only. **LOW_CONFIDENCE / MLB-derived**.
- KBO calibration must wait for KBO-specific tracking or PBP-derived spray data.

Handedness:
- use mirrored geometry by batter side.
- do not assume identical pull/oppo shares by handedness until a league split is sourced.

Hitter-type variation is real and large in Statcast team/player leaderboards; spray should therefore be a distribution influenced by hitter traits/timing, not a fixed league constant.

---

## FAIR_FOUL_REFERENCE

### Availability

| Reference | KBO | MLB | Status |
|---|---|---|---|
| foul/contact | not recovered | derivable from pitch-level Statcast | KBO UNAVAILABLE / MLB PARTIAL |
| foul/swing | not recovered | derivable | KBO UNAVAILABLE / MLB PARTIAL |
| two-strike foul | not recovered | public analyses exist for specific count groups | PARTIAL |
| foul EV distribution | not recovered | no compact official league aggregate recovered | OPEN |
| hard foul existence | yes physically/observationally; no compact league rate | yes | QUALITATIVE_EVIDENCE |

Baseball Savant Statcast Search exposes distinct pitch-result categories including `Foul`, `Foul Tip`, and in-play events, so a league aggregate is reproducibly derivable if 05/08 later elect to build it.

A 2025 Pitcher List analysis reports that pitches in three-ball counts were being fouled at **23.9% of pitches** at the cited point, the highest of its pitch-tracking era series. This is **count-specific**, not a general foul/swing rate, and should not be used as a Phase 2A league target.

The existence of 100+ mph foul contact is mechanically plausible and observed in tracking/video, but no reliable compact league EV distribution for foul balls was recovered. Therefore Phase 2A must **not** cap foul EV at a low value.

Implementation implication:
- fair/foul should be a geometry/timing outcome, not synonymous with weak contact.
- two-strike fouls should preserve the PA except bunt-specific rules; exact frequency target remains OPEN.

---

## SANITY_RANGES

These are deliberately broad **implementation sanity gates**, not tuning targets.

### EV

| Check | Suggested sanity | Evidence level |
|---|---|---|
| units | internally m/s or km/h; convert explicitly | HIGH |
| central MLB reference | mean around 89.4 mph / 143.9 km/h | VERIFIED MLB-only |
| KBO historical mean anchor | ~135 km/h in early 2019-20 Sports2i samples | PARTIAL KBO |
| hard contact marker | >=95 mph / 152.9 km/h | VERIFIED MLB-only |
| elite tail | 105-115+ mph exists routinely among elite MLB/KBO power hitters | PARTIAL cross-league |
| extreme ceiling check | >123 mph should be exceptionally rare / WATCH | VERIFIED MLB extreme |

No PASS/FAIL should require the simulated KBO league mean to equal 89.4 mph.

### LA

| Check | Suggested sanity | Evidence level |
|---|---|---|
| historical KBO mean | ~11.9° (2017 historical TrackMan report) | PARTIAL KBO |
| 2025 MLB mean | 13.5° | VERIFIED MLB-only |
| MLB sweet-spot region | 8-32° | VERIFIED definition |
| historical KBO mean HR LA | ~28.1° | PARTIAL KBO |
| low-angle HR | ~19° possible at very high EV | VERIFIED KBO example |
| engineering output envelope | roughly -30° to +70° before extreme-tail WATCH | LOW_CONFIDENCE |

### Timing

- meaningful timing error scale: around **8-11 ms** in the cited controlled study.
- outside-pitch optimum: approximately **10 ms later** than inside in that study.
- use these as **order-of-magnitude sanity**, not pro-KBO coefficient targets.

### Spray

- fair-territory geometric bounds should be defined by the stadium foul lines, not an arbitrary narrower spray clamp.
- MLB 2025 overall BBE: pull 39.2 / center 36.4 / oppo 24.5.
- broad smoke-check only: pull 30-50 / center 25-45 / oppo 15-35. **LOW_CONFIDENCE, MLB-only**.
- HR should be more pull-skewed than all BBE in an MLB-like environment; 2022-24 pulled airballs produced 66% of MLB HR.

### Fair/foul

- no hard league percentage gate yet.
- Phase 2A should only enforce structural invariants: foul is geometrically outside fair territory at resolution; high-EV fouls are allowed; two-strike non-bunt foul does not terminate PA.

---

## SOURCE_QUALITY

| Source | League/sample | Season | Metric | Reliability | Limitation | Recommended use |
|---|---|---|---|---|---|---|
| Baseball Savant league Statcast | MLB, 124,888 BBE | 2025 | mean EV 89.4 mph, mean LA 13.5°, Hard-Hit 40.9%, BBE/spray profile | High | MLB, not KBO | implementation sanity and measurement definitions |
| MLB Statcast glossary / hit probability | MLB | current | EV, LA, 95 mph hard-hit, 8-32° sweet spot, EV×LA hit probability | High | league transferability | definitions/architecture |
| MLB 2025 Statcast superlatives | MLB | 2025 | max EV 122.9 mph | High | single extreme | extreme-tail guardrail |
| Sports2i via SportsSeoul | KBO early-season league | 2019-2020 | avg batted-ball speed 135.3/135.6 km/h | Medium | early season; exact denominator omitted | historical KBO magnitude only |
| KBO TrackMan via The Athletic/Korean media | KBO player samples | 2020, 2022 | mean/max EV, LA, 95+ mph share | Medium | two players; secondary chain | KBO-player magnitude sanity |
| Chosun TrackMan report | KBO league/player | 2017 | league mean LA 11.92°, mean HR LA 28.07° | Medium | old season and media summary | historical KBO LA anchor |
| Sports2i via Hankook Ilbo | KBO player HR sample | 2020 | Kang Baek-ho HR EV/LA | Medium | 11-HR player sample | EV×LA interaction example |
| Human Movement Science 2019 | 26 high-school players, optical mocap | 2019 | acceptable timing error; inside/outside optimum | High scientific / Medium transfer | non-pro, pitching machine | timing order-of-magnitude + structure |
| J-STAGE college baseball study | 4 college players, 100 swings each | 2017 | inside/outside contact position | Medium | very small sample | pitch-location structural prior |
| MLB Statcast Attack Direction + FanGraphs | MLB bat tracking | 2024-25 context | attack direction/pull relationship, r~0.60 analysis | Medium-High | analysis, not KBO | spray architecture |
| Baseball Savant Batted Ball Leaderboard | MLB | 2022-2024 / 2025 | pull-air HR concentration; BBE spray | High | MLB-only | spray/HR sanity |
| Statcast Search | MLB pitch-level | current | foul pitch-result categories | High definition | aggregate not calculated here | future foul derivation path |

---

## DATA_GAPS

Highest-priority remaining gaps:
1. modern completed-season KBO EV mean/SD/percentiles;
2. KBO EV by GB/LD/FB and hit/out/HR;
3. modern KBO LA histogram and EV×LA outcome surface;
4. KBO pull/center/oppo by handedness and hit type;
5. KBO contact->foul, swing->foul, and two-strike foul rates;
6. foul EV distribution;
7. professional-level timing-error-to-spray and timing-error-to-EV transfer functions.

None should be silently filled with MLB values.

---

## HANDOFF_TO_01

### Implementation prior — strong enough to design around now

- EV and LA must be continuous outputs, not labels chosen after the outcome.
- spray must depend at least conceptually on timing/contact point + pitch location + handedness; handedness mirrors horizontal geometry.
- outside pitch has a later/deeper optimal contact point than inside; experimental difference is ~10 ms in the cited study.
- early/out-front contact biases pull; later/deeper contact biases opposite field.
- timing error should affect both directional accuracy and barrel/sweet-spot quality, but exact coefficients remain design-owned.
- fair/foul must be geometric and must allow hard-hit fouls.
- do not pre-resolve HR/2B before EV/LA/spray/trajectory/park/defense stages.

### Provisional assumptions — allowed for Phase 2A scaffolding, not final calibration

- use MLB Statcast class definitions for debug buckets: GB<10, LD 10-25, FB 25-50, PU>50 degrees.
- use MLB 95 mph as a named `MLB_HARD_HIT_REFERENCE`, never as `KBO_HARD_HIT_THRESHOLD`.
- timing sensitivity on order of ~10 ms can guide test vectors, not production tuning.
- use generic spray distribution only as bootstrap; preserve parameters/interfaces so KBO-specific distributions can replace it.

### Future calibration only

- KBO league EV mean/SD/percentiles.
- KBO spray by handedness/hitter type.
- KBO foul rates/EV.
- exact timing-error -> degrees and timing-error -> EV penalties.

---

## HANDOFF_TO_05

Phase 2A should produce these measurements before any coefficient tuning:

### Batted-ball distributions
- EV mean, SD, min/max, P10/P25/P50/P75/P90/P95/P99.
- LA mean/median/SD and histogram; GB/LD/FB/PU under documented debug boundaries.
- EV×LA 2-D counts and outcome surface.
- max EV and >95/>100/>110/>120 mph rates, clearly labeled MLB sanity comparisons.

### Timing/spray
- timing-error histogram in ms.
- spray-angle distribution by RHB/LHB.
- pull/center/oppo shares using documented sector boundaries.
- spray by inside/middle/outside pitch bucket.
- spray by early/on-time/late timing bucket.
- EV and fair/foul rate by timing-error bucket.

### Fair/foul
- foul / swing.
- foul / contacted swing.
- two-strike foul / two-strike swing.
- foul EV mean/P50/P90/P95/max.
- fair/foul by spray angle and timing-error bucket.

### Initial judgment policy

- KBO direct scalar EV/LA/spray/foul gates: **OPEN** unless a future KBO source is added.
- MLB EV/LA/spray: **SANITY/WATCH only**, never fail a KBO model merely for differing from MLB central values.
- fail structural pathologies immediately: impossible units, EV materially above known baseball extremes at non-negligible frequency, clipped LA distribution, no handedness mirror, no timing-location effect, hard fouls impossible, or foul/fair determined independently of geometry.

Overall gate: **PHASE2A_EV_LA_TIMING_SPRAY_FAIR_FOUL_REFERENCE = PARTIAL_WITH_STRONG_STRUCTURAL_EVIDENCE_AND_OPEN_KBO_DISTRIBUTIONS**.
