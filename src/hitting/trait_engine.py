"""Generic gameplay hooks for data-driven conditional Trait modifiers.

This subclass preserves the canonical HittingEngine formulas and RNG order while
allowing deterministic, pre-RNG Trait modifiers at the existing pitch decisions.
No Trait ID or content name is interpreted here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import parameters as P
from .defense import clamp
from .model import HittingEngine, Pitch, soft_delta


@dataclass(frozen=True)
class PitchTraitModifiers:
    contact_delta: float = 0.0
    power_delta: float = 0.0
    zone_swing_delta: float = 0.0
    chase_delta: float = 0.0
    foul_survival_delta: float = 0.0


TraitGameplayModifier = Callable[[Pitch, int, int], PitchTraitModifiers]


class TraitAwareHittingEngine(HittingEngine):
    """HittingEngine with generic conditional modifier hooks and zero new RNG."""

    def __init__(self, *args, trait_gameplay_modifier: TraitGameplayModifier, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.trait_gameplay_modifier = trait_gameplay_modifier
        self._active_trait_modifiers = PitchTraitModifiers()

    def _swing_probability(self, pitch: Pitch, balls: int, strikes: int) -> float:
        modifiers = self.trait_gameplay_modifier(pitch, balls, strikes)
        self._active_trait_modifiers = modifiers
        base = super()._swing_probability(pitch, balls, strikes)
        if pitch.is_strike:
            return clamp(base + modifiers.zone_swing_delta, P.ZONE_SWING_MIN, P.ZONE_SWING_MAX)
        return clamp(base + modifiers.chase_delta, P.CHASE_MIN, P.CHASE_MAX)

    def _contact_resolution(self, pitch: Pitch, strikes: int, protective_swing: bool = False) -> tuple[str, float, float]:
        modifiers = self._active_trait_modifiers
        contact_delta = modifiers.contact_delta
        power_delta = modifiers.power_delta
        if self.pitch_stat_modifier is not None:
            legacy_contact, legacy_power = self.pitch_stat_modifier(pitch, strikes)
            contact_delta += legacy_contact
            power_delta += legacy_power

        contact = self.hitter.contact + contact_delta
        cdelta = soft_delta(contact, P.CONTACT_POSITIVE_SOFT)
        difficulty = (
            (self.pitcher.stuff - 100) * .006
            + pitch.velocity_quality * .16
            + pitch.movement_quality * .18
            - pitch.hittable_quality * P.CONTACT_HITTABLE_WEIGHT
        )
        contact_score = cdelta * P.CONTACT_SCALE - difficulty
        touch_probability = clamp(P.BIP_BASE + contact_score * .22, .28, .965)
        if protective_swing:
            touch_probability = clamp(
                touch_probability * P.TWO_STRIKE_PROTECTIVE_TOUCH_SCALE,
                P.TWO_STRIKE_PROTECTIVE_TOUCH_MIN,
                P.TWO_STRIKE_PROTECTIVE_TOUCH_MAX,
            )
        if self.rng.random() > touch_probability:
            if protective_swing:
                rescue = P.TWO_STRIKE_PROTECTIVE_MISS_TO_FOUL
            else:
                rescue = P.MISS_TO_FOUL_ZONE_BASE if pitch.is_strike else P.MISS_TO_FOUL_BALL_BASE
                if strikes == 2:
                    discipline_delta = clamp(self.hitter.discipline - 100.0, -20.0, 40.0)
                    rescue += P.TWO_STRIKE_FOUL_RESCUE_BASE
                    rescue += discipline_delta * P.TWO_STRIKE_FOUL_DISCIPLINE_WEIGHT
            rescue += modifiers.foul_survival_delta
            if self.rng.random() < clamp(rescue, 0.0, P.MISS_TO_FOUL_CAP):
                return "foul", contact_delta, power_delta
            return "miss", contact_delta, power_delta

        foul_probability = clamp(
            P.FOUL_BASE - pitch.hittable_quality * .07
            + max(0, -contact_score) * .05
            + modifiers.foul_survival_delta,
            .22, .52,
        )
        if protective_swing:
            foul_probability = clamp(
                foul_probability + P.TWO_STRIKE_PROTECTIVE_FOUL_BONUS,
                P.TWO_STRIKE_PROTECTIVE_FOUL_MIN,
                P.TWO_STRIKE_PROTECTIVE_FOUL_MAX,
            )
        if self.rng.random() < foul_probability:
            return "foul", contact_delta, power_delta
        return "bip", contact_delta, power_delta
