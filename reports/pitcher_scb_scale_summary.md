# Pitcher Stuff / Control / Breaking Raw Scale Re-Centering

## Status

`SCB_RAW_SCALE_READY`

This report covers the raw career-rating representation layer only. Velocity is explicitly exempt and remains frozen to Velocity Scale v2 plus the validated physical safety layer.

## Source

- Main at task start: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`
- Velocity Scale v2 source/base: `c405b3e9c1ec2633fabd0f033c0c923b165bd6af`
- Branch: `feature/pitcher-scb-scale-recenter`
- Physical velocity safety layer copied unchanged from the validated PR #23 implementation.
- H3.2.1 hitter formulas: unchanged.
- Hitter generation/growth: unchanged.
- Velocity generation, growth, raw->km/h mapping, caps and gameplay normalization: unchanged.

## Diagnosis

A 30,000-career `player=True` cohort showed that entry S/C/B values were already in a reasonable prospect range, while development did not lift the career ratings onto the requested human-readable prime scale.

Prime mixed ages 26/28/30 before the patch:

| Stat | Mean | SD |
|---|---:|---:|
| Velocity raw | 94.83 | 11.70 |
| Stuff | 95.90 | 16.94 |
| Control | 91.10 | 18.74 |
| Breaking | 94.89 | 17.99 |
| Physical velocity | 145.39 km/h | 3.27 |

Entry age 18 before/after is intentionally unchanged:

- Stuff 80.34
- Control 75.85
- Breaking 78.85

Therefore the patch does not add a global +15 constant and does not raise high-school pitchers to a prime scale.

## Minimum production patch

Only `src/pitching/growth.py` changes S/C/B representation. A stat-specific development bonus is added to the existing growth mean and goes to zero after age 27.

Final development-only bonuses:

- Stuff: +1.50/season through age 25, +0.80 at ages 26-27
- Control: +1.95/season through age 25, +1.25 at ages 26-27
- Breaking: +1.55/season through age 25, +0.85 at ages 26-27
- Velocity: +0.00 from this recenter layer at every age

Existing talent, random growth, current-stat damping, stat age offsets and aging multipliers remain in force.

## Final prime distribution

Prime mixed ages 26/28/30 after the patch:

| Stat | Mean | SD | P95 | P99 |
|---|---:|---:|---:|---:|
| Stuff | **108.89** | 16.93 | 137 | 148 |
| Control | **108.28** | 18.78 | 139 | 152 |
| Breaking | **108.35** | 17.99 | 138 | ~150 |

All three means satisfy the requested 108-112 gate. The tails remain broad enough for archetype and elite separation. The SDs remain broader than the optional 10-15 guideline, especially Control; this is retained rather than compressing archetype/shared/talent variation in this task.

## Age curve after recentering

| Age | Stuff | Control | Breaking |
|---:|---:|---:|---:|
| 18 | 80.34 | 75.85 | 78.85 |
| 20 | 87.40 | 83.08 | 85.90 |
| 22 | 94.45 | 90.30 | 92.92 |
| 24 | 100.69 | 97.88 | 99.42 |
| 26 | 106.20 | 104.63 | 105.33 |
| 28 | 110.32 | 109.90 | 109.80 |
| 30 | 110.15 | 110.31 | 109.93 |
| 32 | 109.93 | 110.65 | 110.08 |
| 35 | 106.14 | 108.78 | 107.57 |

Approximate peak mean ages are Stuff 28, Control 32 and Breaking 32. This preserves the intended later-development identity of Control/Breaking rather than forcing identical curves.

## Velocity unchanged proof

The same random cohort was simulated before and after. Raw Velocity and mapped physical velocity are identical at every sampled age. Prime physical velocity is unchanged at:

- mean 145.388 km/h
- SD 3.274 km/h

This confirms the S/C/B representation patch does not alter the Velocity v2 physical contract.

## Gameplay normalization contract

Raw career ratings are not equated to H3 mathematical neutral. Joint v3 uses a calibration adapter with:

- raw Stuff 109 -> gameplay-neutral Stuff reference 100
- raw Control 109 -> gameplay-neutral Control reference 100
- raw Breaking 109 -> gameplay-neutral Breaking reference 100

The searched gameplay slopes then operate around these references. This mirrors the successful Velocity architecture: representation scale is separate from gameplay mathematical reference.

## Overall pitcher rating note

The existing `current_ability()` remains a weighted sum of raw pitcher stats. Because Velocity intentionally remains on its physical raw scale while S/C/B are now on a ~110 prime representation scale, a future UI-facing overall score should preferably normalize components or use percentiles before combining them. No UI/overall formula change is made here.

## Gate checks

- Stuff prime mean 108-112: PASS
- Control prime mean 108-112: PASS
- Breaking prime mean 108-112: PASS
- starting population remains prospect-scaled: PASS
- elite tails preserved: PASS
- Velocity distribution unchanged: PASS
- age curve non-pathological: PASS
- dedicated scale/normalization tests: PASS in calibration workflow

Final: `SCB_RAW_SCALE_READY`.
