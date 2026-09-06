import json
import unittest
from datetime import date

from src.production_advance import ProductionAdvancePipelineState
from src.stat_aggregation import (
    GamePerformance,
    PitcherCountingStats,
    aggregate_game_performances,
)


class TeamRecordPersistenceTests(unittest.TestCase):
    @staticmethod
    def _game(day: int, score: tuple[int, int], result: str) -> GamePerformance:
        return GamePerformance(
            game_date=date(2026, 4, day),
            level="FIRST",
            team_result=result,
            score=score,
        )

    def test_win_loss_tie_update_exactly_once(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 3, 31),
            team_record_supported=True,
        )
        state.add_game(self._game(1, (5, 3), "W"))
        state.add_game(self._game(2, (2, 4), "L"))
        state.add_game(self._game(3, (1, 1), "T"))
        self.assertEqual(state.team_wins, 1)
        self.assertEqual(state.team_losses, 1)
        self.assertEqual(state.team_ties, 1)
        self.assertTrue(state.team_record_supported)

    def test_history_truncation_does_not_change_cumulative_record(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 3, 31),
            history_limit=2,
            team_record_supported=True,
        )
        games = (
            self._game(1, (5, 3), "W"),
            self._game(2, (2, 4), "L"),
            self._game(3, (1, 1), "T"),
            self._game(4, (6, 2), "W"),
        )
        for game in games:
            state.add_game(game)
        self.assertEqual(len(state.recent_games), 2)
        self.assertEqual((state.team_wins, state.team_losses, state.team_ties), (2, 1, 1))
        self.assertEqual(state.team_wins + state.team_losses + state.team_ties, 4)

    def test_team_record_roundtrip_is_independent_of_recent_history(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 3, 31),
            history_limit=1,
            team_record_supported=True,
        )
        state.add_game(self._game(1, (5, 3), "W"))
        state.add_game(self._game(2, (2, 4), "L"))
        payload = json.loads(json.dumps(state.as_dict()))
        restored = ProductionAdvancePipelineState.from_dict(payload)
        self.assertEqual(restored.team_record, state.team_record)
        self.assertEqual(len(restored.recent_games), 1)

    def test_old_state_without_team_record_is_safe_and_unsupported(self):
        restored = ProductionAdvancePipelineState.from_dict(
            {"current_date": "2026-03-31"}
        )
        self.assertEqual((restored.team_wins, restored.team_losses, restored.team_ties), (0, 0, 0))
        self.assertFalse(restored.team_record_supported)


class EarnedRunValidityTests(unittest.TestCase):
    def test_exact_er_supported(self):
        line = PitcherCountingStats(
            G=1,
            BF=27,
            outs_pitched=18,
            H=5,
            ER=2,
            er_supported=True,
        )
        self.assertAlmostEqual(line.ERA, 3.0)
        payload = line.as_dict(include_derived=True)
        self.assertEqual(payload["ER"], 2)
        self.assertEqual(payload["ERA"], 3.0)
        self.assertTrue(payload["ER_SUPPORTED"])
        self.assertTrue(payload["ERA_SUPPORTED"])

    def test_er_unsupported_is_not_serialized_as_zero(self):
        line = PitcherCountingStats(
            G=1,
            BF=27,
            outs_pitched=18,
            H=5,
            ER=0,
        ).with_unsupported(("ER",))
        self.assertIsNone(line.ERA)
        payload = line.as_dict(include_derived=True)
        self.assertIsNone(payload["ER"])
        self.assertIsNone(payload["ERA"])
        self.assertFalse(payload["ER_SUPPORTED"])
        self.assertFalse(payload["ERA_SUPPORTED"])

    def test_supported_zero_earned_runs_remains_real_zero(self):
        line = PitcherCountingStats(
            G=1,
            BF=24,
            outs_pitched=18,
            H=4,
            ER=0,
            er_supported=True,
        )
        payload = line.as_dict(include_derived=True)
        self.assertEqual(payload["ER"], 0)
        self.assertEqual(payload["ERA"], 0.0)
        self.assertTrue(payload["ER_SUPPORTED"])

    def test_mixed_aggregation_propagates_unsupported_er(self):
        supported = GamePerformance(
            game_date=date(2026, 4, 1),
            level="FIRST",
            pitcher_stats=PitcherCountingStats(
                G=1,
                BF=24,
                outs_pitched=18,
                H=4,
                ER=0,
                er_supported=True,
            ),
        )
        unsupported = GamePerformance(
            game_date=date(2026, 4, 2),
            level="FIRST",
            pitcher_stats=PitcherCountingStats(
                G=1,
                BF=22,
                outs_pitched=15,
                H=6,
                ER=0,
            ),
            unsupported_stats=("ER",),
        )
        total = aggregate_game_performances((supported, unsupported)).overall.pitcher
        self.assertFalse(total.er_supported)
        self.assertIsNone(total.ERA)
        payload = total.as_dict(include_derived=True)
        self.assertIsNone(payload["ER"])
        self.assertIsNone(payload["ERA"])

    def test_er_support_roundtrip_preserves_distinction(self):
        unsupported = PitcherCountingStats(
            G=1,
            BF=20,
            outs_pitched=15,
            H=4,
            ER=0,
        ).with_unsupported(("ER",))
        restored = PitcherCountingStats.from_dict(
            json.loads(json.dumps(unsupported.as_dict(include_derived=True)))
        )
        self.assertFalse(restored.er_supported)
        self.assertIsNone(restored.ERA)

    def test_legacy_er_without_support_metadata_is_conservatively_unsupported(self):
        restored = PitcherCountingStats.from_dict(
            {
                "G": 1,
                "BF": 20,
                "OUTS_PITCHED": 15,
                "H": 4,
                "ER": 0,
            }
        )
        self.assertEqual(restored.ER, 0)
        self.assertFalse(restored.er_supported)
        self.assertIsNone(restored.ERA)

    def test_official_decision_support_uses_same_zero_vs_unsupported_rule(self):
        line = PitcherCountingStats(G=1, outs_pitched=3).with_unsupported(
            ("W", "L", "SV", "HLD")
        )
        payload = line.as_dict(include_derived=True)
        self.assertIsNone(payload["W"])
        self.assertIsNone(payload["L"])
        self.assertIsNone(payload["SV"])
        self.assertIsNone(payload["HLD"])
        self.assertFalse(payload["W_SUPPORTED"])
        self.assertFalse(payload["L_SUPPORTED"])
        self.assertFalse(payload["SV_SUPPORTED"])
        self.assertFalse(payload["HLD_SUPPORTED"])


if __name__ == "__main__":
    unittest.main()
