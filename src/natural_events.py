"""Minimal natural-event probability contracts layered on frozen H3.2.1.

This module intentionally reuses the validated H3.2.1 advancement curves. It
adds only event-specific interpretation for doubles, caught fly balls, ground
outs, and a future-compatible wild-pitch/passed-ball event contract.
"""
from __future__ import annotations

from enum import Enum

from .hitting.baserunning import (
    clamp,
    first_to_third_probability,
    second_to_home_probability,
)


class PitchMiscEvent(str, Enum):
    NONE = "none"
    WILD_PITCH = "wild_pitch"
    PASSED_BALL = "passed_ball"


def first_to_home_on_double_probability(
    speed: float,
    recovery: float = 100.0,
    depth: str = "medium",
) -> float:
    """Chance that a runner on first scores on a double."""
    base = second_to_home_probability(speed, recovery)
    depth_adjustment = {"shallow": -0.16, "medium": -0.03, "deep": 0.08}
    if depth not in depth_adjustment:
        raise ValueError(f"unknown batted-ball depth: {depth}")
    return clamp(base + depth_adjustment[depth], 0.08, 0.90)


def tag_up_probability(
    speed: float,
    recovery: float = 100.0,
    depth: str = "medium",
    from_base: int = 3,
) -> float:
    """Probability of a successful tag-up after a caught fly ball."""
    if depth not in {"shallow", "medium", "deep"}:
        raise ValueError(f"unknown batted-ball depth: {depth}")
    if from_base == 3:
        base = second_to_home_probability(speed, recovery)
        factor = {"shallow": 0.12, "medium": 0.72, "deep": 1.12}[depth]
        return clamp(base * factor, 0.01, 0.88)
    if from_base == 2:
        base = first_to_third_probability(speed, recovery)
        factor = {"shallow": 0.06, "medium": 0.48, "deep": 0.86}[depth]
        return clamp(base * factor, 0.005, 0.72)
    raise ValueError("tag-up currently supports only second or third base")


def ground_out_advance_probability(
    speed: float,
    recovery: float = 100.0,
    from_base: int = 2,
) -> float:
    """Conservative non-force advancement probability on a ground out."""
    if from_base == 2:
        return clamp(first_to_third_probability(speed, recovery) * 0.42, 0.04, 0.44)
    if from_base == 3:
        return clamp(second_to_home_probability(speed, recovery) * 0.28, 0.03, 0.30)
    raise ValueError("ground-out advancement currently supports second or third base")
