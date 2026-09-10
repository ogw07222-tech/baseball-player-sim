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
from .career import CareerEngine
from .game_provider import GameFixture, ProductionGameProvider
from .game_result import ProductionGameResult
from .stat_aggregation import (
    GamePerformance,
    HitterCountingStats,
    PitcherCountingStats,
    career_stats_from_records,
    season_stats_from_record,
)
from .time_advance import (
    AdvanceOrchestrator,
    AdvancePipelineState,
    AdvanceSummary,
    ScheduleProvider,
)


@dataclass
class ProductionAdvancePipelineState(AdvancePipelineState):
    """Production advance state with persistent cumulative team record.

    PR #26's generic foundation intentionally stored only player aggregation.
    Production consolidation additionally needs exact team W/L/T to compose and
    persist across one-game, week, and month advance.

    ``team_record_supported`` is false when loading an older advance payload or
    attaching the production service after games were already completed without
    a persisted team record. New careers started through this service are exact.
    """

    team_wins: int = 0
    team_losses: int = 0
    team_ties: int = 0
    team_record_supported: bool = False

    @staticmethod
    def _result_from_score(score: tuple[int, int] | None) -> str | None:
        if score is None:
            return None
        runs_for, runs_against = score
        if runs_for > runs_against:
            return "W"
        if runs_for < runs_against:
            return "L"
        return "T"

    def add_game(self, game: GamePerformance) -> None:
        super().add_game(game)
        score_result = self._result_from_score(game.score)
        if score_result is not None:
            if game.team_result is not None and game.team_result != score_result:
                raise ValueError("team_result must match exact final score")
            result = score_result
        else:
            result = game.team_result
            # A no-score legacy/test provider can still contribute its stated
            # result, but it cannot make the cumulative record exact-supported.
            self.team_record_supported = False

        if result == "W":
            self.team_wins += 1
        elif result == "L":
            self.team_losses += 1
        elif result == "T":
            self.team_ties += 1
        else:
            self.team_record_supported = False

    @property
    def team_record(self) -> dict[str, int | bool]:
        return {
            "wins": self.team_wins,
            "losses": self.team_losses,
            "ties": self.team_ties,
            "supported": self.team_record_supported,
        }

    def as_dict(self) -> dict[str, object]:
        payload = super().as_dict()
        payload["team_record"] = dict(self.team_record)
        return payload

    @classmethod
    def from_advance_state(
        cls,
        state: AdvancePipelineState,
        *,
        team_record_supported: bool = False,
    ) -> "ProductionAdvancePipelineState":
        return cls(
            current_date=state.current_date,
            season=state.season,
            career=state.career,
            completed_seasons=list(state.completed_seasons),
            recent_games=list(state.recent_games),
            history_limit=state.history_limit,
            team_record_supported=team_record_supported,
        )

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, object],
        *,
        default_date: date | None = None,
    ) -> "ProductionAdvancePipelineState":
        base = AdvancePipelineState.from_dict(data, default_date=default_date)
        raw = data.get("team_record")
        if isinstance(raw, Mapping):
            wins = int(raw.get("wins", 0))
            losses = int(raw.get("losses", 0))
            ties = int(raw.get("ties", 0))
            supported = bool(raw.get("supported", True))
        else:
            wins = losses = ties = 0
            supported = False
        return cls(
            current_date=base.current_date,
            season=base.season,
            career=base.career,
            completed_seasons=list(base.completed_seasons),
            recent_games=list(base.recent_games),
            history_limit=base.history_limit,
            team_wins=wins,
            team_losses=losses,
            team_ties=ties,
            team_record_supported=supported,
        )


@dataclass(frozen=True)
class CareerSeasonScheduleProvider(ScheduleProvider):
    """Temporary deterministic date adapter for the existing 144-game season.

    This is intentionally not a new KBO scheduling model. It only supplies real
    dates to the advance foundation until a canonical league schedule provider
    exists. Games are placed on non-Mondays from April 1 onward.
    """

    dates: tuple[date, ...]

    def __init__(self, year: int, games: int = config.KBO_FIRST_TEAM_GAMES) -> None:
        out: list[date] = []
        cursor = date(int(year), 4, 1)
        while len(out) < int(games):
            if cursor.weekday() != 0:
                out.append(cursor)
            cursor += timedelta(days=1)
        object.__setattr__(self, "dates", tuple(out))

    def next_game_after(self, after: date) -> date | None:
        return next((game_date for game_date in self.dates if game_date > after), None)

    def game_dates(self, after: date, through: date) -> Sequence[date]:
        return tuple(game_date for game_date in self.dates if after < game_date <= through)

    def game_index(self, game_date: date) -> int:
        try:
            return self.dates.index(game_date)
        except ValueError as exc:
            raise KeyError(f"date is not in temporary career schedule: {game_date}") from exc


class CareerFixtureProvider:
    """Deterministic fixture adapter; no manager/schedule AI lives here."""

    def __init__(self, engine: CareerEngine, schedule: CareerSeasonScheduleProvider) -> None:
        self.engine = engine
        self.schedule = schedule

    def fixture_for(self, game_date: date) -> GameFixture:
        session = self.engine.start_pro_season()
        user_team = self.engine.player.team
        if not user_team:
            raise RuntimeError("career player has no team")
        opponents = [str(row["name"]) for row in config.KBO_TEAMS if row["name"] != user_team]
        index = self.schedule.game_index(game_date)
        opponent = opponents[index % len(opponents)]
        if index % 2 == 0:
            away, home = opponent, user_team
        else:
            away, home = user_team, opponent
        return GameFixture(game_date, away, home, session.current_level)


class CareerGameAdvanceProvider:
    """Run scheduled full games while reusing existing CareerEngine decisions.

    With no explicit provider, this creates the dynamic pitcher-usage provider.
    That makes the #32 usage/rotation path canonical while preserving explicit
    dependency injection for focused compatibility tests.
    """

    def __init__(
        self,
        engine: CareerEngine,
        schedule: CareerSeasonScheduleProvider,
        game_provider: ProductionGameProvider | None = None,
    ) -> None:
        self.engine = engine
        self.schedule = schedule
        self.fixture_provider = CareerFixtureProvider(engine, schedule)
        if game_provider is None:
            from .pitcher_usage import PitcherUsageLeagueState
            from .pitcher_usage_game_provider import DynamicPitcherGameProvider

            existing = getattr(engine, "pitcher_usage_state", None)
            usage_state = (
                existing
                if isinstance(existing, PitcherUsageLeagueState)
                else PitcherUsageLeagueState()
            )
            engine.pitcher_usage_state = usage_state
            game_provider = DynamicPitcherGameProvider(usage_state=usage_state)
        self.game_provider = game_provider
        self.last_result: ProductionGameResult | None = None
        self.recent_results: list[ProductionGameResult] = []
        self.history_limit = 10

    def _participation(self) -> tuple[bool, str]:
        session = self.engine.start_pro_season()
        if self.engine.player.injury is not None:
            return False, "INJURED"
        started = self.engine.rng.random() < self.engine._play_probability(session.current_level)
        if started:
            return True, "FARM" if session.current_level == "FARM" else "STARTED"
        return False, "BENCH"

    def _postgame(self, started: bool) -> None:
        session = self.engine.start_pro_season()
        if self.engine.player.injury is not None and not started:
            self.engine._recover_day()
            self.engine._update_form()
            self.engine._reconsider_roster(session)
        elif started:
            self.engine._fatigue_after_game()
            self.engine._maybe_injure()
            self.engine._update_form()
            self.engine._reconsider_roster(session)
        else:
            self.engine._recover_day()
            self.engine._update_form()
            self.engine._reconsider_roster(session)
        self.engine._maybe_event(session, None, False)

    def advance_game(self, game_date: date) -> GamePerformance:
        session = self.engine.start_pro_season()
        if session.finished:
            raise RuntimeError("professional season already completed")
        if not session.preseason_checked:
            self.engine._check_preseason(session, None, False)
        if session.has_pending_event:
            self.engine.resolve_pending_event()

        fixture = self.fixture_provider.fixture_for(game_date)
        started, reason = self._participation()
        result = self.game_provider.run_game(
            fixture,
            self.engine.rng,
            user_player=self.engine.player,
            user_team=self.engine.player.team,
            user_started=started,
            participation_reason=reason,
        )
        self.last_result = result
        self.recent_results.append(result)
        if len(self.recent_results) > self.history_limit:
            del self.recent_results[: len(self.recent_results) - self.history_limit]

        session.games_completed += 1

        hitter_stats = HitterCountingStats()
        if started and result.user_player_id:
            user_line = result.player_line(result.user_player_id)
            if user_line is None:
                raise AssertionError("started career player is missing from full-game lineup")
            target = session.record.first_team if session.current_level == "FIRST" else session.record.farm
            target.add(user_line.batting_line)
            hitter_stats = user_line.stats
            if session.current_level == "FIRST" and self.engine.player.debut_year is None:
                self.engine.player.debut_year = self.engine.year

        team = self.engine.player.team
        if not team:
            raise RuntimeError("career player lost team during game")
        opponent = fixture.home_team if team == fixture.away_team else fixture.away_team
        score = result.score_for(team)
        performance = GamePerformance(
            game_date=game_date,
            level=session.current_level,
            started=started,
            opponent=opponent,
            hitter_stats=hitter_stats,
            pitcher_stats=PitcherCountingStats(),
            team_result=result.team_result_for(team),
            score=score,
            notable_events=result.notable_events,
        )

        self._postgame(started)
        return performance


class CompositionalAdvanceOrchestrator(AdvanceOrchestrator):
    """Production cursor semantics matching repeated one-game composition.

    PR #26 originally moved a week/month cursor to the requested period end.
    Consolidation requires the persistent state to match N repeated one-game
    calls exactly, so the canonical production cursor remains on the final
    simulated scheduled-game date (or unchanged when the window has no game).
    Counting-stat behavior is inherited unchanged.
    """

    def _advance_dates(
        self,
        period_type: str,
        start: date,
        end: date,
        dates: Iterable[date],
    ) -> AdvanceSummary:
        scheduled = tuple(dates)
        summary = super()._advance_dates(period_type, start, end, scheduled)
        compositional_end = scheduled[-1] if scheduled else start
        self.state.current_date = compositional_end
        return replace(summary, end_date=compositional_end)


class ProductionAdvanceService:
    """Canonical 1-game / 1-week / 1-month production backbone."""

    def __init__(
        self,
        engine: CareerEngine,
        *,
        game_provider: ProductionGameProvider | None = None,
    ) -> None:
        self.engine = engine
        session = engine.start_pro_season()
        self.schedule = CareerSeasonScheduleProvider(engine.year)
        state = self._state_for_engine(session.games_completed)
        self.game_provider = CareerGameAdvanceProvider(
            engine,
            self.schedule,
            game_provider,
        )
        self.orchestrator = CompositionalAdvanceOrchestrator(
            state,
            self.schedule,
            self.game_provider,
            rating_provider=lambda: engine.player.stats.as_dict(),
            roster_provider=lambda: engine.start_pro_season().current_level,
        )
        engine.advance_state = state

    def _state_for_engine(self, games_completed: int) -> ProductionAdvancePipelineState:
        existing = getattr(self.engine, "advance_state", None)
        if isinstance(existing, ProductionAdvancePipelineState):
            return existing
        if isinstance(existing, AdvancePipelineState):
            return ProductionAdvancePipelineState.from_advance_state(existing)

        session = self.engine.start_pro_season()
        current_date = (
            self.schedule.dates[games_completed - 1]
            if games_completed > 0
            else self.schedule.dates[0] - timedelta(days=1)
        )
        season = season_stats_from_record(session.record)
        records = list(self.engine.player.seasons) + [session.record]
        career = career_stats_from_records(records)
        return ProductionAdvancePipelineState(
            current_date=current_date,
            season=season,
            career=career,
            team_record_supported=games_completed == 0,
        )

    @property
    def state(self) -> ProductionAdvancePipelineState:
        state = self.orchestrator.state
        if not isinstance(state, ProductionAdvancePipelineState):
            raise AssertionError("production orchestrator lost production advance state")
        return state

    def advance_one_game(self) -> AdvanceSummary:
        return self.orchestrator.advance_one_game()

    def advance_one_week(self) -> AdvanceSummary:
        return self.orchestrator.advance_one_week()

    def advance_one_month(self) -> AdvanceSummary:
        return self.orchestrator.advance_one_month()
