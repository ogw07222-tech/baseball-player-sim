import unittest

from src.hitting.stadium import QUALITY_APPROXIMATED, StadiumGeometry, resolve_wall_interaction
from src.hitting.trajectory import BattedBallTrajectory


def trajectory(*, valid: bool) -> BattedBallTrajectory:
    return BattedBallTrajectory(
        horizontal_distance_ft=430.0,
        hang_time_s=5.0,
        apex_height_ft=110.0,
        landing_x_ft=0.0,
        landing_y_ft=430.0,
        trajectory_class="fly_ball",
        apex_distance_fraction=0.5,
        valid=valid,
    )


def short_wall() -> StadiumGeometry:
    return StadiumGeometry(
        stadium_id="invalid_guard_probe",
        season=None,
        is_real_stadium=False,
        source_quality=QUALITY_APPROXIMATED,
        wall_radius_ft=(350.0,) * 5,
        wall_height_ft=(8.0,) * 5,
    )


class Phase2CInvalidTrajectoryGuardTests(unittest.TestCase):
    def test_invalid_high_carry_trajectory_cannot_produce_physical_hr(self):
        interaction = resolve_wall_interaction(
            trajectory=trajectory(valid=False),
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=short_wall(),
        )
        self.assertFalse(interaction.physical_hr_shadow)
        self.assertFalse(interaction.reaches_wall)
        self.assertFalse(interaction.clears_wall)
        self.assertFalse(interaction.wall_contact)
        self.assertEqual(interaction.ball_height_at_wall_ft, 0.0)
        self.assertEqual(interaction.clearance_ft, -8.0)

    def test_valid_identical_geometry_preserves_existing_wall_clear(self):
        interaction = resolve_wall_interaction(
            trajectory=trajectory(valid=True),
            spray_angle_deg=0.0,
            is_fair_shadow=True,
            stadium=short_wall(),
        )
        self.assertTrue(interaction.reaches_wall)
        self.assertTrue(interaction.clears_wall)
        self.assertTrue(interaction.physical_hr_shadow)


if __name__ == "__main__":
    unittest.main()
