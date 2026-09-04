"""Stable DTOs exposed to web/presentation clients.

These classes contain already-computed values only. They intentionally do not
import simulation, growth, balance, or probability helpers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AbilityViewModel:
    key: str
    label: str
    rating: int
    delta: int = 0
    trend: str = "flat"


@dataclass(frozen=True)
class TraitViewModel:
    name: str
    category: str
    tone: str


@dataclass(frozen=True)
class PlayerSummaryViewModel:
    name: str
    age: int
    position: str
    bats_throws: str
    team: str | None
    roster_level: str
    form: str
    number: int | None = None
    career_year: int | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class SeasonStatsViewModel:
    G: int
    PA: int
    AVG: float
    OBP: float
    SLG: float
    OPS: float
    HR: int
    RBI: int
    SB: int
    WAR: float | None = None


@dataclass(frozen=True)
class DashboardViewModel:
    player: PlayerSummaryViewModel
    abilities: tuple[AbilityViewModel, ...]
    season_stats: SeasonStatsViewModel
    condition: str
    fatigue: float
    injury: str | None
    form: str
    traits: tuple[TraitViewModel, ...]
    league_code: str = "KBO"
    league_name: str = "KBO League"
    recent_games: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    next_game: dict[str, Any] | None = None
    season_story: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    title_race: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    progress: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
