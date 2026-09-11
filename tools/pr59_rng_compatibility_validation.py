#!/usr/bin/env python3
from __future__ import annotations

import json
import random

from src.hitting.physical import generate_batted_ball_state
from src.rng import RNG

KW = dict(
    hitter_contact=100.0,
    hitter_power=100.0,
    batter_side="R",
    approach="balanced",
    pitch_zone="middle",
    pitch_velocity_quality=0.15,
    pitch_movement_quality=0.05,
    pitch_location_quality=0.10,
    pitch_hittable_quality=0.35,
)


def gen(parent):
    return generate_batted_ball_state(parent_rng=parent, **KW)


def project_rng_probe():
    parent = RNG(20260912)
    control = RNG(20260912)
    before = parent.get_state()
    first = gen(parent)
    after_first = parent.get_state()
    second = gen(parent)
    after_second = parent.get_state()
    draws_parent = [parent.random() for _ in range(8)]
    draws_control = [control.random() for _ in range(8)]
    return {
        "state_unchanged_after_first": before == after_first,
        "state_unchanged_after_second": before == after_second,
        "same_parent_state_same_physical_state": first == second,
        "next_draws_match_control": draws_parent == draws_control,
        "first_state": repr(first),
    }


def stdlib_probe():
    parent = random.Random(20260912)
    control = random.Random(20260912)
    before = parent.getstate()
    first = gen(parent)
    after_first = parent.getstate()
    second = gen(parent)
    after_second = parent.getstate()
    draws_parent = [parent.random() for _ in range(8)]
    draws_control = [control.random() for _ in range(8)]
    return {
        "state_unchanged_after_first": before == after_first,
        "state_unchanged_after_second": before == after_second,
        "same_parent_state_same_physical_state": first == second,
        "next_draws_match_control": draws_parent == draws_control,
        "first_state": repr(first),
    }


class UnsupportedRNG:
    def __init__(self):
        self.draw_calls = 0

    def random(self):
        self.draw_calls += 1
        return 0.5

    def gauss(self, mu, sigma):
        self.draw_calls += 1
        return mu


def unsupported_probe():
    parent = UnsupportedRNG()
    error_type = None
    error_message = None
    try:
        gen(parent)
    except Exception as exc:  # validation deliberately records exact public behavior
        error_type = type(exc).__name__
        error_message = str(exc)
    return {
        "error_type": error_type,
        "error_message": error_message,
        "draw_calls": parent.draw_calls,
        "predictable_type_error": error_type == "TypeError",
        "hidden_parent_consumption": parent.draw_calls != 0,
    }


def main():
    result = {
        "project_rng": project_rng_probe(),
        "stdlib_random": stdlib_probe(),
        "unsupported_rng": unsupported_probe(),
    }
    result["pass"] = all([
        result["project_rng"]["state_unchanged_after_first"],
        result["project_rng"]["state_unchanged_after_second"],
        result["project_rng"]["same_parent_state_same_physical_state"],
        result["project_rng"]["next_draws_match_control"],
        result["stdlib_random"]["state_unchanged_after_first"],
        result["stdlib_random"]["state_unchanged_after_second"],
        result["stdlib_random"]["same_parent_state_same_physical_state"],
        result["stdlib_random"]["next_draws_match_control"],
        result["unsupported_rng"]["predictable_type_error"],
        not result["unsupported_rng"]["hidden_parent_consumption"],
    ])
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
