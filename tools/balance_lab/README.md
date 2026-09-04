# Balance Lab

Developer-only tuning and Monte Carlo workspace for `baseball-player-sim`.

## Purpose

- Reuse the production simulation engine from `src/` instead of copying it.
- Run controlled balance experiments without changing canonical game values.
- Compare candidate coefficient presets.
- Save reproducible reports before promoting values into the main game.

## Rules

1. `tools/balance_lab` may import from `src`, but production simulation logic must not be duplicated here.
2. Experimental values belong in `tools/balance_lab/presets/`.
3. A candidate is never applied to `src/config.py` automatically.
4. Promotion to the main game happens only after Monte Carlo validation and regression tests.
5. Reports belong in `tools/balance_lab/reports/`.

## Initial workflow

```text
Main engine (`src/`)
        ↓ import
Balance Lab + candidate preset
        ↓
Monte Carlo / sensitivity / marginal-value tests
        ↓
report + candidate JSON
        ↓
manual review
        ↓
promote validated values to main game
```

## Planned experiments

- Hitting baseline test
- Real-player calibration
- Marginal stat value
- Growth-path comparison
- Injury/fatigue tests
- Event frequency tests
- Career Monte Carlo

The scaffold intentionally avoids modifying the main game engine.
