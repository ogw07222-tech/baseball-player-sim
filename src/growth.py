"""Season-level growth, growth explosions, and aging decline."""
from __future__ import annotations

from dataclasses import dataclass

from . import config
from .player import Player
from .rng import RNG
from .traits import has_trait

GROWABLE_STATS = config.HITTER_STAT_NAMES


@dataclass(frozen=True)
class GrowthResult:
    age_before: int
    age_after: int
    deltas: dict[str, int]
    explosion: bool


def _age_bias(age: int) -> float:
    for (low, high), bias in config.AGE_GROWTH_BIAS.items():
        if low <= age <= high:
            return bias
    return 0.0


def _trait_growth_bias(player: Player) -> float:
    if has_trait(player.traits, "fast_growth"):
        return 0.9
    if has_trait(player.traits, "slow_growth"):
        return -0.9
    return 0.0


def _explosion_chance(player: Player) -> float:
    chance = config.GROWTH_EXPLOSION_BASE_CHANCE
    chance += max(0, player.stats.talent - config.GROWTH_TALENT_REFERENCE) * config.GROWTH_EXPLOSION_TALENT_SCALE
    if has_trait(player.traits, "fast_growth"):
        chance *= 1.25
    if has_trait(player.traits, "slow_growth"):
        chance *= 0.80
    return max(0.001, min(0.20, chance))


def _normal_growth_delta(player: Player, stat_name: str, rng: RNG) -> int:
    current = getattr(player.stats, stat_name)
    talent_effect = (player.stats.talent - config.GROWTH_TALENT_REFERENCE) * config.GROWTH_TALENT_SCALE
    high_stat_damping = max(0.0, current - 100.0) * config.GROWTH_CURRENT_STAT_DAMPING
    mean = _age_bias(player.age) + talent_effect + _trait_growth_bias(player) - high_stat_damping
    if player.age >= 32 and mean < 0:
        mean *= config.AGING_MULTIPLIER.get(stat_name, 1.0)
    return int(round(rng.gauss(mean, config.GROWTH_BASE_STDDEV)))


def apply_season_growth(player: Player, rng: RNG) -> GrowthResult:
    age_before = player.age
    deltas: dict[str, int] = {}
    for stat_name in GROWABLE_STATS:
        delta = _normal_growth_delta(player, stat_name, rng)
        before = getattr(player.stats, stat_name)
        after = player.stats.apply_delta(stat_name, delta)
        deltas[stat_name] = after - before

    explosion = rng.random() < _explosion_chance(player)
    if explosion:
        count = rng.randint(1, min(3, len(GROWABLE_STATS)))
        for stat_name in rng.sample(GROWABLE_STATS, count):
            bonus = rng.randint(config.GROWTH_EXPLOSION_MIN_BONUS, config.GROWTH_EXPLOSION_MAX_BONUS)
            before = getattr(player.stats, stat_name)
            after = player.stats.apply_delta(stat_name, bonus)
            deltas[stat_name] += after - before

    player.advance_age(1)
    result = GrowthResult(age_before, player.age, deltas, explosion)
    player.growth_history.append({"age_before": result.age_before, "age_after": result.age_after, "deltas": dict(result.deltas), "explosion": result.explosion})
    return result
