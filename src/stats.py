"""Player base-stat model and generation helpers."""

from __future__ import annotations

from dataclasses import dataclass, fields

from . import config
from .rng import RNG


def _non_negative_int(value: float) -> int:
    return max(config.STAT_MIN, int(round(value)))


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

    def apply_delta(self, stat_name: str, delta: int) -> int:
        if stat_name not in config.STAT_NAMES:
            raise KeyError(f"unknown stat: {stat_name}")
        new_value = max(config.STAT_MIN, getattr(self, stat_name) + int(delta))
        setattr(self, stat_name, new_value)
        return new_value


def generate_random_stats(rng: RNG) -> PlayerStats:
    values = {
        name: _non_negative_int(rng.gauss(config.INITIAL_STAT_MEAN, config.INITIAL_STAT_STDDEV))
        for name in config.STAT_NAMES
        if name != "talent"
    }
    values["talent"] = _non_negative_int(
        rng.gauss(config.INITIAL_TALENT_MEAN, config.INITIAL_TALENT_STDDEV)
    )
    return PlayerStats(**values)
