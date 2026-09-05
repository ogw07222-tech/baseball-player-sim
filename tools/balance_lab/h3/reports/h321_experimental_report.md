# H3.2.1 Low-Speed Baserunning Rebalance

**Promotion gate: READY**

H3.1 batting/fielding and H3.2 steal-success logic are frozen. H3.2.1 only gates low-speed steal attempts and adds post-contact 1B→3B, 2B→Home, and DP-avoidance value. Existing IFH/stretch-double/triple value is not added twice.

## Speed +10 marginal value

| Model | OV/PA delta |
|---|---:|
| H3.1 | 0.012313 |
| H3.2 | 0.013578 |
| H3.2.1 | 0.015439 |

## Low-speed steal attempts

| Speed | H3.2 attempts/600 | H3.2.1 attempts/600 | H3.2.1 steal value/PA |
|---:|---:|---:|---:|
| 50 | 3.44 | 0.04 | -0.000008 |
| 60 | 4.30 | 0.14 | -0.000033 |
| 70 | 5.68 | 0.83 | -0.000106 |
| 80 | 7.90 | 3.20 | -0.000172 |
| 90 | 11.17 | 6.82 | +0.000117 |
| 100 | 15.34 | 10.73 | +0.000761 |

## Build search

- CPDS20: first Speed build **11→9**, top-10 Speed builds **0→1**, pure Speed **35/35**.
- CPDS30: first Speed build **5→3**, top-10 Speed builds **4→6**, pure Speed **84/84**.

## PASS/WARN/FAIL

| Gate | Result |
|---|---|
| Baseline Preservation | **PASS** |
| Low-Speed Steal Suppression | **PASS** |
| Low-Speed Steal Value | **PASS** |
| Low-Speed Continuous Value | **PASS** |
| High-Speed Diminishing Returns | **PASS** |
| Speed Marginal Balance | **PASS** |
| Build Diversity | **PASS** |
| Low-Speed Profile Investment | **PASS** |
| Numerical Stability | **PASS** |
| Runtime | **PASS** |

## Recommendation

**READY** for a separate production-port design review. No automatic promotion or main merge.
