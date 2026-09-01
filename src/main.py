"""Minimal Phase 1 terminal smoke run."""

from __future__ import annotations

from .growth import apply_season_growth
from .player import Player
from .rng import RNG


def main() -> None:
    rng = RNG(seed=20260902)
    player = Player.random("Prototype Player", rng)
    print(f"{player.name} | age={player.age}")
    print(player.stats.as_dict())
    print("traits:", [trait.name for trait in player.traits])
    result = apply_season_growth(player, rng)
    print("season growth:", result)


if __name__ == "__main__":
    main()
