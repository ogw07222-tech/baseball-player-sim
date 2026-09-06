import json
import unittest
from datetime import date, timedelta

from src.game_result import PitcherGameLine
from src.inning import BaseStateResolver, InningState, RunnerState
from src.pitcher_usage_game_provider import _charged_pitcher_ids
from src.player import Player
from src.production_advance import ProductionAdvancePipelineState
from src.records import BattingLine
from src.rng import RNG
from src.stat_aggregation import (
    GamePerformance,
    PitcherCountingStats,
    pitcher_stats_from_result,
)
from src.stats import PlayerStats


def player(name: str) -> Player:
    return Player(
        name,
        24,
        PlayerStats(100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
    )


def runner(slot: int, name: str) -> RunnerState:
    return RunnerState("away", slot, player(name))


def game(day: int, score: tuple[int, int], result: str | None = None) -> GamePerformance:
    if result is None:
        result = "W" if score[0] > score[1] else "L" if score[0] < score[1] else "T"
    return GamePerformance(
        date(2026, 4, 1) + timedelta(days=day),
        "FIRST",
        team_result=result,
        score=score,
    )


class FieldersChoiceBlockingTests(unittest.TestCase):
    def _loaded(self, outs: int):
        state = InningState(outs=outs)
        first, second, third, batter = (
            runner(1, "R1"), runner(2, "R2"), runner(3, "R3"), runner(4, "B")
        )
        state.first_runner, state.second_runner, state.third_runner = first, second, third
        resolver = BaseStateResolver(state, RNG(7), lambda _r: BattingLine())
        return state, resolver, first, second, third, batter

    def test_bases_loaded_zero_out_lead_force_is_home(self):
        state, resolver, first, second, third, batter = self._loaded(0)
        resolution = resolver.fielders_choice(batter)
        self.assertEqual(resolution.scored_runners, ())
        self.assertEqual(state.outs, 1)
        self.assertIs(state.first_runner, batter)
        self.assertIs(state.second_runner, first)
        self.assertIs(state.third_runner, second)
        self.assertNotIn(third.player_id, state.runner_ids())
        self.assertEqual(len(state.runner_ids()), len(set(state.runner_ids())))

    def test_bases_loaded_one_out_lead_force_is_home(self):
        state, resolver, first, second, third, batter = self._loaded(1)
        resolution = resolver.fielders_choice(batter)
        self.assertEqual(resolution.scored_runners, ())
        self.assertEqual(state.outs, 2)
        self.assertEqual(state.runner_ids(), (batter.player_id, first.player_id, second.player_id))
        self.assertNotIn(third.player_id, state.runner_ids())

    def test_bases_loaded_two_out_preserves_inning_ending_semantics(self):
        state, resolver, first, _second, _third, batter = self._loaded(2)
        resolution = resolver.fielders_choice(batter)
        self.assertEqual(resolution.scored_runners, ())
        self.assertEqual(state.outs, 3)
        self.assertTrue(resolution.third_out_is_force)
        self.assertIs(state.first_runner, batter)
        self.assertIs(state.second_runner, first)

    def test_other_fielders_choice_states_regression(self):
        cases = (
            (runner(1, "F1"), None, None),
            (runner(1, "FS1"), runner(2, "FS2"), None),
            (runner(1, "FT1"), None, runner(3, "FT3")),
            (None, runner(2, "ST2"), runner(3, "ST3")),
        )
        for first, second, third in cases:
            with self.subTest(first=first, second=second, third=third):
                state = InningState(first_runner=first, second_runner=second, third_runner=third)
                batter = runner(8, "BAT")
                resolution = BaseStateResolver(state, RNG(1), lambda _r: BattingLine()).fielders_choice(batter)
                self.assertEqual(resolution.scored_runners, ())
                self.assertEqual(state.outs, 1)
                self.assertEqual(len(state.runner_ids()), len(set(state.runner_ids())))
                self.assertIs(state.first_runner, batter)


class TeamRecordBlockingTests(unittest.TestCase):
    def test_win_loss_tie_and_cumulative_record(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 4, 1),
            team_record_supported=True,
        )
        state.add_game(game(1, (5, 2)))
        state.add_game(game(2, (1, 4)))
        state.add_game(game(3, (3, 3)))
        self.assertEqual(state.team_record, {"wins": 1, "losses": 1, "ties": 1, "supported": True})

    def test_exact_score_is_canonical(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 4, 1),
            team_record_supported=True,
        )
        with self.assertRaises(ValueError):
            state.add_game(game(1, (5, 2), "L"))

    def test_roundtrip_continue_and_history_truncation(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 4, 1),
            team_record_supported=True,
            history_limit=2,
        )
        for item in (game(1, (4, 1)), game(2, (2, 5)), game(3, (6, 6))):
            state.add_game(item)
        self.assertEqual(len(state.recent_games), 2)
        restored = ProductionAdvancePipelineState.from_dict(json.loads(json.dumps(state.as_dict())))
        restored.add_game(game(4, (7, 2)))
        self.assertEqual(restored.team_record, {"wins": 2, "losses": 1, "ties": 1, "supported": True})
        self.assertEqual(len(restored.recent_games), 2)

    def test_legacy_state_without_team_record_is_safe_and_unsupported(self):
        restored = ProductionAdvancePipelineState.from_dict({}, default_date=date(2026, 4, 1))
        self.assertEqual(restored.team_record, {"wins": 0, "losses": 0, "ties": 0, "supported": False})


class EarnedRunSupportBlockingTests(unittest.TestCase):
    def test_supported_zero_er_is_real_zero(self):
        stats = PitcherCountingStats(G=1, BF=12, outs_pitched=9, H=2, ER=0)
        self.assertTrue(stats.er_supported)
        self.assertEqual(stats.ERA, 0.0)
        payload = stats.as_dict(include_derived=True)
        self.assertEqual(payload["ER"], 0)
        self.assertEqual(payload["ERA"], 0.0)
        self.assertTrue(payload["ER_SUPPORTED"])

    def test_unsupported_er_is_not_serialized_as_zero(self):
        stats = PitcherCountingStats(G=1, BF=12, outs_pitched=9, H=2).with_unsupported(("ER",))
        self.assertFalse(stats.er_supported)
        self.assertIsNone(stats.ERA)
        payload = stats.as_dict(include_derived=True)
        self.assertIsNone(payload["ER"])
        self.assertIsNone(payload["ERA"])
        self.assertFalse(payload["ERA_SUPPORTED"])

    def test_mixed_aggregation_stays_unsupported(self):
        total = PitcherCountingStats(G=1, BF=12, outs_pitched=9, H=2, ER=1)
        total.add(PitcherCountingStats(G=1, BF=10, outs_pitched=6, H=1).with_unsupported(("ER",)))
        self.assertFalse(total.er_supported)
        self.assertIsNone(total.ERA)
        self.assertIsNone(total.as_dict(include_derived=True)["ER"])

    def test_support_metadata_roundtrip_and_legacy_semantics(self):
        unsupported = PitcherCountingStats(G=1, outs_pitched=3).with_unsupported(("ER", "W", "L", "SV", "HLD"))
        restored = PitcherCountingStats.from_dict(json.loads(json.dumps(unsupported.as_dict())))
        self.assertFalse(restored.er_supported)
        self.assertIsNone(restored.ERA)
        legacy = PitcherCountingStats.from_dict({"G": 1, "OUTS_PITCHED": 3, "ER": 0})
        self.assertFalse(legacy.er_supported)
        self.assertIsNone(legacy.ERA)

    def test_source_adapter_and_game_line_propagate_support(self):
        class ExactSource:
            G = 1; BF = 8; outs = 6; H = 1; ER = 0; HR = 0; BB = 1; HBP = 0; SO = 2
        exact = pitcher_stats_from_result(ExactSource(), started=True)
        self.assertTrue(exact.er_supported)
        line = PitcherGameLine("P", "T", "SP", exact, ("ER", "W", "L", "SV", "HLD"))
        self.assertFalse(line.stats.er_supported)
        self.assertIsNone(line.stats.as_dict(include_derived=True)["ERA"])


class InheritedRunResponsibilityTests(unittest.TestCase):
    def test_inherited_and_new_runner_charge_correct_pitcher(self):
        responsibility = {"runner-A": "pitcher-A"}
        charged = _charged_pitcher_ids(
            ("runner-A", "runner-B"),
            responsibility,
            "pitcher-B",
        )
        self.assertEqual(charged, ("pitcher-A", "pitcher-B"))
        self.assertEqual(responsibility, {})


if __name__ == "__main__":
    unittest.main()
