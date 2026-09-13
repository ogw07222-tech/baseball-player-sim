"""Data-driven Common Trait runtime for gameplay-safe conditional modifiers.

P1 intentionally supports only production-observable PA/player state. Trait data is
parsed once and cached; evaluation is deterministic and consumes no RNG.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Iterable, Mapping

_ALLOWED_RARITIES = frozenset({"common", "rare", "epic", "legendary"})
_ALLOWED_POLARITIES = frozenset({"positive", "negative"})
_ALLOWED_IMPLEMENTATION_STATUSES = frozenset({
    "SUPPORTED_NOW", "MAPPABLE_NOW", "NEW_CONTRACT_REQUIRED", "HOLD_UPSTREAM",
})
_SUPPORTED_CONDITION_TYPES = frozenset({
    "strikes_equals",
    "full_count",
    "pitch_type_equals",
    "pitch_zone_equals",
    "pitch_is_strike",
    "pitcher_handedness_equals",
    "player_form_equals",
    "hitter_approach_equals",
})
_SUPPORTED_EFFECT_TYPES = frozenset({
    "contact_modifier",
    "power_modifier",
    "pitch_selection_modifier",
    "chase_modifier",
    "foul_survival_modifier",
})
_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "traits" / "common_traits.json"
)


@dataclass(frozen=True)
class TraitCondition:
    type: str
    value: object


@dataclass(frozen=True)
class TraitEffect:
    type: str
    units: float


@dataclass(frozen=True)
class TraitDefinition:
    id: str
    rarity: str
    polarity: str
    category: str
    name_ko: str
    name_en: str
    description_ko: str
    description_en: str
    tags: tuple[str, ...]
    conditions: tuple[TraitCondition, ...]
    effects: tuple[TraitEffect, ...]
    conflicts: tuple[str, ...]
    upgrades_to: tuple[str, ...]
    enabled: bool
    implementation_status: str
    implementation_note: str | None = None


@dataclass(frozen=True)
class TraitCatalog:
    schema_version: int
    catalog_id: str
    default_locale: str
    definitions: tuple[TraitDefinition, ...]
    by_id: Mapping[str, TraitDefinition]


@dataclass(frozen=True)
class TraitContext:
    balls: int
    strikes: int
    pitch_type: str
    pitch_zone: str
    pitch_is_strike: bool
    pitcher_handedness: str
    hitter_approach: str
    player_form: str


@dataclass(frozen=True)
class TraitEffectUnits:
    contact_modifier: float = 0.0
    power_modifier: float = 0.0
    pitch_selection_modifier: float = 0.0
    chase_modifier: float = 0.0
    foul_survival_modifier: float = 0.0

    def __add__(self, other: "TraitEffectUnits") -> "TraitEffectUnits":
        return TraitEffectUnits(
            contact_modifier=self.contact_modifier + other.contact_modifier,
            power_modifier=self.power_modifier + other.power_modifier,
            pitch_selection_modifier=(
                self.pitch_selection_modifier + other.pitch_selection_modifier
            ),
            chase_modifier=self.chase_modifier + other.chase_modifier,
            foul_survival_modifier=(
                self.foul_survival_modifier + other.foul_survival_modifier
            ),
        )


def _require_nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _require_string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"{field} must be a list of non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field} cannot contain duplicates")
    return tuple(value)


def _parse_definition(raw: object) -> TraitDefinition:
    if not isinstance(raw, dict):
        raise ValueError("trait definition must be an object")
    allowed_fields = {
        "id", "rarity", "polarity", "category", "name_ko", "name_en",
        "description_ko", "description_en", "tags", "conditions", "effects",
        "conflicts", "upgrades_to", "enabled", "implementation_status",
        "implementation_note",
    }
    unknown = set(raw) - allowed_fields
    if unknown:
        raise ValueError(f"unsupported trait fields: {sorted(unknown)}")

    trait_id = _require_nonempty_string(raw.get("id"), "id")
    if not _ID_RE.fullmatch(trait_id):
        raise ValueError(f"invalid stable trait id: {trait_id}")

    rarity = _require_nonempty_string(raw.get("rarity"), "rarity")
    if rarity not in _ALLOWED_RARITIES:
        raise ValueError(f"invalid rarity: {rarity}")
    polarity = _require_nonempty_string(raw.get("polarity"), "polarity")
    if polarity not in _ALLOWED_POLARITIES:
        raise ValueError(f"invalid polarity: {polarity}")

    category = _require_nonempty_string(raw.get("category"), "category")
    name_ko = _require_nonempty_string(raw.get("name_ko"), "name_ko")
    name_en = _require_nonempty_string(raw.get("name_en"), "name_en")
    description_ko = _require_nonempty_string(raw.get("description_ko"), "description_ko")
    description_en = _require_nonempty_string(raw.get("description_en"), "description_en")
    tags = _require_string_list(raw.get("tags"), "tags")
    conflicts = _require_string_list(raw.get("conflicts"), "conflicts")
    upgrades_to = _require_string_list(raw.get("upgrades_to"), "upgrades_to")
    if trait_id in conflicts:
        raise ValueError(f"trait {trait_id} cannot conflict with itself")
    if trait_id in upgrades_to:
        raise ValueError(f"trait {trait_id} cannot upgrade to itself")

    conditions_raw = raw.get("conditions")
    if not isinstance(conditions_raw, list):
        raise ValueError("conditions must be a list")
    conditions: list[TraitCondition] = []
    for condition in conditions_raw:
        if not isinstance(condition, dict) or set(condition) != {"type", "value"}:
            raise ValueError("condition must contain exactly type and value")
        condition_type = _require_nonempty_string(condition.get("type"), "condition.type")
        if condition_type not in _SUPPORTED_CONDITION_TYPES:
            raise ValueError(f"unknown condition type: {condition_type}")
        value = condition.get("value")
        if condition_type == "strikes_equals":
            if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1, 2}:
                raise ValueError("strikes_equals value must be integer 0..2")
        elif condition_type in {"full_count", "pitch_is_strike"}:
            if not isinstance(value, bool):
                raise ValueError(f"{condition_type} value must be boolean")
        elif condition_type == "pitcher_handedness_equals":
            if value not in {"L", "R"}:
                raise ValueError("pitcher_handedness_equals value must be L or R")
        elif condition_type == "player_form_equals":
            if value not in {"normal", "hot", "slump"}:
                raise ValueError("player_form_equals value must be normal/hot/slump")
        elif condition_type == "hitter_approach_equals":
            if value not in {"balanced", "pull", "opposite"}:
                raise ValueError("hitter_approach_equals value must be balanced/pull/opposite")
        elif not isinstance(value, str) or not value:
            raise ValueError(f"{condition_type} value must be a non-empty string")
        conditions.append(TraitCondition(condition_type, value))

    effects_raw = raw.get("effects")
    if not isinstance(effects_raw, list) or not effects_raw:
        raise ValueError("effects must be a non-empty list")
    effects: list[TraitEffect] = []
    for effect in effects_raw:
        if not isinstance(effect, dict) or set(effect) != {"type", "units"}:
            raise ValueError("effect must contain exactly type and units")
        effect_type = _require_nonempty_string(effect.get("type"), "effect.type")
        if effect_type not in _SUPPORTED_EFFECT_TYPES:
            raise ValueError(f"unknown effect type: {effect_type}")
        units = effect.get("units")
        if isinstance(units, bool) or not isinstance(units, (int, float)):
            raise ValueError("effect.units must be numeric")
        units = float(units)
        if not math.isfinite(units):
            raise ValueError("effect.units must be finite")
        effects.append(TraitEffect(effect_type, units))

    enabled = raw.get("enabled")
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be boolean")
    implementation_status = _require_nonempty_string(raw.get("implementation_status"), "implementation_status")
    if implementation_status not in _ALLOWED_IMPLEMENTATION_STATUSES:
        raise ValueError(f"invalid implementation_status: {implementation_status}")
    note = raw.get("implementation_note")
    if note is not None and (not isinstance(note, str) or not note.strip()):
        raise ValueError("implementation_note must be null or non-empty string")

    return TraitDefinition(
        id=trait_id, rarity=rarity, polarity=polarity, category=category,
        name_ko=name_ko, name_en=name_en,
        description_ko=description_ko, description_en=description_en,
        tags=tags, conditions=tuple(conditions), effects=tuple(effects),
        conflicts=conflicts, upgrades_to=upgrades_to, enabled=enabled,
        implementation_status=implementation_status, implementation_note=note,
    )


def parse_trait_catalog(payload: object) -> TraitCatalog:
    if not isinstance(payload, dict):
        raise ValueError("trait catalog root must be an object")
    if set(payload) != {"schema_version", "catalog_id", "default_locale", "traits"}:
        raise ValueError("trait catalog root has unsupported or missing fields")
    if payload["schema_version"] != 1:
        raise ValueError("unsupported trait catalog schema_version")
    catalog_id = _require_nonempty_string(payload["catalog_id"], "catalog_id")
    default_locale = _require_nonempty_string(payload["default_locale"], "default_locale")
    raw_traits = payload["traits"]
    if not isinstance(raw_traits, list):
        raise ValueError("traits must be a list")

    definitions = tuple(_parse_definition(raw) for raw in raw_traits)
    ids = [definition.id for definition in definitions]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate trait id")

    by_id = {definition.id: definition for definition in definitions}
    known = set(by_id)
    for definition in definitions:
        for conflict in definition.conflicts:
            if conflict not in known:
                raise ValueError(f"unknown conflict reference {conflict} from {definition.id}")
        for upgrade in definition.upgrades_to:
            if upgrade not in known:
                raise ValueError(f"unknown upgrade reference {upgrade} from {definition.id}")

    return TraitCatalog(
        schema_version=1,
        catalog_id=catalog_id,
        default_locale=default_locale,
        definitions=definitions,
        by_id=MappingProxyType(by_id),
    )


@lru_cache(maxsize=1)
def load_trait_catalog() -> TraitCatalog:
    with _DEFAULT_CATALOG_PATH.open("r", encoding="utf-8") as handle:
        return parse_trait_catalog(json.load(handle))


def _condition_matches(condition: TraitCondition, context: TraitContext) -> bool:
    kind = condition.type
    value = condition.value
    if kind == "strikes_equals": return context.strikes == value
    if kind == "full_count": return bool(value) is True and context.balls == 3 and context.strikes == 2
    if kind == "pitch_type_equals": return context.pitch_type == value
    if kind == "pitch_zone_equals": return context.pitch_zone == value
    if kind == "pitch_is_strike": return context.pitch_is_strike is value
    if kind == "pitcher_handedness_equals": return context.pitcher_handedness == value
    if kind == "player_form_equals": return context.player_form == value
    if kind == "hitter_approach_equals": return context.hitter_approach == value
    raise ValueError(f"unknown condition type: {kind}")


def trait_active(definition: TraitDefinition, context: TraitContext) -> bool:
    return (
        definition.enabled
        and definition.implementation_status == "SUPPORTED_NOW"
        and all(_condition_matches(condition, context) for condition in definition.conditions)
    )


def evaluate_trait_effect_units(
    trait_ids: Iterable[str],
    context: TraitContext,
    catalog: TraitCatalog | None = None,
) -> TraitEffectUnits:
    catalog = catalog or load_trait_catalog()
    total = TraitEffectUnits()
    for trait_id in sorted(set(trait_ids)):
        definition = catalog.by_id.get(trait_id)
        if definition is None or not trait_active(definition, context):
            continue
        values = {
            "contact_modifier": 0.0,
            "power_modifier": 0.0,
            "pitch_selection_modifier": 0.0,
            "chase_modifier": 0.0,
            "foul_survival_modifier": 0.0,
        }
        for effect in definition.effects:
            values[effect.type] += effect.units
        total += TraitEffectUnits(**values)
    return total
