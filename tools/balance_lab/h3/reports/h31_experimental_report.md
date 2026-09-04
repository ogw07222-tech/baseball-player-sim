# H3.1 Experimental Defensive & Speed Model Validation

> Balance-Lab only. No production `src/` promotion is performed in this pass.

## Scope

- Main reference: `b9fda177973c00a220d83242a3bfc8de42143b0d`
- Experimental branch: `experiment/h3-batted-ball-validation`
- Visible-stat direction: Contact / Power / Discipline / Speed / Defense / Resilience / Talent
- Throwing, Stamina, Mentality are not independent H3.1 gameplay stats.

## Baseline

| AVG | OBP | SLG | OPS | BABIP | HR% | BB% | K% | OV/PA |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.261 | 0.321 | 0.397 | 0.718 | 0.313 | 2.75% | 8.07% | 21.30% | 0.3234 |

500k PA runtime: 13.35s (37,453 PA/s).

## Marginal Stat Value (+10)

| Stat | OV Δ | AVG Δ | OBP Δ | SLG Δ | HR% Δ | BB% Δ | K% Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Contact | +0.01871 | +0.0173 | +0.0159 | +0.0297 | +0.29%p | -0.00%p | -0.76%p |
| Power | +0.01893 | +0.0142 | +0.0134 | +0.0344 | +0.52%p | +0.04%p | +0.08%p |
| Discipline | +0.01556 | +0.0097 | +0.0205 | +0.0143 | +0.05%p | +1.58%p | -1.79%p |
| Speed | +0.01231 | +0.0034 | +0.0034 | +0.0312 | +0.02%p | +0.03%p | -0.10%p |
| Defense | -0.00843 | -0.0082 | -0.0071 | -0.0126 | -0.00%p | +0.07%p | +0.01%p |

C/P/D +10 marginal ratio: **1.22x**.

## Speed

Low-speed OV gains: 50→60 **+0.00118**, 60→70 **+0.00074**, 70→80 **+0.00138**, 80→90 **+0.00199**, 90→100 **+0.00384**.

High-speed OV gains: 100→110 **+0.01231**, 120→130 **+0.00133**, 140→150 **+0.00087**, 160→170 **+0.00053**.

The previous low-speed dead zone is removed, while high-speed diminishing returns remain.

## Defense

| DEF | AVG | BABIP | SLG | 1B% | 2B% | 3B% | OUT% | ERROR% |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 70 | 0.286 | 0.348 | 0.434 | 18.43% | 4.97% | 0.24% | 64.75% | 0.90% |
| 100 | 0.261 | 0.313 | 0.399 | 17.09% | 3.97% | 0.19% | 67.24% | 0.72% |
| 130 | 0.237 | 0.280 | 0.361 | 15.97% | 2.87% | 0.14% | 69.69% | 0.52% |
| 160 | 0.211 | 0.245 | 0.326 | 14.56% | 1.93% | 0.10% | 72.26% | 0.31% |

Difficulty catch probability at DEF100: ROUTINE 99.1%, EASY 95.8%, AVERAGE 55.0%, HARD 43.0%, VERY_HARD 15.0%, EXCEPTIONAL 4.0%. DEF160 still catches only 13.3% of EXCEPTIONAL balls.

Error logic: ROUTINE misses become errors about 98.5% of the time, EASY about 85.9%; AVERAGE and harder misses are hits rather than errors.

## Build search

CPD30 best: **+C5 / +P25 / +D0**, OV 0.38468.
Balanced +10/+10/+10 rank: **13/28**; best advantage: **1.14%**.
CPDS20 first build containing Speed allocation: **rank 14/35**.

## PASS / WARN / FAIL

| Category | Result |
|---|---|
| Baseline Preservation | **PASS** |
| Contact Identity | **PASS** |
| Power Identity | **PASS** |
| Discipline Identity | **PASS** |
| Speed Identity | **PASS** |
| Low-Speed Dead Zone | **PASS** |
| Defense Catch Curve | **PASS** |
| Defense Damage Suppression | **PASS** |
| Routine/Easy Reliability | **PASS** |
| Error Logic | **PASS** |
| Quality vs Defense | **PASS** |
| Triple-Speed Separation | **PASS** |
| C/P/D Marginal Balance | **PASS** |
| Build Diversity | **WARN** |
| Numerical Stability | **PASS** |
| Runtime | **PASS** |

## Remaining issues

- Speed allocation first appears at rank 14/35 in the CPDS20 build search.
- Speed +15 remains the lowest raw-offense investment in starting profiles E (S60) and F (S140); growth reward weighting may still be needed even though the dead zone is removed.

## Promotion gate

**NOT_READY**
