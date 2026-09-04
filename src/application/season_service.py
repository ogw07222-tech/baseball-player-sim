"""Season hub adapter.

The current domain does not model full league standings/rosters. Missing league-wide
collections therefore remain empty instead of fabricating simulation results.
"""
from __future__ import annotations

from ..player import Player
from ..presentation.season_view_model import SeasonViewModel


class SeasonService:
    def build(self, player: Player, *, year: int | None = None, progress: dict[str, object] | None = None) -> SeasonViewModel:
        before = player.as_dict()
        selected = None
        if year is not None:
            selected = next((season for season in reversed(player.seasons) if season.year == year), None)
        elif player.seasons:
            selected = player.seasons[-1]

        season_year = int(year if year is not None else (selected.year if selected else 0))
        batting = ()
        if selected is not None:
            line = selected.first_team
            batting = ({
                "player": player.name,
                "G": line.G,
                "PA": line.PA,
                "AB": line.AB,
                "R": line.R,
                "H": line.H,
                "2B": line.doubles,
                "3B": line.triples,
                "HR": line.HR,
                "RBI": line.RBI,
                "SB": line.SB,
                "BB": line.BB,
                "SO": line.SO,
                "AVG": line.AVG,
                "OBP": line.OBP,
                "SLG": line.SLG,
                "OPS": line.OPS,
                "WAR": None,
                "is_user": True,
            },)

        view_model = SeasonViewModel(
            year=season_year,
            team_name=player.team,
            team_batting=batting,
            progress=dict(progress or {}),
        )
        if player.as_dict() != before:
            raise RuntimeError("season adapter must be read-only")
        return view_model
