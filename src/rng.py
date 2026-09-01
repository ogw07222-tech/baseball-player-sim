"""Central random-number interface for reproducible simulations."""

from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class RNG:
    """Small wrapper around random.Random.

    Every simulation system should receive an RNG instance instead of using
    the module-level random functions. A seed therefore reproduces a run as
    long as call order and algorithms stay unchanged.
    """

    def __init__(self, seed: int | str | bytes | None = None) -> None:
        self.seed = seed
        self._random = random.Random(seed)

    def random(self) -> float:
        return self._random.random()

    def randint(self, a: int, b: int) -> int:
        return self._random.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self._random.uniform(a, b)

    def gauss(self, mu: float, sigma: float) -> float:
        return self._random.gauss(mu, sigma)

    def choice(self, values: Sequence[T]) -> T:
        return self._random.choice(values)

    def sample(self, values: Sequence[T], k: int) -> list[T]:
        return self._random.sample(values, k)

    def weighted_choice(self, items: Sequence[tuple[T, float]]) -> T:
        if not items:
            raise ValueError("items must not be empty")
        total = sum(weight for _, weight in items)
        if total <= 0:
            raise ValueError("sum of weights must be positive")
        target = self.uniform(0.0, total)
        upto = 0.0
        for item, weight in items:
            upto += weight
            if target <= upto:
                return item
        return items[-1][0]
