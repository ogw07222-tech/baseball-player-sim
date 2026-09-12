import math
import unittest
from unittest.mock import patch

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical import generate_batted_ball_state
from src.hitting.physical_defense import (
    DefensiveResolution,
    build_defensive_opportunity,
    resolve_defensive_shadow,
)
from src.hitting.stadium import WallInteraction
from src.hitting.trajectory import BattedBallTrajectory
from src.rng import RNG


def trajectory_at(x, y, *, time_s=4.0, trajectory_class="fly_ball", valid=True):
    distance = math.hypot(x, y)
    return BattedBallTrajectory(
        horizontal_distance_ft=distance,
        hang_time_s=time_s,
        apex_height_ft=100.0,
        landing_x_ft=x,
        landing_y_ft=y,
        trajectory_class=trajectory_class,
        apex_distance_fraction=0.5,
        valid=valid,
    )


def wall_context(radius_ft, *, reaches=False, clears=False, physical_hr=False):
    height = 10.0
    ball_height = 20.0 if reaches else 0.0
    clearance = ball_height - height if reaches else -height
    return WallInteraction(
        stadium_id="test",
        wall_radius_ft=radius_ft,
        wall_height_ft=height,
        reaches_wall=reaches,
        ball_height_at_wall_ft=ball_height,
        clearance_ft=clearance,
        clears_wall=clears,
        wall_contact=False,
        physical_hr_shadow=physical_hr,
    )


def opportunity(x, y, *, time_s=4.0, rating=100.0, wall_radius=500.0):
    return build_defensive_opportunity(
        trajectory=trajectory_at(x, y, time_s=time_s),
        wall_interaction=wall_context(wall_radius),
        defender_rating=rating,
        is_fair_shadow=True,
    )


class Phase2DDefensiveShadowTests(unittest.TestCase):
    def test_probability_is_finite_and_bounded(self):
        for rating in (40.0, 80.0, 100.0, 120.0, 180.0):
            op = opportunity(0.0, 355.0, rating=rating)
            self.assertTrue(op.valid)
            self.assertTrue(math.isfinite(op.baseline_catch_probability))
            self.assertTrue(math.isfinite(op.adjusted_catch_probability))
            self.assertGreaterEqual(op.adjusted_catch_probability, 0.0)
            self.assertLessEqual(op.adjusted_catch_probability, 1.0)

    def test_more_required_distance_cannot_raise_probability(self):
        near = opportunity(0.0, 345.0, time_s=4.0)
        far = opportunity(0.0, 375.0, time_s=4.0)
        self.assertEqual(near.defender_position, "CF")
        self.assertEqual(far.defender_position, "CF")
        self.assertLess(near.required_distance_ft, far.required_distance_ft)
        self.assertGreaterEqual(near.adjusted_catch_probability, far.adjusted_catch_probability)

    def test_more_opportunity_time_cannot_lower_probability(self):
        short = opportunity(0.0, 365.0, time_s=2.0)
        long = opportunity(0.0, 365.0, time_s=5.0)
        self.assertGreaterEqual(long.adjusted_catch_probability, short.adjusted_catch_probability)

    def test_higher_defense_rating_cannot_lower_probability(self):
        low = opportunity(0.0, 365.0, rating=80.0)
        average = opportunity(0.0, 365.0, rating=100.0)
        high = opportunity(0.0, 365.0, rating=120.0)
        self.assertLessEqual(low.adjusted_catch_probability, average.adjusted_catch_probability)
        self.assertLessEqual(average.adjusted_catch_probability, high.adjusted_catch_probability)

    def test_direction_ordering_back_lateral_in(self):
        inward = opportunity(0.0, 265.0, time_s=3.5)
        lateral = opportunity(50.0, 315.0, time_s=3.5)
        back = opportunity(0.0, 365.0, time_s=3.5)
        self.assertAlmostEqual(inward.required_distance_ft, 50.0, places=6)
        self.assertAlmostEqual(lateral.required_distance_ft, 50.0, places=6)
        self.assertAlmostEqual(back.required_distance_ft, 50.0, places=6)
        self.assertEqual(inward.direction_class, "in")
        self.assertEqual(lateral.direction_class, "lateral")
        self.assertEqual(back.direction_class, "back")
        self.assertLessEqual(back.adjusted_catch_probability, lateral.adjusted_catch_probability)
        self.assertLessEqual(lateral.adjusted_catch_probability, inward.adjusted_catch_probability)

    def test_near_wall_cannot_make_equivalent_opportunity_easier(self):
        trajectory = trajectory_at(0.0, 340.0, time_s=4.0)
        far_wall = build_defensive_opportunity(
            trajectory=trajectory,
            wall_interaction=wall_context(500.0),
            defender_rating=100.0,
            is_fair_shadow=True,
        )
        near_wall = build_defensive_opportunity(
            trajectory=trajectory,
            wall_interaction=wall_context(350.0),
            defender_rating=100.0,
            is_fair_shadow=True,
        )
        self.assertFalse(far_wall.near_wall)
        self.assertTrue(near_wall.near_wall)
        self.assertLessEqual(
            near_wall.adjusted_catch_probability,
            far_wall.adjusted_catch_probability,
        )

    def test_left_right_mirror_preserves_difficulty_and_ownership(self):
        radius = 300.0
        angle = math.radians(25.0)
        x = radius * math.sin(angle)
        y = radius * math.cos(angle)
        left = opportunity(-x, y, time_s=4.0)
        right = opportunity(x, y, time_s=4.0)
        self.assertEqual(left.defender_position, "LF")
        self.assertEqual(right.defender_position, "RF")
        self.assertAlmostEqual(left.required_distance_ft, right.required_distance_ft, places=9)
        self.assertEqual(left.direction_class, right.direction_class)
        self.assertAlmostEqual(
            left.adjusted_catch_probability,
            right.adjusted_catch_probability,
            places=12,
        )

    def test_invalid_trajectory_cannot_create_physical_out(self):
        op = build_defensive_opportunity(
            trajectory=trajectory_at(0.0, 350.0, valid=False),
            wall_interaction=wall_context(500.0),
            defender_rating=140.0,
            is_fair_shadow=True,
        )
        result = resolve_defensive_shadow(op, roll=0.0)
        self.assertFalse(op.valid)
        self.assertEqual(op.opportunity_type, "invalid_trajectory")
        self.assertFalse(result.valid)
        self.assertFalse(result.physical_out_shadow)
        self.assertEqual(result.catch_probability, 0.0)
        self.assertIsNone(result.roll)

    def test_ground_like_is_explicitly_not_modeled_v1(self):
        op = build_defensive_opportunity(
            trajectory=trajectory_at(0.0, 120.0, trajectory_class="ground_like"),
            wall_interaction=wall_context(500.0),
            defender_rating=100.0,
            is_fair_shadow=True,
        )
        self.assertFalse(op.valid)
        self.assertEqual(op.opportunity_type, "ground_not_modeled_v1")

    def test_wall_intersection_and_over_wall_are_fail_safe_not_catches(self):
        trajectory = trajectory_at(0.0, 380.0)
        wall_hit = build_defensive_opportunity(
            trajectory=trajectory,
            wall_interaction=wall_context(350.0, reaches=True),
            defender_rating=100.0,
            is_fair_shadow=True,
        )
        over_wall = build_defensive_opportunity(
            trajectory=trajectory,
            wall_interaction=wall_context(350.0, reaches=True, clears=True, physical_hr=True),
            defender_rating=100.0,
            is_fair_shadow=True,
        )
        self.assertFalse(wall_hit.valid)
        self.assertEqual(wall_hit.opportunity_type, "wall_intersection_unmodeled_v1")
        self.assertFalse(over_wall.valid)
        self.assertEqual(over_wall.opportunity_type, "over_wall")

    def test_same_seed_and_state_replay_exactly_and_parent_rng_is_pure(self):
        def run():
            parent = RNG(20260912)
            before = parent.get_state()
            state = generate_batted_ball_state(
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
                defender_rating=112.0,
            )
            return state, before, parent.get_state()

        first, first_before, first_after = run()
        second, second_before, second_after = run()
        self.assertEqual(first_before, first_after)
        self.assertEqual(second_before, second_after)
        self.assertEqual(first, second)
        self.assertEqual(first.defensive_opportunity, second.defensive_opportunity)
        self.assertEqual(first.defensive_resolution, second.defensive_resolution)

    def test_production_engine_passes_existing_defense_scalar_into_shadow(self):
        for seed in range(1, 250):
            outcome = HittingEngine(
                HitterSnapshot(100, 100, 100, 100),
                PitcherSnapshot(),
                117.0,
                RNG(seed),
            ).simulate_plate_appearance()
            if outcome.batted_ball is not None:
                state = outcome.batted_ball.physical_state
                self.assertIsNotNone(state)
                self.assertIsNotNone(state.defensive_opportunity)
                self.assertEqual(state.defensive_opportunity.defender_rating, 117.0)
                return
        self.fail("representative seeds produced no batted ball")

    def test_shadow_resolution_cannot_change_legacy_outcome_or_rng_sequence(self):
        def disabled_resolution(opportunity, *, roll):
            return DefensiveResolution(
                valid=False,
                opportunity=opportunity,
                catch_probability=0.0,
                roll=None,
                physical_out_shadow=False,
            )

        def run(disabled):
            rng = RNG(20260912)
            outcomes = []
            context = patch(
                "src.hitting.physical_defense.resolve_defensive_shadow",
                side_effect=disabled_resolution,
            ) if disabled else None
            if context is not None:
                context.start()
            try:
                for _ in range(2_000):
                    outcomes.append(
                        HittingEngine(
                            HitterSnapshot(100, 100, 100, 100),
                            PitcherSnapshot(),
                            100.0,
                            rng,
                        ).simulate_plate_appearance().result
                    )
            finally:
                if context is not None:
                    context.stop()
            return outcomes, rng.get_state()

        enabled_results, enabled_rng = run(False)
        disabled_results, disabled_rng = run(True)
        self.assertEqual(enabled_results, disabled_results)
        self.assertEqual(enabled_rng, disabled_rng)


if __name__ == "__main__":
    unittest.main()
