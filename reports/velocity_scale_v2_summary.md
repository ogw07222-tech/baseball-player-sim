# Velocity Scale v2 Narrow-Range Calibration

## Source / scope

- main HEAD: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- v1 publication HEAD: `e950f00df5b88f3b27ad09b3494e2b8670cb1d5f`
- v2 calibration execution HEAD: `d5da030e6c5adfc041b3631b0c1fa1bce68d7ba7`
- branch: `feature/velocity-scale-v2-calibration`
- H3.2.1 hitter formula diff: **NONE**
- Stuff / Control / Breaking calibration changes: **NONE**
- persistent inning / base-state changes: **NONE**

Final gate: **VELOCITY_SCALE_V2_READY**

## v1 -> v2 design change

v1 used raw 92 -> 146 km/h with a strong soft upper-tail compression. That made raw 160 / 200 / 250 map to roughly 159.5 / 160.7 / 161.0 km/h, so elite ratings stopped having useful physical separation.

v2 instead uses:

- narrow practical raw population;
- Velocity-specific lower generation/growth variance;
- interpretable central km/h slope;
- only mild nonlinear compression for numerical safety;
- raw 200-250 as a safety domain, not a normal KBO population domain.

## KBO provenance

Primary measurement contract remains **KBO/Sports2i PTS**.

- 2025 broad distribution snapshot: `data/kbo_velocity_distribution_2025.csv`
- scope: 119 pitchers at >=30% regulation innings
- source URL retained in every row: `https://kbo-analytics-2025.vercel.app/`
- individual role / age / max-velocity provenance: `data/kbo_velocity_reference.csv`
- Statiz-cited 2025 100+ IP starter list and KBO season-aggregate player URLs are retained row-by-row in that file.

2025 broad distribution:

- mean: **145.45 km/h**
- median: **145.30 km/h**
- SD: **3.72 km/h**
- P10 / P25 / P50 / P75 / P90 / P95: **141.36 / 143.25 / 145.30 / 147.40 / 150.42 / 151.74 km/h**

Average fastball velocity remains the primary rating anchor. Max velocity is modeled separately.

## Velocity-specific population variance patch

The baseline 120,000-snapshot diagnostic showed that mapping alone could not produce a narrow interpretable rating scale:

- starting raw SD: **14.49**
- age-28 raw SD: **17.79**
- age 20-35 mixed raw SD: **18.02**

Therefore the allowed minimal Velocity-only variance patch was applied:

- `BASE_SDS["velocity"]`: **10.0 -> 5.0**
- Velocity share of the common player offset: **1.00 -> 0.60**
- seasonal Velocity growth noise SD: **3.15 -> 1.50**

Archetype Velocity adjustments, Velocity growth mean curve, Talent effect, and all non-Velocity stat distributions remain unchanged.

After patch:

- starting 120,000 snapshots: mean **80.86**, SD **9.94**, P1/P5/P10/P25/P50/P75/P90/P95/P99 = **61 / 66 / 69 / 74 / 80 / 88 / 95 / 99 / 105**
- age-28 population: mean **95.65**, SD **11.58**, P1/P5/P10/P25/P50/P75/P90/P95/P99 = **71 / 78 / 81 / 87 / 95 / 103 / 111 / 116 / 123**
- age 20-35 mixed population: mean **91.61**, SD **12.08**
- active mixed raw >150: **0.0000%**
- active mixed raw >=200: **0.0000%**

The 20-35 mixed SD is slightly above 12 because it combines different age means; start and prime distributions satisfy the intended narrow 7-12 band. Further compression was rejected because it would unnecessarily reduce archetype separation.

## Candidate models

Three models were scored on KBO distribution fit, player-facing interpretability, elite spacing, and extreme safety.

| Model | Score | Interpretability MAE | Prime mean / SD km/h | 130->140 | 140->150 | 150->160 | raw 250 | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Linear narrow | 21.988 | .718 | 145.62 / 3.24 | 2.80 | 2.80 | 2.80 | 188.84 | REJECT: extreme unsafe |
| Piecewise mild-tail | 1.588 | .451 | 145.62 / 3.24 | 2.80 | 2.00 | 2.00 | 169.54 | PASS candidate |
| Soft mild | **1.491** | **.386** | **145.62 / 3.24** | **2.51** | **2.41** | **2.33** | **179.97** | **CHOSEN** |

## Chosen raw -> physical mapping

Chosen model: **soft mild nonlinear**

Parameters:

- reference raw rating: **97.0**
- reference physical velocity: **146.0 km/h**
- central slope parameter: **0.29 km/h per rating**
- compression scale: **500 ratings**

The compression scale is intentionally large, so the practical 70-160 region behaves close to linear and does not reproduce v1's strong saturation.

Representative mapping:

| Raw Velocity | Avg fastball km/h |
|---:|---:|
| 70 | 138.57 |
| 80 | 141.23 |
| 90 | 144.00 |
| 100 | 146.86 |
| 110 | 149.67 |
| 120 | 152.38 |
| 130 | 154.98 |
| 140 | 157.48 |
| 150 | 159.90 |
| 160 | 162.23 |
| 180 | 166.64 |
| 200 | 170.77 |
| 250 | 179.97 |

This satisfies the main player-facing requirement: a ~160 km/h average fastball is represented around raw **150**, not raw 200-250.

Elite spacing remains meaningful:

- raw 130 -> 140: **+2.51 km/h**
- raw 140 -> 150: **+2.41 km/h**
- raw 150 -> 160: **+2.33 km/h**

## KBO distribution fit

The mapping is evaluated primarily against the age-28 prime diagnostic rather than forcing high-school age-18 prospects to look like established KBO pitchers.

- KBO 2025 broad distribution: mean **145.45**, SD **3.72 km/h**
- simulated age-28 mapped population: mean **145.62**, SD **3.24 km/h**

This is within the predeclared v2 central-distribution gate of 1.0 km/h for both mean and SD.

## Physical -> gameplay contract

The three-way contract is now:

`raw Velocity -> base average fastball km/h -> effort/fatigue physical adjustment -> effective km/h -> H3 gameplay Velocity`

Neutral reference remains:

- **146.0 effective km/h -> H3 gameplay Velocity 100**

The v1 candidate **1.50 gameplay points per km/h** was retested and remains the selected v2 value.

Across the 138-162 km/h Velocity-only diagnostic, approximate mean per +1 km/h effects were:

- Contact: **-0.163 percentage points**
- Whiff: **+0.163 percentage points**
- K: **+0.120 percentage points**
- AVG: **-0.0027**
- SLG: **-0.0046**
- HR: **-0.041 percentage points**
- BB: **+0.014 percentage points**

Directions are monotonic and the BB movement is negligible Monte Carlo noise; Velocity does not alter the direct Control/zone path.

## Age distribution diagnostic

Growth mean formulas were not changed.

| Age | Raw mean / SD | Physical mean / SD | Actual band | Actual mean | Difference |
|---:|---:|---:|---|---:|---:|
| 18 | 80.80 / 9.85 | 141.50 / 2.69 | <=22 | 148.19 | -6.69 |
| 20 | 85.13 / 10.09 | 142.69 / 2.79 | <=22 | 148.19 | -5.50 |
| 22 | 89.49 / 10.37 | 143.90 / 2.90 | <=22 | 148.19 | -4.29 |
| 24 | 92.46 / 10.74 | 144.72 / 3.01 | 23-26 | 144.94 | -0.22 |
| 26 | 94.24 / 11.14 | 145.22 / 3.12 | 23-26 | 144.94 | +0.28 |
| 28 | 95.65 / 11.58 | 145.62 / 3.24 | 27-30 | 145.24 | +0.38 |
| 30 | 94.40 / 12.08 | 145.27 / 3.37 | 27-30 | 145.24 | +0.03 |
| 32 | 93.14 / 12.55 | 144.92 / 3.50 | 31-34 | 143.48 | +1.44 |
| 35 | 86.08 / 13.50 | 142.97 / 3.72 | 35+ | 143.28 | -0.31 |
| 38 | 75.54 / 14.59 | 140.13 / 3.90 | 35+ | 143.28 | -3.15 |

The <=22 comparison is strongly selection-biased because simulated age-18/20 cohorts include prospects who would not all be established KBO pitchers. It is diagnostic only. No age-curve tuning was performed.

## Average vs max velocity

Average fastball remains primary. Max velocity remains separate.

Public reference max-minus-average diagnostics:

- starter: n=7, mean **+6.64 km/h**, SD **1.42**
- reliever: n=16, mean **+6.07 km/h**, SD **1.49**

These remain experimental because sample composition and pitch counts differ.

## Effort / fatigue contract

Effort never changes raw Velocity.

`base raw -> base avg km/h -> + experimental effort bonus - fatigue loss -> effective km/h`

Same-player starter/reliever role-split evidence remains insufficient, so v2 deliberately does **not** canonicalize a permanent reliever +X km/h bonus. Unlike the v1 gate, this missing role coefficient does not block the v2 physical rating scale itself.

## Tests / regression safety

Required v2 tests cover:

- mapping monotonicity / reference / extreme safety;
- elite spacing;
- raw 150 elite-velocity representation;
- raw 250 not required for 160 km/h;
- narrow generated Velocity SD;
- rare extreme generated Velocity;
- Contact / Whiff / K monotonicity;
- negligible direct BB path;
- effort/fatigue raw-rating immutability.

The repository-wide CI also passes Python unit tests, auto-career smoke, balance smoke, high-school/draft calibration gate, web build, and web tests.

## Final gate

### VELOCITY_SCALE_V2_READY

- PASS — KBO central distribution reasonably matched
- PASS — practical raw range is narrow and interpretable
- PASS — population SD sufficiently low
- PASS — 160 km/h does not require raw 200-250
- PASS — elite tail retains meaningful spacing
- PASS — raw 200-250 is a safety domain, not normal population domain
- PASS — average velocity remains primary anchor
- PASS — max velocity separate
- PASS — gameplay sensitivity monotonic / non-pathological
- PASS — BB direct effect negligible
- PASS — H3.2.1 hitter formula diff NONE
- PASS — provenance documented
- PASS — required tests and repository-wide CI PASS

Next step: freeze this physical Velocity mapping and remove Velocity from arbitrary raw-weight search. Joint pitcher Monte Carlo should tune Stuff / Control / Breaking around this physical Velocity contract.
