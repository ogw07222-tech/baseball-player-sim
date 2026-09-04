"""Test-side DTOs for H3.1."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class H3HitterProfile:
    contact: float = 100.0
    power: float = 100.0
    discipline: float = 100.0
    speed: float = 100.0
    handedness: str = "R"
    approach: str = "balanced"

    def __post_init__(self) -> None:
        if self.handedness not in {"L", "R"}:
            raise ValueError("handedness must be L or R")
        if self.approach not in {"pull", "balanced", "opposite"}:
            raise ValueError("unknown approach")


@dataclass(frozen=True)
class H3PitcherProfile:
    stuff: float = 100.0
    control: float = 100.0
    movement: float = 100.0
    handedness: str = "R"


@dataclass(frozen=True)
class H3DefenseProfile:
    defense: float = 100.0

VISIBLE_STAT_DIRECTION = ("contact", "power", "discipline", "speed", "defense", "resilience", "talent")
