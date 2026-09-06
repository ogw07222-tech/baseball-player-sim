"""Production full-game provider over the persistent inning engine.

This module owns orchestration only. H3.2.1 hitting/baserunning probabilities
remain in ``src.hitting`` and natural runner events remain in ``src.natural_events``.
No calibration coefficients are duplicated here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol, Sequence

from . import config
from .game_result import PitcherGameLine, PlayerGameLine, ProductionGameResult
from .inning import PersistentInningEngine, PlayEvent
from .player import Player
from .records import BattingLine
from .rng import RNG
from .simulation import PitcherProfile
from .stat_aggregation import PitcherCountingStats, normalize_level
from .stats import PlayerStats


class GameSafetyLimitError(RuntimeError):
    pass


@dataclass(frozen=True)
class GameFixture:
    game_date: date
    away_team: str
    home_team: str
    level: str = "FIRST"

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", normalize_level(self.level))
        if self.away_team == self.home_team:
            raise ValueError("away and home teams must differ")


@dataclass(frozen=True)
class PitcherSlot:
    pitcher_id: str
    profile: PitcherProfile
    role: str


@dataclass(frozen=True)
class TeamPitchingPlan:
    starter: PitcherSlot
    bullpen: PitcherSlot
    starter_exit_after_inning: int = 6

    def __post_init__(self) -> None:
        if self.starter_exit_after_inning < 1:
            raise ValueError("starter_exit_after_inning must be positive")

    def slot_for_inning(self, inning: int) -> PitcherSlot:
        return self.starter if inning <= self.starter_exit_after_inning else self.bullpen


class LineupProvider(Protocol):
    def lineup(self, team: str, level: str) -> Sequence[Player]:
        ...


class PitcherGameplayProvider(Protocol):
    def plan(self, fixture: GameFixture, team: str, rng: RNG) -> TeamPitchingPlan:
        ...


class TeamLevelProvider(Protocol):
    def level(self, team: str, level: str) -> float:
        ...


class KBOConfiguredTeamLevelProvider:
    """Read existing KBO team levels; it introduces no new strength mapping."""

    def level(self, team: str, level: str) -> float:
        normalized = normalize_level(level)
        row = next((entry for entry in config.KBO_TEAMS if entry["name"] == team), None)
        if row is None:
            return 100.0
        key = "first_team_level" if normalized == "FIRST" else "farm_level"
        return float(row[key])


class ExistingProfilePitcherProvider:
    """Temporary provider using only the existing PitcherProfile adapter.

    The starter and generic bullpen slot are generated from the exact same
    existing team-level contract. There is deliberately no bullpen quality
    coefficient or Joint-v4 calibration value in this integration layer.
    """

    def __init__(
        self,
        team_levels: TeamLevelProvider | None = None,
        *,
        starter_exit_after_inning: int = 6,
    ) -> None:
        self.team_levels = team_levels or KBOConfiguredTeamLevelProvider()
        self.starter_exit_after_inning = int(starter_exit_after_inning)

    def plan(self, fixture: GameFixture, team: str, rng: RNG) -> TeamPitchingPlan:
        level = self.team_levels.level(team, fixture.level)
        starter = PitcherSlot(
            f"{team}:{fixture.game_date.isoformat()}:starter",
            PitcherProfile.from_level(level, rng),
            "starter",
        )
        bullpen = PitcherSlot(
            f"{team}:{fixture.game_date.isoformat()}:bullpen",
            PitcherProfile.from_level(level, rng),
            "bullpen_fallback",
        )
        return TeamPitchingPlan(starter, bullpen, self.starter_exit_after_inning)


class DeterministicNeutralLineupProvider:
    """Canonical integration fallback, not a manager/roster AI.

    It creates nine stable neutral Player objects per team/level and caches them.
    Production roster work can replace this provider without touching the game
    provider or any probability formula.
    """

    POSITIONS = ("CF", "2B", "RF", "1B", "DH", "3B", "LF", "C", "SS")
    SLOT_BY_POSITION = {position: index for index, position in enumerate(POSITIONS)}

    def __init__(self, rating: int = 100) -> None:
        self.rating = int(rating)
        self._cache: dict[tuple[str, str], tuple[Player, ...]] = {}

    def lineup(self, team: str, level: str) -> Sequence[Player]:
        key = (team, normalize_level(level))
        if key not in self._cache:
            players = []
            for index, position in enumerate(self.POSITIONS):
                value = self.rating
                stats = PlayerStats(
                    contact=value,
                    power=value,
                    discipline=value,
                    speed=value,
                    defense=value,
                    throwing=value,
                    stamina=value,
                    durability=value,
                    mentality=value,
                    talent=value,
                )
                players.append(
                    Player(
                        name=f"{team} {position}{index + 1}",
                        age=26,
                        stats=stats,
                        position=position,
                        team=team,
                        roster_level=key[1],
                    )
                )
            self._cache[key] = tuple(players)
        return self._cache[key]


@dataclass
class _PitcherAccumulator:
    slot: PitcherSlot
    team: str
    used: bool = False
    stats: PitcherCountingStats | None = None

    def ensure(self) -> PitcherCountingStats:
        if self.stats is None:
            self.stats = PitcherCountingStats(
                G=1,
                GS=1 if self.slot.role == "starter" else 0,
            )
        self.used = True
        return self.stats


class ProductionGameProvider:
    """Run one deterministic full-team game through PersistentInningEngine."""

    def __init__(
        self,
        lineup_provider: LineupProvider | None = None,
        pitcher_provider: PitcherGameplayProvider | None = None,
        *,
        max_events: int = 2000,
        notable_event_limit: int = 32,
    ) -> None:
        self.lineup_provider = lineup_provider or DeterministicNeutralLineupProvider()
        self.pitcher_provider = pitcher_provider or ExistingProfilePitcherProvider()
        self.max_events = int(max_events)
        self.notable_event_limit = int(notable_event_limit)
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")
        if self.notable_event_limit < 0:
            raise ValueError("notable_event_limit must be non-negative")

    @staticmethod
    def _lineup_with_user(
        base: Sequence[Player],
        user_player: Player | None,
        user_team: str | None,
        team: str,
        started: bool,
    ) -> tuple[Player, ...]:
        lineup = list(base)
        if not (started and user_player is not None and user_team == team):
            return tuple(lineup)
        slot_map = DeterministicNeutralLineupProvider.SLOT_BY_POSITION
        slot = slot_map.get(user_player.position, 8)
        lineup[slot] = user_player
        return tuple(lineup)

    @staticmethod
    def _team_defense(lineup: Sequence[Player]) -> float:
        return sum(float(player.effective_stat("defense")) for player in lineup) / len(lineup)

    @staticmethod
    def _player_lines(team: str, lineup: Sequence[Player], lines: Sequence[BattingLine]) -> list[PlayerGameLine]:
        return [
            PlayerGameLine(
                player_id=f"{team}:{player.name}",
                player_name=player.name,
                team=team,
                lineup_slot=index + 1,
                batting_line=BattingLine.from_dict(line.as_dict()),
            )
            for index, (player, line) in enumerate(zip(lineup, lines))
        ]

    @staticmethod
    def _record_pitcher_event(stats: PitcherCountingStats, event: PlayEvent) -> None:
        stats.outs_pitched += int(event.outs_added)
        stats.R += int(event.runs_scored)
        if event.kind != "plate_appearance":
            return
        stats.BF += 1
        result = event.result
        if result in {"single", "double", "triple", "home_run"}:
            stats.H += 1
        if result == "home_run":
            stats.HR += 1
        elif result == "walk":
            stats.BB += 1
        elif result == "hit_by_pitch":
            stats.HBP += 1
        elif result == "strikeout":
            stats.SO += 1

    @staticmethod
    def _active_slot(
        engine: PersistentInningEngine,
        away_plan: TeamPitchingPlan,
        home_plan: TeamPitchingPlan,
    ) -> tuple[str, PitcherSlot]:
        if engine.state.fielding_side == "away":
            return "away", away_plan.slot_for_inning(engine.state.inning)
        return "home", home_plan.slot_for_inning(engine.state.inning)

    @staticmethod
    def _install_pitcher(
        engine: PersistentInningEngine,
        side: str,
        slot: PitcherSlot,
    ) -> None:
        if side == "away":
            engine.away_pitcher = slot.profile
        else:
            engine.home_pitcher = slot.profile

    def run_game(
        self,
        fixture: GameFixture,
        rng: RNG,
        *,
        user_player: Player | None = None,
        user_team: str | None = None,
        user_started: bool = False,
        participation_reason: str | None = None,
    ) -> ProductionGameResult:
        if user_team is not None and user_team not in {fixture.away_team, fixture.home_team}:
            raise ValueError("user_team must be one of the fixture teams")

        away_lineup = self._lineup_with_user(
            self.lineup_provider.lineup(fixture.away_team, fixture.level),
            user_player,
            user_team,
            fixture.away_team,
            user_started,
        )
        home_lineup = self._lineup_with_user(
            self.lineup_provider.lineup(fixture.home_team, fixture.level),
            user_player,
            user_team,
            fixture.home_team,
            user_started,
        )
        if len(away_lineup) != 9 or len(home_lineup) != 9:
            raise ValueError("lineup provider must return exactly nine players")

        away_plan = self.pitcher_provider.plan(fixture, fixture.away_team, rng)
        home_plan = self.pitcher_provider.plan(fixture, fixture.home_team, rng)

        engine = PersistentInningEngine(
            away_lineup,
            home_lineup,
            rng,
            away_pitcher=away_plan.starter.profile,
            home_pitcher=home_plan.starter.profile,
            away_defense=self._team_defense(away_lineup),
            home_defense=self._team_defense(home_lineup),
            away_running_defense=100.0,
            home_running_defense=100.0,
            away_recovery=100.0,
            home_recovery=100.0,
        )

        accumulators: dict[str, _PitcherAccumulator] = {}
        for team, plan in (
            (fixture.away_team, away_plan),
            (fixture.home_team, home_plan),
        ):
            for slot in (plan.starter, plan.bullpen):
                accumulators[slot.pitcher_id] = _PitcherAccumulator(slot, team)

        notable: list[str] = []
        for _ in range(self.max_events):
            if engine.state.game_over:
                break
            fielding_side, slot = self._active_slot(engine, away_plan, home_plan)
            self._install_pitcher(engine, fielding_side, slot)
            event = engine.step()

            acc = accumulators[slot.pitcher_id]
            self._record_pitcher_event(acc.ensure(), event)

            if len(notable) < self.notable_event_limit:
                if event.kind == "plate_appearance" and event.result == "home_run":
                    notable.append(f"HR:{event.batter_id}")
                elif event.kind == "steal":
                    notable.append("SB" if event.steal_success else "CS")
                if engine.state.game_over and event.half == "bottom" and engine.state.inning >= 9:
                    if engine.state.home_score > engine.state.away_score:
                        notable.append("WALKOFF")
        else:
            raise GameSafetyLimitError(
                f"full game exceeded {self.max_events} events"
            )

        if not engine.state.game_over:
            raise GameSafetyLimitError("full game terminated without game_over")

        player_lines = tuple(
            self._player_lines(fixture.away_team, away_lineup, engine.away_lines)
            + self._player_lines(fixture.home_team, home_lineup, engine.home_lines)
        )
        pitcher_lines: list[PitcherGameLine] = []
        for acc in accumulators.values():
            if not acc.used or acc.stats is None:
                continue
            acc.stats.validate()
            pitcher_lines.append(
                PitcherGameLine(
                    pitcher_id=acc.slot.pitcher_id,
                    team=acc.team,
                    role=acc.slot.role,
                    stats=acc.stats,
                    unsupported_stats=("ER", "W", "L", "SV", "HLD"),
                )
            )
            if acc.stats.SO >= 10 and len(notable) < self.notable_event_limit:
                notable.append(f"HIGH_K:{acc.slot.pitcher_id}:{acc.stats.SO}")

        user_player_id = (
            f"{user_team}:{user_player.name}"
            if user_player is not None and user_team is not None
            else None
        )
        return ProductionGameResult(
            game_date=fixture.game_date,
            away_team=fixture.away_team,
            home_team=fixture.home_team,
            away_score=engine.state.away_score,
            home_score=engine.state.home_score,
            innings_played=engine.state.inning,
            player_lines=player_lines,
            pitcher_lines=tuple(pitcher_lines),
            notable_events=tuple(notable[: self.notable_event_limit]),
            event_count=engine.event_count,
            user_player_id=user_player_id,
            participation_reason=participation_reason,
            safety_cap_hit=False,
        )
