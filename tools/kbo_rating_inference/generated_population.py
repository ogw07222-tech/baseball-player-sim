from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from src.hitting.model import HitterSnapshot, HittingEngine, PitcherSnapshot
from src.hitting.normalization import normalize_hitter
from src.pitching.physical_velocity import base_avg_kmh, gameplay_velocity
from tools.kbo_rating_inference.core import weighted_summary
from tools.pitcher_joint_v3 import calibrate as v3
from tools.pitcher_joint_v4.first_team_population import WeightedSeason, build_first_team_seasons, pa_sampler

KBO_TARGET = {
    "AVG": 0.2616,
    "OBP": 0.3385,
    "SLG": 0.3887,
    "BB%": 0.09149,
    "K%": 0.19687,
    "HR%": 0.0230,
    "BABIP": 0.3122,
}


def hitter_snapshot(row: WeightedSeason) -> HitterSnapshot:
    gp = normalize_hitter(row.contact, row.power, row.discipline, row.speed)
    return HitterSnapshot(gp.contact, gp.power, gp.discipline, gp.speed, "L" if row.bats_throws.startswith("L") else "R", "balanced")


def neutral_metrics(rows: list[WeightedSeason], pa: int, seed: int) -> dict[str, float]:
    choose = pa_sampler(rows, seed ^ 0x7111)
    rng = random.Random(seed ^ 0xC0DE)
    counts = Counter()
    for _ in range(pa):
        out = HittingEngine(hitter_snapshot(next(choose)), PitcherSnapshot(), 100.0, rng).simulate_plate_appearance()
        counts[out.result] += 1
    bb = counts["walk"]; so = counts["strikeout"]; hr = counts["home_run"]
    one = counts["single"]; two = counts["double"]; three = counts["triple"]
    hits = one + two + three + hr
    ab = max(1, pa - bb); bip = max(1, ab - so - hr)
    obp = (hits + bb) / pa
    slg = (one + 2 * two + 3 * three + 4 * hr) / ab
    return {
        "AVG": hits / ab, "OBP": obp, "SLG": slg, "OPS": obp + slg,
        "BB%": bb / pa, "K%": so / pa, "HR%": hr / pa,
        "1B%": one / pa, "2B%": two / pa, "3B%": three / pa,
        "BABIP": (hits - hr) / bip,
    }


def _hitter_row(seed: int, idx: int, row: WeightedSeason) -> dict[str, object]:
    gp = normalize_hitter(row.contact, row.power, row.discipline, row.speed)
    return {
        "seed": seed, "snapshot_id": idx, "age": row.age, "first_team_PA": row.pa,
        "bats_throws": row.bats_throws,
        "raw_contact": row.contact, "raw_power": row.power, "raw_discipline": row.discipline, "raw_speed": row.speed,
        "gp_contact": gp.contact, "gp_power": gp.power, "gp_discipline": gp.discipline, "gp_speed": gp.speed,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def _distribution(rows: list[dict[str, object]], fields: tuple[str, ...], weight_field: str) -> dict[str, dict[str, float]]:
    weights = [float(r[weight_field]) for r in rows]
    return {field: weighted_summary([float(r[field]) for r in rows], weights) for field in fields}


def representative_pitchers(n: int, seed: int) -> list[dict[str, object]]:
    pitchers = v3.build_pitchers(n, seed)
    rows = []
    for i, p in enumerate(pitchers):
        weight = 1.0
        physical = base_avg_kmh(p.stats.velocity)
        rows.append({
            "seed": seed, "snapshot_id": i, "age": p.age, "weight": weight,
            "weight_source": "best_available_age_mix_proxy_no_pitcher_career_usage_engine",
            "raw_velocity": p.stats.velocity, "raw_stuff": p.stats.stuff,
            "raw_control": p.stats.control, "raw_breaking": p.stats.breaking,
            "avg_fastball_kmh": physical, "gp_velocity": gameplay_velocity(physical),
        })
    return rows


def _stable(seed_summaries: list[dict[str, object]]) -> bool:
    if len(seed_summaries) < 2:
        return False
    for stat in ("contact", "power", "discipline", "speed"):
        means = [float(s["raw_distribution"][stat]["mean"]) for s in seed_summaries]
        if max(means) - min(means) > 3.0:
            return False
    for metric, band in (("AVG", .012), ("OBP", .014), ("SLG", .025), ("BB%", .012), ("K%", .018)):
        vals = [float(s["neutral_offense"][metric]) for s in seed_summaries]
        if max(vals) - min(vals) > band:
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--careers-per-seed", type=int, default=600)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--max-seasons", type=int, default=18)
    ap.add_argument("--neutral-pa-per-seed", type=int, default=1700000)
    ap.add_argument("--pitchers", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=261306)
    ap.add_argument("--outdir", default="reports")
    args = ap.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    all_hitter_rows: list[dict[str, object]] = []
    seed_summaries = []
    for s in range(args.seeds):
        seed = args.seed + s * 1000003
        seasons = build_first_team_seasons(args.careers_per_seed, seed, args.max_seasons)
        if not seasons or any(r.pa <= 0 for r in seasons):
            raise RuntimeError("first-team population contains no/zero-PA retained snapshots")
        rows = [_hitter_row(seed, i, row) for i, row in enumerate(seasons)]
        all_hitter_rows.extend(rows)
        raw_dist = _distribution(rows, ("raw_contact", "raw_power", "raw_discipline", "raw_speed"), "first_team_PA")
        raw_dist = {k.removeprefix("raw_"): v for k, v in raw_dist.items()}
        gp_dist = _distribution(rows, ("gp_contact", "gp_power", "gp_discipline", "gp_speed"), "first_team_PA")
        gp_dist = {k.removeprefix("gp_"): v for k, v in gp_dist.items()}
        seed_summaries.append({
            "seed": seed, "careers": args.careers_per_seed, "retained_player_seasons": len(rows),
            "first_team_PA": sum(int(r["first_team_PA"]) for r in rows),
            "raw_distribution": raw_dist, "gameplay_distribution": gp_dist,
            "neutral_offense": neutral_metrics(seasons, args.neutral_pa_per_seed, seed + 77),
        })

    pitcher_rows = representative_pitchers(args.pitchers, args.seed + 7000001)
    _write_csv(outdir / "kbo_generated_first_team_hitter_population.csv", all_hitter_rows)
    _write_csv(outdir / "kbo_generated_first_team_pitcher_population.csv", pitcher_rows)

    combined_raw = _distribution(all_hitter_rows, ("raw_contact", "raw_power", "raw_discipline", "raw_speed"), "first_team_PA")
    combined_gp = _distribution(all_hitter_rows, ("gp_contact", "gp_power", "gp_discipline", "gp_speed"), "first_team_PA")
    pitcher_dist = _distribution(pitcher_rows, ("raw_velocity", "raw_stuff", "raw_control", "raw_breaking"), "weight")
    neutral_mean = {k: statistics.fmean(float(s["neutral_offense"][k]) for s in seed_summaries) for k in seed_summaries[0]["neutral_offense"]}
    old_baseline = {"AVG": .2311, "OBP": .2866, "SLG": .3484, "OPS": .6350, "BB%": .0701, "K%": .2344, "BABIP": .2837}
    improvement = sum(abs(neutral_mean[k] - KBO_TARGET[k]) for k in ("AVG", "OBP", "SLG", "BB%", "K%", "BABIP")) < sum(abs(old_baseline[k] - KBO_TARGET[k]) for k in ("AVG", "OBP", "SLG", "BB%", "K%", "BABIP"))
    stable = _stable(seed_summaries)
    age_weights = [float(r["first_team_PA"]) for r in all_hitter_rows]
    age_summary = weighted_summary([float(r["age"]) for r in all_hitter_rows], age_weights)
    population_ready = stable and improvement and len(all_hitter_rows) > 0 and all(float(r["first_team_PA"]) > 0 for r in all_hitter_rows)

    result = {
        "gate": "KBO_FIRST_TEAM_POPULATION_CONTRACT_READY" if population_ready else "KBO_FIRST_TEAM_POPULATION_CONTRACT_NOT_READY",
        "method": "Production CareerEngine player-season snapshots retained only when first_team.PA > 0 and weighted by first-team PA",
        "hitter": {
            "seeds": args.seeds, "careers_per_seed": args.careers_per_seed,
            "total_careers": args.seeds * args.careers_per_seed,
            "retained_player_seasons": len(all_hitter_rows),
            "total_first_team_PA": sum(int(r["first_team_PA"]) for r in all_hitter_rows),
            "age_pa_weighted": age_summary,
            "raw_distribution": {k.removeprefix("raw_"): v for k, v in combined_raw.items()},
            "gameplay_distribution": {k.removeprefix("gp_"): v for k, v in combined_gp.items()},
            "neutral_offense_mean": neutral_mean,
            "neutral_offense_total_simulated_PA": args.neutral_pa_per_seed * args.seeds,
            "improved_vs_old_equal_weight_mixed_age": improvement,
            "seed_stable": stable,
            "seed_summaries": seed_summaries,
        },
        "pitcher": {
            "n": len(pitcher_rows),
            "usage_weighting": "best available representative age-mixture proxy; no production pitcher career first-team BF/IP engine exists",
            "raw_distribution": {k.removeprefix("raw_"): v for k, v in pitcher_dist.items()},
        },
        "limitations": [
            "Requested 100k-250k CareerEngine careers are computationally expensive because real season gameplay/roster flow is executed; workflow records the actually executed sample only.",
            "No equivalent production pitcher CareerEngine first-team BF/IP usage path currently exists; pitcher population is explicitly marked best-available representative rather than fabricated usage-weighted.",
        ],
    }
    (outdir / "kbo_first_team_population_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "# KBO First-Team Population Summary", "", f"Gate: `{result['gate']}`", "",
        f"Hitter careers executed: {result['hitter']['total_careers']:,}",
        f"Retained first-team player-seasons: {len(all_hitter_rows):,}",
        f"Total retained first-team PA weight: {result['hitter']['total_first_team_PA']:,}",
        f"Neutral diagnostic PA: {result['hitter']['neutral_offense_total_simulated_PA']:,}", "",
        "## Neutral offense",
    ]
    lines += [f"- {k}: {v:.6f}" for k, v in neutral_mean.items()]
    lines += ["", f"Seed stable: **{stable}**", f"Closer to KBO than old equal-weight mixed-age population: **{improvement}**", "", "## Pitcher population limitation", result["pitcher"]["usage_weighting"]]
    (outdir / "kbo_first_team_population_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"gate": result["gate"], "hitter": {"careers": result["hitter"]["total_careers"], "player_seasons": len(all_hitter_rows), "neutral": neutral_mean, "stable": stable}, "pitcher_n": len(pitcher_rows)}, indent=2))


if __name__ == "__main__":
    main()
