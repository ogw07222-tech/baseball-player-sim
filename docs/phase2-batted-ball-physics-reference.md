# Phase 2 batted-ball physics and field-position reference pack

Access date: 2026-09-11 (Asia/Seoul)

Purpose: empirical/physics reference pack for `01 - Gameplay Engine` Phase 2 Physical Batted-Ball Engine and `05 - Balance Lab` validation. Research only; no production gameplay coefficient or rating constant is changed here.

Source of truth at task start: `main@2fd299d5d3d1df9d1dc151cda9da30888efc454e`.

Status labels:
- **VERIFIED**: source and definition are strong enough for direct reference use.
- **PARTIAL**: useful reference exists but league, season, definition, coverage, or transferability is incomplete.
- **OPEN**: no suitable source/value recovered; do not fabricate.

## REFERENCE_STATUS

| Reference lane | Status | Summary |
|---|---|---|
| KBO league-wide batted-ball EV distribution | OPEN | no official/public completed-season league mean/percentile pack recovered |
| KBO league-wide launch-angle distribution | OPEN | no definition-aligned public tracking distribution recovered |
| KBO recent hit-type environment | VERIFIED | completed 2022-2025 KBO-sourced league totals support 2B/3B/HR/XBH targets |
| KBO park geometry | PARTIAL | several parks have official dimensions; full wall polygons/heights are incomplete |
| MLB Statcast EV/LA reference | VERIFIED as MLB-only | official Baseball Savant league aggregate and glossary definitions available |
| Spray/timing physics | PARTIAL | MLB/peer-reviewed structural evidence exists; KBO league-wide distribution not recovered |
| Fair/foul reference | OPEN/PARTIAL | no compact recent KBO league rate; MLB pitch-level public data can derive it but no aggregate retained here |
| Ball-flight physics | VERIFIED structure | gravity + quadratic drag + spin lift are established baseball-flight terms |
| Defensive reach structure | VERIFIED as MLB-only | Statcast Sprint Speed, Jump and Catch Probability definitions available; KBO equivalent unavailable |

## KBO_REFERENCES

### 1. Exit velocity and launch angle

KBO officially adopted TrackMan as the pitch-velocity measurement system from 2025, but the public KBO material recovered in this research does not provide a completed-season league distribution for **batted-ball** exit velocity, launch angle, hard-hit rate, or EV percentiles. Therefore:

- KBO mean EV: **OPEN**
- KBO EV SD/P10/P25/P50/P75/P90/P95: **OPEN**
- KBO hard-hit threshold/rate: **OPEN**
- KBO GB/LD/FB EV: **OPEN**
- KBO HR EV distribution: **OPEN**
- KBO hit-vs-out EV distribution: **OPEN**
- KBO launch-angle mean/distribution: **OPEN**

Do not substitute MLB EV/LA values as KBO calibration truth. They are retained below as physics/measurement sanity references only.

### 2. Completed KBO hit-type / power reference

Completed regular seasons 2022-2025, all 10 teams, using the project’s previously audited KBO-sourced league aggregates:

| Metric | 2022-2025 recent center | Definition | Confidence | Phase 2 use |
|---|---:|---|---|---|
| 2B/PA | ~4.02% | doubles / PA | High | league outcome validation |
| 3B/PA | ~0.38% | triples / PA | High | deep-gap/runner-speed/park validation |
| HR/PA | ~2.06% | HR / PA | High | wall-cross outcome validation |
| XBH/H | ~27.71% | (2B+3B+HR)/H | High | hit-type mix |
| TB/H | ~1.470 | total bases / hits | High | hit-value composition |
| ISO | ~.125 | SLG-AVG | High | power environment |
| approximate HR/BIP | ~3.04% | HR/(AB-SO-HR+SF) | Medium | use only with identical BIP definition |

Known pre-Phase-2 simulation comparison from 05 diagnostic:
- 2B/PA 3.892%: near KBO center.
- 3B/PA .193%: about half the recent KBO level.
- HR/PA 2.713%: about 31.7% above recent KBO center.
- XBH/H 28.593%: close overall, implying a composition problem rather than generic XBH shortage.

For Phase 2, validation should therefore focus on **where the ball lands/crosses the wall** rather than only matching aggregate XBH.

### 3. KBO batted-ball type proxy

A public KBO play-by-play-derived trend source reports approximate 2022-2025 GB/FB shares around:
- 2022: GB 51.4%, FB 44.8%
- 2023: GB 49.4%, FB 47.2%
- 2024: GB 48.2%, FB 48.3%
- 2025: GB 50.9%, FB 46.1%

**PARTIAL only.** The source itself notes incomplete batted-ball type coverage (~70-74%), strong out bias, and poor representation of doubles/triples. These figures are trend context, not launch-angle calibration truth.

### 4. Park effect context

Prior audited KBO-derived references show large stadium differences. Examples include run-factor spreads roughly from Daejeon ~1.206 to Jamsil ~0.888 in a current KBO-derived park-factor view; event-specific one-season HR factors can be much wider and noisier.

Interpretation for Phase 2:
- Park geometry is necessary for team/player distributions and left/center/right HR tails.
- One-year event-specific park factors are too noisy to determine a physical coefficient directly.
- A neutral no-park engine cannot rely on park omission to explain the existing +31.7% league HR/PA bias.

## MLB/PHYSICS_REFERENCES

### A. MLB Statcast EV / LA — structural reference only

Official Baseball Savant league aggregate:

| Season | League | Batted balls | Avg EV | Avg LA | Hard-Hit% | Barrel% | Source status |
|---|---|---:|---:|---:|---:|---:|---|
| 2025 | MLB | 124,888 | 89.4 mph (~143.9 km/h) | 13.5° | 40.9% | 8.6% | VERIFIED MLB-only |
| 2024 | MLB | 124,203 | 88.8 mph (~142.9 km/h) | 13.3° | 38.9% | 7.8% | VERIFIED MLB-only |

Official Statcast definitions:
- **Hard-hit**: exit velocity >= 95 mph (~152.9 km/h).
- **Launch-angle sweet spot**: 8°-32°.
- Common Statcast batted-ball angle classes:
  - ground ball: <10°
  - line drive: 10°-25°
  - fly ball: 25°-50°
  - popup: >50°
- Statcast barrels are EV/LA combinations meeting minimum expected BA/SLG quality thresholds; they are not simply “hard-hit fly balls.”

Use these only for Phase 2 implementation sanity: units, expected magnitudes, classification architecture, and visualization. Do not tune KBO generation to 89.4 mph or 13.5° without KBO evidence.

League-wide MLB EV percentile distribution was not extracted in this pass: **OPEN**.

### B. EV x LA outcome interaction

MLB Statcast expected metrics explicitly use batted-ball exit velocity and launch angle to estimate outcome probabilities; sprint speed can enter selected batted-ball expected-hit models. This supports a Phase 2 architecture where EV and LA are continuous physical inputs rather than preselecting HR/2B outcomes.

A useful validation surface is therefore a 2-D EV×LA outcome grid:
- out probability
- 1B/2B/3B probability after field/park resolution
- wall-cross probability
- carry distance/hang time

This is a **measurement/validation structure**, not a KBO coefficient source.

### C. Spray angle and timing

Direct KBO league-wide pull/center/opposite tracking distribution was not recovered: **OPEN**.

MLB/biomechanics structural references:
- Statcast horizontal launch direction can be represented as field vectors/sectors.
- Public spray presentations commonly divide fair territory into pull/center/opposite thirds.
- Peer-reviewed batting-timing work reports acceptable timing windows on the order of single-digit to low-double-digit milliseconds; outside pitches require later optimal contact than inside pitches.
- A 2019 experimental study reported acceptable timing error of about ±7.9 ms for fastballs and ±10.7 ms for slower/curve conditions, with outside-pitch optimal timing roughly 10 ms later than inside.
- A later biomechanical study reported substantial hitter-to-hitter variation in acceptable timing window.

Phase 2 implication: horizontal spray should plausibly depend on **timing error + pitch location + handedness/bat path**, not a single uniform random spray angle. The exact mapping remains 01/00 design-owned.

### D. Fair / foul

- KBO league contact-to-foul rate: **OPEN**.
- KBO two-strike foul rate: **OPEN**.
- KBO foul EV/contact-quality distribution: **OPEN**.
- MLB compact league aggregate not retained in this pass: **PARTIAL/DERIVABLE** from public pitch-level Statcast descriptions, but not verified here.

Phase 2 should instrument fair/foul separately, including two-strike foul survival and foul EV, but 05 should initially treat these as measurement outputs rather than hard calibration gates.

## BALL_FLIGHT_PHYSICS

Baseball-flight literature supports three material force terms for a lightweight trajectory model:

1. gravity, `g = 9.80665 m/s²`;
2. aerodynamic drag, approximately `F_D = 0.5 * C_D * rho * A * v²` opposite velocity;
3. lift/Magnus force from spin, approximately `F_L = 0.5 * C_L * rho * A * v²` perpendicular to velocity/spin geometry.

Published baseball-flight measurements cover representative batted-ball speeds around 50-110 mph and spin roughly 1500-4500 rpm. Drag and spin are large enough that vacuum projectile motion is not a reasonable baseball carry model.

A published baseball-flight example at sea-level conditions illustrates the scale: a 100 mph, 29° batted ball with 2500 rpm backspin travels roughly **397 ft** with aerodynamic effects versus roughly **571 ft** in vacuum. The exact example is not a KBO calibration target; it demonstrates the direction and magnitude of no-drag bias.

Wind can alter carry materially in the same class of model: a modest 5 mph following/head wind shifts the cited example by several percent in distance. Air density also varies with temperature, pressure, humidity, and elevation.

### Lightweight model comparison

| Candidate | Realism | Computational cost | Required inputs | Expected bias |
|---|---|---|---|---|
| 1. No-drag projectile | Very low | Minimal | EV, LA, spray, launch height | severe over-carry; wrong hang time/wall crossing |
| 2. Constant/effective drag | Medium-low | Very low | EV, LA, spray, rho, effective Cd | better carry, but misses spin-dependent lift/carry |
| 3. Drag + approximate lift | Medium-high for game use | Low | EV, LA, spray, rho, Cd, spin or lift proxy | best lightweight physical transfer across parks/weather; spin uncertainty remains |
| 4. Empirical EV/LA -> distance regression | High in source-domain average | Very low | EV, LA, optionally spray/park | weak transfer to KBO, wind, altitude, unusual spin; less physically interpretable |

## RECOMMENDED_V1_PHYSICS_MODEL

**Research recommendation, not a production formula decision:** option 3, **quadratic drag + approximate lift**, is the strongest Phase 2 V1 architecture if 01/00 want a physical engine rather than an outcome lookup.

Reasoning:
- no-drag is demonstrably too biased for wall-cross/carry;
- drag-only is usable as an implementation stepping stone but systematically omits backspin carry;
- drag+approximate lift remains cheap enough for browser/game simulation with short numerical integration;
- an empirical EV/LA distance model is valuable as a regression test/cross-check but is less transferable from MLB to KBO and across park/weather states.

Suggested architecture inputs, without choosing coefficients:
- `exit_velocity_mps`
- `launch_angle_deg`
- `spray_angle_deg`
- `launch_height_m`
- optional `spin_rpm` / `spin_axis_deg` or an explicit lift proxy
- `air_density_kg_m3`
- optional wind vector
- stadium wall geometry

For a first generic environment, standard-atmosphere sea-level density can be a documented **assumption**, not a KBO empirical value. Exact weather/elevation integration can remain optional.

## STADIUM_GEOMETRY

Current KBO uses nine unique primary 1st-team stadiums because LG and Doosan share Jamsil. Exact wall curves are not public for every venue, so scalar distances must not be invented where geometry is ambiguous.

| Stadium | LF line | LC | CF | RC | RF line | Wall height | Roof | Status / limitation |
|---|---:|---:|---:|---:|---:|---|---|---|
| Jamsil Baseball Stadium | 100 m | ~120 m | 125 m | ~120 m | 100 m | 2.6-2.7 m | Open | VERIFIED line/CF; LC/RC secondary; official wall pages differ by ~0.1 m/version |
| Gocheok Sky Dome | 99 m | OPEN | 122 m | OPEN | 99 m | 4 m | Dome | VERIFIED LF/RF/CF/wall; exact LC/RC OPEN |
| Gwangju-KIA Champions Field | 99 m | ~117 m | 121 m | ~117 m | 99 m | OPEN | Open | VERIFIED LF/RF/CF and open type; LC/RC secondary |
| Daejeon Hanwha Life Ballpark | 99 m | ~115 m | ~122 m | ~112 m | 95 m | generally 2.4 m; 8 m Monster Wall sector | Open | LF/RF and Monster Wall VERIFIED; interior radial distances secondary/approx |
| Suwon KT Wiz Park | ~98 m | ~115 m | ~120 m | ~115 m | ~98 m | ~4 m | Open | detailed geometry APPROXIMATED; club material only verifies broad 95-120 m extent |
| Daegu Samsung Lions Park | ~99.5 m | geometry-dependent | ~122.5 m | geometry-dependent | ~99.5 m | ~3.6 m | Open | APPROXIMATED; polygon/straight-wall geometry makes LC/RC scalar ambiguous |
| Changwon NC Park | ~101 m | ~123 m | ~122 m | ~123 m | ~101 m | ~3.3 m | Open | APPROXIMATED; secondary geometry terminology differs |
| Sajik Baseball Stadium | ~95.8 m | ~113 m | ~121 m | ~113 m | ~95.8 m | variable ~4.8-6 m | Open | APPROXIMATED; wall height varies by sector |
| Incheon SSG Landers Field | ~95 m | ~115 m | ~120 m | ~115 m | ~95 m | ~2.8 m | Open | APPROXIMATED; no current official full geometry recovered |

Exact stadium elevation/altitude values were not source-verified in this pass: **OPEN**.

### Recommended stadium data structure

Do not hard-code only five radial distances. Several KBO parks are asymmetric or have variable wall height. A future-safe schema is:

```text
stadium_id
name
roof_type: open | dome | retractable
season_from / season_to
elevation_m: nullable
wall_segments[]:
  - azimuth_deg_start
  - azimuth_deg_end
  - distance_m or polygon vertices
  - height_m
  - source_status: verified | approximated
foul_boundary / playable_polygon: optional
source_metadata[]
```

For Phase 2 V1, a generic symmetric stadium is defensible if the physics/stadium interfaces are already shaped for piecewise wall geometry.

## DEFENSE_REFERENCES

KBO public Statcast-like defensive tracking for reaction/route/catch probability was not recovered: **OPEN for KBO**.

MLB Statcast offers a useful structural model:
- **Sprint Speed**: top speed in the fastest one-second window of qualified competitive runs; MLB average is about **27 ft/s**, with roughly 23 ft/s slow to 30+ ft/s elite context.
- **Jump**: feet covered in the correct direction during the first three seconds after pitch release.
  - Reaction: movement over first ~1.5 s.
  - Burst: movement over next ~1.5 s.
  - Route component: direction/efficiency relative to required path.
- **Catch Probability**: modeled from opportunity time, distance required, direction, and modern versions also account for wall proximity/context.

Important limitation: MLB Sprint Speed is not directly a KBO outfielder coefficient and is not identical to first-step fielding speed. Use it only as a physical magnitude/architecture prior.

Recommended Phase 2 defensive measurement interface:
- fielder start `(x,y)`
- reaction delay
- acceleration/burst
- max running speed
- route efficiency / path multiplier
- ball hang time
- distance-to-intercept
- wall proximity
- catch opportunity probability/output

The production mapping from ratings to those quantities belongs to 01/02/00, not this research pack.

## PHASE2_VALIDATION_TARGETS

### Batted-ball level

05 should record at minimum:
- EV mean, SD, P10/P25/P50/P75/P90/P95/P99
- LA mean, SD and histogram/buckets
- GB/LD/FB/PU share under a declared LA definition
- spray-angle mean/distribution by batter handedness and pull/center/oppo sectors
- fair/foul rate; two-strike foul rate
- trajectory carry distance and total/landing distance
- hang time
- apex height if cheap to expose
- landing `(x,y)` / radial depth
- wall-cross flag, crossing height, wall sector
- trajectory exit reason: caught / landed fair / foul / wall / HR

### PA/game level

Maintain matched KBO validation metrics:
- BIP
- GB/LD/FB/PU
- 1B, 2B, 3B, HR
- HR/PA
- HR/BIP under explicit denominator
- 3B/PA
- 2B/PA
- XBH/H
- TB/H
- BABIP
- SLG / ISO
- runs/game and R/H

### Defense

Measure:
- balls classified physically reachable / catchable
- catch conversion among catchable balls
- outcome by hang-time x required-distance bucket
- outcome by LF/LC/CF/RC/RF sector
- fielder route distance and time-to-intercept
- wall-adjacent catch conversion separately

### Park

Measure:
- wall-cross rate overall and per BIP
- HR by pull/center/opposite sector and L/C/R wall sectors
- wall-cross EV/LA/spray distributions
- warning-track/deep-out landing distribution
- park-specific 2B/3B/HR mix
- generic-park vs real-park aggregate sensitivity

### Cross-league sanity only

If MLB comparison is used, keep a separate namespace such as `MLB_SANITY_*`. Do not mix MLB 89.4 mph EV or 13.5° LA into KBO pass/fail gates until a KBO-equivalent source exists.

## DATA_GAPS

High-priority OPEN items:
1. completed-season KBO batted-ball EV mean/SD/percentiles;
2. completed-season KBO launch-angle distribution and EV×LA outcome map;
3. KBO spray pull/center/opposite distribution by handedness;
4. KBO fair/foul and two-strike foul rates;
5. KBO batted-ball spin/backspin distribution;
6. exact current wall polygons/heights for several parks;
7. exact stadium elevations/environment metadata;
8. KBO player-tracking defense (reaction, route, sprint/catch probability);
9. KBO base hit/out probability surface by EV/LA/location.

These gaps should stay OPEN rather than being filled by MLB values without a league label.

## HANDOFF_TO_01

Reference package for Physical Batted-Ball Engine design:
- Use continuous EV/LA/spray outputs before hit-type resolution.
- Keep trajectory generation separate from park-wall and defensive resolution.
- Preserve explicit fair/foul and wall-cross states.
- Do not predeclare HR before defense/park geometry; Phase 2 validation needs the wall-cross path to be observable.
- Architect for piecewise/asymmetric wall geometry rather than only a single fence distance.
- Research-preferred V1 flight model is drag + approximate lift; coefficient choice and simplification belong to 01/00.
- Allow defense to consume hang time, landing/intercept location, required distance, wall context and fielder movement state.

No production constant changes are authorized by this document.

## HANDOFF_TO_05

After Phase 2 implementation, run a physics-first validation before overall run tuning:
1. deterministic single-BIP trajectory tests across an EV/LA/spray matrix;
2. conservation/monotonic sanity: greater EV should not systematically reduce vacuum-equivalent range under otherwise identical states; wall crossing must be geometry-consistent;
3. neutral generic-park Monte Carlo for EV/LA/spray/distance/hang-time distributions;
4. full-game 10k for 2B/3B/HR/BABIP/runs and current Phase 1 regression metrics;
5. park sensitivity runs using at least Jamsil-like large geometry and a smaller/higher-HR geometry;
6. defensive catchability matrix by hang time and distance;
7. keep KBO outcome gates separate from MLB physical-sanity references.

Priority KBO Phase 2 outcome gates remain: 2B/PA ~4.02%, 3B/PA ~0.38%, HR/PA ~2.06%, XBH/H ~27.71%, plus the already established broader run environment. EV/LA numerical KBO gates remain OPEN pending better public tracking data.
