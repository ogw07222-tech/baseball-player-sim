"""Validate existing real-player ratings against H3.1 without refitting them."""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .model import simulate_profile
from .profiles import H3HitterProfile

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = REPO_ROOT / "data" / "kbo_2026_real_hitter_ratings_v3.csv"
REPORT_DIR = Path(__file__).with_name("reports")
BASE_SEED = 2026090500


def _simulate_one(index: int, row: dict[str, str], pa: int) -> tuple[int, dict[str, object]]:
    profile = H3HitterProfile(
        contact=float(row["contact"]), power=float(row["power"]),
        discipline=float(row["discipline"]), speed=float(row["speed"]),
        handedness="R", approach="balanced",
    )
    seed = BASE_SEED + index * 1009
    started = time.perf_counter()
    m = simulate_profile(profile, pa, seed, defense=100).as_metrics()
    runtime = time.perf_counter() - started
    out: dict[str, object] = {
        "name": row["name"], "team": row["team"],
        "contact": row["contact"], "power": row["power"],
        "discipline": row["discipline"], "speed": row["speed"],
        "input_rating_source": DEFAULT_SOURCE.name,
        "approach": "balanced", "handedness_assumption": "R",
        "opponent_defense": 100, "pa": pa, "seed": seed,
    }
    for key in ("avg", "obp", "slg", "ops", "hr_rate", "bb_rate", "k_rate"):
        out[f"target_{key}"] = row[f"target_{key}"]
    out.update({
        "h31_avg": m["AVG"], "h31_obp": m["OBP"], "h31_slg": m["SLG"],
        "h31_ops": m["OPS"], "h31_hr_rate": m["HR%"],
        "h31_bb_rate": m["BB%"], "h31_k_rate": m["K%"],
        "h31_babip": m["BABIP"], "h31_1b_rate": m["1B%"],
        "h31_2b_rate": m["2B%"], "h31_3b_rate": m["3B%"],
        "h31_offensive_value": m["offensive_value"], "runtime_s": runtime,
    })
    for stat, metric in (("avg", "AVG"), ("obp", "OBP"), ("slg", "SLG"), ("ops", "OPS")):
        out[f"err_{stat}"] = abs(m[metric] - float(row[f"target_{stat}"]))
    for stat, metric in (("hr_rate", "HR%"), ("bb_rate", "BB%"), ("k_rate", "K%")):
        out[f"err_{stat}"] = abs(m[metric] - float(row[f"target_{stat}"]))
    score = sum((
        float(out["err_avg"]) / .015,
        float(out["err_obp"]) / .015,
        float(out["err_slg"]) / .030,
        float(out["err_hr_rate"]) / .010,
        float(out["err_bb_rate"]) / .015,
        float(out["err_k_rate"]) / .020,
    )) / 6
    out["validation_fit_error"] = score
    out["validation_fit_status"] = "good" if score < 1 else "usable" if score < 2 else "poor"
    return index, out


def run(source: Path = DEFAULT_SOURCE, pa: int = 600_000, workers: int | None = None) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = list(csv.DictReader(source.open(encoding="utf-8")))
    workers = workers or min(8, os.cpu_count() or 4)
    results: list[dict[str, object] | None] = [None] * len(rows)
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_simulate_one, i, row, pa) for i, row in enumerate(rows)]
        for future in as_completed(futures):
            i, result = future.result()
            results[i] = result
    materialized = [r for r in results if r is not None]
    metrics = ("err_avg", "err_obp", "err_slg", "err_ops", "err_hr_rate", "err_bb_rate", "err_k_rate")
    def avg(key: str) -> float:
        return sum(float(r[key]) for r in materialized) / len(materialized)
    def med(key: str) -> float:
        values = sorted(float(r[key]) for r in materialized)
        n = len(values)
        return values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2
    summary: dict[str, object] = {
        "model": "H3.1 experimental validation; v3 ratings unchanged",
        "players": len(materialized), "pa_per_player": pa,
        "total_pa": pa * len(materialized), "workers": workers,
        "wall_runtime_s": time.perf_counter() - started,
        "mae": {key: avg(key) for key in metrics},
        "median_abs_error": {key: med(key) for key in metrics},
        "fit_status_counts": {s: sum(r["validation_fit_status"] == s for r in materialized) for s in ("good", "usable", "poor")},
        "largest_ops_errors": sorted(materialized, key=lambda r: float(r["err_ops"]), reverse=True)[:10],
        "notes": [
            "No player ratings were refit.",
            "Balanced approach and R-handedness are assumed because v3 CSV lacks those fields.",
            "Opponent defense is fixed at 100.",
        ],
    }
    return materialized, summary


def write_reports(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORT_DIR / "h31_real_players_v3_ratings.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    (REPORT_DIR / "h31_real_players_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--pa", type=int, default=600_000)
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()
    rows, summary = run(args.source, args.pa, args.workers)
    write_reports(rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
