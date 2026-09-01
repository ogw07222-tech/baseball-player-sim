"""Trait definitions and random assignment for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import config
from .rng import RNG


class TraitPolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Trait:
    key: str
    name: str
    polarity: TraitPolarity
    tags: frozenset[str]


TRAIT_CATALOG: tuple[Trait, ...] = (
    Trait("fastball_specialist", "직구 특화", TraitPolarity.POSITIVE, frozenset({"batting", "pitch_type"})),
    Trait("fastball_weakness", "직구 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "pitch_type"})),
    Trait("breaking_ball_response", "변화구 대응", TraitPolarity.POSITIVE, frozenset({"batting", "pitch_type"})),
    Trait("breaking_ball_weakness", "변화구 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "pitch_type"})),
    Trait("high_velocity_strength", "고속구 강점", TraitPolarity.POSITIVE, frozenset({"batting", "velocity"})),
    Trait("high_velocity_weakness", "고속구 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "velocity"})),
    Trait("low_pitch_strength", "낮은 공 강점", TraitPolarity.POSITIVE, frozenset({"batting", "zone"})),
    Trait("low_pitch_weakness", "낮은 공 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "zone"})),
    Trait("inside_pitch_strength", "몸쪽 강점", TraitPolarity.POSITIVE, frozenset({"batting", "zone"})),
    Trait("inside_pitch_weakness", "몸쪽 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "zone"})),
    Trait("vs_lhp_strength", "좌완 강점", TraitPolarity.POSITIVE, frozenset({"batting", "platoon"})),
    Trait("vs_lhp_weakness", "좌완 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "platoon"})),
    Trait("vs_rhp_strength", "우완 강점", TraitPolarity.POSITIVE, frozenset({"batting", "platoon"})),
    Trait("vs_rhp_weakness", "우완 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "platoon"})),
    Trait("two_strike_strength", "2스트라이크 강점", TraitPolarity.POSITIVE, frozenset({"batting", "count"})),
    Trait("clutch", "클러치", TraitPolarity.POSITIVE, frozenset({"batting", "pressure"})),
    Trait("pressure_weakness", "압박 상황 취약", TraitPolarity.NEGATIVE, frozenset({"batting", "pressure"})),
    Trait("steal_sense", "도루 센스", TraitPolarity.POSITIVE, frozenset({"baserunning"})),
    Trait("defense_sense", "수비 센스", TraitPolarity.POSITIVE, frozenset({"defense"})),
    Trait("fast_growth", "빠른 성장", TraitPolarity.POSITIVE, frozenset({"growth"})),
    Trait("slow_growth", "느린 성장", TraitPolarity.NEGATIVE, frozenset({"growth"})),
    Trait("volatile", "기복이 심함", TraitPolarity.NEGATIVE, frozenset({"form"})),
    Trait("consistent", "꾸준함", TraitPolarity.POSITIVE, frozenset({"form"})),
    Trait("injury_risk", "부상 위험", TraitPolarity.NEGATIVE, frozenset({"injury"})),
    Trait("quick_recovery", "회복이 빠름", TraitPolarity.POSITIVE, frozenset({"injury"})),
)

CONFLICTS = {
    frozenset(("fastball_specialist", "fastball_weakness")),
    frozenset(("breaking_ball_response", "breaking_ball_weakness")),
    frozenset(("high_velocity_strength", "high_velocity_weakness")),
    frozenset(("low_pitch_strength", "low_pitch_weakness")),
    frozenset(("inside_pitch_strength", "inside_pitch_weakness")),
    frozenset(("vs_lhp_strength", "vs_lhp_weakness")),
    frozenset(("vs_rhp_strength", "vs_rhp_weakness")),
    frozenset(("fast_growth", "slow_growth")),
    frozenset(("volatile", "consistent")),
}


def traits_conflict(a: Trait, b: Trait) -> bool:
    return frozenset((a.key, b.key)) in CONFLICTS


def generate_random_traits(rng: RNG) -> list[Trait]:
    target_count = rng.weighted_choice(config.INITIAL_TRAIT_COUNT_WEIGHTS)
    candidates = list(TRAIT_CATALOG)
    selected: list[Trait] = []
    while candidates and len(selected) < target_count:
        trait = rng.choice(candidates)
        candidates.remove(trait)
        if any(traits_conflict(trait, existing) for existing in selected):
            continue
        selected.append(trait)
    return selected


def has_trait(traits: list[Trait], key: str) -> bool:
    return any(trait.key == key for trait in traits)
