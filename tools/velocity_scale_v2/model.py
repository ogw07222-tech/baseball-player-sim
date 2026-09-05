from __future__ import annotations
from dataclasses import dataclass
import math

LEAGUE_REFERENCE_KMH = 146.0
GAMEPLAY_REFERENCE = 100.0

@dataclass(frozen=True)
class LinearNarrowMap:
    reference_rating: float = 100.0
    reference_kmh: float = LEAGUE_REFERENCE_KMH
    kmh_per_rating: float = 0.28
    def raw_to_kmh(self, raw: float) -> float:
        return self.reference_kmh + (raw-self.reference_rating)*self.kmh_per_rating

@dataclass(frozen=True)
class PiecewiseMildTailMap:
    reference_rating: float = 100.0
    reference_kmh: float = LEAGUE_REFERENCE_KMH
    central_slope: float = 0.28
    tail_start: float = 140.0
    tail_slope: float = 0.20
    safety_start: float = 180.0
    safety_slope: float = 0.05
    def raw_to_kmh(self, raw: float) -> float:
        if raw <= self.tail_start:
            return self.reference_kmh + (raw-self.reference_rating)*self.central_slope
        y0 = self.reference_kmh + (self.tail_start-self.reference_rating)*self.central_slope
        if raw <= self.safety_start:
            return y0 + (raw-self.tail_start)*self.tail_slope
        y1 = y0 + (self.safety_start-self.tail_start)*self.tail_slope
        return y1 + (raw-self.safety_start)*self.safety_slope

@dataclass(frozen=True)
class SoftMildMap:
    reference_rating: float = 100.0
    reference_kmh: float = LEAGUE_REFERENCE_KMH
    slope: float = 0.30
    compression_scale: float = 300.0
    def raw_to_kmh(self, raw: float) -> float:
        d = raw-self.reference_rating
        return self.reference_kmh + self.slope*d/(1.0+abs(d)/self.compression_scale)

@dataclass(frozen=True)
class GameplayVelocityMap:
    points_per_kmh: float = 1.5
    reference_kmh: float = LEAGUE_REFERENCE_KMH
    def kmh_to_gameplay(self, kmh: float) -> float:
        return GAMEPLAY_REFERENCE + (kmh-self.reference_kmh)*self.points_per_kmh

@dataclass(frozen=True)
class PhysicalEffortLayer:
    effort_bonus_kmh: float = 0.0
    fatigue_loss_per_unit: float = 1.0
    def effective_kmh(self, base_kmh: float, fatigue: float = 0.0) -> float:
        return base_kmh + self.effort_bonus_kmh - max(0.0, fatigue)*self.fatigue_loss_per_unit


def finite_monotonic(mapping, xs: tuple[int,...]) -> bool:
    vals=[mapping.raw_to_kmh(x) for x in xs]
    return all(math.isfinite(v) for v in vals) and all(a < b for a,b in zip(vals,vals[1:]))
