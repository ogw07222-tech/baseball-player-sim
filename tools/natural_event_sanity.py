"""Deterministic 100k+ event sanity runner for natural baseball events."""
from __future__ import annotations

from collections import Counter
import json

from src.inning import PersistentInningEngine
from src.player import Player
from src.rng import RNG
from src.simulation import PitcherProfile
from src.stats import PlayerStats


def _player(name: str) -> Player:
    return Player(
        name,
        24,
        PlayerStats(
            contact=100, power=100, discipline=100, speed=100, defense=100,
            throwing=100, stamina=100, durability=100, mentality=100, talent=100,
        ),
        position="SS",
    )


def _lineup(prefix: str) -> list[Player]:
    return [_player(f"{prefix}{index}") for index in range(9)]


def run_sanity(target_events: int = 100_000, seed: int = 20260906) -> dict[str, float | int]:
    if target_events < 1:
        raise ValueError("target_events must be positive")

    total_events = 0
    total_pa = 0
    total_gdp = 0
    total_xbt = 0
    games = 0
    counters: Counter[str] = Counter()

    while total_events < target_events:
        engine = PersistentInningEngine(
            _lineup("A"),
            _lineup("H"),
            RNG(seed + games),
            away_pitcher=PitcherProfile(100, 100, 100, "R"),
            home_pitcher=PitcherProfile(100, 100, 100, "R"),
        )
        result = engine.simulate_game()
        lines = result.away_lines + result.home_lines
        total_events += result.events
        total_pa += sum(line.PA for line in lines)
        total_gdp += sum(line.GDP for line in lines)
        total_xbt += sum(line.XBT for line in lines)
        counters.update(engine.natural_event_counts)
        games += 1

    first_home_attempts = counters["first_to_home_on_double_attempts"]
    first_home_successes = counters["first_to_home_on_double_successes"]
    tag_attempts = counters["tag_up_attempts"]
    tag_successes = counters["tag_up_successes"]

    per_600 = 600.0 / max(1, total_pa)
    return {
        "seed": seed,
        "games": games,
        "events": total_events,
        "PA": total_pa,
        "SF": counters["sacrifice_fly"],
        "SF_per_600_PA": counters["sacrifice_fly"] * per_600,
        "tag_up_attempts": tag_attempts,
        "tag_up_successes": tag_successes,
        "tag_up_success_rate": tag_successes / max(1, tag_attempts),
        "first_to_home_on_double_attempts": first_home_attempts,
        "first_to_home_on_double_successes": first_home_successes,
        "first_to_home_on_double_success_rate": (
            first_home_successes / max(1, first_home_attempts)
        ),
        "wild_pitch": counters["wild_pitch"],
        "passed_ball": counters["passed_ball"],
        "GDP": total_gdp,
        "GDP_per_600_PA": total_gdp * per_600,
        "XBT": total_xbt,
        "XBT_per_600_PA": total_xbt * per_600,
        "fielders_choice": counters["fielders_choice"],
        "ground_advance_attempts": counters["ground_advance_attempts"],
        "ground_advance_successes": counters["ground_advance_successes"],
    }


def main() -> None:
    print(json.dumps(run_sanity(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
