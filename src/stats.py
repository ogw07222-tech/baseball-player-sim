"""Player base-stat model and random generation helpers."""
from __future__ import annotations

from dataclasses import dataclass, fields

from . import config
from .rng import RNG


def _truncated_gauss_int(rng: RNG, mean: float, stddev: float, minimum: int = 0) -> int:
    for _ in range(64):
        value = int(round(rng.gauss(mean, stddev)))
        if value >= minimum:
            return value
    return max(minimum, int(round(mean)))


def _generate_talent(rng: RNG) -> int:
    component = rng.weighted_choice([(entry, entry[0]) for entry in config.TALENT_MIXTURE])
    _, mean, stddev, minimum = component
    return _truncated_gauss_int(rng, mean, stddev, minimum)


@dataclass
class PlayerStats:
    contact: int
    power: int
    discipline: int
    speed: int
    defense: int
    throwing: int
    stamina: int
    durability: int
    mentality: int
    talent: int

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, int):
                raise TypeError(f"{field.name} must be int")
            if value < config.STAT_MIN:
                raise ValueError(f"{field.name} must be >= {config.STAT_MIN}")

    def as_dict(self) -> dict[str, int]:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "PlayerStats":
        return cls(**{name: int(data[name]) for name in config.STAT_NAMES})

    def apply_delta(self, stat_name: str, delta: int) -> int:
        if stat_name not in config.STAT_NAMES:
            raise KeyError(f"unknown stat: {stat_name}")
        new_value = max(config.STAT_MIN, getattr(self, stat_name) + int(delta))
        setattr(self, stat_name, new_value)
        return new_value

    def current_ability(self) -> float:
        weights = {
            "contact": 1.2, "power": 1.1, "discipline": 1.0, "speed": 0.55,
            "defense": 0.75, "throwing": 0.35, "stamina": 0.30,
            "durability": 0.30, "mentality": 0.45,
        }
        return sum(getattr(self, name) * weight for name, weight in weights.items()) / sum(weights.values())


def _generate_cohort_stats(
    rng: RNG,
    position: str,
    stat_bonus: float,
    shared_offset_sd: float,
) -> PlayerStats:
    if position not in config.POSITIONS:
        raise ValueError(f"unsupported position: {position}")
    adjustments = config.POSITION_ADJUSTMENTS.get(position, {})
    shared_offset = rng.gauss(0.0, shared_offset_sd) if shared_offset_sd > 0 else 0.0
    values: dict[str, int] = {}
    for name, (mean, stddev) in config.INITIAL_STAT_DISTRIBUTIONS.items():
        base = _truncated_gauss_int(
            rng,
            mean + stat_bonus + shared_offset,
            stddev,
            config.STAT_MIN,
        )
        values[name] = max(config.STAT_MIN, base + adjustments.get(name, 0))
    values["talent"] = _generate_talent(rng)
    return PlayerStats(**values)


def generate_random_stats(rng: RNG, position: str = "SS") -> PlayerStats:
    """Generate the protagonist/prospect cohort.

    Individual stats are still sampled first; current ability is never sampled
    directly. A shared prospect offset creates the intended correlated spread.
    """
    return _generate_cohort_stats(
        rng,
        position,
        config.PLAYER_STARTING_STAT_BONUS,
        config.PLAYER_STARTING_SHARED_OFFSET_SD,
    )


def generate_high_school_npc_stats(rng: RNG, position: str = "SS") -> PlayerStats:
    """Generate a generic high-school population player for calibration/future NPCs."""
    return _generate_cohort_stats(
        rng,
        position,
        config.NPC_STARTING_STAT_BONUS,
        config.NPC_STARTING_SHARED_OFFSET_SD,
    )
