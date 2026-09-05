"""Experimental starter/reliever effort and fatigue foundation.

Effort is usage context, not a second rating system. Base ratings are never
mutated. Performance boosts are mild while fatigue cost is convex. Workload
state is diagnostic-only and does not implement manager substitution logic.
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


@dataclass(frozen=True)
class WorkloadState:
    pitches: int
    batters_faced_estimate: float
    fatigue: float
    effective_velocity: float
    effective_stuff: float


class EffortModel:
    """Compute usage-context output without changing source ratings."""

    def __init__(self, profile: EffortProfile) -> None:
        self.profile = profile

    def velocity_boost(self) -> float:
        return self.profile.velocity_boost_at_max * self.profile.effort ** 0.90

    def stuff_boost(self) -> float:
        return self.profile.stuff_boost_at_max * self.profile.effort ** 0.90

    def fatigue_multiplier(self) -> float:
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
        stamina_factor = 100.0 / clamp(float(stamina), 30.0, 250.0)
        return base_fatigue * self.fatigue_multiplier() * stamina_factor

    def workload_state(self, pitcher, pitches: int) -> WorkloadState:
        """Return a deterministic workload diagnostic at a pitch count.

        The reference cost is 0.010 fatigue units per pitch at Stamina 100.
        Performance decline starts only after a modest fatigue reserve, allowing
        starters to remain stable through ordinary early/mid outing workload.
        """
        if pitches < 0:
            raise ValueError("pitches must be non-negative")
        fatigue = self.fatigue_gain(float(pitches) * 0.010, float(pitcher.stamina))
        excess = max(0.0, fatigue - 0.55)
        decline = excess ** 1.25 * 2.8
        base = self.effective_stats(pitcher)
        return WorkloadState(
            pitches=int(pitches),
            batters_faced_estimate=float(pitches) / 3.85,
            fatigue=fatigue,
            effective_velocity=base.velocity - decline,
            effective_stuff=base.stuff - decline * 1.05,
        )
