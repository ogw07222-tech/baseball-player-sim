"""Aggregate deterministic growth-validation shards into canonical JSON/CSV."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.growth_validation import (
    SOURCE_BRANCH,
    SOURCE_SHA,
    chart_samples,
    cohort_compare,
    npc_extra,
    summarize,
    write_csv,
)

EXPECTED = {
    "player_pure": 20000,
    "npc_pure": 20000,
    "player_full": 5000,
    "npc_full": 5000,
}


def _restore_row_types(row: dict) -> dict:
    """Restore JSON-coerced mapping keys needed by the in-memory summarizers."""
    snaps = row.get("snaps")
    if isinstance(snaps, dict):
        row["snaps"] = {int(age): values for age, values in snaps.items()}
    return row


def load_group(root: Path, name: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(root.glob(f"{name}_*.json")):
        shard_rows = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(_restore_row_types(row) for row in shard_rows)
    expected = EXPECTED[name]
    if len(rows) != expected:
        raise RuntimeError(f"{name}: expected {expected} rows, got {len(rows)}")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="shards")
    ap.add_argument("--json", default="reports/current_generation_growth_validation.json")
    ap.add_argument("--csv", default="reports/current_generation_growth_validation_samples.csv")
    ap.add_argument("--seed", type=int, default=20260905)
    a = ap.parse_args()

    root = Path(a.input)
    groups = {name: load_group(root, name) for name in EXPECTED}
    pp, np = groups["player_pure"], groups["npc_pure"]
    pf, nf = groups["player_full"], groups["npc_full"]
    summaries = {k: summarize(v) for k, v in groups.items()}
    report = {
        "source": {"branch": SOURCE_BRANCH, "sha": SOURCE_SHA},
        "seed": a.seed,
        "sample_size": {k: len(v) for k, v in groups.items()},
        "positions": "cycled uniformly across config.POSITIONS, matching tools/draft_calibration.py",
        "mode_notes": {
            "pure": "production generation + development profile + Talent + production apply_season_growth; traits cleared; coach/experience/event/injury absent; fixed through age 45",
            "full_player": "production Player.random + production CareerEngine, including high school/draft, coaches, playing time, experience, traits, events, injuries, breakthroughs, aging and retirement",
            "full_npc": "generate_high_school_npc_stats with the same profile/traits/breakthrough-affinity generation as Player.random, then the same production CareerEngine; no hidden NPC-only growth assumptions",
            "sharding": "global sample indices and per-sample seeds exactly match the original unsharded run",
        },
        "summaries": summaries,
        "npc_full_extra": npc_extra(nf),
        "compare_pure": cohort_compare(pp, np),
        "compare_full": cohort_compare(pf, nf),
        "old_v04": {
            "starting_mean": 70.207,
            "peak_mean": 102.086,
            "peak_p90": 116.729,
            "peak_p95": 123.328,
            "peak_p99": 133.273,
            "mean_peak_age": 31.277,
            "talent_peak_corr": 0.511,
            "sample_careers": 300,
            "source": "docs/balance-v0.4.md",
        },
    }
    jp = Path(a.json)
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(Path(a.csv), chart_samples(groups))
    print(json.dumps({"sample_size": report["sample_size"], "source": report["source"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
