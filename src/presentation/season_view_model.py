"""Season hub presentation DTOs."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SeasonViewModel:
    year: int
    league_code: str = "KBO"
    league_name: str = "KBO League"
    standings: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    hitting_leaderboards: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    pitching_leaderboards: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    recent_results: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    team_name: str | None = None
    team_batting: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    team_metrics: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    progress: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
