"""PA-level pitcher adapter for the frozen H3.2.1 hitter engine.

The adapter deliberately keeps production H3.2.1 code unchanged.  It expresses
pitcher influence through the existing public HittingEngine inputs:

1. Control -> legacy H3 control input (zone/count pathway)
2. Velocity + Breaking -> per-swing Contact adjustment
3. Stuff + Breaking -> per-swing Power adjustment as a contact-quality proxy
4. Existing H3.2.1 batted-ball / defense result resolution

Stamina, Resilience and Talent are accepted on the pitcher object but have zero
neutral-PA effect here by construction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.hitting.model import HitterSnapshot, HittingEngine, Pitch, PitcherSnapshot


@dataclass(frozen=True)
class CalibrationWeights:
    """Small, interpretable influence set used by the calibration search.

    Units are effective hitter-stat points per one pitcher-rating point away
    from the 100 reference, except ``w_control_zone`` which scales the legacy
    H3 control delta around 100.
    """

    w_control_zone: float = 0.80
    w_velocity_contact: float = 0.10
    w_breaking_contact: float = 0.06
    w_stuff_quality: float = 0.10
    w_breaking_quality: float = 0.05

    def as_dict(self) -> dict[str, float]:
        return {
            "w_control_zone": self.w_control_zone,
            "w_velocity_contact": self.w_velocity_contact,
            "w_breaking_contact": self.w_breaking_contact,
            "w_stuff_quality": self.w_stuff_quality,
            "w_breaking_quality": self.w_breaking_quality,
        }


class PitcherLike(Protocol):
    velocity: float
    stuff: float
    control: float
    breaking: float
    stamina: float
    resilience: float
    talent: float


@dataclass(frozen=True)
class NeutralPAEffectiveStats:
    velocity: float
    stuff: float
    control: float
    breaking: float


class PitcherPAAdapter:
    """Translate visible pitcher stats into isolated H3.2.1 modifiers."""

    def __init__(self, pitcher: PitcherLike, weights: CalibrationWeights) -> None:
        self.pitcher = pitcher
        self.weights = weights

    def effective_stats(self) -> NeutralPAEffectiveStats:
        # Neutral PA intentionally ignores stamina/resilience/talent.
        return NeutralPAEffectiveStats(
            velocity=float(self.pitcher.velocity),
            stuff=float(self.pitcher.stuff),
            control=float(self.pitcher.control),
            breaking=float(self.pitcher.breaking),
        )

    def pitcher_snapshot(self) -> PitcherSnapshot:
        e = self.effective_stats()
        # H3's legacy ``stuff`` and ``movement`` channels stay neutral here.
        # That prevents the old all-purpose pitcher semantics from leaking into
        # the new visible-stat model.  Only Control uses the zone/location input.
        return PitcherSnapshot(
            stuff=100.0,
            control=100.0 + self.weights.w_control_zone * (e.control - 100.0),
            movement=100.0,
        )

    def pitch_stat_modifier(self, _pitch: Pitch, _strikes: int) -> tuple[float, float]:
        e = self.effective_stats()
        contact_delta = -(
            self.weights.w_velocity_contact * (e.velocity - 100.0)
            + self.weights.w_breaking_contact * (e.breaking - 100.0)
        )
        quality_proxy_delta = -(
            self.weights.w_stuff_quality * (e.stuff - 100.0)
            + self.weights.w_breaking_quality * (e.breaking - 100.0)
        )
        return contact_delta, quality_proxy_delta

    def make_engine(self, hitter: HitterSnapshot, defense: float, rng) -> HittingEngine:
        return HittingEngine(
            hitter=hitter,
            pitcher=self.pitcher_snapshot(),
            defense=defense,
            rng=rng,
            pitch_stat_modifier=self.pitch_stat_modifier,
        )
