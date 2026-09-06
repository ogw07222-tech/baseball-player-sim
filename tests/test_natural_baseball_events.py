import unittest
from unittest.mock import patch

from src.hitting.model import BattedBall, PlateAppearanceOutcome
from src.inning import PersistentInningEngine
from src.natural_events import PitchMiscEvent, tag_up_probability
from src.player import Player
from src.rng import RNG
from src.simulation import PitcherProfile
from src.stats import PlayerStats
from tools.natural_event_sanity import run_sanity


def make_player(name: str, speed: int = 100) -> Player:
    return Player(
        name,
        24,
        PlayerStats(
            contact=100, power=100, discipline=100, speed=speed, defense=100,
            throwing=100, stamina=100, durability=100, mentality=100, talent=100,
        ),
        position="SS",
    )


def make_lineup(prefix: str, speed: int = 100) -> list[Player]:
    return [make_player(f"{prefix}{i}", speed) for i in range(9)]


def make_engine(seed: int = 1) -> PersistentInningEngine:
    return PersistentInningEngine(
        make_lineup("A"),
        make_lineup("H"),
        RNG(seed),
        away_pitcher=PitcherProfile(100, 100, 100, "R"),
        home_pitcher=PitcherProfile(100, 100, 100, "R"),
    )


def ball(ball_type: str, depth: str = "deep") -> BattedBall:
    return BattedBall(
        contact_quality=0.5,
        exit_quality=0.8,
        ball_type=ball_type,
        direction="center",
        depth=depth,
        distance=0.6,
        difficulty_score=0.4,
        difficulty_tier="HARD",
    )


class NaturalBaseballEventTests(unittest.TestCase):
    def test_runner_on_first_can_score_on_double(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        with patch("src.inning.first_to_home_on_double_probability", return_value=1.0):
            event = engine.resolve_plate_appearance(
                PlateAppearanceOutcome("double", batted_ball=ball("line_drive", "deep"))
            )
        self.assertEqual(event.runs_scored, 1)
        self.assertEqual(engine.state.away_score, 1)
        self.assertIsNone(engine.state.first_runner)
        self.assertIsNone(engine.state.third_runner)
        self.assertEqual(engine.state.second_runner.lineup_index, 0)

    def test_runner_on_first_can_hold_at_third_on_double(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        with patch("src.inning.first_to_home_on_double_probability", return_value=0.0):
            engine.resolve_plate_appearance(
                PlateAppearanceOutcome("double", batted_ball=ball("line_drive", "medium"))
            )
        self.assertEqual(engine.state.away_score, 0)
        self.assertEqual(engine.state.third_runner.lineup_index, 7)
        self.assertEqual(engine.state.second_runner.lineup_index, 0)

    def test_sac_fly_scores_runner_from_third(self):
        engine = make_engine()
        engine.state.third_runner = engine._runner("away", 7)
        with patch("src.inning.tag_up_probability", return_value=1.0):
            event = engine.resolve_plate_appearance(
                PlateAppearanceOutcome("out", batted_ball=ball("fly_ball", "deep"))
            )
        self.assertEqual(event.result, "sacrifice_fly")
        self.assertEqual(engine.state.away_score, 1)
        self.assertIsNone(engine.state.third_runner)
        self.assertEqual(engine.away_lines[0].SF, 1)
        self.assertEqual(engine.away_lines[0].PA, 1)
        self.assertEqual(engine.away_lines[0].AB, 0)
        self.assertEqual(engine.away_lines[0].RBI, 1)

    def test_sac_fly_requires_less_than_two_outs(self):
        engine = make_engine()
        engine.state.outs = 2
        engine.state.third_runner = engine._runner("away", 7)
        with patch("src.inning.tag_up_probability", return_value=1.0):
            event = engine.resolve_plate_appearance(
                PlateAppearanceOutcome("out", batted_ball=ball("fly_ball", "deep"))
            )
        self.assertEqual(event.runs_scored, 0)
        self.assertEqual(engine.state.away_score, 0)
        self.assertEqual(engine.away_lines[0].SF, 0)
        self.assertEqual(engine.away_lines[0].AB, 1)

    def test_sac_fly_does_not_count_as_at_bat(self):
        engine = make_engine()
        engine.state.third_runner = engine._runner("away", 7)
        with patch("src.inning.tag_up_probability", return_value=1.0):
            engine.resolve_plate_appearance(
                PlateAppearanceOutcome("out", batted_ball=ball("fly_ball", "deep"))
            )
        self.assertEqual(engine.away_lines[0].PA, 1)
        self.assertEqual(engine.away_lines[0].AB, 0)

    def test_tag_up_second_to_third(self):
        engine = make_engine()
        engine.state.second_runner = engine._runner("away", 7)
        with patch("src.inning.tag_up_probability", return_value=1.0):
            engine.resolve_plate_appearance(
                PlateAppearanceOutcome("out", batted_ball=ball("fly_ball", "deep"))
            )
        self.assertIsNone(engine.state.second_runner)
        self.assertEqual(engine.state.third_runner.lineup_index, 7)
        self.assertEqual(engine.away_lines[7].XBT, 1)
        self.assertEqual(engine.away_lines[7].XBT_attempts, 1)

    def test_shallow_fly_reduces_tag_up_success(self):
        shallow = tag_up_probability(100, 100, "shallow", from_base=3)
        deep = tag_up_probability(100, 100, "deep", from_base=3)
        self.assertLess(shallow, deep)

    def test_wild_pitch_advances_runner_state(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 8)
        engine.state.second_runner = engine._runner("away", 7)
        engine.state.third_runner = engine._runner("away", 6)
        event = engine.resolve_pitch_misc_event(PitchMiscEvent.WILD_PITCH)
        self.assertEqual(event.runs_scored, 1)
        self.assertEqual(engine.state.away_score, 1)
        self.assertIsNone(engine.state.first_runner)
        self.assertEqual(engine.state.second_runner.lineup_index, 8)
        self.assertEqual(engine.state.third_runner.lineup_index, 7)
        self.assertEqual(engine.away_lines[6].R, 1)

    def test_passed_ball_contract_does_not_require_catcher_stat(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        event = engine.resolve_pitch_misc_event(PitchMiscEvent.PASSED_BALL)
        self.assertEqual(event.misc_event, "passed_ball")
        self.assertIsNone(engine.state.first_runner)
        self.assertEqual(engine.state.second_runner.lineup_index, 7)

    def test_fielders_choice_preserves_batter_on_first(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("fielders_choice"))
        self.assertEqual(engine.state.outs, 1)
        self.assertEqual(engine.state.first_runner.lineup_index, 0)
        self.assertNotIn("away:7:A7", engine.state.runner_ids())

    def test_force_runner_removed_on_fielders_choice(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 7)
        engine.state.second_runner = engine._runner("away", 6)
        engine.resolve_plate_appearance(PlateAppearanceOutcome("fielders_choice"))
        self.assertEqual(engine.state.outs, 1)
        self.assertEqual(engine.state.first_runner.lineup_index, 0)
        self.assertEqual(engine.state.second_runner.lineup_index, 7)
        self.assertNotIn("away:6:A6", engine.state.runner_ids())

    def test_no_duplicate_runner_after_any_resolution(self):
        engine = make_engine()
        engine.state.first_runner = engine._runner("away", 8)
        engine.state.second_runner = engine._runner("away", 7)
        engine.state.third_runner = engine._runner("away", 6)
        engine.resolve_pitch_misc_event(PitchMiscEvent.WILD_PITCH)
        engine.state.validate()
        self.assertEqual(len(engine.state.runner_ids()), len(set(engine.state.runner_ids())))

    def test_scored_runner_removed_from_bases(self):
        engine = make_engine()
        runner = engine._runner("away", 7)
        engine.state.first_runner = runner
        with patch("src.inning.first_to_home_on_double_probability", return_value=1.0):
            engine.resolve_plate_appearance(
                PlateAppearanceOutcome("double", batted_ball=ball("line_drive", "deep"))
            )
        self.assertNotIn(runner.player_id, engine.state.runner_ids())
        self.assertEqual(engine.away_lines[7].R, 1)

    def test_same_seed_same_event_sequence(self):
        left = make_engine(20260906)
        right = make_engine(20260906)
        outcomes = [
            PlateAppearanceOutcome("single", batted_ball=ball("ground_ball", "medium")),
            PlateAppearanceOutcome("double", batted_ball=ball("line_drive", "deep")),
            PlateAppearanceOutcome("out", batted_ball=ball("fly_ball", "deep")),
            PlateAppearanceOutcome("out", batted_ball=ball("ground_ball", "shallow")),
        ]
        left_events = [left.resolve_plate_appearance(o) for o in outcomes]
        right_events = [right.resolve_plate_appearance(o) for o in outcomes]
        self.assertEqual(left_events, right_events)
        self.assertEqual(left.state.runner_ids(), right.state.runner_ids())
        self.assertEqual(
            [line.as_dict() for line in left.away_lines],
            [line.as_dict() for line in right.away_lines],
        )

    def test_old_batting_line_without_sf_loads_with_zero(self):
        from src.records import BattingLine
        line = BattingLine.from_dict({"PA": 12, "AB": 10, "H": 3})
        self.assertEqual(line.SF, 0)
        self.assertEqual(line.as_dict()["SF"], 0)

    def test_100k_event_frequency_sanity(self):
        summary = run_sanity(100_000, 20260906)
        print("NATURAL_EVENT_SANITY", summary)
        self.assertGreaterEqual(summary["events"], 100_000)
        self.assertGreater(summary["SF"], 0)
        self.assertGreater(summary["first_to_home_on_double_attempts"], 0)
        self.assertGreater(summary["tag_up_attempts"], 0)
        self.assertLess(summary["SF_per_600_PA"], 20.0)
        self.assertGreater(summary["first_to_home_on_double_success_rate"], 0.05)
        self.assertLess(summary["first_to_home_on_double_success_rate"], 0.95)
        self.assertGreater(summary["tag_up_success_rate"], 0.01)
        self.assertLess(summary["tag_up_success_rate"], 0.95)
        self.assertEqual(summary["wild_pitch"], 0)
        self.assertEqual(summary["passed_ball"], 0)
        self.assertLess(summary["GDP_per_600_PA"], 50.0)


if __name__ == "__main__":
    unittest.main()
