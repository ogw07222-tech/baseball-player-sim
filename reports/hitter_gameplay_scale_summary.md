# Hitter Raw Career Rating ↔ H3 Gameplay Scale Calibration

## Final gates
- `HITTER_GAMEPLAY_SCALE_NOT_READY`
- `HITTER_DISPLAY_GAMEPLAY_RATIO_NOT_READY`

The linear normalization candidate itself is technically healthy, but the full user-facing display contract is not ready for production promotion.

## Source / architecture
- Base: `6818e48504af2eb7f9cd71a3b8a0fbe3497136f3` (`feature/pitcher-scb-scale-recenter`)
- Raw `PlayerStats` and save schema are unchanged.
- Candidate derived contract: `gameplay = 100 + (raw - stat_specific_prime_reference) * 0.60`.
- Existing H3.2.1 formula code is unchanged.
- The candidate is intentionally **not wired into `src/simulation.py`** while the display-ratio gate is NOT_READY.

## Measured 26–30 mixed raw references (30k cohort)
- Contact: 94.27
- Power: 92.78
- Discipline: 87.34
- Speed: 98.04

These values map to gameplay 100 under the candidate. The key blocker is that they do **not** match the intended display semantics where a prime KBO-average hitter should sit around raw 110. A displayed raw 110 is therefore already materially above the actual production-grown population center.

## Candidate slope / ratio
Selected diagnostic slope: **0.60 gameplay points per raw point**. Raw +10 therefore equals gameplay +6 before H3's own nonlinear response. This maps raw SDs around 20–24 to gameplay SDs around 12–14 without adding a second strong nonlinear compression layer.

Contact, Power and Discipline maintain useful low/mid/high separation. Speed is the unresolved exception: existing H3 speed resolution strongly saturates at the high end. In the measured PA diagnostic, raw Speed 130→140 changed SLG by only 0.0015, and 150→160 by only 0.0010. Full steal/baserunning separation was not measured, so Speed cannot yet be declared display-ratio READY.

## Production-grown hitter population vs neutral H3 pitcher
- AVG 0.2623
- OBP 0.3233
- SLG 0.4098
- OPS 0.7331
- BB% 8.267%
- K% 21.122%
- HR% 2.781%
- BABIP 0.3137

This is a large improvement over feeding low raw career ratings directly into H3 and demonstrates that the scale mismatch is real. It is not used as a hidden KBO fit; remaining league deltas are intentionally left for later calibration.

## Profile diagnostic
- Balanced: OPS 0.8970
- Contact Specialist: OPS 0.9047
- Power Hitter: OPS 0.9104
- Disciplined Hitter: OPS 0.9322
- Raw Tool Monster: OPS 1.0887
- Weak Prospect: OPS 0.6158

Profiles are distinct, but their absolute strength also exposes the display-scale mismatch: raw 110/110/110 is much stronger than the measured prime population because the current raw prime references are below 100.

## Failure policy / next prerequisite
Do not retune H3, Velocity, KBO tolerances, or pitcher S/C/B to absorb this. The next prerequisite is a **hitter raw-scale re-centering task** for Contact/Power/Discipline (and a dedicated Speed/baserunning ratio validation) so player-facing prime ratings can live around 108–112. After that, re-measure references and rerun this same normalization gate. Only after both hitter gates become READY should Pitcher Joint Calibration v4 begin.
