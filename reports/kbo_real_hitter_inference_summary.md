# KBO Real Hitter Rating Inference

Gate: `KBO_REAL_HITTER_RATING_INFERENCE_NOT_READY`

## Implemented

- primary season: 2025
- source collector: Baseball-Reference 2025 KBO batting table, with explicit provenance fallback seed
- minimum primary threshold: 100 PA; stricter 300 PA subset supported by downstream reports
- staged search: broad candidate library -> nearest candidates -> bounded local refinement -> alternatives/confidence
- raw search bounds: Contact 60-170, Power 60-180, Discipline 60-170, Speed 50-170
- fixed multi-metric tolerances for AVG/OBP/SLG/BB/K/HR/BABIP
- Speed uses frozen baserunning curves when SB/CS evidence exists; absent running evidence receives a stronger prior
- HBP/source-denominator mismatch is recorded rather than silently absorbed into ratings

## Current data

A 17-player 2025 provenance fallback seed is committed for reproducibility if live full-table collection is blocked. It is not treated as sufficient evidence for READY.

## Why NOT_READY

The candidate simulations did not execute because GitHub did not allocate a hosted runner. Also, authoritative hitter inference is conditional on a READY first-team Joint v4 pitcher context; otherwise the tool labels fits `neutral_provisional`.

No hitter raw rating has been promoted from unexecuted candidate search.
