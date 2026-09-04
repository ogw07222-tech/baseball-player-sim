"""Read-only adapter from Player aggregate to DashboardViewModel."""
from __future__ import annotations

from . import __init__ as _package_marker  # noqa: F401
from ..player import Player
from ..presentation.dashboard_view_model import (
    AbilityViewModel,
    DashboardViewModel,
    PlayerSummaryViewModel,
    SeasonStatsViewModel,
    TraitViewModel,
)

STAT_LABELS = {
    "contact": "컨택",
    "power": "파워",
    "discipline": "선구안",
    "speed": "주력",
    "defense": "수비",
    "throwing": "송구",
    "stamina": "체력",
    "durability": "내구성",
    "mentality": "멘탈",
    "talent": "재능",
}


class DashboardService:
    """Build display data without invoking simulation or mutating Player."""

    def build(self, player: Player, *, year: int | None = None, progress: dict[str, object] | None = None) -> DashboardViewModel:
        before = player.as_dict()
        current = self._current_line(player, year)
        abilities = tuple(
            AbilityViewModel(key=key, label=label, rating=int(getattr(player.stats, key)))
            for key, label in STAT_LABELS.items()
        )
        traits = tuple(
            TraitViewModel(
                name=trait.name,
                category=next(iter(sorted(trait.tags)), "general"),
                tone=trait.polarity.value,
            )
            for trait in player.traits
        )
        story = tuple(self._story_event(event) for event in player.event_history[-8:])
        view_model = DashboardViewModel(
            player=PlayerSummaryViewModel(
                name=player.name,
                age=player.age,
                position=player.position,
                bats_throws=player.bats_throws,
                team=player.team,
                roster_level=player.roster_level,
                form=player.form,
                career_year=max(1, len(player.seasons)) if player.seasons else None,
            ),
            abilities=abilities,
            season_stats=SeasonStatsViewModel(
                G=current.G,
                PA=current.PA,
                AVG=current.AVG,
                OBP=current.OBP,
                SLG=current.SLG,
                OPS=current.OPS,
                HR=current.HR,
                RBI=current.RBI,
                SB=current.SB,
            ),
            condition="unknown",
            fatigue=float(player.fatigue),
            injury=player.injury.name if player.injury else None,
            form=player.form,
            traits=traits,
            season_story=story,
            progress=dict(progress or {}),
        )
        if player.as_dict() != before:
            raise RuntimeError("dashboard adapter must be read-only")
        return view_model

    @staticmethod
    def _current_line(player: Player, year: int | None):
        if year is not None:
            for season in reversed(player.seasons):
                if season.year == year:
                    return season.first_team
        if player.seasons:
            return player.seasons[-1].first_team
        return player.high_school_stats

    @staticmethod
    def _story_event(event: dict[str, object]) -> dict[str, object]:
        return {
            "date": str(event.get("date", event.get("year", ""))),
            "title": str(event.get("title", event.get("event", event.get("name", "커리어 이벤트")))),
            "detail": str(event.get("detail", event.get("description", ""))),
            "category": str(event.get("category", "NORMAL")).upper(),
        }
