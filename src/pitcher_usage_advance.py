"""Date-advance wrapper that keeps dynamic pitcher usage state persistent."""
from __future__ import annotations
from .pitcher_usage import PitcherUsageLeagueState
from .pitcher_usage_game_provider import DynamicPitcherGameProvider
from .production_advance import ProductionAdvanceService

class PitcherUsageProductionAdvanceService:
    """ProductionAdvanceService configured with the dynamic pitcher provider."""
    def __init__(self,engine)->None:
        existing=getattr(engine,"pitcher_usage_state",None)
        usage_state=existing if isinstance(existing,PitcherUsageLeagueState) else PitcherUsageLeagueState()
        engine.pitcher_usage_state=usage_state
        self.gameplay_provider=DynamicPitcherGameProvider(usage_state=usage_state)
        self.delegate=ProductionAdvanceService(engine,game_provider=self.gameplay_provider)
    @property
    def state(self):return self.delegate.state
    @property
    def schedule(self):return self.delegate.schedule
    @property
    def game_provider(self):return self.delegate.game_provider
    def advance_one_game(self):return self.delegate.advance_one_game()
    def advance_one_week(self):return self.delegate.advance_one_week()
    def advance_one_month(self):return self.delegate.advance_one_month()
