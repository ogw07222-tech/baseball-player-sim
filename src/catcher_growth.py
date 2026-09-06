"""Minimal catcher-specific growth adapter for Game Calling.

The general growth engine remains authoritative. This adapter only reshapes the
already-computed general skill growth distribution so Game Calling can develop
as a slightly later-peaking experience-heavy skill.
"""
from __future__ import annotations

from .player import Player


def game_calling_growth_distribution(
    player: Player,
    base_mean: float,
    base_stddev: float,
) -> tuple[float, float]:
    """Return a conservative Game Calling growth distribution.

    The input distribution is derived from the existing mentality/general skill
    path in growth.py, so talent/profile/experience philosophy stays shared.
    """
    age_bonus = 0.25 if player.age <= 27 else (0.10 if player.age <= 31 else 0.0)
    return base_mean + age_bonus, max(0.75, base_stddev * 0.90)
