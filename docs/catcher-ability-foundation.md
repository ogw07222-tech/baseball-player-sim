# Catcher Ability Foundation

## Final ability list

The catcher-specific foundation uses exactly three ratings:

- **Defense** — the existing shared Defense rating.
- **Throwing** — the existing shared Throwing rating.
- **Game Calling** — the only new catcher-specific rating.

There is intentionally no separate `Catching`, `Receiving`, or `Blocking` field.

## Semantics

### Defense

For catchers, the existing Defense raw/display rating represents receiving stability, blocking, difficult-pitch handling, passed-ball prevention potential, wild-pitch mitigation potential, home-plate defensive handling, and general catcher fielding. At other positions the same field keeps its existing position-specific fielding meaning.

### Throwing

For catchers, Throwing represents arm strength, transfer/release, throwing accuracy, and stolen-base-prevention potential. This foundation does not connect Throwing to stolen-base attempt deterrence or caught-stealing probability.

### Game Calling

Game Calling represents pitch-selection quality, sequencing, hitter-approach management, count management, and pitcher-catcher decision quality. It is a raw/display rating on the same broad project scale. It is **not** a direct mutation or bonus to pitcher Stuff, Control, Breaking, Velocity, or any other pitcher raw rating.

Non-catchers carry `game_calling = 0` for schema compatibility and do not use it in gameplay.

## Generation

`Player.random(..., position="C")` first uses the existing player-generation pipeline, including the existing C position adjustments for Defense and Throwing. A catcher-only adapter then:

1. selects one of five lightweight generation archetypes;
2. applies modest Defense/Throwing generation deltas;
3. generates Game Calling around a prospect center in the low/mid-80s;
4. uses weak dependence on Defense and Throwing so the three ratings are related without becoming the same skill.

Archetypes are:

- `defensive`
- `strong_arm`
- `game_manager`
- `balanced`
- `offensive`

The offensive archetype does not receive a new batting formula or batting bonus in this foundation. It is defined relatively by more modest catcher-defense ratings, which preserves existing hitter generation.

## Growth

Game Calling participates in seasonal growth only for position `C`. The existing general growth engine remains authoritative for talent, development profile, experience, traits, and aging philosophy. A narrow catcher adapter uses the existing mentality/general-skill growth distribution as its base, gives Game Calling a small early-to-prime skill-development bias, and slightly reduces variance.

Game Calling is intentionally excluded from the generic growth-explosion stat pool. This keeps it closer to an experience-heavy skill and avoids introducing a new catcher-specific breakthrough formula.

No gameplay value is assigned to any catcher rating here.

## Save compatibility and serialization

`PlayerStats.game_calling` has a safe default of `0`. `PlayerStats.from_dict()` treats a missing field as `0`, so saves from versions that predate Game Calling continue to load without a save-version bump.

`Player.as_dict()` / `Player.from_dict()` preserve both Game Calling and the optional catcher generation archetype. Because display/API-facing code already serializes `stats.as_dict()`, Game Calling is available to presentation adapters without changing the web UI in this task.

## Future gameplay integration contract

A later, separate calibration/integration task may map:

- **Defense** -> receiving / blocking / difficult-pitch handling / WP-PB mitigation
- **Throwing** -> stolen-base attempt deterrence and caught-stealing success, modeled as separate effects
- **Game Calling** -> pitch-selection quality / sequencing / mistake-risk modulation

Game Calling must remain a decision-quality input. Future code must not implement structures such as `pitcher.stuff += catcher.game_calling * k` or mutate any pitcher raw rating.

## Explicit non-goals

Not implemented in this foundation:

- passed-ball probability
- wild-pitch probability or mitigation formula
- stolen-base attempt probability
- caught-stealing probability
- pitch-selection or sequencing gameplay modifier
- catcher gameplay tuning or normalization
- pitcher raw-rating changes
- hitter formula changes
- roster-wide position-distribution redesign
- web UI changes

`CATCHER_GAMEPLAY_INTEGRATION_READY` therefore remains `NOT_RUN`.
