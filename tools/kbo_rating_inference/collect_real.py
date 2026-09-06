from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import urllib.request
from pathlib import Path

BR_LEAGUE_ID = "4e296e3b"
BR_BAT_URL = f"https://www.baseball-reference.com/register/leader.cgi?id={BR_LEAGUE_ID}&type=bat"
BR_PITCH_URL = f"https://www.baseball-reference.com/register/leader.cgi?id={BR_LEAGUE_ID}&type=pitch"


def _fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; baseball-player-sim calibration; +https://github.com/ogw07222-tech/baseball-player-sim)",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _read_table(url: str, marker: str):
    import pandas as pd

    html = _fetch_html(url)
    # Baseball-Reference sometimes wraps full tables in HTML comments.
    html = html.replace("<!--", "").replace("-->", "")
    tables = pd.read_html(io.StringIO(html))
    for table in tables:
        cols = {str(c).strip() for c in table.columns}
        if marker in cols and "Name" in cols:
            return table
    raise RuntimeError(f"unable to locate {marker} table")


def _num(value, default=0.0):
    if value is None:
        return default
    text = str(value).replace(",", "").strip()
    if text in {"", "nan", "NaN", "--"}:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _clean_name(value: str) -> str:
    return re.sub(r"[*#]$", "", str(value).strip())


def _derive_hitter(row) -> dict[str, object]:
    pa = int(_num(row.get("PA")))
    ab = int(_num(row.get("AB")))
    h = int(_num(row.get("H")))
    doubles = int(_num(row.get("2B")))
    triples = int(_num(row.get("3B")))
    hr = int(_num(row.get("HR")))
    bb = int(_num(row.get("BB")))
    so = int(_num(row.get("SO")))
    hbp = int(_num(row.get("HBP")))
    sb = int(_num(row.get("SB")))
    cs = int(_num(row.get("CS")))
    one = max(0, h - doubles - triples - hr)
    bip = max(1, ab - so - hr)
    return {
        "season": 2025,
        "player": _clean_name(row.get("Name", "")),
        "team": str(row.get("Tm", "")),
        "age": int(_num(row.get("Age"))),
        "PA": pa,
        "AB": ab,
        "H": h,
        "1B": one,
        "2B": doubles,
        "3B": triples,
        "HR": hr,
        "BB": bb,
        "HBP": hbp,
        "SO": so,
        "AVG": _num(row.get("BA"), h / ab if ab else 0.0),
        "OBP": _num(row.get("OBP")),
        "SLG": _num(row.get("SLG")),
        "OPS": _num(row.get("OPS")),
        "BB_pct": bb / pa if pa else 0.0,
        "K_pct": so / pa if pa else 0.0,
        "HR_pct": hr / pa if pa else 0.0,
        "BABIP": (h - hr) / bip,
        "SB": sb,
        "CS": cs,
        "SB_attempt_pct": (sb + cs) / pa if pa else 0.0,
        "SB_success": sb / (sb + cs) if sb + cs else math.nan,
        "source": BR_BAT_URL,
    }


def _derive_pitcher(row) -> dict[str, object]:
    bf = int(_num(row.get("BF")))
    h = int(_num(row.get("H")))
    hr = int(_num(row.get("HR")))
    bb = int(_num(row.get("BB")))
    so = int(_num(row.get("SO")))
    hbp = int(_num(row.get("HBP")))
    # Approximate opponent AB from BF minus BB/HBP. Sacrifice detail is unavailable
    # in the BR leader table, so OPP_AVG/BABIP remain explicitly approximate.
    opp_ab = max(1, bf - bb - hbp)
    bip = max(1, opp_ab - so - hr)
    singles = max(0, h - int(_num(row.get("2B"))) - int(_num(row.get("3B"))) - hr)
    tb = singles + 2 * int(_num(row.get("2B"))) + 3 * int(_num(row.get("3B"))) + 4 * hr
    return {
        "season": 2025,
        "player": _clean_name(row.get("Name", "")),
        "team": str(row.get("Tm", "")),
        "age": int(_num(row.get("Age"))),
        "G": int(_num(row.get("G"))),
        "GS": int(_num(row.get("GS"))),
        "IP": str(row.get("IP", "")),
        "BF": bf,
        "H": h,
        "HR": hr,
        "BB": bb,
        "SO": so,
        "ERA": _num(row.get("ERA")),
        "K_pct": so / bf if bf else 0.0,
        "BB_pct": bb / bf if bf else 0.0,
        "HR_pct": hr / bf if bf else 0.0,
        "OPP_AVG": h / opp_ab,
        "OPP_SLG": tb / opp_ab,
        "BABIP": (h - hr) / bip,
        "rate_context": "OPP_AVG/SLG/BABIP approximated from public leader-table components; sac events unavailable",
        "source": BR_PITCH_URL,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _fallback(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pa", type=int, default=100)
    ap.add_argument("--min-bf", type=int, default=100)
    ap.add_argument("--outdir", default="data")
    args = ap.parse_args()
    out = Path(args.outdir)
    meta = {"season": 2025, "hitter_source": BR_BAT_URL, "pitcher_source": BR_PITCH_URL}

    try:
        bat = _read_table(BR_BAT_URL, "PA")
        hitters = [_derive_hitter(row) for _, row in bat.iterrows()]
        hitters = [r for r in hitters if int(r["PA"]) >= args.min_pa and r["player"] and r["player"] != "Name"]
        meta["hitter_mode"] = "live_full_table"
    except Exception as exc:
        hitters = _fallback(Path("data/kbo_2025_hitter_stats_seed.csv"))
        hitters = [r for r in hitters if int(float(r.get("PA", 0))) >= args.min_pa]
        meta["hitter_mode"] = "fallback_seed_partial"
        meta["hitter_error"] = repr(exc)

    try:
        pit = _read_table(BR_PITCH_URL, "BF")
        pitchers = [_derive_pitcher(row) for _, row in pit.iterrows()]
        pitchers = [r for r in pitchers if int(r["BF"]) >= args.min_bf and r["player"] and r["player"] != "Name"]
        meta["pitcher_mode"] = "live_full_table"
    except Exception as exc:
        pitchers = _fallback(Path("data/kbo_2025_pitcher_stats_seed.csv"))
        pitchers = [r for r in pitchers if int(float(r.get("BF", 0))) >= args.min_bf]
        meta["pitcher_mode"] = "fallback_seed_partial"
        meta["pitcher_error"] = repr(exc)

    if not hitters:
        raise RuntimeError("no real hitter rows available")
    if not pitchers:
        raise RuntimeError("no real pitcher rows available")

    _write_csv(out / "kbo_2025_hitter_stats_source.csv", hitters)
    _write_csv(out / "kbo_2025_pitcher_stats_source.csv", pitchers)
    meta.update({"hitters": len(hitters), "pitchers": len(pitchers), "min_pa": args.min_pa, "min_bf": args.min_bf})
    Path("reports").mkdir(exist_ok=True)
    Path("reports/kbo_real_data_provenance.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
