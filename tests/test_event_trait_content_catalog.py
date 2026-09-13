from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from src.content_catalog import ContentValidationError, load_content_catalog, validate_default_content


class EventTraitContentCatalogTests(unittest.TestCase):
    def test_default_catalog_imports_all_source_content(self):
        catalog = validate_default_content()
        self.assertEqual(len(catalog.events), 50)
        self.assertEqual(sum(len(event["choices"]) for event in catalog.events), 146)
        self.assertEqual(len(catalog.traits), 18)
        self.assertEqual(sum(trait["polarity"] == "positive" for trait in catalog.traits), 11)
        self.assertEqual(sum(trait["polarity"] == "negative" for trait in catalog.traits), 7)
        self.assertTrue(all(event["rarity"] == "common" for event in catalog.events))
        self.assertTrue(all(trait["rarity"] == "common" for trait in catalog.traits))

    def test_all_event_and_trait_display_text_is_bilingual(self):
        catalog = validate_default_content()
        for event in catalog.events:
            for field in ("name_ko", "name_en", "description_ko", "description_en"):
                self.assertTrue(str(event[field]).strip(), (event["id"], field))
            for choice in event["choices"]:
                for field in ("label_ko", "label_en", "description_ko", "description_en"):
                    self.assertTrue(str(choice[field]).strip(), (event["id"], choice["id"], field))
        for trait in catalog.traits:
            for field in ("name_ko", "name_en", "description_ko", "description_en"):
                self.assertTrue(str(trait[field]).strip(), (trait["id"], field))

    def test_effect_row_count_and_permanent_rating_targets_match_source_contract(self):
        catalog = validate_default_content()
        effect_rows = 0
        permanent = 0
        positive = 0
        negative = 0
        for event in catalog.events:
            for choice in event["choices"]:
                effect_rows += len(choice["effects"]) + len(choice["trait_requests"]) + len(choice["negative_trait_risks"])
                permanent += sum(effect["type"] == "permanent_rating_delta" for effect in choice["effects"])
                positive += len(choice["trait_requests"])
                negative += len(choice["negative_trait_risks"])
        self.assertEqual(effect_rows, 400)
        self.assertEqual(permanent, 239)
        self.assertEqual(positive, 16)
        self.assertEqual(negative, 20)

    def _payloads(self):
        root = Path(__file__).resolve().parents[1]
        events = json.loads((root / "data/events/normal_events.json").read_text(encoding="utf-8"))
        traits = json.loads((root / "data/traits/traits.json").read_text(encoding="utf-8"))
        return events, traits

    def _assert_invalid(self, mutate, expected):
        event_payload, trait_payload = self._payloads()
        mutate(event_payload, trait_payload)
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "events.json"
            trait_path = Path(tmp) / "traits.json"
            event_path.write_text(json.dumps(event_payload, ensure_ascii=False), encoding="utf-8")
            trait_path.write_text(json.dumps(trait_payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ContentValidationError, expected):
                load_content_catalog(event_path, trait_path)

    def test_duplicate_event_id_is_rejected(self):
        self._assert_invalid(
            lambda events, traits: events["events"].append(copy.deepcopy(events["events"][0])),
            "duplicate EVENT id",
        )

    def test_duplicate_trait_id_is_rejected(self):
        self._assert_invalid(
            lambda events, traits: traits["traits"].append(copy.deepcopy(traits["traits"][0])),
            "duplicate Trait id",
        )

    def test_missing_bilingual_name_is_rejected(self):
        self._assert_invalid(
            lambda events, traits: events["events"][0].__setitem__("name_en", ""),
            "missing non-empty name_en",
        )

    def test_invalid_rarity_and_polarity_are_rejected(self):
        self._assert_invalid(
            lambda events, traits: events["events"][0].__setitem__("rarity", "mythic"),
            "invalid rarity",
        )
        self._assert_invalid(
            lambda events, traits: traits["traits"][0].__setitem__("polarity", "neutral"),
            "invalid polarity",
        )

    def test_unknown_rating_target_and_effect_type_are_rejected(self):
        def bad_rating(events, traits):
            for event in events["events"]:
                for choice in event["choices"]:
                    for effect in choice["effects"]:
                        if effect["type"] == "permanent_rating_delta":
                            effect["target"] = "vision"
                            return
        self._assert_invalid(bad_rating, "unknown rating target")
        self._assert_invalid(
            lambda events, traits: events["events"][0]["choices"][0]["effects"][0].__setitem__("type", "magic_buff"),
            "unknown effect type",
        )

    def test_broken_trait_reference_is_rejected(self):
        def mutate(events, traits):
            target = next(
                choice for event in events["events"] for choice in event["choices"]
                if choice["trait_requests"]
            )
            target["trait_requests"][0]["trait_id"] = "missing_trait"
        self._assert_invalid(mutate, "broken EVENT -> Trait reference")

    def test_conflict_self_reference_is_rejected(self):
        self._assert_invalid(
            lambda events, traits: traits["traits"][0].__setitem__("conflicts", [traits["traits"][0]["id"]]),
            "conflict self-reference",
        )

    def test_upgrade_cycle_is_rejected(self):
        def mutate(events, traits):
            a, b = traits["traits"][0], traits["traits"][1]
            a["upgrades_to"] = [b["id"]]
            b["upgrades_to"] = [a["id"]]
        self._assert_invalid(mutate, "upgrade cycle")

    def test_missing_choice_and_duplicate_choice_id_are_rejected(self):
        self._assert_invalid(
            lambda events, traits: events["events"][0].__setitem__("choices", []),
            "at least one choice",
        )
        def duplicate(events, traits):
            event = events["events"][0]
            event["choices"].append(copy.deepcopy(event["choices"][0]))
        self._assert_invalid(duplicate, "duplicate choice id")


if __name__ == "__main__":
    unittest.main()
