"""Data-driven EVENT/Trait content catalog loader for 04 Events & Story.

This module validates content structure only. It does not mutate Player state,
apply EVENT effects, award Traits, or consume gameplay RNG.

EVENT = interactive player decision.
CAREER = automatic factual timeline record (separate domain).
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


CONTENT_ROOT = Path(__file__).resolve().parents[1] / "data"
DEFAULT_EVENT_CATALOG = CONTENT_ROOT / "events" / "normal_events.json"
DEFAULT_TRAIT_CATALOG = CONTENT_ROOT / "traits" / "traits.json"

RARITIES = frozenset({"common", "rare", "epic", "legendary"})
POLARITIES = frozenset({"positive", "negative"})
SUPPORT_STATUSES = frozenset({"supported", "mappable", "new_contract_required", "unsupported"})
RATING_TARGETS = frozenset({
    "contact", "power", "discipline", "speed", "defense",
    "throwing", "stamina", "durability", "mentality",
})
EVENT_EFFECT_TYPES = frozenset({
    "permanent_rating_delta",
    "temporary_state_modifier",
    "form_modifier",
    "fatigue_modifier",
    "fatigue_delta",
})
TRAIT_EFFECT_TYPES = frozenset({
    "effective_rating_modifier",
    "decision_modifier",
    "variance_modifier",
    "development_context_modifier",
    "legacy_runtime_hook",
})
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class ContentValidationError(ValueError):
    """Raised when EVENT/Trait content data violates the catalog contract."""


@dataclass(frozen=True)
class ContentCatalog:
    events: tuple[Mapping[str, Any], ...]
    traits: tuple[Mapping[str, Any], ...]

    @property
    def event_by_id(self) -> dict[str, Mapping[str, Any]]:
        return {str(item["id"]): item for item in self.events}

    @property
    def trait_by_id(self) -> dict[str, Mapping[str, Any]]:
        return {str(item["id"]): item for item in self.traits}


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContentValidationError(f"cannot load content file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContentValidationError(f"top-level content must be an object: {path}")
    return payload


def _require_text(obj: Mapping[str, Any], field: str, where: str) -> str:
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContentValidationError(f"{where}: missing non-empty {field}")
    return value


def _require_id(obj: Mapping[str, Any], field: str, where: str) -> str:
    value = _require_text(obj, field, where)
    if not ID_RE.fullmatch(value):
        raise ContentValidationError(f"{where}: {field} must be stable snake_case: {value}")
    return value


def _validate_support_status(value: Any, where: str) -> None:
    if value is None:
        return
    if value not in SUPPORT_STATUSES:
        raise ContentValidationError(f"{where}: invalid support_status {value!r}")


def _validate_event_effect(effect: Mapping[str, Any], where: str) -> None:
    effect_type = _require_text(effect, "type", where)
    if effect_type not in EVENT_EFFECT_TYPES:
        raise ContentValidationError(f"{where}: unknown effect type {effect_type}")
    _validate_support_status(effect.get("support_status"), where)
    if effect_type == "permanent_rating_delta":
        target = _require_text(effect, "target", where)
        if target not in RATING_TARGETS:
            raise ContentValidationError(f"{where}: unknown rating target {target}")
        amount = effect.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ContentValidationError(f"{where}: permanent rating amount must be int")
    elif effect_type == "temporary_state_modifier":
        target = _require_text(effect, "target", where)
        if target not in {"temp_stability", "temp_variance"}:
            raise ContentValidationError(f"{where}: unknown temporary state target {target}")
        _require_text(effect, "magnitude", where)
    elif effect_type == "form_modifier":
        if _require_text(effect, "target", where) != "player":
            raise ContentValidationError(f"{where}: form target must be player")
        _require_text(effect, "magnitude", where)
    elif effect_type in {"fatigue_modifier", "fatigue_delta"}:
        if _require_text(effect, "target", where) != "player":
            raise ContentValidationError(f"{where}: fatigue target must be player")


def _validate_trait_effect(effect: Mapping[str, Any], where: str) -> None:
    effect_type = _require_text(effect, "type", where)
    if effect_type not in TRAIT_EFFECT_TYPES:
        raise ContentValidationError(f"{where}: unknown Trait effect type {effect_type}")
    _validate_support_status(effect.get("support_status"), where)
    target = _require_text(effect, "target", where)
    if effect_type == "effective_rating_modifier" and target not in RATING_TARGETS:
        raise ContentValidationError(f"{where}: unknown Trait rating target {target}")


def _validate_traits(raw_traits: Sequence[Any]) -> tuple[Mapping[str, Any], ...]:
    seen: set[str] = set()
    traits: list[Mapping[str, Any]] = []
    for index, item in enumerate(raw_traits):
        where = f"traits[{index}]"
        if not isinstance(item, dict):
            raise ContentValidationError(f"{where}: Trait must be an object")
        trait_id = _require_id(item, "id", where)
        if trait_id in seen:
            raise ContentValidationError(f"{where}: duplicate Trait id {trait_id}")
        seen.add(trait_id)
        for field in ("name_ko", "name_en", "description_ko", "description_en"):
            _require_text(item, field, where)
        rarity = _require_text(item, "rarity", where)
        if rarity not in RARITIES:
            raise ContentValidationError(f"{where}: invalid rarity {rarity}")
        polarity = _require_text(item, "polarity", where)
        if polarity not in POLARITIES:
            raise ContentValidationError(f"{where}: invalid polarity {polarity}")
        trigger = item.get("trigger")
        if not isinstance(trigger, dict):
            raise ContentValidationError(f"{where}: trigger must be an object")
        _require_text(trigger, "type", f"{where}.trigger")
        _validate_support_status(trigger.get("support_status"), f"{where}.trigger")
        effects = item.get("effects")
        if not isinstance(effects, list) or not effects:
            raise ContentValidationError(f"{where}: Trait must define at least one effect")
        for effect_index, effect in enumerate(effects):
            if not isinstance(effect, dict):
                raise ContentValidationError(f"{where}.effects[{effect_index}]: effect must be an object")
            _validate_trait_effect(effect, f"{where}.effects[{effect_index}]")
        conflicts = item.get("conflicts", [])
        if not isinstance(conflicts, list):
            raise ContentValidationError(f"{where}: conflicts must be a list")
        if trait_id in conflicts:
            raise ContentValidationError(f"{where}: conflict self-reference {trait_id}")
        upgrades_to = item.get("upgrades_to", [])
        if not isinstance(upgrades_to, list):
            raise ContentValidationError(f"{where}: upgrades_to must be a list")
        traits.append(item)

    by_id = {str(item["id"]): item for item in traits}
    for trait in traits:
        trait_id = str(trait["id"])
        for conflict in trait.get("conflicts", []):
            if conflict not in by_id:
                external = set(trait.get("external_conflicts", []))
                if conflict not in external:
                    raise ContentValidationError(f"Trait {trait_id}: unknown conflict reference {conflict}")
        for target in trait.get("upgrades_to", []):
            if target not in by_id:
                raise ContentValidationError(f"Trait {trait_id}: unknown upgrade target {target}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(trait_id: str) -> None:
        if trait_id in visiting:
            raise ContentValidationError(f"Trait upgrade cycle detected at {trait_id}")
        if trait_id in visited:
            return
        visiting.add(trait_id)
        for target in by_id[trait_id].get("upgrades_to", []):
            visit(str(target))
        visiting.remove(trait_id)
        visited.add(trait_id)

    for trait_id in by_id:
        visit(trait_id)
    return tuple(traits)


def _validate_events(raw_events: Sequence[Any], trait_ids: set[str]) -> tuple[Mapping[str, Any], ...]:
    seen: set[str] = set()
    events: list[Mapping[str, Any]] = []
    for index, item in enumerate(raw_events):
        where = f"events[{index}]"
        if not isinstance(item, dict):
            raise ContentValidationError(f"{where}: EVENT must be an object")
        event_id = _require_id(item, "id", where)
        if event_id in seen:
            raise ContentValidationError(f"{where}: duplicate EVENT id {event_id}")
        seen.add(event_id)
        rarity = _require_text(item, "rarity", where)
        if rarity not in RARITIES:
            raise ContentValidationError(f"{where}: invalid rarity {rarity}")
        for field in ("name_ko", "name_en", "description_ko", "description_en", "category", "trigger_type"):
            _require_text(item, field, where)
        choices = item.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ContentValidationError(f"{where}: EVENT must contain at least one choice")
        choice_ids: set[str] = set()
        for choice_index, choice in enumerate(choices):
            cwhere = f"{where}.choices[{choice_index}]"
            if not isinstance(choice, dict):
                raise ContentValidationError(f"{cwhere}: choice must be an object")
            choice_id = _require_id(choice, "id", cwhere)
            if choice_id in choice_ids:
                raise ContentValidationError(f"{cwhere}: duplicate choice id {choice_id}")
            choice_ids.add(choice_id)
            for field in ("label_ko", "label_en", "description_ko", "description_en"):
                _require_text(choice, field, cwhere)
            effects = choice.get("effects", [])
            if not isinstance(effects, list):
                raise ContentValidationError(f"{cwhere}: effects must be a list")
            for effect_index, effect in enumerate(effects):
                if not isinstance(effect, dict):
                    raise ContentValidationError(f"{cwhere}.effects[{effect_index}]: effect must be an object")
                _validate_event_effect(effect, f"{cwhere}.effects[{effect_index}]")
            for field in ("trait_requests", "negative_trait_risks"):
                refs = choice.get(field, [])
                if not isinstance(refs, list):
                    raise ContentValidationError(f"{cwhere}: {field} must be a list")
                for ref_index, ref in enumerate(refs):
                    rwhere = f"{cwhere}.{field}[{ref_index}]"
                    if not isinstance(ref, dict):
                        raise ContentValidationError(f"{rwhere}: Trait request must be an object")
                    trait_id = _require_id(ref, "trait_id", rwhere)
                    if trait_id not in trait_ids:
                        raise ContentValidationError(f"{rwhere}: broken EVENT -> Trait reference {trait_id}")
                    rarity = _require_text(ref, "rarity", rwhere)
                    if rarity not in RARITIES:
                        raise ContentValidationError(f"{rwhere}: invalid rarity {rarity}")
        events.append(item)
    return tuple(events)


def load_content_catalog(
    event_path: Path | str = DEFAULT_EVENT_CATALOG,
    trait_path: Path | str = DEFAULT_TRAIT_CATALOG,
) -> ContentCatalog:
    event_payload = _read_json(Path(event_path))
    trait_payload = _read_json(Path(trait_path))
    if event_payload.get("schema_version") != 1 or trait_payload.get("schema_version") != 1:
        raise ContentValidationError("unsupported EVENT/Trait content schema_version")
    raw_traits = trait_payload.get("traits")
    raw_events = event_payload.get("events")
    if not isinstance(raw_traits, list):
        raise ContentValidationError("traits catalog must contain a traits list")
    if not isinstance(raw_events, list):
        raise ContentValidationError("EVENT catalog must contain an events list")
    traits = _validate_traits(raw_traits)
    events = _validate_events(raw_events, {str(item["id"]) for item in traits})
    return ContentCatalog(events=events, traits=traits)


def validate_default_content() -> ContentCatalog:
    """Load and fully validate the checked-in 04 content catalogs."""
    return load_content_catalog()
