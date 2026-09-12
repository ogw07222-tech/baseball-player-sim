import math
import time
import unittest
from unittest.mock import patch

from src.hitting.ground_travel import (
    GroundTravelState,
    generate_ground_travel_state,
    impact_horizontal_speed_proxy,
    rollout_distance_ft,
)
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical import generate_batted_ball_state
from src.hitting.stadium import WallInteraction
from src.hitting.trajectory import BattedBallTrajectory
from src.rng import RNG


def trajectory(distance, spray_deg=0.0, *, hang=2.0, cls="ground_like", valid=True):
    angle = math.radians(spray_deg)
    return BattedBallTrajectory(
        horizontal_distance_ft=distance,
        hang_time_s=hang,
        apex_height_ft=20.0,
        landing_x_ft=distance * math.sin(angle),
        landing_y_ft=distance * math.cos(angle),
        trajectory_class=cls,
        apex_distance_fraction=0.0 if cls == "ground_like" else 0.5,
        valid=valid,
    )


def wall(radius=500.0, *, reaches=False):
    return WallInteraction(
        stadium_id="test",
        wall_radius_ft=radius,
        wall_height_ft=10.0,
        reaches_wall=reaches,
        ball_height_at_wall_ft=5.0 if reaches else 0.0,
        clearance_ft=-5.0 if reaches else -10.0,
        clears_wall=False,
        wall_contact=False,
        physical_hr_shadow=False,
    )


class Phase2EAGroundTravelTests(unittest.TestCase):
    def test_fields_are_finite_and_nonnegative(self):
        state = generate_ground_travel_state(
            trajectory=trajectory(120.0, -12.0, hang=1.2),
            wall_interaction=wall(),
            spray_angle_deg=-12.0,
        )
        self.assertTrue(state.valid)
        numeric = (
            state.impact_horizontal_speed_fps,
            state.post_impact_horizontal_speed_fps,
            state.bounce_distance_ft,
            state.rollout_start_speed_fps,
            state.rollout_distance_ft,
            state.ground_travel_distance_ft,
            state.first_impact_x_ft,
            state.first_impact_y_ft,
            state.final_x_ft,
            state.final_y_ft,
            state.final_radial_distance_ft,
        )
        self.assertTrue(all(math.isfinite(v) for v in numeric))
        self.assertGreaterEqual(state.impact_horizontal_speed_fps, 0.0)
        self.assertGreaterEqual(state.rollout_distance_ft, 0.0)
        self.assertGreaterEqual(state.ground_travel_distance_ft, 0.0)
        self.assertGreaterEqual(state.final_radial_distance_ft, 0.0)

    def test_impact_speed_proxy_is_monotonic_in_distance(self):
        slow = impact_horizontal_speed_proxy(
            first_impact_distance_ft=80.0,
            hang_time_s=1.0,
            trajectory_class="ground_like",
        )
        fast = impact_horizontal_speed_proxy(
            first_impact_distance_ft=120.0,
            hang_time_s=1.0,
            trajectory_class="ground_like",
        )
        self.assertGreaterEqual(fast, slow)

    def test_rollout_is_monotonic_in_speed_and_resistance(self):
        zero = rollout_distance_ft(0.0, 35.0)
        medium = rollout_distance_ft(30.0, 35.0)
        fast = rollout_distance_ft(60.0, 35.0)
        more_resistance = rollout_distance_ft(60.0, 70.0)
        self.assertEqual(zero, 0.0)
        self.assertLessEqual(medium, fast)
        self.assertLessEqual(more_resistance, fast)

    def test_class_effects_keep_popup_ground_travel_below_ground_like(self):
        ground = generate_ground_travel_state(
            trajectory=trajectory(100.0, hang=1.0, cls="ground_like"),
            wall_interaction=wall(),
            spray_angle_deg=0.0,
        )
        popup = generate_ground_travel_state(
            trajectory=trajectory(100.0, hang=1.0, cls="popup"),
            wall_interaction=wall(),
            spray_angle_deg=0.0,
        )
        self.assertTrue(ground.valid)
        self.assertTrue(popup.valid)
        self.assertGreater(ground.ground_travel_distance_ft, popup.ground_travel_distance_ft)

    def test_left_right_mirror_preserves_scalar_travel(self):
        left = generate_ground_travel_state(
            trajectory=trajectory(140.0, -25.0, hang=1.5),
            wall_interaction=wall(),
            spray_angle_deg=-25.0,
        )
        right = generate_ground_travel_state(
            trajectory=trajectory(140.0, 25.0, hang=1.5),
            wall_interaction=wall(),
            spray_angle_deg=25.0,
        )
        self.assertEqual(left.valid, right.valid)
        self.assertAlmostEqual(left.ground_travel_distance_ft, right.ground_travel_distance_ft, places=12)
        self.assertAlmostEqual(left.final_radial_distance_ft, right.final_radial_distance_ft, places=12)
        self.assertAlmostEqual(left.final_x_ft, -right.final_x_ft, places=12)
        self.assertAlmostEqual(left.final_y_ft, right.final_y_ft, places=12)

    def test_wall_stop_clamps_exactly_to_wall_radius(self):
        state = generate_ground_travel_state(
            trajectory=trajectory(300.0, 0.0, hang=2.0),
            wall_interaction=wall(330.0),
            spray_angle_deg=0.0,
        )
        self.assertTrue(state.valid)
        self.assertTrue(state.wall_ground_contact)
        self.assertAlmostEqual(state.final_radial_distance_ft, 330.0, places=12)
        self.assertAlmostEqual(state.final_x_ft, 0.0, places=12)
        self.assertAlmostEqual(state.final_y_ft, 330.0, places=12)

    def test_no_wall_contact_when_unconstrained_final_is_inside(self):
        state = generate_ground_travel_state(
            trajectory=trajectory(80.0, 0.0, hang=2.0),
            wall_interaction=wall(500.0),
            spray_angle_deg=0.0,
        )
        self.assertTrue(state.valid)
        self.assertFalse(state.wall_ground_contact)
        self.assertGreaterEqual(state.final_radial_distance_ft, 80.0)
        self.assertLess(state.final_radial_distance_ft, 500.0)

    def test_invalid_and_air_wall_states_fail_safe(self):
        invalid = generate_ground_travel_state(
            trajectory=trajectory(120.0, valid=False),
            wall_interaction=wall(),
            spray_angle_deg=0.0,
        )
        wall_first = generate_ground_travel_state(
            trajectory=trajectory(380.0),
            wall_interaction=wall(350.0, reaches=True),
            spray_angle_deg=0.0,
        )
        for state in (invalid, wall_first):
            self.assertFalse(state.valid)
            self.assertFalse(state.wall_ground_contact)
            self.assertEqual(state.ground_travel_distance_ft, 0.0)
            self.assertTrue(math.isfinite(state.final_radial_distance_ft))

    def test_invalid_deceleration_fails_safe_without_nan(self):
        state = generate_ground_travel_state(
            trajectory=trajectory(100.0),
            wall_interaction=wall(),
            spray_angle_deg=0.0,
            effective_deceleration_ftps2=-1.0,
        )
        self.assertFalse(state.valid)
        self.assertEqual(state.invalid_reason, "invalid_rollout_deceleration")
        self.assertTrue(math.isfinite(state.rollout_distance_ft))

    def test_same_inputs_are_exactly_deterministic(self):
        args = dict(
            trajectory=trajectory(135.0, 18.0, hang=1.4, cls="line_drive"),
            wall_interaction=wall(500.0),
            spray_angle_deg=18.0,
        )
        self.assertEqual(generate_ground_travel_state(**args), generate_ground_travel_state(**args))

    def test_production_bip_attaches_ground_travel_without_parent_rng_use(self):
        for seed in range(1, 250):
            parent = RNG(seed)
            before = parent.get_state()
            state = generate_batted_ball_state(
                hitter_contact=100.0,
                hitter_power=100.0,
                batter_side="R",
                approach="balanced",
                pitch_zone="middle",
                pitch_velocity_quality=0.0,
                pitch_movement_quality=0.0,
                pitch_location_quality=0.0,
                pitch_hittable_quality=0.35,
                parent_rng=parent,
                defender_rating=100.0,
            )
            self.assertEqual(before, parent.get_state())
            self.assertIsNotNone(state.ground_travel)
            self.assertIsNotNone(state.trajectory)
            self.assertIsNotNone(state.wall_interaction)
            return
        self.fail("failed to generate representative state")

    def test_enabled_disabled_ground_shadow_preserves_legacy_outcomes_and_upstream_state(self):
        def run(disabled):
            rng = RNG(20260912)
            results = []
            upstream = []
            context = patch(
                "src.hitting.ground_travel.generate_ground_travel_state",
                return_value=None,
            ) if disabled else None
            if context is not None:
                context.start()
            try:
                for _ in range(2_000):
                    outcome = HittingEngine(
                        HitterSnapshot(100, 100, 100, 100),
                        PitcherSnapshot(),
                        100.0,
                        rng,
                    ).simulate_plate_appearance()
                    results.append(outcome.result)
                    if outcome.batted_ball is not None and len(upstream) < 100:
                        state = outcome.batted_ball.physical_state
                        upstream.append((
                            state.exit_velocity,
                            state.launch_angle,
                            state.timing,
                            state.spray_angle,
                            state.is_fair,
                            state.contact_quality,
                            state.trajectory,
                            state.wall_interaction,
                            state.defensive_opportunity,
                            state.defensive_resolution,
                        ))
            finally:
                if context is not None:
                    context.stop()
            return results, upstream, rng.get_state()

        enabled_results, enabled_upstream, enabled_rng = run(False)
        disabled_results, disabled_upstream, disabled_rng = run(True)
        self.assertEqual(enabled_results, disabled_results)
        self.assertEqual(enabled_rng, disabled_rng)
        self.assertEqual(enabled_upstream, disabled_upstream)

    def test_fixed_cost_50k_ground_states(self):
        tr = trajectory(120.0, 8.0, hang=1.25)
        wc = wall(500.0)
        started = time.perf_counter()
        for _ in range(50_000):
            state = generate_ground_travel_state(
                trajectory=tr,
                wall_interaction=wc,
                spray_angle_deg=8.0,
            )
            self.assertTrue(state.valid)
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 5.0)


if __name__ == "__main__":
    unittest.main()
