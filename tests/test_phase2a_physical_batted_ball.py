import math
import random
import statistics
import time
import unittest

from src.hitting.model import HitterSnapshot, HittingEngine, Pitch, PitcherSnapshot
from src.hitting.physical import (
    BattedBallState,
    generate_batted_ball_state,
    is_fair_spray,
)
from src.rng import RNG


def physical_state(
    seed: int,
    *,
    contact: float = 100.0,
    power: float = 100.0,
    side: str = "R",
    approach: str = "balanced",
    zone: str = "middle",
):
    return generate_batted_ball_state(
        hitter_contact=contact,
        hitter_power=power,
        batter_side=side,
        approach=approach,
        pitch_zone=zone,
        pitch_velocity_quality=0.0,
        pitch_movement_quality=0.0,
        pitch_location_quality=0.0,
        pitch_hittable_quality=0.35,
        parent_rng=RNG(seed),
    )


class ForcedBIP(HittingEngine):
    def _pitch(self):
        return Pitch(True, "middle", "fastball", 0.0, 0.0, 0.0, 0.35)

    def _hit_by_pitch_probability(self, pitch):
        return 0.0

    def _swing_probability(self, pitch, balls, strikes):
        return 1.0

    def _contact_resolution(self, pitch, strikes, protective_swing=False):
        return "bip", 0.0, 0.0


class Phase2APhysicalBattedBallTests(unittest.TestCase):
    def test_schema_units_and_ranges_are_sane(self):
        state = physical_state(1)
        self.assertIsInstance(state, BattedBallState)
        self.assertTrue(math.isfinite(state.exit_velocity))
        self.assertGreaterEqual(state.exit_velocity, 30.0)
        self.assertLessEqual(state.exit_velocity, 125.0)
        self.assertGreaterEqual(state.launch_angle, -65.0)
        self.assertLessEqual(state.launch_angle, 85.0)
        self.assertGreaterEqual(state.timing, -1.0)
        self.assertLessEqual(state.timing, 1.0)
        self.assertGreaterEqual(state.spray_angle, -75.0)
        self.assertLessEqual(state.spray_angle, 75.0)
        self.assertGreaterEqual(state.contact_quality, 0.0)
        self.assertLessEqual(state.contact_quality, 1.0)

    def test_generation_does_not_consume_parent_rng(self):
        parent = RNG(20260912)
        before = parent.get_state()
        generate_batted_ball_state(
            hitter_contact=100,
            hitter_power=100,
            batter_side="R",
            approach="balanced",
            pitch_zone="middle",
            pitch_velocity_quality=0.1,
            pitch_movement_quality=0.1,
            pitch_location_quality=0.1,
            pitch_hittable_quality=0.3,
            parent_rng=parent,
        )
        self.assertEqual(before, parent.get_state())

    def test_stdlib_random_parent_is_supported_without_consumption(self):
        parent = random.Random(20260912)
        before = parent.getstate()
        kwargs = dict(
            hitter_contact=100,
            hitter_power=100,
            batter_side="R",
            approach="balanced",
            pitch_zone="middle",
            pitch_velocity_quality=0.1,
            pitch_movement_quality=0.1,
            pitch_location_quality=0.1,
            pitch_hittable_quality=0.3,
            parent_rng=parent,
        )
        first = generate_batted_ball_state(**kwargs)
        second = generate_batted_ball_state(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(before, parent.getstate())

    def test_same_parent_state_replays_exactly(self):
        self.assertEqual(physical_state(77), physical_state(77))

    def test_power_improves_exit_velocity_upper_distribution(self):
        low = sorted(physical_state(seed, power=70).exit_velocity for seed in range(1200))
        high = sorted(physical_state(seed, power=140).exit_velocity for seed in range(1200))
        p90 = int(len(low) * 0.90)
        self.assertGreater(high[p90], low[p90] + 4.0)
        self.assertGreater(statistics.mean(high), statistics.mean(low) + 4.0)

    def test_launch_angle_is_continuous_and_does_not_collapse_to_categories(self):
        values = [physical_state(seed).launch_angle for seed in range(600)]
        rounded = {round(value, 3) for value in values}
        self.assertGreater(len(rounded), 500)
        self.assertLess(min(values), 0.0)
        self.assertGreater(max(values), 30.0)

    def test_timing_produces_early_and_late_contact(self):
        values = [physical_state(seed).timing for seed in range(800)]
        self.assertTrue(any(value < -0.25 for value in values))
        self.assertTrue(any(value > 0.25 for value in values))

    def test_spray_uses_both_field_sides(self):
        values = [physical_state(seed).spray_angle for seed in range(800)]
        self.assertTrue(any(value < -10.0 for value in values))
        self.assertTrue(any(value > 10.0 for value in values))

    def test_handedness_is_exact_mirror_for_same_contact_state(self):
        for seed in range(50):
            right = physical_state(seed, side="R")
            left = physical_state(seed, side="L")
            self.assertAlmostEqual(right.exit_velocity, left.exit_velocity, places=12)
            self.assertAlmostEqual(right.launch_angle, left.launch_angle, places=12)
            self.assertAlmostEqual(right.timing, left.timing, places=12)
            self.assertAlmostEqual(right.spray_angle, -left.spray_angle, places=12)

    def test_inside_outside_directional_tendency_for_right_hitter(self):
        inside = [physical_state(seed, side="R", zone="inside").spray_angle for seed in range(1200)]
        outside = [physical_state(seed, side="R", zone="outside").spray_angle for seed in range(1200)]
        self.assertLess(statistics.mean(inside), statistics.mean(outside) - 12.0)

    def test_early_late_timing_changes_spray_tendency(self):
        pairs = [(physical_state(seed).timing, physical_state(seed).spray_angle) for seed in range(2000)]
        early = [spray for timing, spray in pairs if timing > 0.30]
        late = [spray for timing, spray in pairs if timing < -0.30]
        self.assertGreater(len(early), 100)
        self.assertGreater(len(late), 100)
        # Right-handed hitter: early contact tends negative (pull/left field).
        self.assertLess(statistics.mean(early), statistics.mean(late) - 15.0)

    def test_fair_foul_boundary_is_explicit_and_deterministic(self):
        self.assertTrue(is_fair_spray(0.0))
        self.assertTrue(is_fair_spray(-45.0))
        self.assertTrue(is_fair_spray(45.0))
        self.assertFalse(is_fair_spray(-45.001))
        self.assertFalse(is_fair_spray(45.001))

    def test_generated_states_include_strong_fouls(self):
        states = [physical_state(seed, power=140) for seed in range(5000)]
        strong_fouls = [state for state in states if not state.is_fair and state.exit_velocity >= 95.0]
        self.assertGreater(len(strong_fouls), 0)

    def test_production_bip_path_attaches_physical_state(self):
        engine = ForcedBIP(
            HitterSnapshot(100, 100, 100, 100),
            PitcherSnapshot(),
            100.0,
            RNG(12345),
        )
        outcome = engine.simulate_plate_appearance()
        self.assertIsNotNone(outcome.batted_ball)
        self.assertIsNotNone(outcome.batted_ball.physical_state)
        self.assertIsInstance(outcome.batted_ball.physical_state, BattedBallState)

    def test_phase2a_generator_is_constant_time_representative(self):
        start = time.perf_counter()
        for seed in range(20_000):
            physical_state(seed)
        elapsed = time.perf_counter() - start
        # Deliberately loose CI guardrail: catches accidental frame loops/integration.
        self.assertLess(elapsed, 12.0, elapsed)


if __name__ == "__main__":
    unittest.main()
