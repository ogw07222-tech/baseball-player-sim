"""Date-based advance orchestration over gameplay-result providers.

The provider boundary is intentional: this module never generates batting or
pitching results. Week/month advances are compositions of scheduled game
advances, so gameplay calibration can change independently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import calendar
from typing import Callable, Iterable, Mapping, Protocol, Sequence

from .career_source_facts import CareerSourceFact
from .stat_aggregation import (
    CareerStatLine,
    GamePerformance,
    PeriodStatLine,
    SeasonStatLine,
    aggregate_game_performances,
)


class NoScheduledGameError(RuntimeError):
    pass


class ScheduleProvider(Protocol):
    def next_game_after(self, after: date) -> date | None:
        ...

    def game_dates(self, after: date, through: date) -> Sequence[date]:
        """Return scheduled dates with ``after < date <= through``."""
        ...


class GameAdvanceProvider(Protocol):
    def advance_game(self, game_date: date) -> GamePerformance:
        ...


RawRatingProvider = Callable[[], Mapping[str, int]]
RosterProvider = Callable[[], str]


@dataclass(frozen=True)
class DateState:
    current_date: date

    def as_dict(self) -> dict[str, str]:
        return {"current_date": self.current_date.isoformat()}

    @classmethod
    def from_dict(cls, data: Mapping[str, object], *, default_date: date | None = None) -> "DateState":
        fallback = default_date or date(1970, 1, 1)
        raw = data.get("current_date")
        return cls(date.fromisoformat(str(raw)) if raw else fallback)


@dataclass(frozen=True)
class CareerEventSummary:
    game_date: date | None
    kind: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "date": self.game_date.isoformat() if self.game_date else None,
            "kind": self.kind,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CareerEventSummary":
        raw_date = data.get("date")
        return cls(
            date.fromisoformat(str(raw_date)) if raw_date else None,
            str(data.get("kind", "event")),
            str(data.get("message", "")),
        )


@dataclass
class AdvancePipelineState:
    current_date: date
    season: SeasonStatLine = field(default_factory=SeasonStatLine)
    career: CareerStatLine = field(default_factory=CareerStatLine)
    completed_seasons: list[SeasonStatLine] = field(default_factory=list)
    recent_games: list[GamePerformance] = field(default_factory=list)
    history_limit: int = 64

    def __post_init__(self) -> None:
        if self.history_limit <= 0:
            raise ValueError("history_limit must be positive")
        if self.season.year is None:
            self.season.year = self.current_date.year
        self.recent_games = self.recent_games[-self.history_limit :]

    def add_game(self, game: GamePerformance) -> None:
        if self.season.year is None:
            self.season.year = game.game_date.year
        if game.game_date.year != self.season.year:
            self.completed_seasons.append(self.season.copy())
            self.career.seasons = max(self.career.seasons, len(self.completed_seasons))
            self.season = SeasonStatLine(year=game.game_date.year)
        self.season.add_game(game.level, game.stat_line)
        self.career.add_game(game.level, game.stat_line)
        self.career.seasons = max(self.career.seasons, len(self.completed_seasons) + 1)
        self.recent_games.append(game)
        if len(self.recent_games) > self.history_limit:
            del self.recent_games[: len(self.recent_games) - self.history_limit]

    @property
    def last_10_games(self) -> list[GamePerformance]:
        return list(self.recent_games[-10:])

    def as_dict(self) -> dict[str, object]:
        return {
            "current_date": self.current_date.isoformat(),
            "season": self.season.as_dict(),
            "career": self.career.as_dict(),
            "completed_seasons": [s.as_dict() for s in self.completed_seasons],
            "recent_games": [g.as_dict() for g in self.recent_games],
            "history_limit": self.history_limit,
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, object],
        *,
        default_date: date | None = None,
    ) -> "AdvancePipelineState":
        fallback = default_date or date(1970, 1, 1)
        raw_date = data.get("current_date")
        current = date.fromisoformat(str(raw_date)) if raw_date else fallback
        season = SeasonStatLine.from_dict(_mapping(data.get("season")))
        if season.year is None:
            season.year = current.year
        career = CareerStatLine.from_dict(_mapping(data.get("career")))
        completed = [SeasonStatLine.from_dict(_mapping(item)) for item in _sequence(data.get("completed_seasons"))]
        recent = [GamePerformance.from_dict(_mapping(item)) for item in _sequence(data.get("recent_games"))]
        return cls(current_date=current,season=season,career=career,completed_seasons=completed,recent_games=recent,history_limit=int(data.get("history_limit", 64)))


@dataclass(frozen=True)
class AdvanceSummary:
    period_type: str
    start_date: date
    end_date: date
    games_played: int
    team_wins: int
    team_losses: int
    team_ties: int
    team_result_supported: bool
    player_period_stats: PeriodStatLine
    season_before: SeasonStatLine
    season_after: SeasonStatLine
    before_ratings: Mapping[str, int] | None = None
    after_ratings: Mapping[str, int] | None = None
    roster_changes: tuple[str, ...] = ()
    major_events: tuple[CareerEventSummary, ...] = ()
    source_facts: tuple[CareerSourceFact, ...] = ()

    @property
    def rating_delta(self) -> dict[str, int]:
        if self.before_ratings is None or self.after_ratings is None:
            return {}
        keys = set(self.before_ratings) | set(self.after_ratings)
        return {key: int(self.after_ratings.get(key, 0)) - int(self.before_ratings.get(key, 0)) for key in sorted(keys)}

    def as_dict(self) -> dict[str, object]:
        return {
            "period_type": self.period_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "games_played": self.games_played,
            "team_wins": self.team_wins,
            "team_losses": self.team_losses,
            "team_ties": self.team_ties,
            "team_result_supported": self.team_result_supported,
            "player_period_stats": self.player_period_stats.as_dict(include_derived=True),
            "season_before": self.season_before.as_dict(include_derived=True),
            "season_after": self.season_after.as_dict(include_derived=True),
            "rating_delta": self.rating_delta,
            "roster_changes": list(self.roster_changes),
            "major_events": [event.as_dict() for event in self.major_events],
            "source_facts": [fact.as_dict() for fact in self.source_facts],
        }


@dataclass(frozen=True)
class AdvanceResultViewModel:
    period_label: str
    date_range: str
    games_played: int
    hitter_period_line: Mapping[str, object]
    pitcher_period_line: Mapping[str, object]
    team_record_delta: Mapping[str, int] | None
    season_total_line: Mapping[str, object]
    notable_events: tuple[Mapping[str, object], ...]
    rating_changes: Mapping[str, int]

    @classmethod
    def from_summary(cls, summary: AdvanceSummary) -> "AdvanceResultViewModel":
        team_record = ({"wins": summary.team_wins,"losses": summary.team_losses,"ties": summary.team_ties} if summary.team_result_supported else None)
        period = summary.player_period_stats.as_dict(include_derived=True)
        overall = _mapping(period.get("overall"))
        season = summary.season_after.as_dict(include_derived=True)
        _assert_raw_rating_payload(summary.rating_delta)
        return cls(period_label=summary.period_type,date_range=f"{summary.start_date.isoformat()}~{summary.end_date.isoformat()}",games_played=summary.games_played,hitter_period_line=_mapping(overall.get("hitter")),pitcher_period_line=_mapping(overall.get("pitcher")),team_record_delta=team_record,season_total_line=season,notable_events=tuple(event.as_dict() for event in summary.major_events),rating_changes=summary.rating_delta)

    def as_dict(self) -> dict[str, object]:
        return {"period_label":self.period_label,"date_range":self.date_range,"games_played":self.games_played,"hitter_period_line":dict(self.hitter_period_line),"pitcher_period_line":dict(self.pitcher_period_line),"team_record_delta":dict(self.team_record_delta) if self.team_record_delta is not None else None,"season_total_line":dict(self.season_total_line),"notable_events":[dict(event) for event in self.notable_events],"rating_changes":dict(self.rating_changes)}


class AdvanceOrchestrator:
    def __init__(self,state:AdvancePipelineState,schedule:ScheduleProvider,game_provider:GameAdvanceProvider,*,rating_provider:RawRatingProvider|None=None,roster_provider:RosterProvider|None=None)->None:
        self.state=state;self.schedule=schedule;self.game_provider=game_provider;self.rating_provider=rating_provider;self.roster_provider=roster_provider

    def advance_one_game(self) -> AdvanceSummary:
        game_date=self.schedule.next_game_after(self.state.current_date)
        if game_date is None:raise NoScheduledGameError("no scheduled game after current date")
        return self._advance_dates("GAME",self.state.current_date,game_date,[game_date])

    def advance_one_week(self) -> AdvanceSummary:
        start=self.state.current_date;end=start+timedelta(days=7);dates=self.schedule.game_dates(start,end);return self._advance_dates("WEEK",start,end,dates)

    def advance_one_month(self) -> AdvanceSummary:
        start=self.state.current_date;end=_add_one_calendar_month(start);dates=self.schedule.game_dates(start,end);return self._advance_dates("MONTH",start,end,dates)

    def get_weekly_summary(self) -> PeriodStatLine:
        start=self.state.current_date-timedelta(days=7);games=[g for g in self.state.recent_games if start<g.game_date<=self.state.current_date];return aggregate_game_performances(games)

    def get_monthly_summary(self,year:int,month:int)->PeriodStatLine:
        games=[g for g in self.state.recent_games if g.game_date.year==year and g.game_date.month==month];return aggregate_game_performances(games)

    def _advance_dates(self,period_type:str,start:date,end:date,dates:Iterable[date])->AdvanceSummary:
        before=self.state.season.copy();before_ratings=_rating_snapshot(self.rating_provider);before_roster=self.roster_provider() if self.roster_provider else None;games=[];events=[]
        for scheduled_date in dates:
            if not start<scheduled_date<=end:raise ValueError("schedule returned date outside requested range")
            game=self.game_provider.advance_game(scheduled_date)
            if game.game_date!=scheduled_date:raise ValueError("game provider returned mismatched date")
            self.state.add_game(game);games.append(game);events.extend(CareerEventSummary(game.game_date,"game",message) for message in game.notable_events)
        self.state.current_date=end;after_ratings=_rating_snapshot(self.rating_provider);after_roster=self.roster_provider() if self.roster_provider else None;roster_changes=()
        if before_roster is not None and after_roster is not None and before_roster!=after_roster:roster_changes=(f"{before_roster}->{after_roster}",)
        wins=sum(g.team_result=="W" for g in games);losses=sum(g.team_result=="L" for g in games);ties=sum(g.team_result=="T" for g in games);supported=bool(games) and all(g.team_result is not None for g in games)
        return AdvanceSummary(period_type,start,end,len(games),wins,losses,ties,supported,aggregate_game_performances(games),before,self.state.season.copy(),before_ratings,after_ratings,roster_changes,tuple(events))


@dataclass(frozen=True)
class ListScheduleProvider:
    dates: tuple[date, ...]
    def __init__(self,dates:Iterable[date])->None:object.__setattr__(self,"dates",tuple(sorted(set(dates))))
    def next_game_after(self,after:date)->date|None:return next((game_date for game_date in self.dates if game_date>after),None)
    def game_dates(self,after:date,through:date)->Sequence[date]:return tuple(game_date for game_date in self.dates if after<game_date<=through)


def _add_one_calendar_month(value:date)->date:
    if value.month==12:year,month=value.year+1,1
    else:year,month=value.year,value.month+1
    day=min(value.day,calendar.monthrange(year,month)[1]);return date(year,month,day)


def _rating_snapshot(provider:RawRatingProvider|None)->dict[str,int]|None:
    if provider is None:return None
    payload={str(k):int(v) for k,v in provider().items()};_assert_raw_rating_payload(payload);return payload


def _assert_raw_rating_payload(payload:Mapping[str,int])->None:
    forbidden=("normalized","gameplay_","effective_");bad=[key for key in payload if any(token in key.lower() for token in forbidden)]
    if bad:raise ValueError(f"UI stat pipeline accepts raw/display ratings only: {bad}")


def _mapping(value:object)->Mapping[str,object]:return value if isinstance(value,Mapping) else {}
def _sequence(value:object)->Sequence[object]:return value if isinstance(value,Sequence) and not isinstance(value,(str,bytes)) else ()
