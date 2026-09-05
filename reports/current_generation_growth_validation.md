# Current Generation × Current Growth Validation

## 1. Source branch / SHA

- Branch: `feature/h32-production-integration`
- Production snapshot actually executed: `c3ebae8763337bfec5b0ec8e1eee0ec03d078cf9`
- Initial inspected snapshot before concurrent draft-only branch updates: `bb3257a0295d094590cd39c3f703405eaabe1f9f`
- Master seed: `20260905`
- Validation only. No production growth, generation, Talent, profile, aging, event, coach, injury, retirement, or threshold tuning was performed.

## 2. Sample size

| Cohort | Mode | N |
|---|---:|---:|
| Player | PURE GROWTH | 20,000 |
| General HS NPC | PURE GROWTH | 20,000 |
| Player | FULL CAREER | 5,000 |
| General HS NPC | FULL CAREER | 5,000 |

PURE uses production generation/profile/Talent and production `apply_season_growth`, with growth traits cleared and coach/experience/event/injury effects absent. FULL uses the production `CareerEngine`. NPCs are generated from `generate_high_school_npc_stats(...)` and then use the same career engine assumptions as Players.

## 3. Age-18 starting distribution

### Player

| Metric | PURE | FULL |
|---|---:|---:|
| Mean | 79.702 | 79.785 |
| SD | 9.775 | 10.008 |
| P1 | 57.325 | 55.850 |
| P5 | 63.617 | 63.073 |
| P10 | 67.207 | 67.220 |
| P25 | 73.083 | 73.125 |
| P50 | 79.683 | 80.013 |
| P75 | 86.350 | 86.277 |
| P90 | 92.243 | 92.376 |
| P95 | 95.775 | 96.102 |
| P99 | 102.433 | 102.860 |
| Min | 41.692 | 38.700 |
| Max | 114.442 | 116.850 |

Player PURE starting bands: `<60` 2.170%, `60–69` 14.045%, `70–79` 35.010%, `80–89` 34.050%, `90–99` 12.910%, `100–109` 1.745%, `110+` 0.070%.

### Player vs General HS NPC at age 18

| Metric | Player FULL | NPC FULL |
|---|---:|---:|
| Mean | 79.785 | 69.819 |
| SD | 10.008 | 6.963 |
| P10 | 67.220 | 60.900 |
| P25 | 73.125 | 65.092 |
| P50 | 80.013 | 69.942 |
| P75 | 86.277 | 74.442 |
| P90 | 92.376 | 78.642 |
| P95 | 96.102 | 81.084 |
| P99 | 102.860 | 85.784 |
| >=80 | 48.040% | 6.640% |
| >=90 | 15.040% | 0.180% |
| >=100 | 2.100% | 0.000% |

The intended starting relationship is present: Player mean is about +10 higher and Player SD is materially wider.

## 4. Age curve table

### Player FULL CAREER

| Age | N | Mean | P10 | P50 | P90 | >=90 | >=100 | >=110 | >=120 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 18 | 5000 | 79.785 | 67.220 | 80.013 | 92.376 | 15.040% | 2.100% | 0.120% | 0.000% |
| 20 | 4998 | 86.624 | 73.308 | 86.725 | 99.575 | 37.075% | 9.424% | 1.261% | 0.100% |
| 22 | 4994 | 93.003 | 78.925 | 92.946 | 106.826 | 60.833% | 25.831% | 6.047% | 0.761% |
| 24 | 4993 | 98.465 | 83.645 | 98.558 | 112.842 | 76.888% | 45.183% | 15.241% | 3.184% |
| 25 | 4992 | 100.749 | 85.750 | 100.929 | 115.574 | 82.071% | 53.486% | 20.613% | 5.329% |
| 26 | 4991 | 102.931 | 87.517 | 103.150 | 118.042 | 85.734% | 60.289% | 27.149% | 7.754% |
| 28 | 4930 | 107.701 | 92.168 | 107.821 | 123.088 | 92.556% | 74.118% | 42.130% | 15.112% |
| 30 | 4849 | 109.686 | 94.083 | 109.567 | 125.325 | 94.762% | 78.820% | 48.340% | 19.365% |
| 32 | 4788 | 110.403 | 94.581 | 109.950 | 126.421 | 95.322% | 79.929% | 49.854% | 21.303% |
| 35 | 4732 | 109.435 | 93.183 | 108.771 | 126.495 | 93.956% | 76.057% | 46.006% | 19.844% |
| 37 | 4002 | 107.520 | 90.751 | 106.779 | 124.825 | 91.254% | 70.115% | 40.405% | 16.817% |
| 40 | 1898 | 102.641 | 84.483 | 101.971 | 120.610 | 80.822% | 55.796% | 27.871% | 10.801% |

Ages 19/21/23/27/29/31/33 are also present in the canonical JSON. FULL age curves after retirement begins are survivor-conditioned distributions; `N` is therefore reported explicitly.

### General HS NPC FULL CAREER

| Age | N | Mean | P50 | P90 | >=100 | >=110 | >=120 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 18 | 5000 | 69.819 | 69.942 | 78.642 | 0.000% | 0.000% | 0.000% |
| 20 | 4989 | 76.618 | 76.625 | 86.465 | 0.180% | 0.000% | 0.000% |
| 22 | 4977 | 82.914 | 82.850 | 93.553 | 1.929% | 0.181% | 0.000% |
| 24 | 4967 | 88.454 | 88.342 | 100.285 | 10.469% | 0.987% | 0.121% |
| 26 | 4965 | 92.917 | 92.742 | 105.692 | 23.525% | 4.189% | 0.383% |
| 28 | 4770 | 97.945 | 97.808 | 110.970 | 41.992% | 11.635% | 1.719% |
| 30 | 4562 | 100.248 | 100.062 | 113.808 | 50.285% | 17.185% | 3.178% |
| 32 | 4386 | 101.214 | 100.829 | 115.550 | 53.671% | 20.269% | 4.720% |
| 35 | 4252 | 100.733 | 100.025 | 116.108 | 50.118% | 19.802% | 5.668% |

## 5. Peak ability distribution

| Metric | Player PURE | Player FULL | NPC PURE | NPC FULL |
|---|---:|---:|---:|---:|
| Mean | 96.538 | 112.397 | 86.525 | 101.976 |
| SD | 11.581 | 13.684 | 9.361 | 12.669 |
| P10 | 81.917 | 95.368 | 74.774 | 85.916 |
| P25 | 88.800 | 103.883 | 80.242 | 93.723 |
| P50 | 96.383 | 112.125 | 86.333 | 102.292 |
| P75 | 104.142 | 120.804 | 92.508 | 109.677 |
| P90 | 111.333 | 128.936 | 98.259 | 117.495 |
| P95 | 115.642 | 134.333 | 102.118 | 122.217 |
| P99 | 124.742 | 148.025 | 109.867 | 135.017 |
| Max | 161.192 | 179.267 | 146.258 | 169.542 |

Player FULL peak bands: `<90` 5.44%, `90–99` 11.08%, `100–109` 25.98%, `110–119` 30.44%, `120–129` 18.06%, `130–139` 6.36%, `140–149` 1.76%, `150+` 0.88%.

NPC FULL peak bands: `<90` 17.02%, `90–99` 24.66%, `100–109` 34.24%, `110–119` 17.14%, `120–129` 5.28%, `130–139` 1.16%, `140–149` 0.30%, `150+` 0.20%.

## 6. Peak age distribution

| Metric | Player PURE | Player FULL | NPC PURE | NPC FULL |
|---|---:|---:|---:|---:|
| Mean | 28.915 | 31.327 | 28.959 | 30.998 |
| Median | 29 | 31 | 29 | 31 |
| P10 | 26 | 28 | 26 | 28 |
| P90 | 32 | 36 | 32 | 36 |

Player FULL: `<=22` 0.14%, `23–24` 0.16%, `25–26` 2.14%, `27–28` 15.72%, `29–30` 26.36%, `31–32` 22.44%, `33+` 33.04%.

NPC FULL: `<=22` 0.60%, `23–24` 0.54%, `25–26` 2.62%, `27–28` 19.34%, `29–30` 25.64%, `31–32` 20.86%, `33+` 30.40%.

## 7. Total growth distribution

| Metric | Player PURE | Player FULL | NPC PURE | NPC FULL |
|---|---:|---:|---:|---:|
| Mean | 16.836 | 32.611 | 16.820 | 32.157 |
| Median | 16.442 | 31.817 | 16.442 | 31.729 |
| SD | 6.312 | 9.410 | 6.310 | 10.177 |
| P10 | 9.367 | 21.798 | 9.283 | 20.424 |
| P90 | 24.375 | 44.220 | 24.408 | 44.059 |
| P95 | 27.425 | 48.577 | 27.267 | 48.984 |
| P99 | 35.350 | 60.937 | 34.600 | 62.567 |
| 40+ | 0.475% | 18.500% | 0.410% | 18.280% |

The FULL production context roughly doubles mean career growth relative to PURE for both cohorts.

## 8. Starting ability bucket analysis — Player FULL

| Start | N | Mean start | Mean peak | Mean growth | Peak age | P90 peak |
|---|---:|---:|---:|---:|---:|---:|
| <65 | 344 | 60.019 | 91.757 | 31.739 | 30.378 | 105.706 |
| 65–69 | 467 | 67.817 | 101.157 | 33.340 | 31.118 | 113.278 |
| 70–74 | 727 | 72.617 | 105.249 | 32.632 | 31.300 | 116.863 |
| 75–79 | 960 | 77.512 | 110.390 | 32.879 | 31.422 | 121.457 |
| 80–84 | 1016 | 82.392 | 115.025 | 32.633 | 31.390 | 126.833 |
| 85–89 | 734 | 87.316 | 120.049 | 32.733 | 31.485 | 131.567 |
| 90–94 | 443 | 92.247 | 124.380 | 32.133 | 31.528 | 135.155 |
| 95–99 | 204 | 97.292 | 129.081 | 31.790 | 31.480 | 140.602 |
| 100+ | 105 | 103.733 | 135.930 | 32.197 | 31.848 | 146.268 |

FULL growth is strikingly flat by starting-ability bucket: almost every Player bucket receives about +32 peak growth.

## 9. Talent bucket analysis

### Player FULL

| Talent | N | Start | Peak | Growth | Peak age | P90 peak |
|---|---:|---:|---:|---:|---:|---:|
| <70 | 774 | 80.198 | 106.128 | 25.931 | 29.884 | 121.298 |
| 70–89 | 1795 | 79.774 | 109.625 | 29.850 | 30.743 | 124.557 |
| 90–109 | 1460 | 79.838 | 113.116 | 33.278 | 31.434 | 128.162 |
| 110–129 | 581 | 79.050 | 116.801 | 37.751 | 32.768 | 132.075 |
| 130–149 | 242 | 80.239 | 123.407 | 43.168 | 33.636 | 138.021 |
| 150–179 | 112 | 78.737 | 133.119 | 54.382 | 35.098 | 151.616 |
| 180+ | 36 | 81.403 | 146.610 | 65.207 | 36.722 | 171.317 |

- corr(Talent, peak) = **0.4369**
- corr(Talent, total growth) = **0.6479**

### NPC FULL

- corr(Talent, peak) = **0.5062**
- corr(Talent, total growth) = **0.6358**
- Talent 130–149: mean peak 112.818, growth 43.326, 86.831% reach 100+.
- Talent 150+: mean peak 126.232, growth 56.630, 98.039% reach 100+, 64.706% reach 120+.

## 10. Development profile analysis

### Player FULL

| Profile | N | Start | Age22 | Age25 | Age28 | Age31 | Peak | Peak age | Growth |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| early_bloomer | 974 | 79.543 | 96.166 | 105.332 | 109.598 | 109.056 | 112.168 | 29.830 | 32.625 |
| normal | 2790 | 79.617 | 92.984 | 100.924 | 108.497 | 109.993 | 112.096 | 31.272 | 32.479 |
| late_bloomer | 979 | 80.167 | 90.615 | 97.116 | 104.933 | 111.703 | 113.306 | 32.508 | 33.139 |
| very_late_bloomer | 257 | 81.080 | 90.315 | 95.312 | 102.239 | 110.680 | 113.066 | 33.113 | 31.986 |

The profile system clearly changes curve timing, but FULL-career peak levels converge tightly around 112–113.

### NPC FULL

Early, normal, and late profiles also show distinct timing. Their mean peaks are 102.192, 101.949, and 102.947 respectively; very-late is lower at 98.093.

## 11. Instant-impact prospect analysis — Player FULL

| Group | N | Age18 | Age22 | Age25 | Peak | Peak P90 | Peak age |
|---|---:|---:|---:|---:|---:|---:|---:|
| Start >=90 | 752 | 95.219 | 108.145 | 115.499 | 127.268 | 140.636 | 31.560 |
| Start >=100 | 105 | 103.733 | 116.865 | 123.933 | 135.930 | 146.268 | 31.848 |

For start >=90, 76.064% reach peak >=120. For start >=100, 95.238% reach peak >=120.

## 12. Low-start / high-Talent analysis

### Player FULL: start <75 and Talent >=130

- N = 117
- Mean start = 68.083
- Mean peak = 117.275
- Peak P90 = 131.897
- Mean peak age = 34.470
- Mean growth = 49.192
- Reach 100+: 92.308%
- Reach 110+: 72.650%
- Reach 120+: 38.462%

### NPC FULL: start <70 and Talent >=130

- N = 205
- Mean start = 64.122
- Mean peak = 112.176
- Peak P90 = 128.407
- Mean peak age = 34.093
- Reach 90+: 94.146%
- Reach 100+: 83.902%
- Reach 110+: 57.561%
- Reach 120+: 26.829%

Late-blooming routes clearly exist, but high Talent makes reaching pro-level ability very likely rather than merely possible.

## 13. High-start / low-Talent analysis

Player FULL `start>=90 & Talent<90`:

- N = 396
- Mean start = 95.224
- Mean peak = 123.267
- Mean growth = 28.044
- Mean peak age = 30.795
- 64.394% reach 120+.

This archetype does exist, but the intended “immediate contributor with limited ceiling” signal is weak because even the low-Talent subset still receives very large FULL-career growth.

## 14. Individual stat age curves

### Player FULL

| Stat | 18 | 22 | 25 | 28 | 31 | 35 | Mean individual peak |
|---|---:|---:|---:|---:|---:|---:|---:|
| Contact | 80.257 | 95.526 | 105.836 | 115.526 | 120.443 | 122.348 | 127.879 |
| Power | 78.466 | 99.065 | 109.364 | 118.365 | 123.018 | 124.122 | 129.306 |
| Discipline | 73.160 | 85.067 | 92.746 | 99.719 | 102.109 | 103.111 | 109.003 |
| Speed | 83.780 | 92.123 | 96.879 | 101.227 | 101.274 | 95.734 | 106.619 |
| Defense | 80.741 | 91.621 | 97.865 | 103.539 | 104.841 | 102.692 | 110.141 |

Speed is the clearest stat to decline earlier: 101.274 at age 31 to 95.734 at age 35, while Contact and Power remain elevated. The Speed aging direction therefore works as intended.

## 15. Extreme-tail audit

| Threshold | Player FULL | NPC FULL |
|---|---:|---:|
| Peak >=120 | 27.060% | 6.940% |
| Peak >=130 | 9.000% | 1.660% |
| Peak >=140 | 2.640% | 0.500% |
| Peak >=150 | 0.880% | 0.200% |
| Peak >=170 | 0.100% | 0.000% |
| Peak >=200 | 0.000% | 0.000% |

Individual-stat tail rates:

| Threshold | Player FULL | NPC FULL |
|---|---:|---:|
| >=150 | 10.528% | 5.000% |
| >=180 | 1.152% | 0.456% |
| >=200 | 0.208% | 0.064% |
| >=250 | 0.004% | 0.000% |

The main balance concern is not impossible extreme peaks: no cohort produced a 200+ overall peak. The concern is the much more common 100–130 range.

## 16. KBO-level threshold rates

Using the design interpretation `100 ≈ KBO first-team average`:

- Player FULL reaches 100+ in 25.831% of active careers by age 22, 53.486% by 25, 74.118% by 28, and about 80% around age 31–32.
- General HS NPC FULL reaches 100+ in 1.929% by 22, 16.915% by 25, 41.992% by 28, and 53.671% of surviving careers by age 32.
- Across the whole NPC cohort, **58.320% eventually reach peak >=100**, 24.080% reach 110+, and 6.940% reach 120+.

NPC population funnel from 5,000 general HS players:

- Age 18 >=80: 332 (6.64%)
- Age 18 >=90: 9 (0.18%)
- Career peak >=90: 4,149 (82.98%)
- Career peak >=100: 2,916 (58.32%)
- Career peak >=110: 1,204 (24.08%)
- Career peak >=120: 347 (6.94%)

Equivalent per 10,000 NPCs: 8,298 / 5,832 / 2,408 / 694 respectively.

## 17. PURE GROWTH vs FULL CAREER comparison

The central result is the difference between modes:

| Metric | Player PURE | Player FULL | NPC PURE | NPC FULL |
|---|---:|---:|---:|---:|
| Start mean | 79.702 | 79.785 | 69.705 | 69.819 |
| Peak mean | 96.538 | 112.397 | 86.525 | 101.976 |
| Mean growth | 16.836 | 32.611 | 16.820 | 32.157 |
| Peak P90 | 111.333 | 128.936 | 98.259 | 117.495 |
| Mean peak age | 28.915 | 31.327 | 28.959 | 30.998 |

The starting distributions are stable across modes, while FULL adds roughly another +15.8 ability of mean career growth over PURE. Therefore the large final distribution shift is not caused by generation alone; it emerges from the combined production-career context (experience, coaches, traits, events, breakthroughs and the other FULL mechanics).

No single FULL subsystem is isolated by this experiment, so causal attribution to one mechanic would require a separate ablation study.

## 18. Old v0.4 comparison

| Metric | Old v0.4 | Current Player FULL | Change |
|---|---:|---:|---:|
| Starting mean | 70.207 | 79.785 | +9.578 |
| Peak mean | 102.086 | 112.397 | +10.311 |
| Peak P90 | 116.729 | 128.936 | +12.207 |
| Peak P95 | 123.328 | 134.333 | +11.005 |
| Peak P99 | 133.273 | 148.025 | +14.752 |
| Mean peak age | 31.277 | 31.327 | +0.050 |
| Talent↔peak correlation | 0.511 | 0.4369 | -0.0741 |

The ~+10 starting-ability shift carries almost one-for-one into mean peak, while the upper tail moves more strongly (+12 to +15). The old baseline only used 300 careers, so tail comparisons should be interpreted more cautiously than the current 5,000-career result.

## 19. Player vs NPC combined comparison / observed balance concerns

| Metric | Player FULL | General HS NPC FULL |
|---|---:|---:|
| Age18 mean | 79.785 | 69.819 |
| Age18 SD | 10.008 | 6.963 |
| Age18 P90 | 92.376 | 78.642 |
| Peak mean | 112.397 | 101.976 |
| Peak P90 | 128.936 | 117.495 |
| Peak P99 | 148.025 | 135.017 |
| Mean peak age | 31.327 | 30.998 |
| Mean career growth | 32.611 | 32.157 |
| Peak >=100 | 83.480% | 58.320% |
| Peak >=110 | 57.500% | 24.080% |
| Peak >=120 | 27.060% | 6.940% |
| Peak >=130 | 9.000% | 1.660% |

Player advantage:

- Start mean gap = 9.966
- Peak mean gap = 10.421
- Peak P90 gap = 11.441
- Peak >=100 odds ratio = 3.610
- Peak >=110 odds ratio = 4.264
- Peak >=120 odds ratio = 4.969
- Classification: **gap preserved** (not growth amplification).

Observed concerns:

1. **General-NPC pro-level supply is very high.** If `100` truly denotes KBO first-team average and `generate_high_school_npc_stats` represents the general high-school population, 58.32% eventually reaching 100+ is difficult to reconcile with the intended population funnel.
2. **FULL-career growth is about twice PURE growth.** Both cohorts rise about +32 from start to peak in FULL versus +16.8 in PURE.
3. **Starting ability has weak control over total FULL growth.** Player starting buckets from <65 through 100+ all receive roughly +32 ability on average.
4. **High-start / low-Talent ceiling separation is weak.** Players starting >=90 with Talent <90 still peak at 123.267 on average and 64.394% reach 120+.
5. **Late-bloomer routes exist strongly.** This is positive structurally, but high-Talent low-start players reach 100+ at very high rates (Player 92.308%; NPC 83.902%), making the path close to deterministic rather than merely plausible.
6. **Development profiles change timing more than final level in FULL.** Player early/normal/late/very-late peaks cluster tightly around 112–113.
7. **Extreme overall tails are not the primary issue.** 150+ and 170+ exist but are rare; 200+ overall peaks did not occur.
8. **Draft funnel also appears permissive:** 3,599 / 5,000 general NPCs (71.98%) received an actual production draft round in this synthetic cohort. This is an observed adjacent concern rather than a growth-tuning result.

NPC draft-caliber subsets further show the elevation:

- Start top 10%: peak mean 114.429; 95.0% reach 100+.
- Start top 5%: peak mean 116.018; 97.6% reach 100+.
- Start top 1%: peak mean 122.194; 100% reach 100+, 50% reach 120+.
- Talent top 10%: peak mean 116.037; 88.34% reach 100+.
- Talent top 5%: peak mean 121.439; 93.893% reach 100+.

Answers to the requested interpretation questions:

1. **Is the Player advantaged over general HS NPCs?** Yes. About +10 ability at start and +10.4 mean peak, with 3.6–5.0× higher odds of reaching 100/110/120 thresholds.
2. **How large is the advantage?** Large but mostly preserved rather than amplified by growth; the engine retains approximately the initial gap.
3. **What percentage of general HS NPCs reach KBO-average 100?** 58.32% at career peak in FULL.
4. **Are top HS prospects immediately pro-competitive?** Some are, but most top NPC prospects still develop substantially; the top 1% by starting ability average 88.152 at 18 and 122.194 at peak.
5. **Does low-start + high-Talent late blooming exist?** Yes, very strongly.
6. **Do Players cluster at overly high peaks?** The Player FULL median peak is 112.125 and 27.06% reach 120+, so the distribution is materially elevated relative to the stated 100=KBO-average scale.
7. **Are NPCs too low to supply professionals?** No. The opposite issue appears: the general NPC population supplies 100+ players extremely frequently.
8. **Is the current growth engine simultaneously suitable for both cohorts?** Under the stated KBO scale and general-NPC interpretation, the FULL-career output indicates recalibration is warranted.

## 20. Recommendation / final verdict

# GROWTH_RECALIBRATION_RECOMMENDED

This is a validation verdict, **not a tuning change**. No growth parameters, generation parameters, profile weights, Talent mixture, event effects, coach effects, aging, retirement, or thresholds were changed in this work.

The next appropriate step is a separate ablation/calibration task focused on explaining why FULL career growth (~+32) is roughly double PURE growth (~+16.8), while preserving the validated Player-vs-NPC starting gap and the useful development-profile timing differences.

Canonical raw outputs:

- `reports/current_generation_growth_validation.json`
- `reports/current_generation_growth_validation_samples.csv`
