# Merge recommendation

- `PHYSICAL_VELOCITY_SAFETY_READY`: **READY**. Promote `src/pitching/physical_velocity.py` after Velocity Scale v2 is merged.
- `PITCHER_JOINT_CALIBRATION_V2_READY`: **NOT_READY**. Do not promote searched Stuff/Control/Breaking coefficients.

Reason for joint failure: current prime raw pitcher center is ~95.5 rather than the requested ~110, while forcing Velocity itself to 110 would break its frozen physical KBO distribution. Recenter/define the S/C/B raw-scale contract first, then rerun the same frozen KBO objective.
