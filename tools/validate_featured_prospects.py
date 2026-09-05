#!/usr/bin/env python3
"""Validate the static Featured High School Prospect dataset.

This tool is intentionally data-only. It imports no production gameplay modules.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "high_school" / "featured_prospects_2026.json"

REQUIRED_FIELDS = {
    "id",
    "display_name",
    "school_name",
    "grade",
    "position",
    "throws",
    "bats",
    "is_featured",
    "sources",
}
VALID_POSITIONS = {"P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "IF", "OF"}
VALID_THROWS = {"R", "L", None}
VALID_BATS = {"R", "L", "S", None}
ID_PATTERN = re.compile(r"^featured_hs_2026_\d{3}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

FORBIDDEN_GAMEPLAY_FIELDS = {
    "velocity",
    "stuff",
    "control",
    "breaking",
    "stamina",
    "resilience",
    "talent",
    "contact",
    "power",
    "discipline",
    "speed",
    "defense",
    "overall",
    "overall_rating",
    "potential",
    "potential_rating",
    "draft_score",
    "performance_score",
    "scouting_grade",
    "archetype",
    "draft_eligible",
    "draft_candidate",
    "draft_round",
    "draft_projection",
}


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_source(source: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(source, dict):
        return ["source must be an object"]

    required = {"type", "publisher", "title", "date", "url"}
    missing = sorted(required - set(source))
    if missing:
        errors.append(f"source missing fields: {', '.join(missing)}")
        return errors

    for key in ("type", "publisher", "title"):
        if not _nonempty_string(source.get(key)):
            errors.append(f"source.{key} must be a non-empty string")

    date = source.get("date")
    if date is not None and (not isinstance(date, str) or not DATE_PATTERN.fullmatch(date)):
        errors.append("source.date must be YYYY-MM-DD or null")

    url = source.get("url")
    if not _nonempty_string(url):
        errors.append("source.url must be a non-empty string")
    else:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("source.url must be an absolute http(s) URL")

    return errors


def _find_forbidden_fields(value: object, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_GAMEPLAY_FIELDS:
                errors.append(f"{path}.{key}: forbidden gameplay/integration field")
            errors.extend(_find_forbidden_fields(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_forbidden_fields(child, f"{path}[{index}]"))
    return errors


def validate(data: object) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return ["top-level JSON must be an object"], warnings

    errors.extend(_find_forbidden_fields(data))

    if data.get("dataset_year") != 2026:
        errors.append("dataset_year must be 2026")
    if not isinstance(data.get("version"), int) or data["version"] < 1:
        errors.append("version must be an integer >= 1")
    if not _nonempty_string(data.get("data_version")):
        errors.append("data_version must be a non-empty string")

    prospects = data.get("prospects")
    if not isinstance(prospects, list) or not prospects:
        errors.append("prospects must be a non-empty array")
        return errors, warnings

    ids: list[str] = []
    record_keys: list[tuple[object, ...]] = []

    for index, prospect in enumerate(prospects):
        label = f"prospects[{index}]"
        if not isinstance(prospect, dict):
            errors.append(f"{label}: must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - set(prospect))
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
            continue

        prospect_id = prospect["id"]
        if not _nonempty_string(prospect_id) or not ID_PATTERN.fullmatch(prospect_id):
            errors.append(f"{label}.id: invalid stable ID")
        else:
            ids.append(prospect_id)

        if not _nonempty_string(prospect["display_name"]):
            errors.append(f"{label}.display_name: empty")
        if not _nonempty_string(prospect["school_name"]):
            errors.append(f"{label}.school_name: empty")

        if prospect["grade"] not in {1, 2, 3}:
            errors.append(f"{label}.grade: invalid grade {prospect['grade']!r}")
        if prospect["position"] not in VALID_POSITIONS:
            errors.append(f"{label}.position: invalid position {prospect['position']!r}")
        if prospect["throws"] not in VALID_THROWS:
            errors.append(f"{label}.throws: invalid handedness {prospect['throws']!r}")
        if prospect["bats"] not in VALID_BATS:
            errors.append(f"{label}.bats: invalid handedness {prospect['bats']!r}")
        if prospect["is_featured"] is not True:
            errors.append(f"{label}.is_featured: must be true")

        height = prospect.get("height_cm")
        if height is not None and (not isinstance(height, int) or not 130 <= height <= 220):
            errors.append(f"{label}.height_cm: impossible/out-of-range value")
        weight = prospect.get("weight_kg")
        if weight is not None and (not isinstance(weight, int) or not 35 <= weight <= 160):
            errors.append(f"{label}.weight_kg: impossible/out-of-range value")

        sources = prospect["sources"]
        if not isinstance(sources, list) or not sources:
            errors.append(f"{label}.sources: at least one provenance source is required")
        else:
            for source_index, source in enumerate(sources):
                for source_error in _valid_source(source):
                    errors.append(f"{label}.sources[{source_index}]: {source_error}")

        record_keys.append(
            (
                prospect.get("display_name"),
                prospect.get("school_name"),
                prospect.get("grade"),
                prospect.get("position"),
            )
        )

    duplicate_ids = [value for value, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"duplicate IDs: {', '.join(sorted(duplicate_ids))}")

    duplicate_records = [value for value, count in Counter(record_keys).items() if count > 1]
    if duplicate_records:
        formatted = "; ".join(" / ".join(map(str, value)) for value in duplicate_records)
        errors.append(f"duplicate records: {formatted}")

    for index, prospect in enumerate(prospects):
        if isinstance(prospect, dict):
            if prospect.get("throws") is None:
                warnings.append(f"prospects[{index}].throws: unknown/null")
            if prospect.get("bats") is None:
                warnings.append(f"prospects[{index}].bats: unknown/null")

    return errors, warnings


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: unable to parse {path}: {exc}")
        return 1

    errors, warnings = validate(data)

    prospects = data.get("prospects", []) if isinstance(data, dict) else []
    print(f"Dataset: {path}")
    print(f"Prospects: {len(prospects) if isinstance(prospects, list) else 0}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        print("DATA_VALIDATION=FAIL")
        return 1

    print("DUPLICATE_ID=0")
    print("REQUIRED_FIELD_ERRORS=0")
    print("SOURCE_PROVENANCE=PASS")
    print("DATA_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
