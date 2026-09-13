import math
import time
import unittest
from collections import Counter
from datetime import date
from unittest.mock import patch

from src.game_provider import GameFixture, ProductionGameProvider
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical import BattedBallState, generate_batted_ball_state
from src.hitting.trajectory import BattedBallTrajectory, generate_batted_ball_trajectory
from src.rng import RNG


def state(*, ev=100.0, la=29.0, spray=0.0, side="R"):
    return BattedBallState(
        exit_velocity=ev,
        launch_angle=la,
        timing=0.0,
        spray_angle=spray,
        is_fair=abs(spray) <= 45.0,
        contact_quality=0.7,
        pitch_location_x=0.0,
        pitch_location_y=0.0,
        batter_side=side,
    )


def generated_state(seed: int):
    return generate_batted_ball_state(
        hitter_contact=100,
        hitter_power=100,
        batter_side="R",
        approach="balanced",
        pitch_zone="middle",
        pitch_velocity_quality=0.0,
        pitch_movement_quality=0.0,
        pitch_location_quality=0.0,
        pitch_hittable_quality=0.35,
        parent_rng=RNG(seed),
    )


class Phase2BTrajectoryTests(unittest.TestCase):
    def test_trajectory_schema_and_finite_outputs(self):
        trajectory = generate_batted_ball_trajectory(state())
        self.assertIsInstance(trajectory, BattedBallTrajectory)
        for value in (
            trajectory.horizontal_distance_ft,
            trajectory.hang_time_s,
            trajectory.apex_height_ft,
            trajectory.landing_x_ft,
            trajectory.landing_y_ft,
        ):
            self.assertTrue(math.isfinite(value))
        self.assertGreaterEqual(trajectory.horizontal_distance_ft, 0.0)
        self.assertGreaterEqual(trajectory.hang_time_s, 0.0)
        self.assertGreaterEqual(trajectory.apex_height_ft, 0.0)
        self.assertTrue(trajectory.valid)

    def test_research_anchor_is_baseball_like_not_vacuum_range(self):
        trajectory = generate_batted_ball_trajectory(state(ev=100.0, la=29.0))
        self.assertGreater(trajectory.horizontal_distance_ft, 390.0)
        self.assertLess(trajectory.horizontal_distance_ft, 405.0)
        self.assertLess(trajectory.horizontal_distance_ft, 500.0)

    def test_higher_ev_increases_carry_at_same_launch_angle(self):
        low = generate_batted_ball_trajectory(state(ev=80.0, la=29.0))
        mid = generate_batted_ball_trajectory(state(ev=100.0, la=29.0))
        high = generate_batted_ball_trajectory(state(ev=110.0, la=29.0))
        self.assertLess(low.horizontal_distance_ft, mid.horizontal_distance_ft)
        self.assertLess(mid.horizontal_distance_ft, high.horizontal_distance_ft)
        self.assertLess(low.apex_height_ft, mid.apex_height_ft)
        self.assertLess(mid.apex_height_ft, high.apex_height_ft)

    def test_launch_angle_shape_peaks_near_high_twenty_not_forty_five(self):
        d20 = generate_batted_ball_trajectory(state(ev=100.0, la=20.0))
        d29 = generate_batted_ball_trajectory(state(ev=100.0, la=29.0))
        d45 = generate_batted_ball_trajectory(state(ev=100.0, la=45.0))
        d60 = generate_batted_ball_trajectory(state(ev=100.0, la=60.0))
        self.assertGreater(d29.horizontal_distance_ft, d20.horizontal_distance_ft)
        self.assertGreater(d29.horizontal_distance_ft, d45.horizontal_distance_ft)
        self.assertGreater(d45.horizontal_distance_ft, d60.horizontal_distance_ft)
        self.assertGreater(d45.hang_time_s, d29.hang_time_s)
        self.assertGreater(d60.hang_time_s, d45.hang_time_s)
        self.assertGreater(d60.apex_height_ft, d45.apex_height_ft)

    def test_negative_and_near_zero_launch_are_shallow_and_stable(self):
        negative = generate_batted_ball_trajectory(state(ev=90.0, la=-10.0))
        zero = generate_batted_ball_trajectory(state(ev=90.0, la=0.0))
        low = generate_batted_ball_trajectory(state(ev=90.0, la=4.0))
        self.assertLess(negative.horizontal_distance_ft, 30.0)
        self.assertLess(zero.horizontal_distance_ft, 70.0)
        self.assertLess(negative.hang_time_s, 0.5)
        self.assertGreater(low.horizontal_distance_ft, zero.horizontal_distance_ft)
        self.assertEqual(negative.apex_height_ft, 3.0)

    def test_extreme_launch_angles_remain_stable(self):
        for launch_angle in (-65.0, -45.0, 75.0, 85.0):
            trajectory = generate_batted_ball_trajectory(state(ev=125.0, la=launch_angle))
            self.assertTrue(math.isfinite(trajectory.horizontal_distance_ft))
            self.assertLessEqual(trajectory.horizontal_distance_ft, 550.0)
            self.assertLessEqual(trajectory.hang_time_s, 9.0)
            self.assertLessEqual(trajectory.apex_height_ft, 260.0)

    def test_coordinate_mirror_and_center_field_axis(self):
        center = generate_batted_ball_trajectory(state(ev=100.0, la=29.0, spray=0.0))
        left = generate_batted_ball_trajectory(state(ev=100.0, la=29.0, spray=-25.0))
        right = generate_batted_ball_trajectory(state(ev=100.0, la=29.0, spray=25.0))
        self.assertAlmostEqual(center.landing_x_ft, 0.0, places=12)
        self.assertGreater(center.landing_y_ft, 0.0)
        self.assertAlmostEqual(left.landing_x_ft, -right.landing_x_ft, places=12)
        self.assertAlmostEqual(left.landing_y_ft, right.landing_y_ft, places=12)
        self.assertAlmostEqual(left.horizontal_distance_ft, right.horizontal_distance_ft, places=12)

    def test_same_state_is_exactly_deterministic(self):
        source = state(ev=103.2, la=31.7, spray=-17.4)
        self.assertEqual(
            generate_batted_ball_trajectory(source),
            generate_batted_ball_trajectory(source),
        )

    def test_phase2a_fields_are_identical_with_trajectory_disabled(self):
        with patch("src.hitting.trajectory.generate_batted_ball_trajectory", return_value=None):
            baseline = [generated_state(seed) for seed in range(500)]
        candidate = [generated_state(seed) for seed in range(500)]
        for before, after in zip(baseline, candidate):
            self.assertEqual(before.exit_velocity, after.exit_velocity)
            self.assertEqual(before.launch_angle, after.launch_angle)
            self.assertEqual(before.timing, after.timing)
            self.assertEqual(before.spray_angle, after.spray_angle)
            self.assertEqual(before.is_fair, after.is_fair)
            self.assertEqual(before.contact_quality, after.contact_quality)
            self.assertIsNone(before.trajectory)
            self.assertIsNotNone(after.trajectory)

    def test_production_bip_state_has_trajectory(self):
        for seed in range(1, 200):
            outcome = HittingEngine(
                HitterSnapshot(100, 100, 100, 100),
                PitcherSnapshot(),
                100.0,
                RNG(seed),
            ).simulate_plate_appearance()
            if outcome.batted_ball is not None:
                self.assertIsNotNone(outcome.batted_ball.physical_state)
                self.assertIsNotNone(outcome.batted_ball.physical_state.trajectory)
                return
        self.fail("representative seeds produced no batted ball")

    def test_trajectory_generator_constant_time_guardrail(self):
        sources = [
            state(
                ev=70.0 + (i % 55),
                la=-20.0 + (i % 90),
                spray=-40.0 + (i % 81),
            )
            for i in range(50_000)
        ]
        start = time.perf_counter()
        trajectories = [generate_batted_ball_trajectory(source) for source in sources]
        elapsed = time.perf_counter() - start
        self.assertEqual(len(trajectories), 50_000)
        # Deliberately broad CI guard: catches accidental stepping/integration.
        self.assertLess(elapsed, 6.0, elapsed)

    def test_phase2a_vs_phase2b_paired_50k_pa_and_games_preserve_outcomes(self):
        def run_pa(disabled: bool):
            results = Counter()
            start = time.perf_counter()
            context = patch("src.hitting.trajectory.generate_batted_ball_trajectory", return_value=None) if disabled else None
            if context is not None:
                context.start()
            try:
                rng = RNG(20260912)
                for _ in range(50_000):
                    outcome = HittingEngine(
                        HitterSnapshot(100, 100, 100, 100),
                        PitcherSnapshot(),
                        100.0,
                        rng,
                    ).simulate_plate_appearance()
                    results[outcome.result] += 1
                final_rng = rng.get_state()
            finally:
                if context is not None:
                    context.stop()
            return results, final_rng, time.perf_counter() - start

        baseline_results, baseline_rng, baseline_time = run_pa(True)
        candidate_results, candidate_rng, candidate_time = run_pa(False)
        self.assertEqual(baseline_results, candidate_results)
        self.assertEqual(baseline_rng, candidate_rng)

        def run_games(disabled: bool):
            summaries = []
            start = time.perf_counter()
            context = patch("src.hitting.trajectory.generate_batted_ball_trajectory", return_value=None) if disabled else None
            if context is not None:
                context.start()
            try:
                provider = ProductionGameProvider()
                fixture = GameFixture(date(2026, 4, 1), "Away", "Home")
                for seed in range(250):
                    result = provider.run_game(fixture, RNG(900000 + seed))
                    summaries.append((
                        result.away_score,
                        result.home_score,
                        result.innings_played,
                        result.event_count,
                    ))
            finally:
                if context is not None:
                    context.stop()
            return summaries, time.perf_counter() - start

        baseline_games, baseline_game_time = run_games(True)
        candidate_games, candidate_game_time = run_games(False)
        self.assertEqual(baseline_games, candidate_games)

        pa_ratio = candidate_time / max(baseline_time, 1e-9)
        game_ratio = candidate_game_time / max(baseline_game_time, 1e-9)
        print(
            "PHASE2_CUMULATIVE_PAIRED_PERFORMANCE",
            {
                "pa_baseline_s": baseline_time,
                "pa_candidate_s": candidate_time,
                "pa_ratio": pa_ratio,
                "game_baseline_s": baseline_game_time,
                "game_candidate_s": candidate_game_time,
                "game_ratio": game_ratio,
                "note": "trajectory-enabled path now includes Phase2B/C/D/E-A/E-B",
            },
        )
        # This comparison originally isolated Phase2B. Since Phase2C+ attach all
        # downstream metadata only when a trajectory exists, disabling trajectory
        # now disables the entire cumulative Phase2 stack. Keep the paired run as
        # outcome/RNG regression plus telemetry; stage-owned O(1) performance gates
        # are the direct 50k guards, and 05 owns cumulative paired validation.
        self.assertGreater(baseline_time, 0.0)
        self.assertGreater(candidate_time, 0.0)
        self.assertGreater(baseline_game_time, 0.0)
        self.assertGreater(candidate_game_time, 0.0)


if __name__ == "__main__":
    unittest.main()
