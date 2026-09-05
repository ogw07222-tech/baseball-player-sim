"""Experimental starter/reliever effort and fatigue foundation.

Effort is usage context, not a second rating system.  Base ratings are never
mutated.  Performance boosts are mild while fatigue cost is convex.
"""
from __future__ import annotations

from dataclasses import dataclass


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class EffortProfile:
    effort: float
    velocity_boost_at_max: float = 4.0
    stuff_boost_at_max: float = 4.0
    fatigue_multiplier_at_max: float = 1.90

    def __post_init__(self) -> None:
        if not 0.0 <= self.effort <= 1.0:
            raise ValueError("effort must be in [0, 1]")
        if not 0.0 <= self.velocity_boost_at_max <= 8.0:
            raise ValueError("velocity boost must be in [0, 8]")
        if not 0.0 <= self.stuff_boost_at_max <= 8.0:
            raise ValueError("stuff boost must be in [0, 8]")
        if not 1.0 <= self.fatigue_multiplier_at_max <= 2.3:
            raise ValueError("fatigue multiplier must be in [1.0, 2.3]")


@dataclass(frozen=True)
class EffectiveEffortStats:
    velocity: float
    stuff: float
    control: float
    breaking: float
    fatigue_multiplier: float


class EffortModel:
    """Compute role-like effective output without changing the source ratings."""

    def __init__(self, profile: EffortProfile) -> None:
        self.profile = profile

    def velocity_boost(self) -> float:
        # Mild diminishing returns in output.
        return self.profile.velocity_boost_at_max * self.profile.effort ** 0.90

    def stuff_boost(self) -> float:
        return self.profile.stuff_boost_at_max * self.profile.effort ** 0.90

    def fatigue_multiplier(self) -> float:
        # Convex: approaching max effort becomes disproportionately expensive.
        span = self.profile.fatigue_multiplier_at_max - 1.0
        return 1.0 + span * self.profile.effort ** 2.0

    def effective_stats(self, pitcher) -> EffectiveEffortStats:
        return EffectiveEffortStats(
            velocity=float(pitcher.velocity) + self.velocity_boost(),
            stuff=float(pitcher.stuff) + self.stuff_boost(),
            control=float(pitcher.control),
            breaking=float(pitcher.breaking),
            fatigue_multiplier=self.fatigue_multiplier(),
        )

    def fatigue_gain(self, base_fatigue: float, stamina: float) -> float:
        if base_fatigue < 0:
            raise ValueError("base_fatigue must be non-negative")
        # 100 Stamina is the reference.  Higher stamina reduces same-effort cost;
        # lower stamina increases it.  Clamp only protects extreme test ratings.
        stamina_factor = 100.0 / clamp(float(stamina), 30.0, 250.0)
        return base_fatigue * self.fatigue_multiplier() * stamina_factor
