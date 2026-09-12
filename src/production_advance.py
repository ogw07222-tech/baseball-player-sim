"""Career/date integration for the canonical production full-game provider.

This module composes existing career participation/postgame rules with the
provider-based date advance foundation. It does not own gameplay probabilities,
roster evaluation math, growth, injury, or event formulas.

The canonical default game provider is the dynamic pitcher-usage provider from
PR #32. The lower-level ProductionGameProvider remains available only when a
caller explicitly injects it for compatibility or focused tests.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Iterable, Mapping, Sequence

from . import config
from .career import CareerEngine, SeasonFinalizationResult
from .career_source_facts import CareerSourceFact
from .game_provider import GameFixture, ProductionGameProvider
from .game_result import ProductionGameResult
from .interactive_events import InteractiveEvent, InteractiveEventResolution, event_state_for_engine, maybe_generate_interactive_event, resolve_interactive_event
from .stat_aggregation import GamePerformance,HitterCountingStats,PitcherCountingStats,SeasonStatLine,career_stats_from_records,season_stats_from_record
from .time_advance import AdvanceOrchestrator,AdvancePipelineState,AdvanceSummary,ScheduleProvider


class SeasonCompleteError(RuntimeError):
    """Advance commands require explicit season finalization after game 144."""


@dataclass
class ProductionAdvancePipelineState(AdvancePipelineState):
    team_wins:int=0;team_losses:int=0;team_ties:int=0;team_record_supported:bool=False
    @staticmethod
    def _result_from_score(score:tuple[int,int]|None)->str|None:
        if score is None:return None
        runs_for,runs_against=score
        if runs_for>runs_against:return "W"
        if runs_for<runs_against:return "L"
        return "T"
    def add_game(self,game:GamePerformance)->None:
        super().add_game(game);score_result=self._result_from_score(game.score)
        if score_result is not None:
            if game.team_result is not None and game.team_result!=score_result:raise ValueError("team_result must match exact final score")
            result=score_result
        else:result=game.team_result;self.team_record_supported=False
        if result=="W":self.team_wins+=1
        elif result=="L":self.team_losses+=1
        elif result=="T":self.team_ties+=1
        else:self.team_record_supported=False
    @property
    def team_record(self)->dict[str,int|bool]:return {"wins":self.team_wins,"losses":self.team_losses,"ties":self.team_ties,"supported":self.team_record_supported}
    def as_dict(self)->dict[str,object]:payload=super().as_dict();payload["team_record"]=dict(self.team_record);return payload
    @classmethod
    def from_advance_state(cls,state:AdvancePipelineState,*,team_record_supported:bool=False)->"ProductionAdvancePipelineState":return cls(current_date=state.current_date,season=state.season,career=state.career,completed_seasons=list(state.completed_seasons),recent_games=list(state.recent_games),history_limit=state.history_limit,team_record_supported=team_record_supported)
    @classmethod
    def from_dict(cls,data:Mapping[str,object],*,default_date:date|None=None)->"ProductionAdvancePipelineState":
        base=AdvancePipelineState.from_dict(data,default_date=default_date);raw=data.get("team_record")
        if isinstance(raw,Mapping):wins=int(raw.get("wins",0));losses=int(raw.get("losses",0));ties=int(raw.get("ties",0));supported=bool(raw.get("supported",True))
        else:wins=losses=ties=0;supported=False
        return cls(current_date=base.current_date,season=base.season,career=base.career,completed_seasons=list(base.completed_seasons),recent_games=list(base.recent_games),history_limit=base.history_limit,team_wins=wins,team_losses=losses,team_ties=ties,team_record_supported=supported)


@dataclass(frozen=True)
class CareerSeasonScheduleProvider(ScheduleProvider):
    dates:tuple[date,...]
    def __init__(self,year:int,games:int=config.KBO_FIRST_TEAM_GAMES)->None:
        out=[];cursor=date(int(year),4,1)
        while len(out)<int(games):
            if cursor.weekday()!=0:out.append(cursor)
            cursor+=timedelta(days=1)
        object.__setattr__(self,"dates",tuple(out))
    def next_game_after(self,after:date)->date|None:return next((d for d in self.dates if d>after),None)
    def game_dates(self,after:date,through:date)->Sequence[date]:return tuple(d for d in self.dates if after<d<=through)
    def game_index(self,game_date:date)->int:
        try:return self.dates.index(game_date)
        except ValueError as exc:raise KeyError(f"date is not in temporary career schedule: {game_date}") from exc


class CareerFixtureProvider:
    def __init__(self,engine:CareerEngine,schedule:CareerSeasonScheduleProvider)->None:self.engine=engine;self.schedule=schedule
    def fixture_for(self,game_date:date)->GameFixture:
        session=self.engine.start_pro_season();user_team=self.engine.player.team
        if not user_team:raise RuntimeError("career player has no team")
        opponents=[str(row["name"]) for row in config.KBO_TEAMS if row["name"]!=user_team];index=self.schedule.game_index(game_date);opponent=opponents[index%len(opponents)]
        if index%2==0:away,home=opponent,user_team
        else:away,home=user_team,opponent
        return GameFixture(game_date,away,home,session.current_level)


class CareerGameAdvanceProvider:
    def __init__(self,engine:CareerEngine,schedule:CareerSeasonScheduleProvider,game_provider:ProductionGameProvider|None=None)->None:
        self.engine=engine;self.schedule=schedule;self.fixture_provider=CareerFixtureProvider(engine,schedule);self._pending_source_facts:list[CareerSourceFact]=[];self._generated_interactive_events:list[InteractiveEvent]=[]
        if game_provider is None:
            from .pitcher_usage import PitcherUsageLeagueState
            from .pitcher_usage_game_provider import DynamicPitcherGameProvider
            existing=getattr(engine,"pitcher_usage_state",None);usage_state=existing if isinstance(existing,PitcherUsageLeagueState) else PitcherUsageLeagueState();engine.pitcher_usage_state=usage_state;game_provider=DynamicPitcherGameProvider(usage_state=usage_state)
        self.game_provider=game_provider;self.last_result:ProductionGameResult|None=None;self.recent_results:list[ProductionGameResult]=[];self.history_limit=10
    def drain_source_facts(self)->tuple[CareerSourceFact,...]:
        facts=tuple(self._pending_source_facts);self._pending_source_facts.clear();return facts
    def drain_interactive_events(self)->tuple[InteractiveEvent,...]:
        events=tuple(self._generated_interactive_events);self._generated_interactive_events.clear();return events
    def _participation(self)->tuple[bool,str]:
        session=self.engine.start_pro_season()
        if self.engine.player.injury is not None:return False,"INJURED"
        started=self.engine.rng.random()<self.engine._play_probability(session.current_level)
        if started:return True,"FARM" if session.current_level=="FARM" else "STARTED"
        return False,"BENCH"
    def _postgame(self,started:bool,game_date:date)->None:
        session=self.engine.start_pro_season()
        if self.engine.player.injury is not None and not started:self.engine._recover_day();self.engine._update_form();self.engine._reconsider_roster(session)
        elif started:self.engine._fatigue_after_game();self.engine._maybe_injure();self.engine._update_form();self.engine._reconsider_roster(session)
        else:self.engine._recover_day();self.engine._update_form();self.engine._reconsider_roster(session)
        event=maybe_generate_interactive_event(player=self.engine.player,state=event_state_for_engine(self.engine),seed=self.engine.rng.seed,season=self.engine.year,game_number=session.games_completed,simulated_date=game_date,level=session.current_level)
        if event is not None:self._generated_interactive_events.append(event)
    def advance_game(self,game_date:date)->GamePerformance:
        self.engine.begin_source_fact_capture(game_date,'post_game');session=self.engine.start_pro_season()
        if session.finished:raise RuntimeError("professional season already completed")
        # Production P1 no longer auto-resolves legacy v0.4 decision events.
        # New InteractiveEvent generation is non-blocking and declarative.
        fixture=self.fixture_provider.fixture_for(game_date);started,reason=self._participation();result=self.game_provider.run_game(fixture,self.engine.rng,user_player=self.engine.player,user_team=self.engine.player.team,user_started=started,participation_reason=reason)
        self.last_result=result;self.recent_results.append(result)
        if len(self.recent_results)>self.history_limit:del self.recent_results[:len(self.recent_results)-self.history_limit]
        session.games_completed+=1;hitter_stats=HitterCountingStats()
        if started and result.user_player_id:
            user_line=result.player_line(result.user_player_id)
            if user_line is None:raise AssertionError("started career player is missing from full-game lineup")
            target=session.record.first_team if session.current_level=="FIRST" else session.record.farm;target.add(user_line.batting_line);hitter_stats=user_line.stats
            if session.current_level=="FIRST" and self.engine.player.debut_year is None:self.engine.player.debut_year=self.engine.year
        team=self.engine.player.team
        if not team:raise RuntimeError("career player lost team during game")
        opponent=fixture.home_team if team==fixture.away_team else fixture.away_team;score=result.score_for(team)
        performance=GamePerformance(game_date=game_date,level=session.current_level,started=started,opponent=opponent,hitter_stats=hitter_stats,pitcher_stats=PitcherCountingStats(),team_result=result.team_result_for(team),score=score,notable_events=result.notable_events)
        self._postgame(started,game_date);self._pending_source_facts.extend(self.engine.drain_source_facts());return performance


class CompositionalAdvanceOrchestrator(AdvanceOrchestrator):
    def _advance_dates(self,period_type:str,start:date,end:date,dates:Iterable[date])->AdvanceSummary:
        scheduled=tuple(dates);summary=super()._advance_dates(period_type,start,end,scheduled);compositional_end=scheduled[-1] if scheduled else start;self.state.current_date=compositional_end
        drain=getattr(self.game_provider,'drain_source_facts',None);facts=tuple(drain()) if callable(drain) else ()
        return replace(summary,end_date=compositional_end,source_facts=facts)


class ProductionAdvanceService:
    """Canonical game/week/month advance plus explicit season-boundary lifecycle."""
    def __init__(self,engine:CareerEngine,*,game_provider:ProductionGameProvider|None=None)->None:
        self.engine=engine;self._injected_game_provider=game_provider;self.schedule=CareerSeasonScheduleProvider(engine.year);session=engine.current_session;games_completed=session.games_completed if session is not None else 0;self._bind(self._state_for_engine(games_completed))
    def _bind(self,state:ProductionAdvancePipelineState)->None:
        self.game_provider=CareerGameAdvanceProvider(self.engine,self.schedule,self._injected_game_provider);self.orchestrator=CompositionalAdvanceOrchestrator(state,self.schedule,self.game_provider,rating_provider=lambda:self.engine.player.stats.as_dict(),roster_provider=lambda:self.engine.current_session.current_level if self.engine.current_session is not None else self.engine.player.roster_level);self.engine.advance_state=state
    def _state_for_engine(self,games_completed:int)->ProductionAdvancePipelineState:
        existing=getattr(self.engine,"advance_state",None)
        if isinstance(existing,ProductionAdvancePipelineState):return existing
        if isinstance(existing,AdvancePipelineState):return ProductionAdvancePipelineState.from_advance_state(existing)
        current_date=self.schedule.dates[games_completed-1] if games_completed>0 else self.schedule.dates[0]-timedelta(days=1);session=self.engine.current_session;season=season_stats_from_record(session.record) if session is not None else SeasonStatLine(year=self.engine.year);records=list(self.engine.player.seasons)+([session.record] if session is not None else []);career=career_stats_from_records(records);return ProductionAdvancePipelineState(current_date=current_date,season=season,career=career,team_record_supported=games_completed==0)
    def _ensure_active_session(self)->None:
        if self.engine.phase!='PRO':raise RuntimeError("career is not in professional phase")
        if self.engine.current_session is None:self.engine.start_pro_season()
    def _ensure_advance_allowed(self)->None:
        self._ensure_active_session();session=self.engine.current_session
        if session is not None and session.finished:raise SeasonCompleteError("professional season is complete; finalize season before advancing")
    @property
    def state(self)->ProductionAdvancePipelineState:
        state=self.orchestrator.state
        if not isinstance(state,ProductionAdvancePipelineState):raise AssertionError("production orchestrator lost production advance state")
        return state
    @property
    def season_complete(self)->bool:session=self.engine.current_session;return bool(session is not None and session.finished)
    @property
    def pending_interactive_events(self)->tuple[InteractiveEvent,...]:return event_state_for_engine(self.engine).pending
    def drain_generated_interactive_events(self)->tuple[InteractiveEvent,...]:return self.game_provider.drain_interactive_events()
    def resolve_interactive_event(self,event_id:str,choice_id:str,*,resolved_at:date|None=None)->InteractiveEventResolution:
        return resolve_interactive_event(state=event_state_for_engine(self.engine),event_id=event_id,choice_id=choice_id,resolved_at=resolved_at or self.state.current_date)
    def advance_one_game(self)->AdvanceSummary:self._ensure_advance_allowed();return self.orchestrator.advance_one_game()
    def advance_one_week(self)->AdvanceSummary:self._ensure_advance_allowed();return self.orchestrator.advance_one_week()
    def advance_one_month(self)->AdvanceSummary:self._ensure_advance_allowed();return self.orchestrator.advance_one_month()
    def finalize_season(self)->SeasonFinalizationResult:
        self.engine.begin_source_fact_capture(self.state.current_date,'lifecycle');result=self.engine.finalize_completed_pro_season()
        if hasattr(self.engine,"advance_state"):delattr(self.engine,"advance_state")
        return result
    def start_next_season(self)->None:
        if self.engine.phase!='PRO':raise RuntimeError("career is not in professional phase")
        if self.engine.current_session is not None:raise RuntimeError("professional season already active")
        self.engine.start_pro_season();self.schedule=CareerSeasonScheduleProvider(self.engine.year);self._bind(self._state_for_engine(0))