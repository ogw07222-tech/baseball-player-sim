# KBO Velocity Scale Calibration Summary

## Source / scope

- main HEAD: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- calibration execution branch HEAD: `8d2377bce13a15c63403239680fe6830e23786d9`
- H3.2.1 hitter formula diff: **NONE**
- persistent inning / base-state changes: **NONE**
- Physical reference system: **KBO/Sports2i PTS**
- Primary league anchor: **2025 KBO average fastball 146.0 km/h**

## Provenance

- 2025 broad distribution (119 pitchers, >=30% regulation innings): `https://kbo-analytics-2025.vercel.app/`
- 2025 100+ IP starter velocity list (Statiz-cited): `https://sports.news.nate.com/view/20260116n26163`
- Individual KBO season-aggregate PTS player pages and exact URLs are retained row-by-row in `data/kbo_velocity_reference.csv`.
- The 119-row distribution snapshot used for shape validation is retained in `data/kbo_velocity_distribution_2025.csv`.
- Measurement contract is KBO/Sports2i PTS; club TrackMan readings are not mixed into the mapping.

## Actual public reference sample

- 2025 starter sample n=9: mean 146.99, median 146.60, SD 3.06 km/h
- 2025 reliever sample n=5: mean 141.94, median 142.00, SD 1.72 km/h
- Curated cross-player role gap: -5.05 km/h. **Descriptive only; not a causal effort estimate.**

The public sample is not an exhaustive league export, so the official 146.0 km/h league aggregate remains the central anchor. Same-player role-split evidence is insufficient to canonicalize a reliever bonus.

## Mapping candidates

- linear: fit error 1.477; mapped mean 146.12, SD 5.76; raw30/100/250 -> 126.2/148.6/196.6 km/h
- piecewise: fit error 1.428; mapped mean 146.16, SD 5.62; raw30/100/250 -> 133.5/148.6/169.6 km/h
- soft_nonlinear: fit error 1.066; mapped mean 146.09, SD 5.19; raw30/100/250 -> 132.9/148.6/161.0 km/h

Chosen experimental physical mapping: **soft_nonlinear**, raw reference **92.00** -> 146.0 km/h.

## Physical -> gameplay contract

- H3 gameplay Velocity 100 = **146.0 effective km/h**
- chosen experimental scale = **1.50 gameplay points / km/h**
- Raw Velocity 100 is **not** assumed to equal H3 Velocity 100.

Velocity-only adapter changes Contact input only. Stuff, Control and Breaking/movement are held neutral, so this stage does not fit league offense.

## Per-km/h sensitivity

Across 142->150 km/h: Contact -0.256 pp/km/h; K +0.090 pp/km/h; AVG -0.0022/km/h; SLG -0.0034/km/h; BB total shift -0.040 pp.

### +3 / +5 / +8 km/h summary

- +3: Contact -0.67 pp, Whiff +0.67 pp, K +0.43 pp, AVG -0.0088, SLG -0.0154, BB -0.07 pp
- +5: Contact -0.98 pp, Whiff +0.98 pp, K +0.72 pp, AVG -0.0144, SLG -0.0245, BB -0.04 pp
- +8: Contact -1.60 pp, Whiff +1.60 pp, K +1.00 pp, AVG -0.0218, SLG -0.0360, BB -0.08 pp

## Max velocity model

- Starter expected max-minus-avg: 6.64 km/h (sample SD 1.42)
- Reliever expected max-minus-avg: 6.07 km/h (sample SD 1.49)
- Max velocity remains a separate stochastic/sample-size-sensitive diagnostic; it is not a fixed offset used as the primary rating anchor.

## Growth age diagnostic (no tuning)

- age 20: simulated raw mean 85.97 -> 144.20 km/h; public <=22 sample mean 148.19; diff -3.98
- age 22: simulated raw mean 90.21 -> 145.45 km/h; public <=22 sample mean 148.19; diff -2.74
- age 24: simulated raw mean 93.23 -> 146.34 km/h; public 23-26 sample mean 144.94; diff +1.40
- age 26: simulated raw mean 94.99 -> 146.84 km/h; public 23-26 sample mean 144.94; diff +1.90
- age 28: simulated raw mean 96.33 -> 147.22 km/h; public 27-30 sample mean 145.24; diff +1.98
- age 30: simulated raw mean 95.03 -> 146.84 km/h; public 27-30 sample mean 145.24; diff +1.60
- age 32: simulated raw mean 94.01 -> 146.55 km/h; public 31-34 sample mean 143.48; diff +3.07
- age 35: simulated raw mean 86.84 -> 144.55 km/h; public 35+ sample mean 143.28; diff +1.27

## Extreme safety

- raw 30: 132.90 km/h
- raw 50: 135.16 km/h
- raw 70: 139.33 km/h
- raw 100: 148.58 km/h
- raw 130: 156.18 km/h
- raw 160: 159.52 km/h
- raw 200: 160.73 km/h
- raw 250: 160.97 km/h

## Final gate

### VELOCITY_SCALE_CALIBRATION_NOT_READY

The raw->physical and physical->gameplay contracts are usable experimentally, but the final production gate is held **NOT_READY** because the public dataset is not exhaustive and, critically, same-player starter/reliever role-split evidence is insufficient to convert the observed cross-player gap into a canonical effort bonus. Do not infer a permanent reliever +km/h value from the curated cross-player sample.

Next step after strengthening role provenance: rerun Velocity/Stuff/Control/Breaking joint Monte Carlo with Velocity supplied through this physical-km/h adapter rather than a raw arbitrary weight.

## 2025 broad velocity distribution anchor

The secondary public table contains **119 pitchers at >=30% of regulation innings**: mean 145.45, median 145.30, SD 3.72, P10/P20/P50/P80/P90/P95 = 141.36/142.68/145.30/148.12/150.42/151.74 km/h. The official 146.0 km/h all-league aggregate remains the primary center anchor; this 119-pitcher table is used for distribution-shape validation.
