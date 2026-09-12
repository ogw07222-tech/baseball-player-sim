import math
import time
import unittest
from dataclasses import replace
from unittest.mock import patch

from src.hitting.ground_travel import GroundTravelState
from src.hitting import ground_travel_parameters as GP
from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.physical_defense import DefensiveOpportunity, DefensiveResolution
from src.hitting.retrieval import (
    PhysicalHitResolution,
    build_retrieval_state,
    owner_for_location,
    resolve_physical_hit_shadow,
    runner_arrival_times,
    throw_timing_to_base,
)
from src.hitting import retrieval_parameters as P
from src.rng import RNG


def coord(radius_ft: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return radius_ft * math.sin(angle), radius_ft * math.cos(angle)


def ground_at(x: float, y: float, *, valid: bool = True, wall: bool = False) -> GroundTravelState:
    radial = math.hypot(x, y)
    return GroundTravelState(
        valid=valid,
        surface_class=GP.SURFACE_CLASS_NEUTRAL,
        impact_horizontal_speed_fps=70.0 if valid else 0.0,
        post_impact_horizontal_speed_fps=35.0 if valid else 0.0,
        bounce_distance_ft=8.0 if valid else 0.0,
        rollout_start_speed_fps=24.0 if valid else 0.0,
        rollout_distance_ft=12.0 if valid else 0.0,
        ground_travel_distance_ft=20.0 if valid else 0.0,
        first_impact_x_ft=x,
        first_impact_y_ft=y,
        final_x_ft=x,
        final_y_ft=y,
        final_radial_distance_ft=radial,
        wall_ground_contact=wall,
        ground_model_version=GP.GROUND_MODEL_VERSION,
        invalid_reason=None if valid else "test_invalid",
    )


def caught_resolution() -> DefensiveResolution:
    opportunity = DefensiveOpportunity(
        valid=True,
        defender_position="CF",
        opportunity_type="airborne",
        catch_x_ft=0.0,
        catch_y_ft=300.0,
        nominal_start_x_ft=0.0,
        nominal_start_y_ft=315.0,
        required_distance_ft=15.0,
        opportunity_time_s=4.0,
        direction_class="in",
        near_wall=False,
        baseline_catch_probability=0.9,
        defender_rating=100.0,
        adjusted_catch_probability=0.9,
    )
    return DefensiveResolution(
        valid=True,
        opportunity=opportunity,
        catch_probability=0.9,
        roll=0.1,
        physical_out_shadow=True,
    )


class Phase2EBRetrievalHitShadowTests(unittest.TestCase):
    def test_ownership_sectors_cover_expected_roles(self):
        cases = [
            ((0.0, 10.0), "C"),
            ((0.0, 60.5), "P"),
            (coord(120.0, -38.0), "3B"),
            (coord(145.0, -12.0), "SS"),
            (coord(145.0, 12.0), "2B"),
            (coord(120.0, 38.0), "1B"),
            (coord(280.0, -27.0), "LF"),
            ((0.0, 300.0), "CF"),
            (coord(280.0, 27.0), "RF"),
        ]
        for location, expected in cases:
            self.assertEqual(owner_for_location(*location)[0], expected)

    def test_left_right_mirror_preserves_retrieval_timing(self):
        x, y = coord(300.0, 27.0)
        left = build_retrieval_state(ground_travel=ground_at(-x, y), defender_rating=100.0)
        right = build_retrieval_state(ground_travel=ground_at(x, y), defender_rating=100.0)
        self.assertEqual(left.defender_position, "LF")
        self.assertEqual(right.defender_position, "RF")
        self.assertAlmostEqual(left.retrieval_distance_ft, right.retrieval_distance_ft, places=9)
        self.assertAlmostEqual(left.total_retrieval_time_s, right.total_retrieval_time_s, places=12)

    def test_farther_ball_same_owner_does_not_reduce_retrieval_time(self):
        near = build_retrieval_state(ground_travel=ground_at(0.0, 330.0), defender_rating=100.0)
        far = build_retrieval_state(ground_travel=ground_at(0.0, 390.0), defender_rating=100.0)
        self.assertEqual(near.defender_position, "CF")
        self.assertEqual(far.defender_position, "CF")
        self.assertLess(near.retrieval_distance_ft, far.retrieval_distance_ft)
        self.assertLessEqual(near.total_retrieval_time_s, far.total_retrieval_time_s)

    def test_higher_defense_rating_reduces_or_preserves_retrieval_time(self):
        ball = ground_at(0.0, 380.0)
        low = build_retrieval_state(ground_travel=ball, defender_rating=80.0)
        high = build_retrieval_state(ground_travel=ball, defender_rating=120.0)
        self.assertGreaterEqual(low.reaction_time_s, high.reaction_time_s)
        self.assertLessEqual(low.effective_fielder_speed_fps, high.effective_fielder_speed_fps)
        self.assertGreaterEqual(low.total_retrieval_time_s, high.total_retrieval_time_s)

    def test_extreme_defense_ratings_stay_bounded(self):
        ball = ground_at(0.0, 360.0)
        for rating in (-1_000_000.0, 1_000_000.0):
            state = build_retrieval_state(ground_travel=ball, defender_rating=rating)
            self.assertTrue(state.valid)
            self.assertGreaterEqual(state.reaction_time_s, P.REACTION_MIN_S)
            self.assertLessEqual(state.reaction_time_s, P.REACTION_MAX_S)
            self.assertGreaterEqual(state.effective_fielder_speed_fps, P.FIELDER_SPEED_MIN_FPS)
            self.assertLessEqual(state.effective_fielder_speed_fps, P.FIELDER_SPEED_MAX_FPS)

    def test_throw_distance_and_relay_contract(self):
        retrieval = build_retrieval_state(ground_travel=ground_at(0.0, 300.0), defender_rating=100.0)
        near_throw = throw_timing_to_base(replace(retrieval, ball_x_ft=60.0, ball_y_ft=70.0), "1B")
        far_throw = throw_timing_to_base(replace(retrieval, ball_x_ft=0.0, ball_y_ft=360.0), "1B")
        self.assertLess(near_throw.throw_distance_ft, far_throw.throw_distance_ft)
        self.assertLessEqual(near_throw.total_throw_time_s, far_throw.total_throw_time_s)
        self.assertEqual(near_throw.relay_penalty_s, 0.0)
        self.assertEqual(far_throw.relay_penalty_s, P.RELAY_PENALTY_S)

    def test_runner_speed_monotonicity(self):
        slow = runner_arrival_times(80.0)
        neutral = runner_arrival_times(100.0)
        fast = runner_arrival_times(120.0)
        for index in range(3):
            self.assertGreaterEqual(slow[index], neutral[index])
            self.assertGreaterEqual(neutral[index], fast[index])

    def test_phase2d_catch_short_circuits_to_out_without_retrieval(self):
        result = resolve_physical_hit_shadow(
            ground_travel=ground_at(0.0, 300.0),
            defensive_resolution=caught_resolution(),
            defender_rating=100.0,
            runner_speed_rating=100.0,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_result_shadow, "OUT")
        self.assertFalse(result.retrieval.valid)
        self.assertEqual(result.retrieval.invalid_reason, "air_caught")
        self.assertIsNone(result.defense_1b)

    def test_controlled_routine_grounder_resolves_out(self):
        x, y = coord(105.0, 32.0)
        result = resolve_physical_hit_shadow(
            ground_travel=ground_at(x, y), defensive_resolution=None,
            defender_rating=100.0, runner_speed_rating=100.0,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_result_shadow, "OUT")
        self.assertLessEqual(result.defense_1b.defense_arrival_time_s, result.runner_time_1b_s)

    def test_controlled_remote_ball_can_resolve_single(self):
        result = resolve_physical_hit_shadow(
            ground_travel=ground_at(0.0, 210.0), defensive_resolution=None,
            defender_rating=100.0, runner_speed_rating=100.0,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_result_shadow, "1B")
        self.assertGreater(result.margin_1b_s, 0.0)
        self.assertLessEqual(result.margin_2b_s, 0.0)

    def test_controlled_deep_gap_can_resolve_double(self):
        result = resolve_physical_hit_shadow(
            ground_travel=ground_at(200.0, 350.0, wall=True), defensive_resolution=None,
            defender_rating=100.0, runner_speed_rating=100.0,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_result_shadow, "2B")
        self.assertGreater(result.margin_2b_s, 0.0)
        self.assertLessEqual(result.margin_3b_s, 0.0)

    def test_controlled_extreme_deep_ball_can_resolve_triple(self):
        result = resolve_physical_hit_shadow(
            ground_travel=ground_at(-280.0, 280.0, wall=True), defensive_resolution=None,
            defender_rating=100.0, runner_speed_rating=100.0,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.physical_result_shadow, "3B")
        self.assertGreater(result.margin_3b_s, 0.0)

    def test_phase2e_b_never_creates_home_run(self):
        locations = [(0.0, 100.0), (0.0, 210.0), (200.0, 350.0), (-280.0, 280.0)]
        for x, y in locations:
            result = resolve_physical_hit_shadow(
                ground_travel=ground_at(x, y), defensive_resolution=None,
                defender_rating=100.0, runner_speed_rating=120.0,
            )
            self.assertNotEqual(result.physical_result_shadow, "HR")
            self.assertIn(result.physical_result_shadow, {"OUT", "1B", "2B", "3B"})

    def test_invalid_ground_state_fails_safe(self):
        result = resolve_physical_hit_shadow(
            ground_travel=ground_at(0.0, 0.0, valid=False), defensive_resolution=None,
            defender_rating=100.0, runner_speed_rating=100.0,
        )
        self.assertFalse(result.valid)
        self.assertIsNone(result.physical_result_shadow)
        self.assertFalse(result.retrieval.valid)
        self.assertTrue(math.isfinite(result.margin_1b_s))

    def test_same_inputs_are_exactly_deterministic(self):
        kwargs = dict(
            ground_travel=ground_at(160.0, 300.0), defensive_resolution=None,
            defender_rating=112.0, runner_speed_rating=118.0,
        )
        self.assertEqual(resolve_physical_hit_shadow(**kwargs), resolve_physical_hit_shadow(**kwargs))

    def test_production_wires_existing_hitter_speed_and_defense(self):
        for seed in range(1, 300):
            outcome = HittingEngine(
                HitterSnapshot(100.0, 100.0, 100.0, 123.0),
                PitcherSnapshot(), 114.0, RNG(seed),
            ).simulate_plate_appearance()
            if outcome.batted_ball is None:
                continue
            state = outcome.batted_ball.physical_state
            self.assertIsNotNone(state)
            self.assertIsNotNone(state.physical_hit_resolution)
            physical = state.physical_hit_resolution
            if physical.retrieval.invalid_reason != "air_caught":
                self.assertEqual(physical.retrieval.defender_rating, 114.0)
            if physical.valid and physical.physical_result_shadow != "OUT":
                expected = runner_arrival_times(123.0)
                self.assertEqual(
                    (physical.runner_time_1b_s, physical.runner_time_2b_s, physical.runner_time_3b_s),
                    expected,
                )
            return
        self.fail("representative seeds produced no batted ball")

    def test_shadow_enabled_disabled_preserves_legacy_rng_and_upstream_metadata(self):
        def disabled_shadow(*, ground_travel, defensive_resolution, defender_rating, runner_speed_rating):
            from src.hitting.retrieval import _invalid_resolution
            return _invalid_resolution("disabled_for_regression_test")

        def run(disabled: bool):
            rng = RNG(20260912)
            results = []
            upstream = []
            context = patch("src.hitting.retrieval.resolve_physical_hit_shadow", side_effect=disabled_shadow) if disabled else None
            if context is not None:
                context.start()
            try:
                for _ in range(2_000):
                    outcome = HittingEngine(
                        HitterSnapshot(100.0, 100.0, 100.0, 112.0),
                        PitcherSnapshot(), 107.0, rng,
                    ).simulate_plate_appearance()
                    results.append(outcome.result)
                    if outcome.batted_ball is not None:
                        state = outcome.batted_ball.physical_state
                        upstream.append((
                            state.exit_velocity, state.launch_angle, state.timing, state.spray_angle,
                            state.is_fair, state.contact_quality,
                            state.trajectory, state.wall_interaction,
                            state.defensive_opportunity, state.defensive_resolution,
                            state.ground_travel,
                        ))
            finally:
                if context is not None:
                    context.stop()
            return results, upstream, rng.get_state()

        enabled_results, enabled_upstream, enabled_rng = run(False)
        disabled_results, disabled_upstream, disabled_rng = run(True)
        self.assertEqual(enabled_results, disabled_results)
        self.assertEqual(enabled_upstream, disabled_upstream)
        self.assertEqual(enabled_rng, disabled_rng)

    def test_fixed_cost_50k_resolution_guard(self):
        ground = ground_at(180.0, 300.0)
        started = time.perf_counter()
        for _ in range(50_000):
            resolve_physical_hit_shadow(
                ground_travel=ground,
                defensive_resolution=None,
                defender_rating=100.0,
                runner_speed_rating=100.0,
            )
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 5.0)

    def test_distribution_smoke_does_not_collapse_owner_or_result(self):
        owners = set()
        results = set()
        for seed in range(1, 2_500):
            outcome = HittingEngine(
                HitterSnapshot(100.0, 100.0, 100.0, 100.0),
                PitcherSnapshot(), 100.0, RNG(seed),
            ).simulate_plate_appearance()
            if outcome.batted_ball is None:
                continue
            physical = outcome.batted_ball.physical_state.physical_hit_resolution
            if physical is None or not physical.valid:
                continue
            if physical.retrieval.defender_position is not None:
                owners.add(physical.retrieval.defender_position)
            if physical.physical_result_shadow is not None:
                results.add(physical.physical_result_shadow)
        self.assertGreaterEqual(len(owners), 3)
        self.assertIn("OUT", results)
        self.assertTrue(results.intersection({"1B", "2B", "3B"}))
        self.assertNotIn("HR", results)


if __name__ == "__main__":
    unittest.main()
