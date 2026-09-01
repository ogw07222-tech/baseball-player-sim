"""Player aggregate for the career simulator."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .rng import RNG
from .stats import PlayerStats, generate_random_stats
from .traits import Trait, generate_random_traits


@dataclass
class Player:
    name: str
    age: int
    stats: PlayerStats
    traits: list[Trait] = field(default_factory=list)
    nationality: str = "KOR"
    position: str | None = None
    growth_history: list[dict[str, object]] = field(default_factory=list)

    def advance_age(self, years: int = 1) -> None:
        if years < 0:
            raise ValueError("years must be non-negative")
        self.age += years

    @classmethod
    def random(cls, name: str, rng: RNG) -> "Player":
        return cls(
            name=name,
            age=rng.randint(config.INITIAL_AGE_MIN, config.INITIAL_AGE_MAX),
            stats=generate_random_stats(rng),
            traits=generate_random_traits(rng),
        )
