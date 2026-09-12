import math
import time
import unittest
from collections import Counter
from unittest.mock import patch

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical import BattedBallState, generate_batted_ball_state
from src.hitting.stadium import (
    DAEJEON_ASYMMETRIC_2026,
    GENERIC_ENGINEERING_BASELINE,
    GOCHEOK_LIKE_2026,
    JAMSIL_LIKE_2026,
    M_TO_FT,
    QUALITY_APPROXIMATED,
    StadiumGeometry,
    WallInteraction,
    resolve_wall_interaction,
)
from src.hitting.trajectory import BattedBallTrajectory, generate_batted_ball_trajectory
from src.rng import RNG


def source_state(*, ev=100.0, la=29.0, spray=0.0):
    return BattedBallState(
        exit_velocity=ev,
        launch_angle=la,
        timing=0.0,
        spray_angle=spray,
        is_fair=abs(spray) <= 45.0,
        contact_quality=0.7,
        pitch_location_x=0.0,
        pitch_location_y=0.0,
        batter_side="R",
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


def fake_trajectory(*, distance=400.0, apex=100.0, spray=0.0):
    radians = math.radians(spray)
    return BattedBallTrajectory(
        horizontal_distance_ft=distance,
        hang_time_s=5.0,
        apex_height_ft=apex,
        landing_x_ft=distance * math.sin(radians),
        landing_y_ft=distance * math.cos(radians),
        trajectory_class="fly_ball",
        apex_distance_fraction=0.5,
        valid=True,
    )


def test_stadium(radius_ft: float, height_ft: float) -> StadiumGeometry:
    values_r = (radius_ft,) * 5
    values_h = (height_ft,) * 5
    return StadiumGeometry(
        stadium_id=f"test_{radius_ft}_{height_ft}",
        season=None,
        is_real_stadium=False,
        source_quality=QUALITY_APPROXIMATED,
        wall_radius_ft=values_r,
        wall_height_ft=values_h,
    )


class Phase2CStadiumWallTests(unittest.TestCase):
    def test_generic_stadium_anchors_and_interpolation(self):
        stadium = GENERIC_ENGINEERING_BASELINE
        lf_radius, lf_height = stadium.wall_at_spray(-45.0)
        center_radius, center_height = stadium.wall_at_spray(0.0)
        mid_radius, mid_height = stadium.wall_at_spray(-11.25)
        self.assertAlmostEqual(lf_radius, 100.0 * M_TO_FT, places=9)
        self.assertAlmostEqual(center_radius, 122.0 * M_TO_FT, places=9)
        self.assertAlmostEqual(mid_radius, 118.5 * M_TO_FT, places=9)
        self.assertAlmostEqual(lf_height, 3.0 * M_TO_FT, places=9)
        self.assertAlmostEqual(center_height, 3.0 * M_TO_FT, places=9)
        self.assertAlmostEqual(mid_height, 3.0 * M_TO_FT, places=9)
        self.assertFalse(stadium.is_real_stadium)

    def test_representative_fixture_metadata_exists(self):
        self.assertTrue(JAMSIL_LIKE_2026.is_real_stadium)
        self.assertTrue(GOCHEOK_LIKE_2026.is_real_stadium)
        self.assertTrue(DAEJEON_ASYMMETRIC_2026.is_real_stadium)
        self.assertEqual(DAEJEON_ASYMMETRIC_2026.source_quality, QUALITY_APPROXIMATED)

    def test_daejeon_asymmetry_and_variable_height_are_visible(self):
        left_radius, left_height = DAEJEON_ASYMMETRIC_2026.wall_at_spray(-45.0)
        right_radius, right_height = DAEJEON_ASYMMETRIC_2026.wall_at_spray(45.0)
        right_mid_radius, right_mid_height = DAEJEON_ASYMMETRIC_2026.wall_at_spray(33.75)
        self.assertGreater(left_radius, right_radius)
        self.assertLess(left_height, right_height)
        self.assertGreater(right_mid_radius, right_radius)
        self.assertAlmostEqual(right_mid_height, 8.0 * M_TO_FT, places=9)

    def test_height_profile_hits_launch_apex_ground_and_beyond_safely(self):
        trajectory = generate_batted_ball_trajectory(source_state(ev=100.0, la=29.0))
        self.assertAlmostEqual(trajectory.height_at_horizontal_distance(0.0), 3.0, places=12)
        apex_x = trajectory.horizontal_distance_ft * trajectory.apex_distance_fraction
        self.assertAlmostEqual(
            trajectory.height_at_horizontal_distance(apex_x),
            trajectory.apex_height_ft,
            places=10,
        )
        self.assertEqual(
            trajectory.height_at_horizontal_distance(trajectory.horizontal_distance_ft),
            0.0,
        )
        self.assertEqual(
            trajectory.height_at_horizontal_distance(trajectory.horizontal_distance_ft + 50.0),
            0.0,
        )

    def test_height_profile_is_finite_across_representative_distances(self):
        trajectory = generate_batted_ball_trajectory(source_state(ev=110.0, la=35.0))
        for fraction in (0.0, 0.1, 0.25, 0.5, 0.75, 0.99, 1.0):
            height = trajectory.height_at_horizontal_distance(
                trajectory.horizontal_distance_ft * fraction
            )
            self.assertTrue(math.isfinite(height))
            self.assertGreaterEqual(height, 0.0)
            self.assertLessEqual(height, trajectory.apex_height_ft)

    def test_wall_interaction_reaches_clears_and_foul_shadow_gate(self):
        trajectory = fake_trajectory(distance=400.0, apex=100.0)
        stadium = test_stadium(300.0, 8.0)
        fair = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=stadium,
        )
        foul = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=50.0,
            is_fair_shadow=False,
            stadium=stadium,
        )
        self.assertTrue(fair.reaches_wall)
        self.assertTrue(fair.clears_wall)
        self.assertTrue(fair.physical_hr_shadow)
        self.assertTrue(foul.clears_wall)
        self.assertFalse(foul.physical_hr_shadow)

    def test_insufficient_distance_is_impossible_hr(self):
        interaction = resolve_wall_interaction(
            trajectory=fake_trajectory(distance=250.0, apex=120.0),
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=test_stadium(300.0, 4.0),
        )
        self.assertFalse(interaction.reaches_wall)
        self.assertFalse(interaction.clears_wall)
        self.assertFalse(interaction.physical_hr_shadow)
        self.assertEqual(interaction.ball_height_at_wall_ft, 0.0)

    def test_reaches_wall_below_top_is_not_hr(self):
        interaction = resolve_wall_interaction(
            trajectory=fake_trajectory(distance=400.0, apex=30.0),
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=test_stadium(390.0, 20.0),
        )
        self.assertTrue(interaction.reaches_wall)
        self.assertLess(interaction.ball_height_at_wall_ft, interaction.wall_height_ft)
        self.assertFalse(interaction.clears_wall)
        self.assertFalse(interaction.physical_hr_shadow)

    def test_higher_wall_cannot_create_hr(self):
        trajectory = fake_trajectory(distance=400.0, apex=100.0)
        low = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=test_stadium(300.0, 8.0),
        )
        high = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=test_stadium(300.0, 90.0),
        )
        self.assertTrue(low.physical_hr_shadow)
        self.assertFalse(high.physical_hr_shadow)

    def test_farther_wall_cannot_create_hr(self):
        trajectory = fake_trajectory(distance=400.0, apex=50.0)
        near = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=test_stadium(250.0, 8.0),
        )
        far = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=test_stadium(395.0, 8.0),
        )
        self.assertTrue(near.physical_hr_shadow)
        self.assertFalse(far.physical_hr_shadow)

    def test_symmetric_park_mirrors_wall_query_and_result(self):
        trajectory_left = fake_trajectory(distance=420.0, apex=100.0, spray=-25.0)
        trajectory_right = fake_trajectory(distance=420.0, apex=100.0, spray=25.0)
        left = resolve_wall_interaction(
            trajectory=trajectory_left,
            spray_angle_deg=-25.0,
            is_fair_shadow=True,
            stadium=GENERIC_ENGINEERING_BASELINE,
        )
        right = resolve_wall_interaction(
            trajectory=trajectory_right,
            spray_angle_deg=25.0,
            is_fair_shadow=True,
            stadium=GENERIC_ENGINEERING_BASELINE,
        )
        self.assertAlmostEqual(left.wall_radius_ft, right.wall_radius_ft, places=12)
        self.assertAlmostEqual(left.wall_height_ft, right.wall_height_ft, places=12)
        self.assertAlmostEqual(left.ball_height_at_wall_ft, right.ball_height_at_wall_ft, places=12)
        self.assertEqual(left.physical_hr_shadow, right.physical_hr_shadow)

    def test_same_inputs_are_exactly_deterministic(self):
        trajectory = generate_batted_ball_trajectory(source_state(ev=103.0, la=31.0, spray=-17.0))
        first = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=-17.0,
            is_fair_shadow=True,
            stadium=GENERIC_ENGINEERING_BASELINE,
        )
        second = resolve_wall_interaction(
            trajectory=trajectory,
            spray_angle_deg=-17.0,
            is_fair_shadow=True,
            stadium=GENERIC_ENGINEERING_BASELINE,
        )
        self.assertEqual(first, second)

    def test_production_bip_state_has_wall_shadow(self):
        for seed in range(1, 200):
            outcome = HittingEngine(
                HitterSnapshot(100, 100, 100, 100),
                PitcherSnapshot(),
                100.0,
                RNG(seed),
            ).simulate_plate_appearance()
            if outcome.batted_ball is not None:
                state = outcome.batted_ball.physical_state
                self.assertIsNotNone(state)
                self.assertIsNotNone(state.trajectory)
                self.assertIsInstance(state.wall_interaction, WallInteraction)
                self.assertEqual(state.wall_interaction.stadium_id, "generic_neutral_v1")
                return
        self.fail("representative seeds produced no batted ball")

    def test_phase2b_fields_and_parent_rng_are_unchanged_when_wall_shadow_disabled(self):
        def run(disabled: bool):
            parent = RNG(20260912)
            before = parent.get_state()
            context = patch("src.hitting.stadium.resolve_wall_interaction", return_value=None) if disabled else None
            if context is not None:
                context.start()
            try:
                states = [
                    generate_batted_ball_state(
                        hitter_contact=100,
                        hitter_power=100,
                        batter_side="R",
                        approach="balanced",
                        pitch_zone="middle",
                        pitch_velocity_quality=0.0,
                        pitch_movement_quality=0.0,
                        pitch_location_quality=0.0,
                        pitch_hittable_quality=0.35,
                        parent_rng=parent,
                    )
                    for _ in range(100)
                ]
            finally:
                if context is not None:
                    context.stop()
            return states, before, parent.get_state()

        baseline, before, baseline_after = run(True)
        candidate, _, candidate_after = run(False)
        self.assertEqual(before, baseline_after)
        self.assertEqual(baseline_after, candidate_after)
        for old, new in zip(baseline, candidate):
            self.assertEqual(old.exit_velocity, new.exit_velocity)
            self.assertEqual(old.launch_angle, new.launch_angle)
            self.assertEqual(old.timing, new.timing)
            self.assertEqual(old.spray_angle, new.spray_angle)
            self.assertEqual(old.trajectory, new.trajectory)
            self.assertIsNone(old.wall_interaction)
            self.assertIsNotNone(new.wall_interaction)

    def test_phase2b_vs_phase2c_paired_pa_outcomes_are_identical(self):
        def run(disabled: bool):
            results = Counter()
            rng = RNG(20260912)
            context = patch("src.hitting.stadium.resolve_wall_interaction", return_value=None) if disabled else None
            start = time.perf_counter()
            if context is not None:
                context.start()
            try:
                for _ in range(20_000):
                    result = HittingEngine(
                        HitterSnapshot(100, 100, 100, 100),
                        PitcherSnapshot(),
                        100.0,
                        rng,
                    ).simulate_plate_appearance().result
                    results[result] += 1
            finally:
                if context is not None:
                    context.stop()
            return results, rng.get_state(), time.perf_counter() - start

        baseline, baseline_rng, baseline_time = run(True)
        candidate, candidate_rng, candidate_time = run(False)
        self.assertEqual(baseline, candidate)
        self.assertEqual(baseline_rng, candidate_rng)
        ratio = candidate_time / max(baseline_time, 1e-9)
        print("PHASE2C_PAIRED_PERFORMANCE", {"baseline_s": baseline_time, "candidate_s": candidate_time, "ratio": ratio})
        self.assertLess(ratio, 1.60)

    def test_wall_lookup_constant_time_guardrail(self):
        trajectory = fake_trajectory(distance=430.0, apex=120.0)
        start = time.perf_counter()
        interactions = [
            resolve_wall_interaction(
                trajectory=trajectory,
                spray_angle_deg=-45.0 + (index % 91),
                is_fair_shadow=True,
                stadium=GENERIC_ENGINEERING_BASELINE,
            )
            for index in range(50_000)
        ]
        elapsed = time.perf_counter() - start
        self.assertEqual(len(interactions), 50_000)
        self.assertLess(elapsed, 5.0, elapsed)


if __name__ == "__main__":
    unittest.main()
