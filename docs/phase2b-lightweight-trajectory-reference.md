# Phase 2B lightweight baseball trajectory reference

Access date: 2026-09-12 (Asia/Seoul)

Purpose: research/reference pack for `01 - Gameplay Engine` Physical Batted-Ball Phase 2B trajectory / hang-time / landing-position implementation and `05 - Balance Lab` validation. Research only; no production coefficient or gameplay formula is changed here.

Task-start source of truth: `main@835587210161c4f26bf433cd98ad0d92ada4cad3`.

Runtime constraints assumed by this report:
- no frame-by-frame physics;
- no runtime timestep integration;
- no iterative root solve;
- BIP cost must be O(1);
- one canonical trajectory engine for all games;
- no literal fielder movement simulation.

Status labels:
- **VERIFIED**: strong source/definition.
- **PARTIAL**: useful but condition/sample/model transfer is incomplete.
- **DERIVED**: straightforward calculation from verified physical constants/assumptions, not an empirical baseball observation.
- **OPEN**: no suitably aligned reference recovered.

## REFERENCE_STATUS

| Lane | Status | Summary |
|---|---|---|
| Baseball size/mass | VERIFIED | MLB official ball specification gives weight/circumference range |
| Gravity | VERIFIED | standard gravity 9.80665 m/s^2 |
| Standard sea-level atmosphere | VERIFIED | rho ~1.225 kg/m^3, 15 C, 101325 Pa |
| Drag importance | VERIFIED | measured/Statcast-calibrated baseball literature shows major carry reduction |
| Spin/lift importance | VERIFIED structure | Magnus/lift materially changes carry; exact batted-ball spin remains a calibration gap |
| Vacuum projectile as production model | REJECTED | severe over-carry and wrong optimum launch angle |
| Runtime numerical integration | OUT_OF_SCOPE | violates project constraints |
| O(1) EVxLA lookup/surrogate | RECOMMENDED | can be generated offline from a high-fidelity trajectory model and queried in fixed time |
| O(1) vacuum-plus-correction surrogate | RECOMMENDED_SECONDARY | transparent and fast, but requires careful cross-output calibration |
| KBO trajectory distribution | OPEN | no public KBO distance/hang/apex grid recovered |

---

## PHYSICAL_CONSTANTS

### Baseball geometry / mass

MLB Official Baseball Rules specify:
- mass: **5.00-5.25 oz = 141.75-148.84 g**;
- circumference: **9.00-9.25 in = 228.6-234.95 mm**.

If treated as a sphere, the circumference range implies diameter approximately:
- `d = C/pi` -> **72.77-74.79 mm**.

A runtime engine may use a single documented nominal mass/diameter, but the official rule provides a range rather than one exact value. A midpoint such as ~145 g and ~73.8 mm is therefore an **engineering assumption**, not an official fixed baseball constant.

### Gravity

- standard gravity: **g = 9.80665 m/s^2**.
- Source: NIST / internationally adopted standard gravity.
- Confidence: High.

### Standard atmosphere

U.S. Standard Atmosphere / NASA sea-level reference:
- density: **rho = 1.225 kg/m^3**;
- temperature: **288.15 K = 15 C**;
- pressure: **101325 Pa**;
- gravity: **9.80665 m/s^2**.

Use of fixed standard atmosphere is evaluated below.

### Typical batted-ball EV / LA context

From the Phase 2A pack:
- modern MLB central EV is around high-80s mph; 95 mph is the MLB hard-hit threshold;
- 100-110 mph contact is strong/elite but common enough to matter;
- ~120+ mph is extreme Statcast territory;
- LA classes: GB <10 deg, LD 10-25, FB 25-50, PU >50 deg (MLB Statcast convention only).

For trajectory validation, **80, 90, 100, 110 mph** cover a useful ordinary-to-elite flight grid; they are not KBO quantiles.

### Drag and lift

Baseball aerodynamic force structure:
- drag: approximately `F_D = 0.5 * rho * C_D * A * v^2`, opposite relative airflow;
- lift/Magnus: approximately `F_L = 0.5 * rho * C_L * A * v^2`, direction set by spin axis / relative flow.

Experimental literature covers baseball speeds roughly 50-110 mph and spins around 1500-4500 rpm. Recent free-flight work confirms both drag and lift depend on spin/seam state. MLB also publishes historical drag estimates because drag materially changes batted-ball distance.

Representative coefficient magnitude from recent validated CFD/experimental comparison at spin factor ~0.20:
- `C_D ~0.34`;
- `C_L ~0.216`;
with comparable experimental lift results clustered roughly 0.18-0.28 for that condition.

These are **reference magnitudes, not universal Phase 2B constants**.

---

## VACUUM_MODEL_BIAS

### Verified baseball example

Alan Nathan reference case:
- EV: **100 mph**;
- LA: **29 deg**;
- backspin: **2500 rpm**;
- launch height: **3 ft**;
- air: approximately sea level, 60 F;
- aerodynamic trajectory: **397 ft** to ground;
- vacuum trajectory with same EV/LA/height: **571 ft**.

Therefore:
- actual / vacuum carry = **0.695**;
- vacuum distance overprediction = about **174 ft**;
- vacuum relative overprediction vs aerodynamic result = about **43.8%**.

This is decisive evidence that a raw no-drag projectile is unsuitable for production wall-cross / landing distance.

### Derived vacuum grid at the same 29 deg and 3-ft launch height

Using exact no-drag projectile kinematics with `g=9.80665 m/s^2`:

| EV | Vacuum flight time | Vacuum first-ground range | Empirical/aero comparison |
|---:|---:|---:|---|
| 80 mph | 3.59 s | **368 ft** | exact real carry not assigned |
| 90 mph | 4.02 s | **465 ft** | exact real carry not assigned |
| 100 mph | 4.46 s | **572 ft** | verified aero example ~397 ft -> vacuum +44% |
| 110 mph | 4.90 s | **691 ft** | exact real carry not assigned |

`80/90/110` values above are **DERIVED VACUUM ONLY**. Do not assume a fixed 0.695 attenuation across speed because drag/lift are velocity-, spin-, and condition-dependent.

Additional real-world evidence:
- Nathan/Statcast modeling finds maximum baseball carry near ~30 deg rather than vacuum 45 deg.
- A 100 mph non-spinning trajectory series produced maximum distance around 30 deg and hang times increasing from ~2.1 s at 5 deg to ~6.6 s at 45 deg.
- MLB drag reporting gives a rule of thumb that a 0.01 change in drag coefficient shifts a 100-mph batted ball by roughly **5 ft**.

Conclusion: **VACUUM_ONLY = FAIL** for Phase 2B production distance/hang-time.

---

## MODEL_COMPARISON

| Candidate | Runtime complexity | Loops/root solve | Inputs | Realism | Numerical stability | Calibration difficulty | Season-sim suitability |
|---|---|---|---|---|---|---|---|
| A. Vacuum projectile | O(1) | none | EV, LA, launch height | **Low** | Excellent | Very easy | Fast but physically unacceptable |
| B. Empirical distance attenuation | O(1) | none | EV, LA (+ optional class) | Medium | Excellent | Medium | Excellent if only landing distance matters |
| C. Constant effective-drag approximation | O(1) only if reduced to fitted algebraic surrogate | none at runtime | EV, LA, rho, fitted drag term | Medium | Good | Medium-high | Good, but true quadratic-drag landing solve is not naturally a simple exact closed form |
| D. EVxLA -> carry/hang/apex lookup or fitted surface | **O(1)** | none | EV, LA; optional spin class/air state | **High within calibrated domain** | Excellent | Medium offline / low runtime | **Excellent** |
| E. Simplified drag+lift closed-form surrogate | O(1) if pre-fit | none | EV, LA, effective drag/lift/spin proxy | Medium-high | Good if bounded | High | Very good if carefully fitted |

### Important distinction

A high-fidelity physical model can still be used **offline** to generate reference surfaces. The project prohibition applies to runtime per-BIP stepping. Offline integration is compatible with a runtime O(1) lookup.

---

## RECOMMENDED_LIGHTWEIGHT_MODEL

### Candidate 1 — primary recommendation: offline physics surface + runtime bilinear lookup

Build a deterministic offline grid from a trusted baseball trajectory model (Nathan-style drag/lift, fixed reference atmosphere, documented spin assumption/proxy), keyed by EV and LA.

Store per grid cell:
- `carry_distance_m`;
- `hang_time_s` to first ground-level return;
- `apex_height_m`;
- optionally horizontal/vertical terminal speed at first impact.

Runtime:
1. clamp/select EV and LA cell;
2. bilinear interpolate four neighboring cells;
3. convert carry + spray into landing `(x,y)` with `sin/cos`;
4. no stepping, no loops, no root solve.

Complexity: **fixed O(1)**.

Advantages:
- inherits realistic drag/lift shape;
- preserves the real ~25-35 deg carry optimum rather than 45 deg;
- one canonical engine can serve every game;
- trivial browser/season-sim cost;
- grid can later be versioned for KBO ball/weather/spin assumptions.

Primary limitation:
- interpolation is only as good as the offline model and grid domain.

### Candidate 2 — secondary recommendation: vacuum analytical base + fitted correction surfaces

Calculate the exact vacuum quantities in O(1):
- ground-intersection time;
- range;
- vacuum apex.

Then apply bounded fitted corrections:
- `distance = vacuum_distance * f_D(EV, LA)`;
- `hang = vacuum_hang * f_T(EV, LA)`;
- `apex = vacuum_apex * f_H(EV, LA)`.

The correction functions may be low-order polynomial/rational surfaces or small lookup tables derived offline from the same high-fidelity model.

Advantages:
- transparent physical baseline;
- fixed arithmetic cost;
- especially convenient for low/negative LA ground-impact calculations.

Risk:
- independently fit distance/time/apex corrections can become mutually inconsistent unless fitted jointly.

### Recommendation rank

1. **EVxLA offline surface + bilinear interpolation** — strongest combination of fidelity, stability, runtime speed.
2. **Vacuum + joint correction surface** — strong fallback if 01 wants more analytic transparency.

Do not use raw vacuum alone.

---

## HANG_TIME_REFERENCES

Statcast definition: hang time is contact until first contact with ground/wall/fielder. Phase 2B ground-level flight time should be named distinctly if it ignores fielder/wall interception.

A published trajectory example using Alan Nathan's calculator for a **100 mph, non-spinning ball** gives:

| LA | Flight/hang time |
|---:|---:|
| 5 deg | **2.1 s** |
| 10 deg | **3.1 s** |
| 15 deg | **3.9 s** |
| 20 deg | **4.5 s** |
| 30 deg | **5.6 s** |
| 40 deg | **6.3 s** |
| 45 deg | **6.6 s** |

This is model-based, not a league distribution, but excellent for absurd-value detection.

An actual Statcast example: Cody Bellinger at Coors, EV **105.2 mph**, LA **50 deg**, hang time **6.8 s**, max height **172 ft**.

Broad Phase 2B sanity regions (not calibration targets):
- very low liner / shallow air ball: roughly **<2-3 s**;
- ordinary line-drive region: roughly **2-4.5 s** depending EV/LA;
- ordinary fly: roughly **4-6 s**;
- high fly / popup: roughly **5-8 s**;
- sustained values much above ~8-9 s should trigger WATCH unless EV/LA explicitly support a very high popup.

The category boundaries overlap intentionally; hang time is continuous and EV-dependent.

---

## DISTANCE_REFERENCES

### Realistic optimum angle

Baseball aerodynamic modeling and Statcast fitting show maximum carry around **high-20s / ~30 deg**, not vacuum 45 deg. The optimum shifts with EV, spin, and air density.

### HR-class trajectory

Reference example:
- 100 mph / 29 deg / 2500 rpm at sea-level-like conditions -> ~397 ft.

Statcast context:
- MLB home runs routinely occupy roughly 350-450 ft projected-distance territory;
- extreme Statcast HR distance record is **505 ft**.

For Phase 2B, projected carry materially above ~500-520 ft should be an extreme-tail WATCH unless supported by unusually high EV/conditions. This is MLB sanity only, not a KBO hard cap.

### Atmospheric sensitivity

Nathan/Statcast analysis around a ~401-ft fly-ball baseline reports approximate changes:
- +10 degrees temperature -> **+3.3 ft** in that analysis;
- +1000 ft elevation -> **+5.9 ft**;
- +50 percentage-point relative humidity at 750 ft -> **+0.9 ft**;
- 5 mph tailwind -> **+18.8 ft**.

Another 100 mph/29 deg example gives ~397 ft neutral, ~413 ft with 5 mph out wind, ~380 ft with 5 mph in wind.

Interpretation: wind can be large; humidity is comparatively small through air-density alone; altitude/temperature matter but can be deferred in a generic V1.

---

## APEX_REFERENCES

Statcast defines Max Height as measured/projected apex height.

Strong actual high-fly anchor:
- 105.2 mph, 50 deg Bellinger fly: **172 ft apex**, **6.8 s** hang.

No compact public league distribution of apex by BBE class was recovered: **OPEN**.

Broad Phase 2B sanity ranges, deliberately loose and MLB/physics-derived:
- low liner: approximately **<10-30 ft apex**;
- normal line drive: approximately **10-60 ft**;
- ordinary fly: approximately **40-130 ft**;
- high fly/popup: approximately **100-200+ ft**.

These overlap and are **LOW_CONFIDENCE sanity bands**, not KBO targets. A 172-ft, 50-deg Statcast fly demonstrates that >150 ft is physically ordinary for a very high fly, not necessarily an error.

Runtime validation should prefer the joint `(EV, LA, hang, apex)` surface over isolated category thresholds.

---

## GROUND_BALL_REFERENCE

Phase 2B only needs **first ground impact**. No bounce/roll/friction is required.

For low/negative LA, a useful O(1) analytical baseline is exact vacuum vertical intersection from launch height `h`:

`vy = v*sin(theta)`

`t_ground = (vy + sqrt(vy^2 + 2*g*h)) / g`

`x_ground = v*cos(theta) * t_ground`

For a 90 mph batted ball launched from 3 ft, derived no-drag examples are:
- -15 deg -> ~0.084 s, ~11 ft;
- -10 deg -> ~0.121 s, ~16 ft;
- -5 deg -> ~0.203 s, ~27 ft;
- 0 deg -> ~0.432 s, ~57 ft.

These are **DERIVED**, not empirical Statcast values.

Research assessment:
- for sharply negative LA, flight is so short that aerodynamic carry error is much less important than for deep flies;
- the analytic first-impact formula is therefore a defensible Phase 2B V1 baseline for negative/near-zero LA, especially if a bounded correction is applied near the upper end of the ground-ball range;
- do not extend this into post-impact rolling distance in Phase 2B.

---

## STANDARD_ATMOSPHERE_DECISION

### V1 decision

**YES — a fixed standard-atmosphere generic trajectory model is defensible for Phase 2B V1**, provided the limitation is explicit.

Recommended fixed reference condition:
- rho = **1.225 kg/m^3**;
- temperature = **15 C**;
- pressure = **101325 Pa**;
- no wind;
- fixed/reference spin treatment embedded in the offline surface.

### What can be omitted in V1

| Effect | V1 omission | Research judgment |
|---|---|---|
| humidity | **acceptable** | air-density effect relatively small in Nathan reference |
| stadium-specific density | **acceptable for generic engine** | needed later for park-specific realism |
| temperature | **acceptable with documented reference** | several feet of carry effect, not structural failure |
| altitude | **acceptable for generic KBO-neutral V1** | matters for park fidelity; Denver-scale differences prove it cannot be ignored forever |
| wind | **acceptable only as explicit no-wind assumption** | potentially large game-to-game distance effect; defer, do not pretend it is negligible |

This V1 should be interpreted as a **neutral-air trajectory**, not a stadium/weather simulator.

---

## PHASE2B_SANITY_RANGES

These are broad guards for 05, not coefficient targets.

### Distance
- negative LA: first impact should generally be shallow and monotonic shallower as LA becomes more negative for fixed EV;
- HR-like 100 mph / high-20s LA: order of magnitude around **400 ft**, not 570+ ft;
- ~500 ft is already extreme MLB Statcast HR territory;
- non-negligible frequency of 600+ ft realistic-air trajectories = **FAIL**.

### Hang time
- low line/near-ground air: ~0-3 s;
- line-drive region: ~2-4.5 s;
- ordinary fly: ~4-6 s;
- high fly/popup: ~5-8 s;
- >9 s recurring = **WATCH/FAIL**.

### Apex
- low liner: <~30 ft;
- LD: ~10-60 ft;
- ordinary FB: ~40-130 ft;
- high fly/popup: ~100-200+ ft;
- use joint EV/LA consistency, not category alone.

### Numerical invariants
- finite outputs for all allowed EV/LA;
- no NaN/Inf;
- distance >=0;
- hang time >=0;
- apex >= launch height for LA>0;
- for mirrored spray, carry/hang/apex identical and landing lateral coordinate sign-flipped only;
- at fixed EV near the fly-ball domain, distance should rise then fall with LA, with optimum far below vacuum 45 deg;
- at fixed LA in ordinary range, distance should generally increase with EV;
- very negative LA should produce short first-ground time/distance.

---

## DATA_GAPS

1. modern KBO batted-ball distance / hang-time / apex distributions;
2. KBO batted-ball spin distribution and spin-vs-EV/LA mapping;
3. KBO-specific baseball drag/COR comparison to MLB ball;
4. KBO park/weather atmospheric states;
5. an authoritative public empirical EVxLA->distance grid for KBO;
6. class-specific league apex distributions;
7. exact low-LA first-impact Statcast aggregate.

These gaps do not block Phase 2B architecture; they block KBO-specific fine calibration.

---

## HANDOFF_TO_01

### Implementation prior

- reject raw vacuum carry for air balls;
- maintain `EV`, `LA`, `spray`, `launch_height` as continuous physical inputs;
- use a single deterministic O(1) trajectory function for all games;
- return at least `carry_distance`, `ground_flight_time`, `apex_height`, `landing_x`, `landing_y`;
- distinguish trajectory-to-ground quantities from later wall/fielder interception metrics;
- ground/negative-LA path may use direct analytical first-impact solution;
- preserve exact left/right mirror symmetry in coordinate transform.

### Preferred runtime candidate

**Offline drag/lift trajectory grid -> runtime bilinear EVxLA lookup**.

Optional future dimensions should be architecturally possible without being required now:
- spin/lift class;
- air-density class;
- wind state.

### Secondary candidate

Vacuum closed form + joint fitted correction surfaces for distance/hang/apex.

### Do not implement

- per-BIP numerical integration;
- timestep loops;
- iterative root finding;
- vacuum-only fly-ball distance.

---

## HANDOFF_TO_05

Phase 2B validation output should include:

1. `distance_m`: mean/SD/P1/P10/P25/P50/P75/P90/P95/P99/max;
2. `hang_time_s`: same distribution;
3. `apex_height_m`: same distribution;
4. EVxLA grid for distance/hang/apex;
5. fixed-EV angle sweep demonstrating a ~high-20s/30-deg distance maximum, not 45 deg;
6. 100 mph / 29 deg reference comparison against ~397-ft aero and ~571-ft vacuum anchors;
7. low-LA first-impact grid (-15/-10/-5/0/+5/+10 deg) across representative EVs;
8. high-LA hang/apex tail checks;
9. mirror-spray test: same longitudinal carry/time/apex, opposite lateral coordinate;
10. numerical stability grid including min/max supported EV and LA.

Initial status rules:
- raw vacuum 100/29 near ~570 ft in production -> **FAIL**;
- realistic-air 100/29 order of ~400 ft -> **PASS/WATCH**, exact calibration remains model-dependent;
- max-distance angle near 45 deg -> **FAIL**;
- max-distance angle broadly high-20s/low-30s -> **PASS/WATCH**;
- recurring 600+ ft air-ball carries -> **FAIL**;
- NaN/Inf/nonmonotonic pathological grids -> **FAIL**.

Overall gate: **PHASE2B_LIGHTWEIGHT_TRAJECTORY_REFERENCE = VERIFIED_FOR_ARCHITECTURE_PARTIAL_FOR_KBO_CALIBRATION**.
