# H3.2 Stolen-Base Integration Validation

Balance-Lab only. No `src/`, `web/`, save-schema, production ratings, or `main` changes are part of this pass.

## H3.1 -> H3.2 baseline

| Metric | H3.1 | H3.2 |
|---|---:|---:|
| AVG | 0.2611 | 0.2611 |
| OBP | 0.3207 | 0.3207 |
| SLG | 0.3974 | 0.3974 |
| OPS | 0.7181 | 0.7181 |
| Batting value/PA | 0.323416 | 0.323416 |
| Baserunning value/PA | 0 | 0.001000 |
| Total value/PA | 0.323416 | 0.324416 |

Batting metrics are identical because H3.2 steals use an independent RNG stream.

## Stolen-base model

Attempt base: `0.004 + (0.300 - 0.004) * sigmoid((Speed - 110) / 18)`, then bounded situational adjustment.

Success base: `0.48 + (0.91 - 0.48) * sigmoid((Speed - 92) / 18)`, adjusted by opponent running defense and situation, clipped to `[0.42, 0.925]`.

Validation run values: SB `+0.20`, CS `-0.42` runs.

## Speed / stolen-base curve

| Speed | Attempts/600 | SB/600 | CS/600 | Success | BR value/PA |
|---:|---:|---:|---:|---:|---:|
| 50 | 3.44 | 1.74 | 1.70 | 50.5% | -0.000613 |
| 60 | 4.30 | 2.35 | 1.95 | 54.6% | -0.000583 |
| 70 | 5.68 | 3.37 | 2.32 | 59.2% | -0.000499 |
| 80 | 7.90 | 4.98 | 2.92 | 63.0% | -0.000385 |
| 90 | 11.17 | 7.61 | 3.55 | 68.2% | +0.000052 |
| 100 | 15.34 | 11.50 | 3.85 | 74.9% | +0.001140 |
| 110 | 18.69 | 14.99 | 3.70 | 80.2% | +0.002405 |
| 120 | 22.26 | 18.84 | 3.42 | 84.6% | +0.003886 |
| 130 | 25.87 | 22.65 | 3.22 | 87.5% | +0.005295 |
| 140 | 28.82 | 25.61 | 3.21 | 88.9% | +0.006291 |
| 150 | 30.70 | 27.62 | 3.08 | 90.0% | +0.007047 |
| 160 | 31.68 | 28.67 | 3.01 | 90.5% | +0.007448 |
| 170 | 32.14 | 29.21 | 2.93 | 90.9% | +0.007686 |

## Speed +10 marginal value

H3.1 batting-only Speed +10: **+0.012313/PA**  
H3.2 batting component: **+0.012313/PA**  
H3.2 stolen-base component: **+0.001265/PA**  
H3.2 total: **+0.013578/PA**

## Build search

CPDS20 first Speed allocation: **rank 14/35 -> 11/35**.  
CPDS20 Speed builds in top 10: **0**; pure Speed stack rank: **35/35**.  
CPDS30 first Speed allocation: **rank 5/84**; Speed builds in top 10: **4**; pure Speed stack rank: **84/84**.

## Interaction check

Higher Contact or Discipline creates more on-base opportunities and therefore more steal opportunities; Power changes this only indirectly through the batting profile. Speed itself does not directly alter BB/K/HR through the stolen-base module.

## Validation status

| Category | Result |
|---|---|
| Baseline Preservation | **PASS** |
| Steal Curve | **PASS** |
| League Plausibility | **PASS** |
| CS Penalty | **PASS** |
| Speed Marginal Value | **PASS** |
| Build Diversity | **WARN** |
| Interaction Behavior | **PASS** |
| Numerical Stability | **PASS** |
| Runtime | **PASS** |

## Remaining issue

Steals improve Speed value without creating a Speed-dominant build, but low-Speed +15 investment is still far below C/P/D in the S60 starting profile and CPDS20 still has no Speed allocation in its top 10. The steal system should therefore be preserved as a valid component, while Speed build diversity remains a separate balance issue.

## Promotion gate

**NOT_READY**

H3.2 is suitable as a Balance-Lab experiment, but not yet recommended for production promotion.
