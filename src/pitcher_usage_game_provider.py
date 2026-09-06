"""Dynamic pitcher-usage integration for the production full-game provider.

This drop-in provider keeps the persistent inning engine and all gameplay
probability formulas intact while replacing the fixed-six-inning handoff.

Pitcher run accounting also preserves inherited-run responsibility. A run is
charged to the pitcher who allowed that runner to reach base, not simply to the
pitcher who happens to be active when the runner scores.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from .game_provider import (
    DeterministicNeutralLineupProvider,
    GameFixture,
    GameSafetyLimitError,
    KBOConfiguredTeamLevelProvider,
    LineupProvider,
    ProductionGameProvider,
    TeamLevelProvider,
)
from .game_result import PitcherGameLine, ProductionGameResult
from .inning import PersistentInningEngine
from .pitcher_usage import (
    PitcherRole,
    PitcherUsageLeagueState,
    PitcherUsageManager,
    PitcherUsageMember,
)
from .rng import RNG
from .simulation import PitcherProfile
from .stat_aggregation import PitcherCountingStats, normalize_level


@dataclass(frozen=True)
class UsagePitcherSlot:
    pitcher_id: str
    profile: PitcherProfile
    stamina: float = 100.0
    resilience: float = 100.0

    @property
    def member(self) -> PitcherUsageMember:
        return PitcherUsageMember(self.pitcher_id, self.stamina, self.resilience)


class PitcherStaffProvider(Protocol):
    def staff(self, fixture: GameFixture, team: str) -> Sequence[UsagePitcherSlot]:
        ...


class DeterministicPitcherStaffProvider:
    """Stable fallback staff using only the existing team-level contract."""

    def __init__(
        self,
        team_levels: TeamLevelProvider | None = None,
        size: int = 12,
    ) -> None:
        if size < 7:
            raise ValueError("pitcher staff must contain at least seven pitchers")
        self.team_levels = team_levels or KBOConfiguredTeamLevelProvider()
        self.size = int(size)
        self._cache: dict[tuple[str, str], tuple[UsagePitcherSlot, ...]] = {}

    def staff(self, fixture: GameFixture, team: str) -> Sequence[UsagePitcherSlot]:
        level = normalize_level(fixture.level)
        key = (team, level)
        if key not in self._cache:
            team_level = self.team_levels.level(team, level)
            slots: list[UsagePitcherSlot] = []
            for index in range(self.size):
                profile_rng = RNG(f"pitcher-staff:{team}:{level}:{index}")
                slots.append(
                    UsagePitcherSlot(
                        f"{team}:{level}:P{index + 1}",
                        PitcherProfile.from_level(team_level, profile_rng),
                    )
                )
            self._cache[key] = tuple(slots)
        return self._cache[key]


@dataclass
class _UsageAccumulator:
    slot: UsagePitcherSlot
    team: str
    game_role: str
    used: bool = False
    stats: PitcherCountingStats | None = None

    def ensure(self) -> PitcherCountingStats:
        if self.stats is None:
            self.stats = PitcherCountingStats(
                G=1,
                GS=1 if self.game_role == PitcherRole.STARTER.value else 0,
            )
        self.used = True
        return self.stats


def _run_snapshot(engine: PersistentInningEngine) -> dict[str, int]:
    """Return identity-keyed batter run totals for exact scorer detection."""
    snapshot: dict[str, int] = {}
    for side, lineup, lines in (
        ("away", engine.away_lineup, engine.away_lines),
        ("home", engine.home_lineup, engine.home_lines),
    ):
        for index, (player, line) in enumerate(zip(lineup, lines)):
            snapshot[f"{side}:{index}:{player.name}"] = int(line.R)
    return snapshot


def _scored_runner_ids(
    before: Mapping[str, int],
    after: Mapping[str, int],
) -> tuple[str, ...]:
    """Recover exact scoring runner identities from BattingLine.R deltas."""
    scored: list[str] = []
    for runner_id, after_runs in after.items():
        before_runs = int(before.get(runner_id, 0))
        delta = int(after_runs) - before_runs
        if delta < 0:
            raise AssertionError("runner run total cannot decrease during a game")
        scored.extend([runner_id] * delta)
    return tuple(scored)


def _charged_pitcher_ids(
    scored_runner_ids: Sequence[str],
    responsibility: dict[str, str],
    current_pitcher_id: str,
) -> tuple[str, ...]:
    """Resolve pitcher responsibility and consume scored-runner ownership."""
    charged: list[str] = []
    for runner_id in scored_runner_ids:
        charged.append(responsibility.pop(runner_id, current_pitcher_id))
    return tuple(charged)


class DynamicPitcherGameProvider(ProductionGameProvider):
    """Full-game provider with persistent rotation, bullpen and workload state."""

    def __init__(
        self,
        lineup_provider: LineupProvider | None = None,
        staff_provider: PitcherStaffProvider | None = None,
        usage_state: PitcherUsageLeagueState | None = None,
        *,
        max_events: int = 2000,
        notable_event_limit: int = 32,
    ) -> None:
        super().__init__(
            lineup_provider=lineup_provider or DeterministicNeutralLineupProvider(),
            pitcher_provider=None,
            max_events=max_events,
            notable_event_limit=notable_event_limit,
        )
        self.staff_provider = staff_provider or DeterministicPitcherStaffProvider()
        self.usage_state = usage_state or PitcherUsageLeagueState()
        self.usage_manager = PitcherUsageManager(self.usage_state)

    @staticmethod
    def _margin(engine: PersistentInningEngine, side: str) -> int:
        if side == "away":
            return int(engine.state.away_score - engine.state.home_score)
        return int(engine.state.home_score - engine.state.away_score)

    @staticmethod
    def _fielding_side(engine: PersistentInningEngine) -> str:
        return str(engine.state.fielding_side)

    @staticmethod
    def _install(
        engine: PersistentInningEngine,
        side: str,
        slot: UsagePitcherSlot,
    ) -> None:
        if side == "away":
            engine.away_pitcher = slot.profile
        else:
            engine.home_pitcher = slot.profile

    def _choose_reliever(
        self,
        team: str,
        members: Sequence[PitcherUsageMember],
        slots: dict[str, UsagePitcherSlot],
        fixture: GameFixture,
        engine: PersistentInningEngine,
        used_ids: set[str],
    ) -> tuple[UsagePitcherSlot | None, str | None]:
        pitcher_id, reason = self.usage_manager.select_reliever(
            team,
            members,
            fixture.game_date,
            int(engine.state.inning),
            self._margin(engine, self._fielding_side(engine)),
            used_ids,
        )
        return (slots[pitcher_id] if pitcher_id is not None else None, reason)

    def run_game(
        self,
        fixture: GameFixture,
        rng: RNG,
        *,
        user_player=None,
        user_team: str | None = None,
        user_started: bool = False,
        participation_reason: str | None = None,
    ) -> ProductionGameResult:
        if user_team is not None and user_team not in {
            fixture.away_team,
            fixture.home_team,
        }:
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

        team_slots: dict[str, dict[str, UsagePitcherSlot]] = {}
        team_members: dict[str, tuple[PitcherUsageMember, ...]] = {}
        starters: dict[str, UsagePitcherSlot] = {}
        emergency_reasons: dict[str, str | None] = {}

        for team in (fixture.away_team, fixture.home_team):
            staff = tuple(self.staff_provider.staff(fixture, team))
            slots = {slot.pitcher_id: slot for slot in staff}
            members = tuple(slot.member for slot in staff)
            self.usage_manager.ensure_team(team, members)
            starter_id, reason = self.usage_manager.select_starter(
                team, members, fixture.game_date
            )
            team_slots[team] = slots
            team_members[team] = members
            starters[team] = slots[starter_id]
            emergency_reasons[starter_id] = reason

        engine = PersistentInningEngine(
            away_lineup,
            home_lineup,
            rng,
            away_pitcher=starters[fixture.away_team].profile,
            home_pitcher=starters[fixture.home_team].profile,
            away_defense=self._team_defense(away_lineup),
            home_defense=self._team_defense(home_lineup),
            away_running_defense=100.0,
            home_running_defense=100.0,
            away_recovery=100.0,
            home_recovery=100.0,
        )

        active = {
            "away": starters[fixture.away_team],
            "home": starters[fixture.home_team],
        }
        team_by_side = {"away": fixture.away_team, "home": fixture.home_team}
        used_ids = {fixture.away_team: set(), fixture.home_team: set()}
        accumulators: dict[str, _UsageAccumulator] = {}
        run_responsibility: dict[str, str] = {}

        for team, starter in starters.items():
            accumulators[starter.pitcher_id] = _UsageAccumulator(
                starter, team, PitcherRole.STARTER.value
            )

        notable: list[str] = []
        exhaustion_marked: set[str] = set()

        for _ in range(self.max_events):
            if engine.state.game_over:
                break

            side = self._fielding_side(engine)
            team = team_by_side[side]
            slot = active[side]
            acc = accumulators[slot.pitcher_id]
            usage_state = self.usage_state.team(team).pitchers[slot.pitcher_id]
            should_change = False

            if acc.used and acc.stats is not None:
                if acc.game_role == PitcherRole.STARTER.value:
                    should_change = self.usage_manager.starter_should_exit(
                        acc.stats,
                        int(engine.state.inning),
                        slot.stamina,
                    )
                else:
                    should_change = self.usage_manager.reliever_should_exit(
                        usage_state, acc.stats
                    )

            if should_change:
                next_slot, reason = self._choose_reliever(
                    team,
                    team_members[team],
                    team_slots[team],
                    fixture,
                    engine,
                    used_ids[team] | {slot.pitcher_id},
                )
                if next_slot is not None:
                    active[side] = next_slot
                    slot = next_slot
                    role = self.usage_state.team(team).pitchers[
                        slot.pitcher_id
                    ].current_role
                    accumulators.setdefault(
                        slot.pitcher_id,
                        _UsageAccumulator(slot, team, role),
                    )
                    emergency_reasons[slot.pitcher_id] = reason
                    if reason and len(notable) < self.notable_event_limit:
                        notable.append(f"PITCHER_EMERGENCY:{team}:{reason}")
                elif team not in exhaustion_marked:
                    exhaustion_marked.add(team)
                    if len(notable) < self.notable_event_limit:
                        notable.append(f"BULLPEN_EXHAUSTED:{team}")

            self._install(engine, side, slot)
            runs_before = _run_snapshot(engine)
            event = engine.step()
            runs_after = _run_snapshot(engine)
            scored_runner_ids = _scored_runner_ids(runs_before, runs_after)

            acc = accumulators[slot.pitcher_id]
            stats = acc.ensure()
            self._record_pitcher_event(stats, event)

            # The base provider charges all event runs to the active pitcher.
            # Dynamic mid-inning changes require inherited-run ownership instead.
            if event.runs_scored:
                if len(scored_runner_ids) != int(event.runs_scored):
                    raise AssertionError(
                        "scoring-runner identity count does not match event runs"
                    )
                stats.R -= int(event.runs_scored)
                charged_pitchers = _charged_pitcher_ids(
                    scored_runner_ids,
                    run_responsibility,
                    slot.pitcher_id,
                )
                for pitcher_id in charged_pitchers:
                    responsible_acc = accumulators.get(pitcher_id)
                    if responsible_acc is None:
                        raise AssertionError(
                            f"missing accumulator for responsible pitcher: {pitcher_id}"
                        )
                    responsible_acc.ensure().R += 1

            active_runner_ids = set(engine.state.runner_ids())
            if (
                event.kind == "plate_appearance"
                and event.batter_id is not None
                and event.batter_id in active_runner_ids
            ):
                run_responsibility[event.batter_id] = slot.pitcher_id

            # Retired/scored runners no longer carry pitcher responsibility.
            for runner_id in tuple(run_responsibility):
                if runner_id not in active_runner_ids:
                    run_responsibility.pop(runner_id, None)

            used_ids[team].add(slot.pitcher_id)

            if len(notable) < self.notable_event_limit:
                if event.kind == "plate_appearance" and event.result == "home_run":
                    notable.append(f"HR:{event.batter_id}")
                elif event.kind == "steal":
                    notable.append("SB" if event.steal_success else "CS")
                if (
                    engine.state.game_over
                    and event.half == "bottom"
                    and engine.state.inning >= 9
                    and engine.state.home_score > engine.state.away_score
                ):
                    notable.append("WALKOFF")
        else:
            raise GameSafetyLimitError(
                f"full game exceeded {self.max_events} events"
            )

        if not engine.state.game_over:
            raise GameSafetyLimitError("full game terminated without game_over")

        player_lines = tuple(
            self._player_lines(
                fixture.away_team, away_lineup, engine.away_lines
            )
            + self._player_lines(
                fixture.home_team, home_lineup, engine.home_lines
            )
        )
        pitcher_lines: list[PitcherGameLine] = []

        for pitcher_id, acc in accumulators.items():
            if not acc.used or acc.stats is None:
                continue
            acc.stats.validate()
            started = acc.game_role == PitcherRole.STARTER.value
            season_role = self.usage_state.team(acc.team).pitchers[
                pitcher_id
            ].current_role
            self.usage_manager.record_outing(
                acc.team,
                acc.slot.member,
                fixture.game_date,
                season_role,
                started=started,
                BF=acc.stats.BF,
                outs=acc.stats.outs_pitched,
                H=acc.stats.H,
                R=acc.stats.R,
                HR=acc.stats.HR,
                BB=acc.stats.BB,
                HBP=acc.stats.HBP,
                SO=acc.stats.SO,
                emergency_reason=emergency_reasons.get(pitcher_id),
            )
            pitcher_lines.append(
                PitcherGameLine(
                    pitcher_id=pitcher_id,
                    team=acc.team,
                    role=acc.game_role if started else season_role,
                    stats=acc.stats,
                    unsupported_stats=("ER", "W", "L", "SV", "HLD"),
                )
            )

        for team in (fixture.away_team, fixture.home_team):
            for pitcher_id, old_role, new_role in self.usage_manager.evaluate_roles(
                team, team_members[team], fixture.game_date
            ):
                if len(notable) < self.notable_event_limit:
                    notable.append(
                        f"ROLE_CHANGE:{team}:{pitcher_id}:{old_role}->{new_role}"
                    )

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
