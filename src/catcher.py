"""Catcher-only rating generation foundation.

This module defines catcher rating semantics and generation only. It does not
apply any gameplay effect to pitching, passed-ball, wild-pitch, steal, or
caught-stealing probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass

from .rng import RNG
from .stats import PlayerStats

CATCHER_POSITION = "C"

# (name, weight, defense delta, throwing delta, game-calling delta)
CATCHER_ARCHETYPES: tuple[tuple[str, float, int, int, int], ...] = (
    ("defensive", 0.22, 8, 1, 5),
    ("strong_arm", 0.18, 2, 10, 1),
    ("game_manager", 0.20, 4, 0, 10),
    ("balanced", 0.25, 3, 3, 3),
    ("offensive", 0.15, -4, -2, -2),
)


@dataclass(frozen=True)
class CatcherFoundation:
    archetype: str
    defense: int
    throwing: int
    game_calling: int


def _choose_archetype(rng: RNG) -> tuple[str, float, int, int, int]:
    return rng.weighted_choice([(entry, entry[1]) for entry in CATCHER_ARCHETYPES])


def generate_catcher_foundation(
    stats: PlayerStats,
    rng: RNG,
    archetype: str | None = None,
) -> CatcherFoundation:
    """Apply catcher-only generation adjustments to an existing stat line.

    Defense and Throwing are the existing shared raw ratings. Game Calling is
    generated on the same display scale. The dependency on Defense/Throwing is
    deliberately weak so the three ratings are related without collapsing into
    one skill.
    """
    if archetype is None:
        selected = _choose_archetype(rng)
    else:
        matches = [entry for entry in CATCHER_ARCHETYPES if entry[0] == archetype]
        if not matches:
            raise ValueError(f"unknown catcher archetype: {archetype}")
        selected = matches[0]

    name, _, defense_delta, throwing_delta, calling_delta = selected
    stats.defense = max(0, stats.defense + defense_delta)
    stats.throwing = max(0, stats.throwing + throwing_delta)

    # Prospect center is in the low/mid-80s. Existing growth can move mature
    # catchers toward the broader KBO-ish 100-110 display region. The two weak
    # shared terms provide a natural ~0.2-0.3 relationship rather than identity.
    mean = 82.0 + 0.18 * (stats.defense - 83.0) + 0.12 * (stats.throwing - 93.0)
    stats.game_calling = max(0, int(round(rng.gauss(mean, 14.0))) + calling_delta)

    return CatcherFoundation(
        archetype=name,
        defense=stats.defense,
        throwing=stats.throwing,
        game_calling=stats.game_calling,
    )
