"""Experiment registry for Balance Lab.

Experiment implementations should call production code under `src/` and accept
explicit candidate parameters rather than patching production constants in place.
"""

from __future__ import annotations


PLANNED_EXPERIMENTS: tuple[str, ...] = (
    "hitting-baseline",
    "real-player-calibration",
    "marginal-stat-value",
    "growth-path-comparison",
    "injury-fatigue",
    "event-frequency",
    "career-monte-carlo",
)


def list_experiments() -> tuple[str, ...]:
    return PLANNED_EXPERIMENTS
