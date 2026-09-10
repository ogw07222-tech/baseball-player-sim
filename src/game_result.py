"""Production full-game result contracts.

This module owns no gameplay probabilities. It packages outputs emitted by the
persistent inning engine for downstream aggregation, UI adapters, and tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .records import BattingLine
from .stat_aggregation import HitterCountingStats, PitcherCountingStats, hitter_stats_from_result


@dataclass(frozen=True)
class PlayerGameLine:
    player_id: str
    player_name: str
    team: str
    lineup_slot: int
    batting_line: BattingLine

    @property
    def stats(self) -> HitterCountingStats:
        return hitter_stats_from_result(self.batting_line)


@dataclass(frozen=True)
class PitcherGameLine:
    pitcher_id: str
    team: str
    role: str
    stats: PitcherCountingStats
    unsupported_stats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # The provider may keep internal zero-valued counters for unsupported
        # official statistics, but downstream consumers must never mistake those
        # placeholders for exact data.
        if self.unsupported_stats:
            object.__setattr__(
                self,
                "stats",
                self.stats.with_unsupported(self.unsupported_stats),
            )


@dataclass(frozen=True)
class ProductionGameResult:
    game_date: date
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    innings_played: int
    player_lines: tuple[PlayerGameLine, ...] = ()
    pitcher_lines: tuple[PitcherGameLine, ...] = ()
    notable_events: tuple[str, ...] = ()
    event_count: int = 0
    user_player_id: str | None = None
    participation_reason: str | None = None
    safety_cap_hit: bool = False

    def __post_init__(self) -> None:
        if self.away_score < 0 or self.home_score < 0:
            raise ValueError("game scores must be non-negative")
        if self.innings_played < 1:
            raise ValueError("innings_played must be positive")
        if self.event_count < 0:
            raise ValueError("event_count must be non-negative")

    @property
    def winner(self) -> str | None:
        if self.away_score == self.home_score:
            return None
        return self.away_team if self.away_score > self.home_score else self.home_team

    @property
    def loser(self) -> str | None:
        if self.away_score == self.home_score:
            return None
        return self.home_team if self.away_score > self.home_score else self.away_team

    def score_for(self, team: str) -> tuple[int, int]:
        if team == self.away_team:
            return self.away_score, self.home_score
        if team == self.home_team:
            return self.home_score, self.away_score
        raise KeyError(f"team not in game: {team}")

    def team_result_for(self, team: str) -> str:
        runs_for, runs_against = self.score_for(team)
        if runs_for > runs_against:
            return "W"
        if runs_for < runs_against:
            return "L"
        return "T"

    def player_line(self, player_id: str) -> PlayerGameLine | None:
        return next((line for line in self.player_lines if line.player_id == player_id), None)

    def pitcher_line(self, pitcher_id: str) -> PitcherGameLine | None:
        return next((line for line in self.pitcher_lines if line.pitcher_id == pitcher_id), None)
