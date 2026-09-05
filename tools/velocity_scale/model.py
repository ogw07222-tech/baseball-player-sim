"""Experimental three-stage pitcher velocity contract.

Raw career rating -> KBO-PTS average fastball km/h -> normalized H3 gameplay
Velocity.  Nothing here mutates production ratings or H3.2.1 formulas.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

LEAGUE_REFERENCE_KMH = 146.0


def _finite(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("velocity input must be finite")
    return value


@dataclass(frozen=True)
class LinearVelocityMap:
    raw_reference: float = 84.0
    center_kmh: float = LEAGUE_REFERENCE_KMH
    slope: float = 0.32

    def raw_to_kmh(self, raw_velocity: float) -> float:
        raw = _finite(raw_velocity)
        return self.center_kmh + (raw - self.raw_reference) * self.slope

    def kmh_to_raw(self, kmh: float) -> float:
        if self.slope <= 0:
            raise ValueError("slope must be positive")
        return self.raw_reference + (_finite(kmh) - self.center_kmh) / self.slope


@dataclass(frozen=True)
class PiecewiseVelocityMap:
    raw_reference: float = 84.0
    center_kmh: float = LEAGUE_REFERENCE_KMH
    central_slope: float = 0.32
    tail_slope: float = 0.075
    low_knot: float = 60.0
    high_knot: float = 140.0

    def raw_to_kmh(self, raw_velocity: float) -> float:
        raw = _finite(raw_velocity)
        if raw < self.low_knot:
            at_knot = self.center_kmh + (self.low_knot - self.raw_reference) * self.central_slope
            return at_knot + (raw - self.low_knot) * self.tail_slope
        if raw > self.high_knot:
            at_knot = self.center_kmh + (self.high_knot - self.raw_reference) * self.central_slope
            return at_knot + (raw - self.high_knot) * self.tail_slope
        return self.center_kmh + (raw - self.raw_reference) * self.central_slope

    def kmh_to_raw(self, kmh: float) -> float:
        value = _finite(kmh)
        low_kmh = self.raw_to_kmh(self.low_knot)
        high_kmh = self.raw_to_kmh(self.high_knot)
        if value < low_kmh:
            return self.low_knot + (value - low_kmh) / self.tail_slope
        if value > high_kmh:
            return self.high_knot + (value - high_kmh) / self.tail_slope
        return self.raw_reference + (value - self.center_kmh) / self.central_slope


@dataclass(frozen=True)
class SoftVelocityMap:
    raw_reference: float = 84.0
    center_kmh: float = LEAGUE_REFERENCE_KMH
    amplitude_kmh: float = 15.0
    raw_scale: float = 46.0

    def raw_to_kmh(self, raw_velocity: float) -> float:
        raw = _finite(raw_velocity)
        return self.center_kmh + self.amplitude_kmh * math.tanh((raw - self.raw_reference) / self.raw_scale)

    def kmh_to_raw(self, kmh: float) -> float:
        value = _finite(kmh)
        ratio = (value - self.center_kmh) / self.amplitude_kmh
        # Exact tails are asymptotic and intentionally have no finite inverse.
        ratio = max(-0.999999, min(0.999999, ratio))
        return self.raw_reference + self.raw_scale * math.atanh(ratio)


@dataclass(frozen=True)
class VelocityGameplayContract:
    physical_reference_kmh: float = LEAGUE_REFERENCE_KMH
    gameplay_reference: float = 100.0
    gameplay_points_per_kmh: float = 1.0

    def kmh_to_gameplay(self, effective_kmh: float) -> float:
        return self.gameplay_reference + (
            _finite(effective_kmh) - self.physical_reference_kmh
        ) * self.gameplay_points_per_kmh

    def gameplay_to_kmh(self, gameplay_velocity: float) -> float:
        if self.gameplay_points_per_kmh <= 0:
            raise ValueError("gameplay_points_per_kmh must be positive")
        return self.physical_reference_kmh + (
            _finite(gameplay_velocity) - self.gameplay_reference
        ) / self.gameplay_points_per_kmh

    def contact_delta(self, effective_kmh: float) -> float:
        # H3.2.1 is frozen.  This adapter changes only the hitter Contact input.
        return self.gameplay_reference - self.kmh_to_gameplay(effective_kmh)


@dataclass(frozen=True)
class VelocityWorkloadModel:
    """Physical-km/h role effort and fatigue skeleton.

    ``effort`` is contextual usage, not a second rating.  Fatigue is a normalized
    workload state.  Stamina 100 is the reference and higher Stamina slows loss.
    """

    effort_bonus_kmh_at_max: float = 1.5
    fatigue_loss_kmh_at_one: float = 2.4

    def effective_kmh(
        self,
        base_avg_kmh: float,
        effort: float,
        fatigue: float,
        stamina: float = 100.0,
    ) -> float:
        base = _finite(base_avg_kmh)
        effort = max(0.0, min(1.0, _finite(effort)))
        fatigue = max(0.0, _finite(fatigue))
        stamina = max(30.0, min(250.0, _finite(stamina)))
        boost = self.effort_bonus_kmh_at_max * effort ** 0.90
        stamina_factor = 100.0 / stamina
        loss = self.fatigue_loss_kmh_at_one * fatigue ** 1.20 * stamina_factor
        return base + boost - loss


@dataclass(frozen=True)
class MaxVelocityModel:
    starter_gap_mean: float
    starter_gap_sd: float
    reliever_gap_mean: float
    reliever_gap_sd: float

    def expected_max(self, avg_kmh: float, role: str) -> float:
        if role == "starter":
            return _finite(avg_kmh) + self.starter_gap_mean
        if role == "reliever":
            return _finite(avg_kmh) + self.reliever_gap_mean
        raise ValueError(f"unknown role: {role}")
