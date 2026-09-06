"""Persistent inning/base-state orchestration for production H3.2.1.

This module is deliberately an orchestration layer. It does not own or retune
hitting/baserunning probabilities. Plate appearances come from
``src.simulation.simulate_plate_appearance_outcome`` and state-sensitive
baserunning decisions delegate to the validated adapters in
``src.hitting.baserunning``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from .hitting.baserunning import (
    GameState,
    StateTransition,
    apply_double_play_to_state,
    apply_first_to_third_to_state,
    apply_second_to_home_to_state,
    apply_steal_to_state,
)
from .hitting.model import PlateAppearanceOutcome
from .player import Player
from .records import BattingLine
from .rng import RNG
from .simulation import PitcherProfile, simulate_plate_appearance_outcome

Side = Literal["away", "home"]
Half = Literal["top", "bottom"]


@dataclass(frozen=True)
class RunnerState:
    """Identity-preserving runner snapshot backed by the canonical Player."""

    side: Side
    lineup_index: int
    player: Player

    @property
    def player_id(self) -> str:
        return f"{self.side}:{self.lineup_index}:{self.player.name}"

    @property
    def speed(self) -> float:
        return float(self.player.effective_stat("speed"))


@dataclass
class InningState:
    inning: int = 1
    half: Half = "top"
    outs: int = 0
    home_score: int = 0
    away_score: int = 0
    first_runner: RunnerState | None = None
    second_runner: RunnerState | None = None
    third_runner: RunnerState | None = None
    away_batting_order_index: int = 0
    home_batting_order_index: int = 0
    current_batter: Player | None = None
    current_pitcher: PitcherProfile | None = None
    game_over: bool = False

    @property
    def batting_side(self) -> Side:
        return "away" if self.half == "top" else "home"

    @property
    def fielding_side(self) -> Side:
        return "home" if self.half == "top" else "away"

    @property
    def batting_order_index(self) -> int:
        return self.away_batting_order_index if self.half == "top" else self.home_batting_order_index

    @batting_order_index.setter
    def batting_order_index(self, value: int) -> None:
        if self.half == "top":
            self.away_batting_order_index = int(value)
        else:
            self.home_batting_order_index = int(value)

    def clear_bases(self) -> None:
        self.first_runner = None
        self.second_runner = None
        self.third_runner = None

    def runner_ids(self) -> tuple[str, ...]:
        return tuple(
            runner.player_id
            for runner in (self.first_runner, self.second_runner, self.third_runner)
            if runner is not None
        )

    def to_h32_game_state(self) -> GameState:
        """Boolean H3.2.1 formula-state view from the batting team's perspective."""
        score_diff = (
            self.away_score - self.home_score
            if self.half == "top"
            else self.home_score - self.away_score
        )
        return GameState(
            inning=self.inning,
            outs=self.outs,
            score_diff=score_diff,
            first_occupied=self.first_runner is not None,
            second_occupied=self.second_runner is not None,
            third_occupied=self.third_runner is not None,
        )

    def validate(self) -> None:
        if self.inning < 1:
            raise AssertionError("inning must be positive")
        if self.half not in {"top", "bottom"}:
            raise AssertionError("invalid half inning")
        if not 0 <= self.outs <= 3:
            raise AssertionError("outs must stay in [0, 3] before transition")
        if self.home_score < 0 or self.away_score < 0:
            raise AssertionError("score must never be negative")
        runner_ids = self.runner_ids()
        if len(runner_ids) != len(set(runner_ids)):
            raise AssertionError("one runner cannot occupy multiple bases")
        for runner in (self.first_runner, self.second_runner, self.third_runner):
            if runner is not None and runner.side != self.batting_side:
                raise AssertionError("base runner must belong to batting team")


@dataclass(frozen=True)
class PlayEvent:
    kind: Literal["plate_appearance", "steal"]
    inning: int
    half: Half
    batter_id: str | None = None
    result: str | None = None
    runs_scored: int = 0
    outs_added: int = 0
    steal_attempted: bool = False
    steal_success: bool = False


@dataclass(frozen=True)
class GameResult:
    home_score: int
    away_score: int
    final_inning: int
    events: int
    home_lines: tuple[BattingLine, ...]
    away_lines: tuple[BattingLine, ...]


@dataclass(frozen=True)
class BaseResolution:
    scored_runners: tuple[RunnerState, ...] = ()
    resolved_result: str | None = None
    outs_added: int = 0
    dp_completed: bool = False
    dp_avoided: bool = False


class BaseStateResolver:
    """Identity-aware movement that reuses the frozen H3.2.1 state adapters."""

    def __init__(self, state: InningState, rng: RNG, line_for_runner, recovery: float = 100.0) -> None:
        self.state = state
        self.rng = rng
        self.line_for_runner = line_for_runner
        self.recovery = recovery

    def _record_xbt_attempt(self, runner: RunnerState, success: bool, kind: str) -> None:
        line = self.line_for_runner(runner)
        line.XBT_attempts += 1
        if success:
            line.XBT += 1
            if kind == "first_to_third":
                line.first_to_third += 1
            elif kind == "second_to_home":
                line.second_to_home += 1

    def force_batter_to_first(self, batter: RunnerState) -> BaseResolution:
        """Walk/HBP/ROE minimum forced-advancement policy."""
        scored: list[RunnerState] = []
        first = self.state.first_runner
        second = self.state.second_runner
        third = self.state.third_runner
        if first is not None:
            if second is not None:
                if third is not None:
                    scored.append(third)
                self.state.third_runner = second
            self.state.second_runner = first
        self.state.first_runner = batter
        return BaseResolution(tuple(scored))

    def single(self, batter: RunnerState) -> BaseResolution:
        """Single: failed extra-base attempts fall back to the next safe base."""
        scored: list[RunnerState] = []
        first = self.state.first_runner
        second = self.state.second_runner
        third = self.state.third_runner
        self.state.clear_bases()

        if third is not None:
            scored.append(third)

        if second is not None:
            formula_state = self.state.to_h32_game_state()
            formula_state.second_occupied = True
            transition = apply_second_to_home_to_state(second.speed, formula_state, self.rng, self.recovery)
            self._record_xbt_attempt(second, transition.success, "second_to_home")
            if transition.success:
                scored.append(second)
            else:
                self.state.third_runner = second

        if first is not None:
            if self.state.third_runner is None:
                formula_state = self.state.to_h32_game_state()
                formula_state.first_occupied = True
                transition = apply_first_to_third_to_state(first.speed, formula_state, self.rng, self.recovery)
                self._record_xbt_attempt(first, transition.success, "first_to_third")
                if transition.success:
                    self.state.third_runner = first
                else:
                    self.state.second_runner = first
            else:
                self.state.second_runner = first

        self.state.first_runner = batter
        return BaseResolution(tuple(scored))

    def double(self, batter: RunnerState) -> BaseResolution:
        """Unsupported 1B->Home on a double uses a conservative deterministic fallback."""
        scored = tuple(
            runner
            for runner in (self.state.third_runner, self.state.second_runner)
            if runner is not None
        )
        first = self.state.first_runner
        self.state.clear_bases()
        if first is not None:
            self.state.third_runner = first
        self.state.second_runner = batter
        return BaseResolution(scored)

    def triple(self, batter: RunnerState) -> BaseResolution:
        scored = tuple(
            runner
            for runner in (self.state.third_runner, self.state.second_runner, self.state.first_runner)
            if runner is not None
        )
        self.state.clear_bases()
        self.state.third_runner = batter
        return BaseResolution(scored)

    def home_run(self) -> BaseResolution:
        scored = tuple(
            runner
            for runner in (self.state.third_runner, self.state.second_runner, self.state.first_runner)
            if runner is not None
        )
        self.state.clear_bases()
        return BaseResolution(scored)

    def ground_ball_out(self, batter: RunnerState) -> BaseResolution:
        if self.state.outs >= 2 or self.state.first_runner is None:
            self.state.outs += 1
            return BaseResolution(resolved_result="out", outs_added=1)

        formula_state = self.state.to_h32_game_state()
        transition = apply_double_play_to_state(batter.speed, formula_state, self.rng)
        if not transition.attempted:
            self.state.outs += 1
            return BaseResolution(resolved_result="out", outs_added=1)

        self.state.outs = formula_state.outs
        self.state.first_runner = None
        if transition.success:
            return BaseResolution(
                resolved_result="out",
                outs_added=transition.outs_added,
                dp_completed=True,
            )

        self.state.first_runner = batter
        return BaseResolution(
            resolved_result="fielders_choice",
            outs_added=transition.outs_added,
            dp_avoided=True,
        )


class PersistentInningEngine:
    """PA -> persistent base state -> next PA orchestration with runner identity."""

    def __init__(
        self,
        away_lineup: Sequence[Player],
        home_lineup: Sequence[Player],
        rng: RNG,
        *,
        away_pitcher: PitcherProfile | None = None,
        home_pitcher: PitcherProfile | None = None,
        away_defense: float = 100.0,
        home_defense: float = 100.0,
        away_running_defense: float = 100.0,
        home_running_defense: float = 100.0,
        away_recovery: float = 100.0,
        home_recovery: float = 100.0,
    ) -> None:
        if len(away_lineup) != 9 or len(home_lineup) != 9:
            raise ValueError("persistent game engine requires nine-player lineups")
        if len({id(player) for player in away_lineup}) != 9:
            raise ValueError("away lineup contains duplicate player objects")
        if len({id(player) for player in home_lineup}) != 9:
            raise ValueError("home lineup contains duplicate player objects")

        self.away_lineup = tuple(away_lineup)
        self.home_lineup = tuple(home_lineup)
        self.rng = rng
        self.away_pitcher = away_pitcher or PitcherProfile(100, 100, 100, "R")
        self.home_pitcher = home_pitcher or PitcherProfile(100, 100, 100, "R")
        self.away_defense = float(away_defense)
        self.home_defense = float(home_defense)
        self.away_running_defense = float(away_running_defense)
        self.home_running_defense = float(home_running_defense)
        self.away_recovery = float(away_recovery)
        self.home_recovery = float(home_recovery)
        self.state = InningState()
        self.away_lines = tuple(BattingLine(G=1) for _ in range(9))
        self.home_lines = tuple(BattingLine(G=1) for _ in range(9))
        self.event_count = 0

    def _lineup(self, side: Side) -> tuple[Player, ...]:
        return self.away_lineup if side == "away" else self.home_lineup

    def _lines(self, side: Side) -> tuple[BattingLine, ...]:
        return self.away_lines if side == "away" else self.home_lines

    def line_for_runner(self, runner: RunnerState) -> BattingLine:
        return self._lines(runner.side)[runner.lineup_index]

    def _runner(self, side: Side, lineup_index: int) -> RunnerState:
        return RunnerState(side, lineup_index, self._lineup(side)[lineup_index])

    def _current_runner(self) -> RunnerState:
        side = self.state.batting_side
        return self._runner(side, self.state.batting_order_index % 9)

    def _current_pitcher(self) -> PitcherProfile:
        return self.home_pitcher if self.state.half == "top" else self.away_pitcher

    def _defense_level(self) -> float:
        return self.home_defense if self.state.half == "top" else self.away_defense

    def _running_defense_level(self) -> float:
        return self.home_running_defense if self.state.half == "top" else self.away_running_defense

    def _recovery_level(self) -> float:
        return self.home_recovery if self.state.half == "top" else self.away_recovery

    def _advance_batting_order(self, side: Side) -> None:
        if side == "away":
            self.state.away_batting_order_index = (self.state.away_batting_order_index + 1) % 9
        else:
            self.state.home_batting_order_index = (self.state.home_batting_order_index + 1) % 9

    def _add_team_run(self, side: Side) -> None:
        if side == "home":
            self.state.home_score += 1
        else:
            self.state.away_score += 1

    def _score_runner(self, runner: RunnerState) -> None:
        self.line_for_runner(runner).R += 1
        self._add_team_run(runner.side)

    def _score_runners(self, runners: Sequence[RunnerState]) -> int:
        for runner in runners:
            self._score_runner(runner)
        return len(runners)

    def _walkoff_reached(self) -> bool:
        return (
            self.state.half == "bottom"
            and self.state.inning >= 9
            and self.state.home_score > self.state.away_score
        )

    def _finish_half_inning(self) -> None:
        if self.state.outs < 3:
            return
        self.state.clear_bases()
        self.state.outs = 0
        self.state.current_batter = None
        self.state.current_pitcher = None

        if self.state.half == "top":
            if self.state.inning >= 9 and self.state.home_score > self.state.away_score:
                self.state.game_over = True
                return
            self.state.half = "bottom"
            return

        if self.state.inning >= 9 and self.state.home_score != self.state.away_score:
            self.state.game_over = True
            return

        self.state.inning += 1
        self.state.half = "top"

    def attempt_steal_between_plate_appearances(self) -> PlayEvent | None:
        """Try the validated 1B->2B steal against actual occupied bases."""
        if self.state.game_over or self.state.first_runner is None:
            return None

        event_inning, event_half = self.state.inning, self.state.half
        runner = self.state.first_runner
        formula_state = self.state.to_h32_game_state()
        transition: StateTransition = apply_steal_to_state(
            runner.speed,
            formula_state,
            self.rng,
            self._running_defense_level(),
        )
        if not transition.attempted:
            return None

        line = self.line_for_runner(runner)
        line.SB_attempts += 1
        self.state.outs = formula_state.outs
        if transition.success:
            self.state.first_runner = None
            self.state.second_runner = runner
            line.SB += 1
        else:
            self.state.first_runner = None
            line.CS += 1

        event = PlayEvent(
            kind="steal",
            inning=event_inning,
            half=event_half,
            steal_attempted=True,
            steal_success=transition.success,
            outs_added=transition.outs_added,
        )
        self.event_count += 1
        if self.state.outs >= 3:
            self._finish_half_inning()
        self.state.validate()
        return event

    def resolve_plate_appearance(self, outcome: PlateAppearanceOutcome) -> PlayEvent:
        """Apply one already-simulated PA result to the persistent state."""
        if self.state.game_over:
            raise RuntimeError("cannot resolve a PA after game over")

        event_inning, event_half = self.state.inning, self.state.half
        side = self.state.batting_side
        batter = self._current_runner()
        batter_line = self.line_for_runner(batter)
        self.state.current_batter = batter.player
        self.state.current_pitcher = self._current_pitcher()
        resolver = BaseStateResolver(self.state, self.rng, self.line_for_runner, self._recovery_level())

        result = outcome.result
        runs_scored = 0
        outs_before = self.state.outs
        resolved_result = result

        if result in {"walk", "hit_by_pitch"}:
            resolution = resolver.force_batter_to_first(batter)
            runs_scored = self._score_runners(resolution.scored_runners)
            batter_line.record_pa(result, rbi=runs_scored)
        elif result == "reached_on_error":
            resolution = resolver.force_batter_to_first(batter)
            runs_scored = self._score_runners(resolution.scored_runners)
            batter_line.record_pa("reached_on_error")
        elif result == "single":
            resolution = resolver.single(batter)
            runs_scored = self._score_runners(resolution.scored_runners)
            batter_line.record_pa("single", rbi=runs_scored)
        elif result == "double":
            resolution = resolver.double(batter)
            runs_scored = self._score_runners(resolution.scored_runners)
            batter_line.record_pa("double", rbi=runs_scored)
        elif result == "triple":
            resolution = resolver.triple(batter)
            runs_scored = self._score_runners(resolution.scored_runners)
            batter_line.record_pa("triple", rbi=runs_scored)
        elif result == "home_run":
            resolution = resolver.home_run()
            runs_scored = self._score_runners(resolution.scored_runners)
            self._add_team_run(side)
            runs_scored += 1
            batter_line.record_pa("home_run", runs=1, rbi=runs_scored)
        elif result == "strikeout":
            self.state.outs += 1
            batter_line.record_pa("strikeout")
        elif result == "out":
            is_ground_ball = outcome.batted_ball is not None and outcome.batted_ball.ball_type == "ground_ball"
            if is_ground_ball:
                resolution = resolver.ground_ball_out(batter)
                resolved_result = resolution.resolved_result or "out"
                batter_line.record_pa(resolved_result)
                if resolution.dp_completed:
                    batter_line.GDP += 1
                elif resolution.dp_avoided:
                    batter_line.DP_avoided += 1
            else:
                self.state.outs += 1
                batter_line.record_pa("out")
        elif result == "fielders_choice":
            if self.state.first_runner is not None:
                self.state.first_runner = batter
            self.state.outs += 1
            batter_line.record_pa("fielders_choice")
        else:
            raise ValueError(f"unsupported persistent PA result: {result}")

        outs_added = self.state.outs - outs_before
        self._advance_batting_order(side)

        if self._walkoff_reached():
            self.state.game_over = True
            self.state.current_batter = None
            self.state.current_pitcher = None
        elif self.state.outs >= 3:
            self._finish_half_inning()
        else:
            self.state.current_batter = None
            self.state.current_pitcher = None

        self.event_count += 1
        self.state.validate()
        return PlayEvent(
            kind="plate_appearance",
            inning=event_inning,
            half=event_half,
            batter_id=batter.player_id,
            result=resolved_result,
            runs_scored=runs_scored,
            outs_added=outs_added,
        )

    def play_plate_appearance(self) -> PlayEvent:
        if self.state.game_over:
            raise RuntimeError("game is already over")
        batter = self._current_runner()
        pitcher = self._current_pitcher()
        self.state.current_batter = batter.player
        self.state.current_pitcher = pitcher
        outcome = simulate_plate_appearance_outcome(
            batter.player,
            pitcher,
            self.rng,
            pressure=False,
            defense_level=self._defense_level(),
        )
        return self.resolve_plate_appearance(outcome)

    def step(self) -> PlayEvent:
        """Advance one baseball event: steal attempt if made, otherwise one PA."""
        steal_event = self.attempt_steal_between_plate_appearances()
        if steal_event is not None:
            return steal_event
        return self.play_plate_appearance()

    def simulate_game(self, max_events: int = 2000) -> GameResult:
        for _ in range(max_events):
            if self.state.game_over:
                break
            self.step()
        else:
            raise RuntimeError("persistent game exceeded safety event limit")

        return GameResult(
            home_score=self.state.home_score,
            away_score=self.state.away_score,
            final_inning=self.state.inning,
            events=self.event_count,
            home_lines=self.home_lines,
            away_lines=self.away_lines,
        )
