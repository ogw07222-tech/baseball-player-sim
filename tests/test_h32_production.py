import math
import unittest

from src.hitting.baserunning import (
    GameState,
    apply_double_play_to_state,
    apply_first_to_third_to_state,
    apply_second_to_home_to_state,
    apply_steal_to_state,
    dp_completion_probability,
    first_to_third_probability,
    second_to_home_probability,
    steal_attempt_probability,
    steal_success_probability,
)
from src.hitting.defense import catch_probability
from src.hitting.model import HitterSnapshot, HittingEngine, Pitch, PitcherSnapshot
from src.player import Player
from src.records import BattingLine
from src.rng import RNG
from src.simulation import _maybe_compat_steal
from src.stats import PlayerStats


def run_profile(hitter: HitterSnapshot, pa: int, seed: int = 20260905, defense: float = 100.0):
    engine = HittingEngine(hitter, PitcherSnapshot(), defense, RNG(seed))
    counts = {key: 0 for key in (
        "walk", "hit_by_pitch", "strikeout", "out", "fielders_choice",
        "reached_on_error", "single", "double", "triple", "home_run",
    )}
    for _ in range(pa):
        counts[engine.simulate_plate_appearance().result] += 1
    hits = counts["single"] + counts["double"] + counts["triple"] + counts["home_run"]
    ab = pa - counts["walk"] - counts["hit_by_pitch"]
    total_bases = (
        counts["single"] + 2 * counts["double"] + 3 * counts["triple"]
        + 4 * counts["home_run"]
    )
    obp = (hits + counts["walk"] + counts["hit_by_pitch"]) / pa
    return {
        "AVG": hits / ab,
        "OBP": obp,
        "SLG": total_bases / ab,
        "OPS": obp + total_bases / ab,
        "HR%": counts["home_run"] / pa,
        "BB%": counts["walk"] / pa,
        "HBP%": counts["hit_by_pitch"] / pa,
        "K%": counts["strikeout"] / pa,
        "H%": hits / pa,
        **counts,
    }


def test_pitch(is_strike: bool, hittable: float = 0.0) -> Pitch:
    return Pitch(is_strike, "middle", "fastball", 0.0, 0.0, 0.0, hittable)


class H32ProductionPortTests(unittest.TestCase):
    def test_phase1_neutral_profile_stays_in_bounded_offense_band(self):
        metrics = run_profile(HitterSnapshot(100, 100, 100, 100), 100_000)
        self.assertGreater(metrics["BB%"], .070)
        self.assertLess(metrics["BB%"], .100)
        self.assertGreater(metrics["HBP%"], .006)
        self.assertLess(metrics["HBP%"], .020)
        self.assertGreater(metrics["K%"], .150)
        self.assertLess(metrics["K%"], .205)
        self.assertGreater(metrics["H%"], .220)
        self.assertLess(metrics["H%"], .285)
        self.assertGreater(metrics["HR%"], .020)
        self.assertLess(metrics["HR%"], .036)

    def test_count_terms_are_independent_at_full_count(self):
        engine = HittingEngine(
            HitterSnapshot(100, 100, 100, 100),
            PitcherSnapshot(),
            100.0,
            RNG(1),
        )
        strike = test_pitch(True)
        ball = test_pitch(False, -0.82)
        # Full count protects the zone while retaining three-ball selectivity.
        self.assertGreater(
            engine._swing_probability(strike, 3, 2),
            engine._swing_probability(strike, 3, 1),
        )
        self.assertLess(
            engine._swing_probability(strike, 3, 2),
            engine._swing_probability(strike, 0, 2),
        )
        # Full-count chase remains lower than another two-strike count.
        self.assertLess(
            engine._swing_probability(ball, 3, 2),
            engine._swing_probability(ball, 0, 2),
        )
        self.assertLess(
            engine._swing_probability(ball, 3, 0),
            engine._swing_probability(ball, 3, 1),
        )

    def test_discipline_chase_separation_is_bounded_and_meaningful(self):
        ball = test_pitch(False, -0.82)
        neutral = HittingEngine(HitterSnapshot(100, 100, 100, 100), PitcherSnapshot(), 100.0, RNG(2))
        poor = HittingEngine(HitterSnapshot(100, 100, 75, 100), PitcherSnapshot(), 100.0, RNG(2))
        good = HittingEngine(HitterSnapshot(100, 100, 125, 100), PitcherSnapshot(), 100.0, RNG(2))
        p_neutral = neutral._swing_probability(ball, 0, 0)
        p_poor = poor._swing_probability(ball, 0, 0)
        p_good = good._swing_probability(ball, 0, 0)
        self.assertGreater(p_poor, p_neutral)
        self.assertGreater(p_neutral, p_good)
        self.assertLess(p_poor - p_neutral, .09)

    def test_hbp_is_out_of_zone_only_and_control_sensitive(self):
        strike = test_pitch(True)
        ball = test_pitch(False, -0.82)
        wild = HittingEngine(HitterSnapshot(100, 100, 100, 100), PitcherSnapshot(control=70), 100.0, RNG(3))
        neutral = HittingEngine(HitterSnapshot(100, 100, 100, 100), PitcherSnapshot(control=100), 100.0, RNG(3))
        command = HittingEngine(HitterSnapshot(100, 100, 100, 100), PitcherSnapshot(control=130), 100.0, RNG(3))
        self.assertEqual(neutral._hit_by_pitch_probability(strike), 0.0)
        self.assertGreater(wild._hit_by_pitch_probability(ball), neutral._hit_by_pitch_probability(ball))
        self.assertGreater(neutral._hit_by_pitch_probability(ball), command._hit_by_pitch_probability(ball))

    def test_two_strike_foul_does_not_become_strike_three(self):
        class ScriptedEngine(HittingEngine):
            def __init__(self):
                super().__init__(HitterSnapshot(100, 100, 100, 100), PitcherSnapshot(), 100.0, RNG(9))
                self.strikes_seen = []
                self.calls = 0

            def _pitch(self):
                return test_pitch(True)

            def _is_hit_by_pitch(self, pitch):
                return False

            def _swing_probability(self, pitch, balls, strikes):
                return 1.0

            def _contact_resolution(self, pitch, strikes):
                self.strikes_seen.append(strikes)
                self.calls += 1
                if self.calls <= 3:
                    return "foul", 0.0, 0.0
                return "miss", 0.0, 0.0

        engine = ScriptedEngine()
        result = engine.simulate_plate_appearance()
        self.assertEqual(result.result, "strikeout")
        self.assertEqual(engine.strikes_seen, [0, 1, 2, 2])

    def test_contact_monotonicity(self):
        low = run_profile(HitterSnapshot(80, 100, 100, 100), 35_000, 11)
        high = run_profile(HitterSnapshot(120, 100, 100, 100), 35_000, 11)
        self.assertGreater(high["AVG"], low["AVG"])
        self.assertLess(high["K%"], low["K%"])

    def test_power_monotonicity(self):
        low = run_profile(HitterSnapshot(100, 80, 100, 100), 35_000, 12)
        high = run_profile(HitterSnapshot(100, 120, 100, 100), 35_000, 12)
        self.assertGreater(high["SLG"], low["SLG"])
        self.assertGreater(high["HR%"], low["HR%"])

    def test_discipline_monotonicity(self):
        low = run_profile(HitterSnapshot(100, 100, 80, 100), 35_000, 13)
        high = run_profile(HitterSnapshot(100, 100, 120, 100), 35_000, 13)
        self.assertGreater(high["BB%"], low["BB%"])
        self.assertLess(high["K%"], low["K%"])

    def test_speed_monotonicity(self):
        low = run_profile(HitterSnapshot(100, 100, 100, 60), 35_000, 14)
        high = run_profile(HitterSnapshot(100, 100, 100, 140), 35_000, 14)
        self.assertGreater(high["SLG"], low["SLG"])

    def test_defense_monotonicity(self):
        poor = run_profile(HitterSnapshot(100, 100, 100, 100), 35_000, 15, 70)
        good = run_profile(HitterSnapshot(100, 100, 100, 100), 35_000, 15, 130)
        self.assertGreater(poor["H%"], good["H%"])

    def test_steal_suppression_success_and_diminishing_returns(self):
        state = GameState(5, 1, 0, True, False, False)
        self.assertLess(steal_attempt_probability(60, state), steal_attempt_probability(100, state))
        self.assertLess(steal_attempt_probability(100, state), steal_attempt_probability(140, state))
        self.assertLess(steal_success_probability(60, state), steal_success_probability(140, state))
        self.assertLess(steal_success_probability(220, state), .926)
        self.assertLess(steal_attempt_probability(50, state), .002)
        self.assertLess(steal_attempt_probability(70, state), .01)
        self.assertLess(
            steal_attempt_probability(170, state) - steal_attempt_probability(150, state),
            steal_attempt_probability(120, state) - steal_attempt_probability(100, state),
        )

    def test_dp_and_advancement_improve_with_speed(self):
        self.assertGreater(dp_completion_probability(60), dp_completion_probability(140))
        self.assertLess(first_to_third_probability(60), first_to_third_probability(140))
        self.assertLess(second_to_home_probability(60), second_to_home_probability(140))

    def test_game_state_adapters_mutate_only_on_resolved_events(self):
        class AlwaysZero:
            def random(self):
                return 0.0

        state = GameState(5, 1, 0, True, False, False)
        steal = apply_steal_to_state(140, state, AlwaysZero(), 100.0)
        self.assertTrue(steal.attempted and steal.success)
        self.assertFalse(state.first_occupied)
        self.assertTrue(state.second_occupied)

        state = GameState(5, 1, 0, True, False, False)
        advance = apply_first_to_third_to_state(120, state, AlwaysZero(), 100.0)
        self.assertTrue(advance.attempted and advance.success)
        self.assertFalse(state.first_occupied)
        self.assertTrue(state.third_occupied)

        state = GameState(5, 1, 0, False, True, False)
        home = apply_second_to_home_to_state(120, state, AlwaysZero(), 100.0)
        self.assertTrue(home.attempted and home.success)
        self.assertEqual(home.runs_scored, 1)
        self.assertFalse(state.second_occupied)

        state = GameState(5, 0, 0, True, False, False)
        dp = apply_double_play_to_state(60, state, AlwaysZero())
        self.assertTrue(dp.attempted and dp.success)
        self.assertEqual(dp.outs_added, 2)
        self.assertEqual(state.outs, 2)
        self.assertFalse(state.first_occupied)

    def test_defense_tier_bounds(self):
        self.assertGreater(catch_probability("ROUTINE", 100), .98)
        self.assertLess(catch_probability("EXCEPTIONAL", 160), .25)
        self.assertGreater(catch_probability("HARD", 160), catch_probability("HARD", 70))

    def test_probability_safety(self):
        state = GameState(8, 1, 0, True, False, False)
        for stat in (30, 40, 50, 70, 100, 130, 160, 190, 220):
            values = (
                steal_attempt_probability(stat, state),
                steal_success_probability(stat, state),
                first_to_third_probability(stat),
                second_to_home_probability(stat),
                dp_completion_probability(stat),
            )
            self.assertTrue(all(math.isfinite(v) and 0 <= v <= 1 for v in values))

    def test_deterministic_seed(self):
        a = run_profile(HitterSnapshot(100, 100, 100, 100), 10_000, 321)
        b = run_profile(HitterSnapshot(100, 100, 100, 100), 10_000, 321)
        self.assertEqual(a, b)

    def test_compat_baserunning_does_not_consume_parent_rng(self):
        player = Player(
            "RNG",
            18,
            PlayerStats(100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
        )
        line = BattingLine()
        parent = RNG(444)
        before = parent.get_state()
        _maybe_compat_steal(player, line, "single", parent, 0, 4, 100.0)
        self.assertEqual(before, parent.get_state())

    def test_old_batting_line_save_load_defaults(self):
        old = {
            "G": 10, "PA": 20, "AB": 17, "H": 6, "2B": 2, "3B": 0,
            "HR": 1, "BB": 3, "SO": 4, "HBP": 0, "SB": 1, "CS": 0,
            "R": 3, "RBI": 4,
        }
        line = BattingLine.from_dict(old)
        self.assertEqual(line.ROE, 0)
        self.assertEqual(line.SB_attempts, 0)
        self.assertEqual(line.DP_avoided, 0)
        self.assertEqual(line.XBT, 0)
        restored = BattingLine.from_dict(line.as_dict())
        self.assertEqual(line.as_dict(), restored.as_dict())


if __name__ == "__main__":
    unittest.main()
