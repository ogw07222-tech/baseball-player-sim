"""Deterministic shard runner for current-generation growth validation.

Validation-only execution helper. It delegates every simulated career to the
production-backed run_pure_one/run_full_one functions in growth_validation.py.
Global sample indices preserve the exact seed mapping of the unsharded run.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tools.growth_validation import run_full_one, run_pure_one


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("pure", "full"), required=True)
    ap.add_argument("--cohort", choices=("player", "npc"), required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--master", type=int, default=20260905)
    ap.add_argument("--offset", type=int, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    fn = run_pure_one if a.kind == "pure" else run_full_one
    items = [
        (a.cohort, idx, a.master + a.offset + idx)
        for idx in range(a.start, a.start + a.count)
    ]
    if a.workers <= 1:
        rows = [fn(item) for item in items]
    else:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            rows = list(ex.map(fn, items, chunksize=16))

    path = Path(a.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "kind": a.kind,
        "cohort": a.cohort,
        "start": a.start,
        "count": len(rows),
        "first_seed": a.master + a.offset + a.start,
        "last_seed": a.master + a.offset + a.start + a.count - 1,
    }))


if __name__ == "__main__":
    main()
