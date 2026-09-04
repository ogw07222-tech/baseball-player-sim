"""Application facade for presentation clients.

This module deliberately depends on domain objects and presentation DTOs, never the
other way around. A future HTTP/desktop bridge can expose this facade unchanged.
"""
from __future__ import annotations

from ..player import Player
from ..presentation.dashboard_view_model import DashboardViewModel
from ..presentation.season_view_model import SeasonViewModel
from .dashboard_service import DashboardService
from .season_service import SeasonService


class GameService:
    def __init__(self) -> None:
        self.dashboard_service = DashboardService()
        self.season_service = SeasonService()

    def get_dashboard(self, player: Player, **kwargs: object) -> DashboardViewModel:
        return self.dashboard_service.build(player, **kwargs)

    def get_season(self, player: Player, **kwargs: object) -> SeasonViewModel:
        return self.season_service.build(player, **kwargs)
