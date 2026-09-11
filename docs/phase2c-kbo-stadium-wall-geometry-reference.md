# Phase 2C KBO stadium geometry and wall reference

Access date: 2026-09-12 (Asia/Seoul)

Purpose: research/reference pack for `01 - Gameplay Engine` Phase 2C stadium-wall resolution and `05 - Balance Lab` validation. Research only; no production gameplay formula, HR coefficient, park factor, or trajectory coefficient is changed here.

Task-start source of truth: `main@39aa1f1d619ad1a4d3b4595d3b3aa6e6e6fdb2ca`.

Status labels:
- **VERIFIED**: official club/KBO/municipal/facility source directly supports the value.
- **APPROXIMATED**: reputable secondary/reference source supports the value, but no matching primary source was recovered.
- **CONFLICTING**: credible sources disagree; do not silently average.
- **UNAVAILABLE**: no sufficiently reliable value recovered.

## REFERENCE_STATUS

| Lane | Status | Summary |
|---|---|---|
| 2026 KBO primary home-stadium set | VERIFIED | KBO 2026 schedule/current games confirm the nine primary venues listed below; LG/Doosan share Jamsil |
| LF/RF/CF anchors | VERIFIED/PARTIAL | primary-source coverage is strong for Jamsil, Gocheok, Gwangju, Daejeon endpoints; secondary for several other parks |
| Power-alley anchors | PARTIAL | several parks lack official LC/RC dimensions; do not invent missing anchors |
| Wall heights | PARTIAL/CONFLICTING | strong for Gocheok/Daejeon; secondary for several others; Jamsil has current 2.6 m vs older official 2.7 m conflict |
| Roof/open classification | VERIFIED/PARTIAL | Gocheok dome; other primary parks open-air |
| Stadium altitude | OPEN | no stadium-by-stadium authoritative elevation pack recovered in this pass |
| O(1) radial wall model | RESEARCH-READY | fixed-sector piecewise interpolation is adequate for Phase 2C V1 |

---

## CURRENT_KBO_STADIUMS

KBO's 2026 regular-season schedule and current attendance/game pages confirm these primary venues in active first-team use:

- LG Twins / Doosan Bears — **Jamsil Baseball Stadium**
- Kiwoom Heroes — **Gocheok Sky Dome**
- SSG Landers — **Incheon SSG Landers Field (Munhak)**
- KT Wiz — **Suwon KT Wiz Park**
- Hanwha Eagles — **Daejeon Hanwha Life Ballpark**
- Samsung Lions — **Daegu Samsung Lions Park**
- KIA Tigers — **Gwangju-KIA Champions Field**
- Lotte Giants — **Sajik Baseball Stadium**
- NC Dinos — **Changwon NC Park**

2026 is the final regular-season year at the current Jamsil Baseball Stadium before the planned temporary venue transition from 2027. Phase 2C data therefore should be season-versioned rather than assuming stadium geometry is timeless.

---

## GEOMETRY_TABLE

Distances are home plate to outfield wall, metres. `LF/LC/CF/RC/RF` means left foul line / left-center / center / right-center / right foul line.

| Stadium | LF | LC | CF | RC | RF | Roof | Quality / notes |
|---|---:|---:|---:|---:|---:|---|---|
| Jamsil | **100** | UNAVAILABLE | **125** | UNAVAILABLE | **100** | Open | LF/CF/RF VERIFIED by Seoul Metropolitan Government; power alleys not source-verified here |
| Gocheok Sky Dome | **99** | UNAVAILABLE | **122** | UNAVAILABLE | **99** | Dome | LF/CF/RF VERIFIED by Kiwoom/Seoul; no reliable LC/RC published in primary source recovered |
| Incheon SSG Landers Field | **95** | **115** | **120** | **115** | **95** | Open | APPROXIMATED from stable secondary references; KBO confirms venue/current use |
| Suwon KT Wiz Park | **98** | **115** | **120** | **115** | **98** | Open | LF/CF/RF supported by trusted sports reporting; LC/RC secondary -> APPROXIMATED |
| Daejeon Hanwha Life Ballpark | **99** | **115** | **122** | **112** | **95** | Open | LF/RF VERIFIED by Daejeon City; 5-anchor polygon widely reported by reputable sports media -> LC/CF/RC APPROXIMATED pending primary plan drawing |
| Daegu Samsung Lions Park | **99.5** | geometry-dependent | **122.5** | geometry-dependent | **99.5** | Open | LF/CF/RF APPROXIMATED; octagonal/straight-segment shape means one scalar LC/RC is definition-sensitive; secondary sources conflict between ~107 m and ~123.4 m labels depending on anchor convention |
| Gwangju-KIA Champions Field | **99** | UNAVAILABLE | **121** | UNAVAILABLE | **99** | Open | LF/CF/RF VERIFIED by KIA club; power alleys unavailable |
| Sajik Baseball Stadium | **95.8** | **113** | **121** | **113** | **95.8** | Open | APPROXIMATED from stable secondary geometry; current primary dimension page not recovered |
| Changwon NC Park | **101.2** | ~107 or sector-dependent | **122** | ~107 or sector-dependent | **101.2** | Open | LF/RF/CF supported by NCSoft/architectural feature source; detailed sector anchors are PARTIAL/APPROXIMATED |

### Geometry-specific cautions

**Daegu**
- The stadium has a distinctive polygonal/octagonal outfield.
- Secondary references expose incompatible-looking `LC/RC` values because they refer to different vertices/segments (`~107 m` vs `~123.4 m`).
- Therefore do **not** force one five-anchor tuple as VERIFIED.
- Phase 2C should use more wall anchors or a piecewise polygon for Daegu.

**Daejeon**
- It is intentionally asymmetric and pentagonal.
- Daejeon City directly confirms LF 99 m, RF 95 m, ordinary wall ~2.4 m and right-side 8 m Monster Wall.
- Reputable reporting gives the full five-anchor shape 99 / 115 / 122 / 112 / 95 m.
- This is an ideal validation park for asymmetric radial-wall logic.

**Changwon**
- Architecture source directly supports LF/RF ~101.2 m and CF 122 m.
- Secondary geometry indicates non-monotonic sector distances (some center-adjacent sectors farther than straight CF), so a simple ellipse is not sufficient if full fidelity is desired.

---

## WALL_HEIGHT_TABLE

| Stadium | Wall height | Quality | Notes |
|---|---|---|---|
| Jamsil | **2.6-2.7 m** | **CONFLICTING** | 2026 Yonhap reports 2.6 m; older Seoul official Gocheok-comparison page says Jamsil 2.7 m. Store source-versioned value/range until direct current facility measurement is recovered. |
| Gocheok | **4.0 m** | **VERIFIED** | Kiwoom official stadium guide and Seoul source agree. |
| Incheon SSG | **2.8 m** | **APPROXIMATED** | stable secondary reference; current official value not recovered. |
| Suwon KT | **4.0 m** | **APPROXIMATED** | trusted sports reporting + secondary references agree. |
| Daejeon | **2.4 m ordinary; 8.0 m Monster Wall sector** | **VERIFIED/PARTIAL sector map** | Daejeon City confirms 2.4 m ordinary wall and 8 m right-side Monster Wall. Exact angular start/end of 8 m sector not source-verified here; reputable media reports Monster Wall width ~32 m. |
| Daegu | **~3.6 m** | **APPROXIMATED** | consistent secondary reference; primary wall-height source not recovered. |
| Gwangju | UNAVAILABLE | **UNAVAILABLE** | club official page gives distances but not wall height in recovered content. |
| Sajik | **~6.0 m** | **APPROXIMATED** | stable secondary current-stadium reference; historical renovations make versioning important. |
| Changwon | **~3.3 m** | **APPROXIMATED** | consistent secondary reference; primary architecture source recovered for dimensions but not wall height. |

`altitude_m` for all nine parks: **UNAVAILABLE in this pack**. Phase 2B neutral atmosphere should continue to use its documented generic state until a separate elevation/weather pack is built.

---

## DATA_QUALITY

### Strongest primary references

1. **KBO 2026 regular-season schedule/current attendance**
   - Confirms current first-team venues and 2026 usage.
   - Reliability: High.
   - Does not supply geometry.

2. **Seoul Metropolitan Government — Jamsil archive/facility pages**
   - Jamsil LF/RF 100 m, CF 125 m.
   - Reliability: High.
   - Wall height conflict exists between older city comparison material (2.7 m) and 2026 reporting (2.6 m).

3. **Kiwoom Heroes official — Gocheok stadium guide**
   - LF/RF 99 m, CF 122 m, wall 4 m.
   - Reliability: High.

4. **KIA Tigers official — Champions Field guide**
   - LF/RF 99 m, CF 121 m, open-air classification.
   - Reliability: High.

5. **Daejeon Metropolitan City — Daejeon Hanwha Life Ballpark feature/press materials**
   - Asymmetric field; LF 99 m, RF 95 m, ordinary wall 2.4 m, 8 m Monster Wall.
   - Reliability: High.
   - Full 5-anchor values rely on reputable sports media until an official plan/drawing is recovered.

6. **NCSoft/architectural feature — Changwon NC Park**
   - LF/RF about 101.2 m, CF 122 m.
   - Reliability: Medium-High for dimensions.

### Secondary-only values

Incheon, Suwon LC/RC, Daegu detailed polygon, Sajik detailed geometry, several wall heights remain `APPROXIMATED`. They are adequate for test fixtures but should not be labeled `verified_kbo_geometry=true` in a canonical data file.

---

## GENERIC_STADIUM_REFERENCE

Phase 2C implementation should not be blocked by incomplete KBO geometry.

Recommended **GENERIC_ENGINEERING_BASELINE** — explicitly *not* a measured KBO mean:

```text
name: generic_neutral_v1
LF_line: 100 m
LF_power_alley: 115 m
CF: 122 m
RF_power_alley: 115 m
RF_line: 100 m
wall_height: 3.0 m
roof_type: open
altitude_m: null / neutral-atmosphere handled by Phase 2B
```

Rationale:
- values sit inside the broad envelope of active KBO parks;
- they produce a useful neutral test shape;
- symmetry makes mirror-invariant validation straightforward;
- no claim is made that these are arithmetic KBO averages.

The generic stadium should carry metadata such as:

```text
source_status = GENERIC_ENGINEERING_BASELINE
is_real_stadium = false
calibration_authority = none
```

---

## RECOMMENDED_RADIAL_MODEL

### Recommendation: fixed angular anchors + piecewise-linear interpolation

For Phase 2C V1:

```text
wall_anchor[] = {
  spray_angle_deg,
  radius_m,
  height_m,
  source_status
}
```

Use a small fixed set of sorted anchors and fixed-sector dispatch.

### Standard simple park

Five anchors are enough for a symmetric/regular test park:

```text
-45 deg  LF line
-22.5    LF/LC power alley
  0      CF
+22.5    RC/RF power alley
+45      RF line
```

`wall_distance(theta)` and `wall_height(theta)` are obtained by linear interpolation between the two enclosing fixed anchors.

Runtime cost:
- fixed branch/switch;
- a handful of multiplies/adds;
- **O(1)**;
- no loops required if a fixed maximum sector count is compiled into the park object.

### Complex parks

Use **7-9 anchors** where shape/height changes matter:
- Daejeon: extra anchors at Monster Wall start/end and pentagon vertices.
- Daegu: extra anchors at polygon corners; do not compress conflicting LC/RC conventions into one point.
- Changwon: extra anchors around center-adjacent bulges if source geometry is later verified.

With a fixed per-stadium anchor count cap, runtime remains O(1). Precompute sector boundaries/index mapping when loading the stadium; a BIP should not scan the anchor array.

### Why not a single ellipse/parabola?

A smooth symmetric curve cannot faithfully represent:
- Daejeon's asymmetric 95 m RF + 8 m wall;
- Daegu's polygonal outfield;
- variable wall heights.

Piecewise-linear radial geometry is both faster and more faithful to published dimensions.

---

## WALL_INTERSECTION_REQUIREMENTS

### Stadium-side minimum

```text
wall_radius_m(theta)
wall_height_m(theta)
fair_angle_min_deg
fair_angle_max_deg
```

Optional later:
- pole height;
- wall-top rail thickness;
- ground-rule sectors;
- bullpen/opening geometry.

### Trajectory-side minimum

`carry_distance` and `apex_height` alone are **not sufficient** to determine wall clearance uniquely.

Phase 2B/2C needs one of:

1. an O(1) callable/coefficients for `height_at_horizontal_distance(r)`; or
2. a small closed-form trajectory-shape descriptor, e.g. polynomial/normalized arc coefficients; or
3. an offline lookup that directly returns `height_at_radius` for requested radius buckets/interpolated state.

Recommended contract:

```text
trajectory:
  carry_distance_m
  hang_time_s
  apex_height_m
  horizontal_height_coefficients  # fixed-size O(1) representation

stadium:
  wall_radius_m(theta)
  wall_height_m(theta)
```

Decision:

```text
if not fair_angle(theta):
    physical_hr = false  # authoritative fair/foul migration is a separate gate
elif carry_distance < wall_radius:
    result = lands_before_wall
else:
    h_wall = height_at_horizontal_distance(wall_radius)
    if h_wall > wall_height:
        result = wall_clear / potential_HR
    else:
        result = wall_contact_or_in_play
```

Equality/tolerance at the wall top should be a deterministic numerical-policy decision owned by 01, not inferred from research data.

### Key invariant

A ball may have `carry_distance > wall_radius` in an unconstrained open-field trajectory yet **fail to be a HR** if its modeled height at the wall is below the wall top. Phase 2C must not reduce HR logic to `carry > wall_distance` alone.

---

## FOUL_POLE_AND_LINES

For a home-plate coordinate system with straight center field at `0 deg`, the two foul lines are geometrically separated by 90 degrees; using:

```text
LF line = -45 deg
CF      =   0 deg
RF line = +45 deg
```

is a natural coordinate convention.

The wall model should anchor the foul poles at those endpoints and only interpolate the **outfield wall** inside that angular domain.

Important separation:
- Phase 2C geometry may provide authoritative physical foul-line/pole coordinates.
- This research does **not** automatically authorize migration of the existing Phase 2A fair/foul shadow path.
- `FAIR_FOUL_AUTHORITATIVE_MIGRATION` remains a separate 01/00 integration decision.

Near-pole HR/foul classification should eventually be determined from the physical horizontal direction relative to the foul line/pole, not from empirical park factor.

---

## PARK_FACTOR_SEPARATION

### Physical geometry layer

Phase 2C should own:
- wall radius as function of spray angle;
- wall height as function of spray angle;
- roof/open metadata where useful;
- foul-pole/fair-boundary geometry.

### Empirical park-factor layer

Park factor is broader and includes effects not encoded by wall geometry:
- air density / elevation / temperature;
- prevailing wind;
- batter eye/background;
- foul territory;
- playing surface;
- historical roster/opponent/schedule context;
- statistical noise.

Therefore:

**geometry should be implemented first; empirical park factor should remain a separate later calibration/correction layer.**

Do not multiply a geometry-based HR probability by an empirical HR park factor inside the same initial physical decision without a double-counting audit.

---

## PHASE2C_VALIDATION_TARGETS

05 should measure at minimum:

### Physical wall outcomes
- `wall_reached / fair_air_BIP`
- `wall_clear / wall_reached`
- `wall_contact / wall_reached`
- `lands_before_wall / fair_air_BIP`
- near-wall non-HR count (`landing/carry within e.g. configurable 0-5 m of wall`)
- no `physical_HR` with `height_at_wall <= wall_height`.

### Spray sectors
- HR rate by fixed sectors: LF line / LF alley / CF / RF alley / RF line.
- wall-contact rate by sector.
- wall-clearance margin distribution `(height_at_wall - wall_height)`.
- corner vs CF HR rate under identical EV/LA test inputs.

### Park comparison
- generic neutral vs Jamsil-like large park.
- generic neutral vs Daejeon asymmetric park.
- identical BIP corpus replayed through all parks.
- park-to-park HR ratio and wall-contact ratio.

Do **not** interpret geometry-only park-to-park ratios as full empirical park factors.

### Sensitivity/invariants
- +1 m / +2 m wall-height sensitivity.
- +/-5 m radius sensitivity by sector.
- left/right mirror symmetry in generic symmetric park.
- Daejeon asymmetry must survive handedness-independent trajectory replay; mirror only when the stadium itself is mirrored in a dedicated test fixture.
- exact foul-line angles should map to pole boundary deterministically.
- no NaN/Inf/negative wall distance or height.

---

## DATA_GAPS

1. Official/current LC/RC anchors for Jamsil, Gocheok, Gwangju.
2. Primary-source full geometry for Incheon, Suwon, Daegu, Sajik, Changwon.
3. Current sector-specific wall-height maps for all parks.
4. Exact Daejeon Monster Wall angular start/end or CAD/polygon vertices.
5. Current Daegu polygon vertices under a single coordinate convention.
6. Stadium elevations.
7. Foul-pole heights and unusual ground-rule sectors.
8. Season-version history for renovations, especially Sajik and future Jamsil replacement.

These gaps do not block Phase 2C V1 because generic geometry plus verified/partial anchors are sufficient to validate the wall-resolution architecture.

---

## HANDOFF_TO_01

### Implementation prior

- Use a **season-versioned stadium object**.
- Runtime wall geometry should be fixed-anchor, piecewise-linear and O(1).
- Five anchors are enough for generic/simple parks; support up to ~7-9 fixed anchors for Daejeon/Daegu/Changwon.
- Precompute fixed sector dispatch; no per-BIP anchor scan is necessary.
- Store wall height independently from wall radius.
- Require an O(1) `height_at_horizontal_distance(r)` trajectory contract from Phase 2B; `carry + apex` alone is insufficient.
- HR physical gate must require both wall reach and wall clearance.
- Keep geometry separate from empirical park-factor correction.

### Data-policy prior

Each real-stadium field should preserve:

```text
value
source_status: VERIFIED | APPROXIMATED | CONFLICTING | UNAVAILABLE
source_name
source_date/access_date
season_from/season_to
```

Do not silently replace unavailable real values with the generic baseline. Generic fallback must remain explicitly labeled.

### No automatic fair/foul migration

The stadium model may expose `fair_angle_min/max` and foul-pole endpoints, but changing Phase 2A fair/foul authority is a separate integration task.

---

## HANDOFF_TO_05

Build three canonical validation fixtures first:

1. **GENERIC_NEUTRAL_V1** — symmetric 100/115/122/115/100 m, 3 m wall.
2. **JAMSIL_LIKE** — 100/125/100 large-radius test park; wall-height range tested at 2.6 and 2.7 m until conflict is resolved.
3. **DAEJEON_ASYMMETRIC** — 99/115/122/112/95 m with 2.4 m wall and an 8 m right-side high-wall sector fixture.

Replay an identical deterministic BIP corpus through all three and report:
- physical HR count/rate;
- wall contact;
- wall clearance margins;
- HR by spray sector;
- near-wall non-HR;
- sensitivity to wall height/radius;
- impossible-HR invariant count.

Only after these physics invariants pass should 05 compare resulting HR/PA against the recent KBO league outcome target.

Overall gate:

**`PHASE2C_KBO_STADIUM_GEOMETRY_REFERENCE = PARTIAL_BUT_IMPLEMENTATION_READY_WITH_QUALITY_FLAGS`**.
