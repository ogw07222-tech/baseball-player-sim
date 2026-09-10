import unittest
from datetime import date

from src.game_provider import (
    DeterministicNeutralLineupProvider,
    GameFixture,
    ProductionGameProvider,
)
from src.game_result import PitcherGameLine, ProductionGameResult
from src.hitting.model import PlateAppearanceOutcome
from src.inning import KBO_REGULAR_SEASON_MAX_INNING, PersistentInningEngine
from src.production_advance import ProductionAdvancePipelineState
from src.rng import RNG
from src.simulation import PitcherProfile
from src.stat_aggregation import GamePerformance, HitterCountingStats, PitcherCountingStats


def _engine(seed: int = 1) -> PersistentInningEngine:
    lineups = DeterministicNeutralLineupProvider()
    return PersistentInningEngine(
        lineups.lineup("Away", "FIRST"),
        lineups.lineup("Home", "FIRST"),
        RNG(seed),
        away_pitcher=PitcherProfile(100, 100, 100, "R"),
        home_pitcher=PitcherProfile(100, 100, 100, "R"),
    )


def _finish_with_strikeout(engine: PersistentInningEngine) -> None:
    engine.state.outs = 2
    engine.resolve_plate_appearance(PlateAppearanceOutcome("strikeout"))


class KBORegularSeasonExtraInningTests(unittest.TestCase):
    def test_ninth_inning_tie_advances_to_tenth(self):
        engine = _engine()
        engine.state.inning = 9
        engine.state.half = "bottom"
        engine.state.away_score = 2
        engine.state.home_score = 2

        _finish_with_strikeout(engine)

        self.assertFalse(engine.state.game_over)
        self.assertEqual(engine.state.inning, 10)
        self.assertEqual(engine.state.half, "top")

    def test_tenth_inning_tie_advances_to_eleventh(self):
        engine = _engine()
        engine.state.inning = 10
        engine.state.half = "bottom"
        engine.state.away_score = 3
        engine.state.home_score = 3

        _finish_with_strikeout(engine)

        self.assertFalse(engine.state.game_over)
        self.assertEqual(engine.state.inning, 11)
        self.assertEqual(engine.state.half, "top")

    def test_eleventh_inning_tie_terminates_as_draw(self):
        engine = _engine()
        engine.state.inning = KBO_REGULAR_SEASON_MAX_INNING
        engine.state.half = "bottom"
        engine.state.away_score = 4
        engine.state.home_score = 4

        _finish_with_strikeout(engine)

        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.inning, 11)
        self.assertEqual(engine.state.away_score, engine.state.home_score)

    def test_twelfth_inning_cannot_be_entered_after_completed_eleventh(self):
        engine = _engine()
        engine.state.inning = 11
        engine.state.half = "bottom"
        engine.state.away_score = 0
        engine.state.home_score = 0

        _finish_with_strikeout(engine)

        self.assertTrue(engine.state.game_over)
        self.assertLessEqual(engine.state.inning, KBO_REGULAR_SEASON_MAX_INNING)
        with self.assertRaises(RuntimeError):
            engine.step()

    def test_away_lead_after_eleventh_top_still_gets_home_half(self):
        engine = _engine()
        engine.state.inning = 11
        engine.state.half = "top"
        engine.state.away_score = 5
        engine.state.home_score = 4

        _finish_with_strikeout(engine)

        self.assertFalse(engine.state.game_over)
        self.assertEqual(engine.state.inning, 11)
        self.assertEqual(engine.state.half, "bottom")

    def test_eleventh_inning_walkoff_still_terminates_immediately(self):
        engine = _engine()
        engine.state.inning = 11
        engine.state.half = "bottom"
        engine.state.away_score = 2
        engine.state.home_score = 2

        engine.resolve_plate_appearance(PlateAppearanceOutcome("home_run"))

        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.inning, 11)
        self.assertEqual(engine.state.home_score, 3)

    def test_regulation_walkoff_regression(self):
        engine = _engine()
        engine.state.inning = 9
        engine.state.half = "bottom"
        engine.state.away_score = 1
        engine.state.home_score = 1

        engine.resolve_plate_appearance(PlateAppearanceOutcome("home_run"))

        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.inning, 9)
        self.assertEqual(engine.state.home_score, 2)

    def test_regulation_non_tie_end_regression(self):
        engine = _engine()
        engine.state.inning = 9
        engine.state.half = "bottom"
        engine.state.away_score = 3
        engine.state.home_score = 2

        _finish_with_strikeout(engine)

        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.inning, 9)

    def test_home_lead_after_top_skips_unnecessary_bottom_half(self):
        engine = _engine()
        engine.state.inning = 9
        engine.state.half = "top"
        engine.state.away_score = 1
        engine.state.home_score = 2

        _finish_with_strikeout(engine)

        self.assertTrue(engine.state.game_over)
        self.assertEqual(engine.state.half, "top")
        self.assertEqual(engine.state.inning, 9)

    def test_draw_representation_and_stat_aggregation(self):
        state = ProductionAdvancePipelineState(
            current_date=date(2026, 4, 1),
            team_record_supported=True,
        )
        game = GamePerformance(
            game_date=date(2026, 4, 2),
            level="FIRST",
            hitter_stats=HitterCountingStats(G=1),
            team_result="T",
            score=(2, 2),
        )

        state.add_game(game)

        self.assertEqual(state.team_wins, 0)
        self.assertEqual(state.team_losses, 0)
        self.assertEqual(state.team_ties, 1)
        self.assertEqual(state.season.first_team.hitter.G, 1)
        self.assertEqual(len(state.recent_games), 1)
        self.assertTrue(state.team_record_supported)

    def test_tied_production_result_has_no_team_or_pitcher_win_loss(self):
        pitcher_line = PitcherGameLine(
            pitcher_id="Away:P1",
            team="Away",
            role="reliever",
            stats=PitcherCountingStats(G=1),
            unsupported_stats=("W", "L"),
        )
        result = ProductionGameResult(
            game_date=date(2026, 4, 3),
            away_team="Away",
            home_team="Home",
            away_score=3,
            home_score=3,
            innings_played=11,
            pitcher_lines=(pitcher_line,),
        )

        self.assertIsNone(result.winner)
        self.assertIsNone(result.loser)
        self.assertEqual(result.team_result_for("Away"), "T")
        self.assertEqual(result.team_result_for("Home"), "T")
        self.assertIsNone(result.pitcher_lines[0].stats.as_dict()["W"])
        self.assertIsNone(result.pitcher_lines[0].stats.as_dict()["L"])

    def test_deterministic_full_game_replay_and_inning_cap(self):
        fixture = GameFixture(date(2026, 4, 4), "Away", "Home")
        first = ProductionGameProvider().run_game(fixture, RNG(20260910))
        second = ProductionGameProvider().run_game(fixture, RNG(20260910))

        first_signature = (
            first.away_score,
            first.home_score,
            first.innings_played,
            first.event_count,
            first.team_result_for("Away"),
        )
        second_signature = (
            second.away_score,
            second.home_score,
            second.innings_played,
            second.event_count,
            second.team_result_for("Away"),
        )
        self.assertEqual(first_signature, second_signature)
        self.assertLessEqual(first.innings_played, KBO_REGULAR_SEASON_MAX_INNING)

    def test_representative_full_games_never_enter_twelfth(self):
        fixture = GameFixture(date(2026, 4, 5), "Away", "Home")
        for seed in range(32):
            result = ProductionGameProvider().run_game(fixture, RNG(seed))
            self.assertLessEqual(
                result.innings_played,
                KBO_REGULAR_SEASON_MAX_INNING,
                msg=f"seed {seed} entered inning {result.innings_played}",
            )


if __name__ == "__main__":
    unittest.main()
