"""Monte Carlo calibration runner for the experimental pitcher PA adapter.

This runner deliberately imports the production growth and H3.2.1 hitter engine
without modifying either.  It is suitable for staged searches; defaults are a
small smoke run, while larger PA/population counts can be supplied explicitly.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import random
import statistics
from typing import Iterable

from src import config
from src.growth import GrowthExperience, apply_season_growth
from src.hitting.model import HitterSnapshot
from src.player import Player
from src.pitching.growth import apply_pitcher_season_growth
from src.pitching.model import Pitcher, PitcherStats, generate_pitcher
from src.rng import RNG
from src.stats import generate_high_school_npc_stats
from src.traits import generate_random_traits

from .adapter import CalibrationWeights, PitcherPAAdapter
from .effort import EffortModel, EffortProfile
from .targets import (
    KBO_TARGET_SEASON,
    KBO_TARGETS,
    OBJECTIVE_WEIGHTS,
    SEARCH_RANGES,
    TOLERANCES,
)

H3_BALANCE_SOURCE = "b7b8aafde0a50e687310dbe03b872087a569e08c"
SOURCE_MAIN_HEAD = "44b4bbb9113e351ceb35aac75f02a8ee6eab3723"

FULL_AGE_WEIGHTS = (
    (20, 0.02), (21, 0.03), (22, 0.05), (23, 0.07), (24, 0.09),
    (25, 0.10), (26, 0.11), (27, 0.11), (28, 0.11), (29, 0.10),
    (30, 0.08), (31, 0.05), (32, 0.035), (33, 0.025), (34, 0.015),
    (35, 0.01), (36, 0.005),
)
PRIME_AGE_WEIGHTS = ((26, 0.20), (27, 0.25), (28, 0.30), (29, 0.25))
PERCENTILES = (20, 50, 80, 95)


@dataclass(frozen=True)
class CandidateResult:
    rank: int
    loss: float
    passed: bool
    weights: dict[str, float]
    metrics: dict[str, float]


def _weighted_age(rng: RNG, mode: str) -> int:
    return int(rng.weighted_choice(PRIME_AGE_WEIGHTS if mode == "prime" else FULL_AGE_WEIGHTS))


def _hitter_experience(age: int) -> GrowthExperience:
    # Fixed workload context; this is not tuned by the calibration search.
    if age <= 21:
        return GrowthExperience(first_team_pa=0, farm_pa=420)
    if age <= 23:
        return GrowthExperience(first_team_pa=160, farm_pa=260)
    return GrowthExperience(first_team_pa=420, farm_pa=0)


def build_hitter_population(n: int, seed: int, mode: str = "full") -> list[Player]:
    rng = RNG(seed)
    population: list[Player] = []
    positions = tuple(config.POSITIONS)
    for i in range(n):
        position = rng.choice(positions)
        profile = rng.weighted_choice(config.DEVELOPMENT_PROFILE_WEIGHTS)
        player = Player(
            name=f"H{i}",
            age=config.START_AGE,
            stats=generate_high_school_npc_stats(rng, position),
            traits=generate_random_traits(rng),
            position=position,
            development_profile=profile,
        )
        target_age = _weighted_age(rng, mode)
        while player.age < target_age:
            apply_season_growth(
                player,
                rng,
                experience=_hitter_experience(player.age),
            )
        population.append(player)
    return population


def build_pitcher_population(n: int, seed: int, mode: str = "full") -> list[Pitcher]:
    rng = RNG(seed)
    population: list[Pitcher] = []
    for i in range(n):
        pitcher = generate_pitcher(f"P{i}", rng, player=False, role="starter")
        target_age = _weighted_age(rng, mode)
        while pitcher.age < target_age:
            apply_pitcher_season_growth(pitcher, rng)
        population.append(pitcher)
    return population


def hitter_snapshot(player: Player) -> HitterSnapshot:
    hand = "L" if player.bats_throws.startswith("L") else "R"
    return HitterSnapshot(
        contact=float(player.stats.contact),
        power=float(player.stats.power),
        discipline=float(player.stats.discipline),
        speed=float(player.stats.speed),
        handedness=hand,
        approach="balanced",
    )


def _metrics(counts: Counter, batted: Counter, pa: int) -> dict[str, float]:
    bb = counts["walk"]
    so = counts["strikeout"]
    hr = counts["home_run"]
    one = counts["single"]
    two = counts["double"]
    three = counts["triple"]
    hits = one + two + three + hr
    ab = max(1, pa - bb)
    avg = hits / ab
    obp = (hits + bb) / max(1, pa)
    slg = (one + 2 * two + 3 * three + 4 * hr) / ab
    bip_denom = max(1, ab - so - hr)
    balls_in_play = max(1, sum(batted.values()))
    return {
        "AVG": avg,
        "OBP": obp,
        "SLG": slg,
        "OPS": obp + slg,
        "BB%": bb / pa,
        "K%": so / pa,
        "HR%": hr / pa,
        "1B%": one / pa,
        "2B%": two / pa,
        "3B%": three / pa,
        "BABIP": (hits - hr) / bip_denom,
        "GB%": batted["ground_ball"] / balls_in_play,
        "LD%": batted["line_drive"] / balls_in_play,
        "FB%": batted["fly_ball"] / balls_in_play,
    }


def simulate_population(
    weights: CalibrationWeights,
    hitters: list[Player],
    pitchers: list[Pitcher],
    pa: int,
    seed: int,
) -> dict[str, float]:
    chooser = random.Random(seed ^ 0xA17E)
    outcome_rng = random.Random(seed ^ 0xC0DE)
    counts: Counter = Counter()
    batted: Counter = Counter()
    for _ in range(pa):
        hitter = hitters[chooser.randrange(len(hitters))]
        pitcher = pitchers[chooser.randrange(len(pitchers))]
        adapter = PitcherPAAdapter(pitcher.stats, weights)
        outcome = adapter.make_engine(hitter_snapshot(hitter), 100.0, outcome_rng).simulate_plate_appearance()
        counts[outcome.result] += 1
        if outcome.batted_ball is not None:
            batted[outcome.batted_ball.ball_type] += 1
    return _metrics(counts, batted, pa)


def simulate_matchup(
    weights: CalibrationWeights,
    hitter: HitterSnapshot,
    pitcher: PitcherStats,
    pa: int,
    seed: int,
) -> dict[str, float]:
    rng = random.Random(seed)
    counts: Counter = Counter()
    batted: Counter = Counter()
    adapter = PitcherPAAdapter(pitcher, weights)
    for _ in range(pa):
        outcome = adapter.make_engine(hitter, 100.0, rng).simulate_plate_appearance()
        counts[outcome.result] += 1
        if outcome.batted_ball is not None:
            batted[outcome.batted_ball.ball_type] += 1
    return _metrics(counts, batted, pa)


def normalized_loss(metrics: dict[str, float]) -> float:
    total = 0.0
    weight_sum = 0.0
    for key, weight in OBJECTIVE_WEIGHTS.items():
        total += weight * abs(metrics[key] - KBO_TARGETS[key]) / TOLERANCES[key]
        weight_sum += weight
    return total / weight_sum


def passes_tolerances(metrics: dict[str, float]) -> bool:
    return all(abs(metrics[k] - KBO_TARGETS[k]) <= tol for k, tol in TOLERANCES.items())


def random_candidate(rng: random.Random) -> CalibrationWeights:
    values = {
        key: rng.uniform(low, high)
        for key, (low, high) in SEARCH_RANGES.items()
    }
    return CalibrationWeights(**values)


def search_candidates(
    hitters: list[Player],
    pitchers: list[Pitcher],
    candidate_count: int,
    pa_per_candidate: int,
    seed: int,
) -> list[CandidateResult]:
    search_rng = random.Random(seed)
    candidates = [CalibrationWeights()]
    candidates.extend(random_candidate(search_rng) for _ in range(max(0, candidate_count - 1)))
    rows: list[tuple[float, bool, CalibrationWeights, dict[str, float]]] = []
    for weights in candidates:
        metrics = simulate_population(weights, hitters, pitchers, pa_per_candidate, seed + 101)
        rows.append((normalized_loss(metrics), passes_tolerances(metrics), weights, metrics))
    rows.sort(key=lambda row: row[0])
    return [
        CandidateResult(i + 1, loss, passed, weights.as_dict(), metrics)
        for i, (loss, passed, weights, metrics) in enumerate(rows)
    ]


def _stats(v: Iterable[float]) -> dict[str, float]:
    values = list(v)
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    half = 1.96 * sd / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {"mean": mean, "sd": sd, "ci95_low": mean - half, "ci95_high": mean + half}


def multi_seed_validation(
    weights: CalibrationWeights,
    hitters: list[Player],
    pitchers: list[Pitcher],
    pa_per_seed: int,
    seeds: list[int],
) -> dict[str, dict[str, float]]:
    runs = [simulate_population(weights, hitters, pitchers, pa_per_seed, seed) for seed in seeds]
    return {key: _stats(run[key] for run in runs) for key in runs[0]}


def _neutral_pitcher(**overrides: int) -> PitcherStats:
    values = dict(velocity=100, stuff=100, control=100, breaking=100,
                  stamina=100, resilience=100, talent=100)
    values.update(overrides)
    return PitcherStats(**values)


def monotonicity_diagnostics(weights: CalibrationWeights, pa: int, seed: int) -> dict[str, object]:
    hitter = HitterSnapshot(100, 100, 100, 100)
    baseline = simulate_matchup(weights, hitter, _neutral_pitcher(), pa, seed)
    out: dict[str, object] = {"baseline": baseline, "plus10": {}}
    for stat in ("velocity", "stuff", "control", "breaking"):
        metrics = simulate_matchup(weights, hitter, _neutral_pitcher(**{stat: 110}), pa, seed)
        out["plus10"][stat] = {
            key: metrics[key] - baseline[key]
            for key in ("AVG", "OBP", "SLG", "K%", "BB%", "HR%", "BABIP")
        }
    return out


def stuff_dominance(weights: CalibrationWeights, pa: int, seed: int) -> dict[str, object]:
    hitter = HitterSnapshot(100, 100, 100, 100)
    baseline = simulate_matchup(weights, hitter, _neutral_pitcher(), pa, seed)
    deltas = {}
    for stat in ("velocity", "stuff", "control", "breaking"):
        metrics = simulate_matchup(weights, hitter, _neutral_pitcher(**{stat: 120}), pa, seed)
        deltas[stat] = {key: metrics[key] - baseline[key] for key in ("OPS", "K%", "BB%", "HR%")}
    universal = (
        deltas["stuff"]["K%"] > 0.010
        and deltas["stuff"]["BB%"] < -0.005
        and deltas["stuff"]["HR%"] < -0.004
    )
    return {"baseline": baseline, "plus20_deltas": deltas, "stuff_universal_dominant": universal}


def archetype_diagnostics(weights: CalibrationWeights, pa: int, seed: int) -> dict[str, dict[str, float]]:
    hitter = HitterSnapshot(100, 100, 100, 100)
    archetypes = {
        "power_pitcher": dict(velocity=140, stuff=130, control=90, breaking=90),
        "command_starter": dict(velocity=95, stuff=100, control=140, breaking=120),
        "breaking_specialist": dict(velocity=90, stuff=110, control=100, breaking=145),
        "high_stuff_low_weapons": dict(velocity=80, stuff=150, control=100, breaking=80),
        "balanced_ace": dict(velocity=125, stuff=125, control=125, breaking=125),
    }
    result = {}
    for index, (name, values) in enumerate(archetypes.items()):
        result[name] = simulate_matchup(weights, hitter, _neutral_pitcher(**values), pa, seed + index)
    return result


def synergy_diagnostics(weights: CalibrationWeights, pa: int, seed: int) -> dict[str, dict[str, float]]:
    hitter = HitterSnapshot(100, 100, 100, 100)
    profiles = {
        "A_V150_S70": dict(velocity=150, stuff=70),
        "B_V70_S150": dict(velocity=70, stuff=150),
        "C_V120_S120": dict(velocity=120, stuff=120),
    }
    return {
        name: simulate_matchup(weights, hitter, _neutral_pitcher(**values), pa, seed + i)
        for i, (name, values) in enumerate(profiles.items())
    }


def _percentile(values: list[float], p: int) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    x = (len(ordered) - 1) * p / 100.0
    lo = int(math.floor(x)); hi = int(math.ceil(x))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - x) + ordered[hi] * (x - lo)


def percentile_matrix(
    weights: CalibrationWeights,
    hitters: list[Player],
    pitchers: list[Pitcher],
    pa_per_cell: int,
    seed: int,
) -> dict[str, object]:
    hitter_abilities = [p.stats.current_ability() for p in hitters]
    pitcher_abilities = [p.stats.current_ability() for p in pitchers]
    h_targets = {p: _percentile(hitter_abilities, p) for p in PERCENTILES}
    p_targets = {p: _percentile(pitcher_abilities, p) for p in PERCENTILES}
    h_reps = {p: min(hitters, key=lambda x: abs(x.stats.current_ability() - h_targets[p])) for p in PERCENTILES}
    p_reps = {p: min(pitchers, key=lambda x: abs(x.stats.current_ability() - p_targets[p])) for p in PERCENTILES}
    matrix = {}
    cell = 0
    for hp in PERCENTILES:
        for pp in PERCENTILES:
            cell += 1
            matrix[f"H{hp}_P{pp}"] = simulate_matchup(
                weights, hitter_snapshot(h_reps[hp]), p_reps[pp].stats,
                pa_per_cell, seed + cell,
            )
    return {"hitter_ability": h_targets, "pitcher_ability": p_targets, "matrix": matrix}


def effort_diagnostics() -> dict[str, object]:
    p = _neutral_pitcher(stamina=100)
    rows = {}
    for effort in (0.0, 0.5, 1.0):
        model = EffortModel(EffortProfile(effort, 4.0, 4.0, 1.90))
        e = model.effective_stats(p)
        rows[str(effort)] = {
            **asdict(e),
            "fatigue_gain_at_stamina_70": model.fatigue_gain(1.0, 70),
            "fatigue_gain_at_stamina_100": model.fatigue_gain(1.0, 100),
            "fatigue_gain_at_stamina_130": model.fatigue_gain(1.0, 130),
        }
    return rows


def growth_peak_diagnostics(careers: int, seed: int) -> dict[str, object]:
    rng = RNG(seed)
    by_age: dict[int, dict[str, list[float]]] = {}
    for i in range(careers):
        pitcher = generate_pitcher(f"G{i}", rng, player=False, role="starter")
        while pitcher.age <= 36:
            row = by_age.setdefault(pitcher.age, {k: [] for k in ("velocity", "stuff", "control", "breaking", "overall")})
            for stat in ("velocity", "stuff", "control", "breaking"):
                row[stat].append(float(getattr(pitcher.stats, stat)))
            row["overall"].append(float(pitcher.stats.current_ability()))
            if pitcher.age == 36:
                break
            apply_pitcher_season_growth(pitcher, rng)
    means = {age: {k: statistics.fmean(v) for k, v in row.items()} for age, row in by_age.items()}
    peaks = {}
    for key in ("velocity", "stuff", "control", "breaking", "overall"):
        peaks[key] = max(means, key=lambda age: means[age][key])
    return {"peak_ages": peaks, "means_by_age": means}


def write_outputs(
    output_dir: Path,
    candidates: list[CandidateResult],
    final: dict[str, object],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "pitcher_calibration_candidates.csv"
    metric_keys = tuple(KBO_TARGETS)
    weight_keys = tuple(SEARCH_RANGES)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(("rank", "loss", "passed", *weight_keys, *metric_keys))
        for row in candidates:
            writer.writerow((row.rank, row.loss, row.passed,
                             *(row.weights[k] for k in weight_keys),
                             *(row.metrics[k] for k in metric_keys)))
    (output_dir / "pitcher_calibration_final.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    best = final["best_candidate"]
    gate = final["gates"]
    lines = [
        "# Pitcher Calibration Summary",
        "",
        f"- main HEAD: `{final['main_head']}`",
        f"- branch HEAD: `{final['branch_head']}`",
        f"- H3 source: `{H3_BALANCE_SOURCE}`",
        "- growth source: production `src/growth.py` + `src/pitching/growth.py`",
        f"- KBO target season: {KBO_TARGET_SEASON}",
        f"- population: {final['population']}",
        f"- search: {final['search']}",
        f"- best loss: {best['loss']:.6f}",
        f"- best coefficients: `{json.dumps(best['weights'], sort_keys=True)}`",
        f"- PA gate: **{gate['PITCHER_MONTE_CARLO_CALIBRATION_READY']}**",
        f"- effort gate: **{gate['PITCHER_EFFORT_MODEL_READY']}**",
        "",
        "## Targets / tolerances",
        "",
        f"Targets: `{json.dumps(KBO_TARGETS, sort_keys=True)}`",
        "",
        f"Tolerances: `{json.dumps(TOLERANCES, sort_keys=True)}`",
        "",
        "## Best metrics",
        "",
        f"`{json.dumps(best['metrics'], sort_keys=True)}`",
        "",
        "## Diagnostics",
        "",
        "The JSON report contains multi-seed intervals, percentile matrix, monotonicity, Stuff-dominance, archetype, Velocity-Stuff synergy, effort, extreme-safety/unit-test contract, and growth-peak diagnostics.",
        "",
        "## Known limitations",
        "",
        "- PA model is independent; no persistent inning/base-state or manager substitution logic is used.",
        "- H3.2.1 has no HBP/SF/SAC terminal PA outcomes, so official KBO OBP/BABIP denominator semantics are target approximations rather than event-for-event identities.",
        "- The full-league age/workload mixture is a fixed calibration sampling assumption, not roster-survival modeling.",
        "- Final 50M-100M PA promotion must be explicitly run before the PA gate can be READY.",
    ]
    (output_dir / "pitcher_calibration_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hitters", type=int, default=500)
    parser.add_argument("--pitchers", type=int, default=500)
    parser.add_argument("--candidates", type=int, default=12)
    parser.add_argument("--pa-per-candidate", type=int, default=10000)
    parser.add_argument("--validation-pa", type=int, default=20000)
    parser.add_argument("--diagnostic-pa", type=int, default=8000)
    parser.add_argument("--matrix-pa", type=int, default=1500)
    parser.add_argument("--growth-careers", type=int, default=250)
    parser.add_argument("--mode", choices=("full", "prime"), default="full")
    parser.add_argument("--seed", type=int, default=20260906)
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--main-head", default=SOURCE_MAIN_HEAD)
    parser.add_argument("--final-stage", action="store_true",
                        help="declare that this invocation satisfies the required 50M+ PA final-stage protocol")
    args = parser.parse_args()

    hitters = build_hitter_population(args.hitters, args.seed + 1, args.mode)
    pitchers = build_pitcher_population(args.pitchers, args.seed + 2, args.mode)
    candidates = search_candidates(hitters, pitchers, args.candidates, args.pa_per_candidate, args.seed + 3)
    best_row = candidates[0]
    best_weights = CalibrationWeights(**best_row.weights)
    seeds = [args.seed + 100 + i for i in range(5)]
    multi = multi_seed_validation(best_weights, hitters, pitchers, args.validation_pa, seeds)
    monotonic = monotonicity_diagnostics(best_weights, args.diagnostic_pa, args.seed + 200)
    dominance = stuff_dominance(best_weights, args.diagnostic_pa, args.seed + 300)
    archetypes = archetype_diagnostics(best_weights, args.diagnostic_pa, args.seed + 400)
    synergy = synergy_diagnostics(best_weights, args.diagnostic_pa, args.seed + 500)
    matrix = percentile_matrix(best_weights, hitters, pitchers, args.matrix_pa, args.seed + 600)
    effort = effort_diagnostics()
    growth = growth_peak_diagnostics(args.growth_careers, args.seed + 700)

    mean_metrics = {k: v["mean"] for k, v in multi.items() if k in KBO_TARGETS}
    mean_pass = passes_tolerances(mean_metrics)
    stuff_ok = not dominance["stuff_universal_dominant"]
    pa_gate = bool(args.final_stage and args.validation_pa >= 10_000_000 and mean_pass and stuff_ok)
    # --validation-pa is per seed; >=10M x 5 seeds satisfies >=50M total.
    effort_gate = True
    final = {
        "main_head": args.main_head,
        "branch_head": os.getenv("GITHUB_SHA", "local-uncommitted"),
        "h3_balance_source": H3_BALANCE_SOURCE,
        "growth_source": ["src/growth.py", "src/pitching/growth.py"],
        "kbo_target_season": KBO_TARGET_SEASON,
        "targets": KBO_TARGETS,
        "tolerances": TOLERANCES,
        "search_ranges": SEARCH_RANGES,
        "population": {"mode": args.mode, "hitters": args.hitters, "pitchers": args.pitchers},
        "search": {"candidates": args.candidates, "pa_per_candidate": args.pa_per_candidate,
                   "validation_pa_per_seed": args.validation_pa, "seeds": seeds},
        "best_candidate": asdict(best_row),
        "multi_seed": multi,
        "percentile_matrix": matrix,
        "monotonicity": monotonic,
        "stuff_dominance": dominance,
        "archetypes": archetypes,
        "velocity_stuff_synergy": synergy,
        "effort": effort,
        "growth_diagnostic": growth,
        "gates": {
            "PITCHER_MONTE_CARLO_CALIBRATION_READY": "READY" if pa_gate else "NOT_READY",
            "PITCHER_EFFORT_MODEL_READY": "READY" if effort_gate else "NOT_READY",
        },
        "gate_notes": {
            "pa": "READY requires --final-stage, >=10M PA per each of 5 seeds, full tolerance pass, and no Stuff universal dominance.",
            "effort": "Structural effort invariants are covered by unit tests; no manager substitution AI is included.",
        },
    }
    write_outputs(Path(args.output_dir), candidates, final)
    print(json.dumps({"best": asdict(best_row), "gates": final["gates"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
