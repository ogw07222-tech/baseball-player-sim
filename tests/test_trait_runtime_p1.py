import copy
import unittest
from pathlib import Path

from src import config
from src.hitting import parameters as P
from src.hitting.model import HittingEngine, Pitch
from src.player import Player
from src.rng import RNG
from src.simulation import (
    PitcherProfile, _common_trait_pitch_modifier, _condition_modifiers,
    _hitter_snapshot, _pitcher_snapshot, _trait_contact_modifier,
    simulate_plate_appearance_outcome,
)
from src.trait_runtime import TraitContext, TraitEffectUnits, evaluate_trait_effect_units, load_trait_catalog, parse_trait_catalog
from src.traits import TRAIT_CATALOG, generate_random_traits, trait_from_key, traits_conflict


def ctx(**overrides) -> TraitContext:
    values = dict(balls=0, strikes=0, pitch_type="fastball", pitch_zone="middle", pitch_is_strike=True, pitcher_handedness="R", hitter_approach="balanced", player_form="normal")
    values.update(overrides)
    return TraitContext(**values)


def minimal_payload() -> dict[str, object]:
    return {"schema_version": 1, "catalog_id": "test", "default_locale": "ko", "traits": [{
        "id": "test_trait", "rarity": "common", "polarity": "positive", "category": "test",
        "name_ko": "테스트", "name_en": "Test", "description_ko": "테스트 설명", "description_en": "Test description",
        "tags": ["batting"], "conditions": [{"type": "strikes_equals", "value": 2}],
        "effects": [{"type": "contact_modifier", "units": 1.0}], "conflicts": [], "upgrades_to": [],
        "enabled": True, "implementation_status": "SUPPORTED_NOW",
    }]}


def neutral_player() -> Player:
    return Player.random("Trait Test", RNG(901), trait_count=0)


def legacy_reference(player: Player, pitcher: PitcherProfile, rng: RNG):
    condition_contact, condition_power = _condition_modifiers(player)
    def modifier(pitch: Pitch, strikes: int) -> tuple[float, float]:
        trait = _trait_contact_modifier(player, pitcher, pitch.pitch_type, pitch.zone, pitch.velocity_quality > .35, strikes, False)
        return condition_contact + trait, condition_power + trait * .25
    return HittingEngine(_hitter_snapshot(player), _pitcher_snapshot(pitcher), 100.0, rng, modifier).simulate_plate_appearance()


class TraitCatalogP1Tests(unittest.TestCase):
    def test_loader_success_and_batch_a_count(self):
        catalog = load_trait_catalog()
        self.assertEqual((catalog.schema_version, catalog.default_locale, len(catalog.definitions)), (1, "ko", 11))
        self.assertTrue(all(d.rarity == "common" and d.name_ko and d.name_en for d in catalog.definitions))

    def test_duplicate_id_fails(self):
        payload = minimal_payload(); payload["traits"].append(copy.deepcopy(payload["traits"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate trait id"): parse_trait_catalog(payload)

    def test_unknown_effect_fails(self):
        payload = minimal_payload(); payload["traits"][0]["effects"][0]["type"] = "mystery_effect"
        with self.assertRaisesRegex(ValueError, "unknown effect type"): parse_trait_catalog(payload)

    def test_unknown_condition_fails(self):
        payload = minimal_payload(); payload["traits"][0]["conditions"][0]["type"] = "mystery_condition"
        with self.assertRaisesRegex(ValueError, "unknown condition type"): parse_trait_catalog(payload)

    def test_bilingual_names_are_required(self):
        for field in ("name_ko", "name_en"):
            payload = minimal_payload(); payload["traits"][0][field] = ""
            with self.assertRaisesRegex(ValueError, field): parse_trait_catalog(payload)

    def test_invalid_conflict_reference_fails(self):
        payload = minimal_payload(); payload["traits"][0]["conflicts"] = ["not_loaded"]
        with self.assertRaisesRegex(ValueError, "unknown conflict reference"): parse_trait_catalog(payload)

    def test_self_conflict_fails(self):
        payload = minimal_payload(); payload["traits"][0]["conflicts"] = ["test_trait"]
        with self.assertRaisesRegex(ValueError, "cannot conflict with itself"): parse_trait_catalog(payload)

    def test_invalid_upgrade_and_duplicate_upgrade_fail(self):
        payload = minimal_payload(); payload["traits"][0]["upgrades_to"] = ["not_loaded"]
        with self.assertRaisesRegex(ValueError, "unknown upgrade reference"): parse_trait_catalog(payload)
        payload = minimal_payload(); second = copy.deepcopy(payload["traits"][0]); second["id"] = "upgrade_trait"; payload["traits"].append(second)
        payload["traits"][0]["upgrades_to"] = ["upgrade_trait", "upgrade_trait"]
        with self.assertRaisesRegex(ValueError, "cannot contain duplicates"): parse_trait_catalog(payload)

    def test_unsupported_field_type_fails(self):
        payload = minimal_payload(); payload["traits"][0]["enabled"] = "yes"
        with self.assertRaisesRegex(ValueError, "enabled must be boolean"): parse_trait_catalog(payload)

    def test_condition_false_is_zero_and_true_applies(self):
        self.assertEqual(evaluate_trait_effect_units(["two_strike_compact"], ctx(strikes=1)), TraitEffectUnits())
        true = evaluate_trait_effect_units(["two_strike_compact"], ctx(strikes=2))
        self.assertEqual((true.contact_modifier, true.foul_survival_modifier), (1.0, 1.0))

    def test_positive_negative_and_conflict_metadata(self):
        catalog = load_trait_catalog()
        self.assertEqual(catalog.by_id["full_count_filter"].polarity, "positive")
        self.assertEqual(catalog.by_id["full_count_chaser"].polarity, "negative")
        self.assertTrue(traits_conflict(trait_from_key("full_count_filter"), trait_from_key("full_count_chaser")))

    def test_multiple_traits_compose_and_order_is_independent(self):
        context = ctx(balls=3, strikes=2, pitch_type="breaking")
        ids = ["full_count_filter", "breaking_ball_track", "two_strike_compact"]
        a = evaluate_trait_effect_units(ids, context); b = evaluate_trait_effect_units(reversed(ids), context)
        self.assertEqual(a, b)
        self.assertEqual((a.contact_modifier, a.pitch_selection_modifier, a.foul_survival_modifier), (2.0, 2.0, 1.0))

    def test_legacy_and_common_save_ids_round_trip(self):
        player = neutral_player(); player.traits = [trait_from_key("fastball_specialist"), trait_from_key("two_strike_compact")]
        loaded = Player.from_dict(player.as_dict())
        self.assertEqual([t.key for t in loaded.traits], ["fastball_specialist", "two_strike_compact"])
        self.assertEqual(loaded.traits[1].name, "생존 스윙")

    def test_random_generation_remains_legacy_catalog_only(self):
        legacy_ids = {trait.key for trait in TRAIT_CATALOG}; common_ids = set(load_trait_catalog().by_id)
        self.assertTrue(legacy_ids.isdisjoint(common_ids))
        for seed in range(200): self.assertTrue(all(t.key in legacy_ids for t in generate_random_traits(RNG(seed))))


class BatchATargetedBehaviorTests(unittest.TestCase):
    def test_all_batch_a_targeted_conditions(self):
        cases = [
            ("two_strike_compact", ctx(strikes=2), "contact_modifier", 1.0),
            ("full_count_filter", ctx(balls=3, strikes=2), "pitch_selection_modifier", 1.0),
            ("full_count_chaser", ctx(balls=3, strikes=2, pitch_is_strike=False), "chase_modifier", 1.0),
            ("fastball_timing_read", ctx(pitch_type="fastball"), "power_modifier", 1.0),
            ("breaking_ball_track", ctx(pitch_type="breaking"), "contact_modifier", 1.0),
            ("low_zone_contact", ctx(pitch_zone="low", pitch_is_strike=True), "foul_survival_modifier", 1.0),
            ("high_zone_level_swing", ctx(pitch_zone="high", pitch_is_strike=True), "power_modifier", 1.0),
            ("high_pitch_overreach", ctx(pitch_zone="high", pitch_is_strike=False), "chase_modifier", 1.0),
            ("lefty_release_read", ctx(pitcher_handedness="L"), "contact_modifier", 1.0),
            ("hot_streak_discipline", ctx(player_form="hot"), "pitch_selection_modifier", 1.0),
            ("slump_tinkerer", ctx(player_form="slump"), "contact_modifier", -1.0),
        ]
        for trait_id, context, field, expected in cases:
            with self.subTest(trait_id=trait_id): self.assertEqual(getattr(evaluate_trait_effect_units([trait_id], context), field), expected)

    def test_batch_a_conditions_do_not_leak_outside_context(self):
        false_contexts = {
            "two_strike_compact": ctx(strikes=1), "full_count_filter": ctx(balls=2, strikes=2), "full_count_chaser": ctx(balls=3, strikes=1),
            "fastball_timing_read": ctx(pitch_type="breaking"), "breaking_ball_track": ctx(pitch_type="fastball"),
            "low_zone_contact": ctx(pitch_zone="low", pitch_is_strike=False), "high_zone_level_swing": ctx(pitch_zone="high", pitch_is_strike=False),
            "high_pitch_overreach": ctx(pitch_zone="high", pitch_is_strike=True), "lefty_release_read": ctx(pitcher_handedness="R"),
            "hot_streak_discipline": ctx(player_form="normal"), "slump_tinkerer": ctx(player_form="normal"),
        }
        for trait_id, context in false_contexts.items():
            with self.subTest(trait_id=trait_id): self.assertEqual(evaluate_trait_effect_units([trait_id], context), TraitEffectUnits())

    def test_generic_effect_units_reach_real_gameplay_hook(self):
        pitch = Pitch(True, "low", "fastball", .5, .0, .0, .2)
        m = _common_trait_pitch_modifier(("two_strike_compact", "fastball_timing_read", "low_zone_contact"), "normal", "balanced", "R", pitch, 0, 2)
        self.assertEqual(m.contact_delta, 3.0 * config.TRAIT_EFFECT)
        self.assertEqual(m.power_delta, config.TRAIT_EFFECT * .25)
        self.assertAlmostEqual(m.foul_survival_delta, 2.0 * config.TRAIT_EFFECT * P.TWO_STRIKE_FOUL_DISCIPLINE_WEIGHT)

    def test_pitch_selection_and_chase_handlers_have_expected_direction(self):
        strike = Pitch(True, "middle", "fastball", 0, 0, 0, 0); ball = Pitch(False, "middle", "fastball", 0, 0, 0, 0)
        good_strike = _common_trait_pitch_modifier(("full_count_filter",), "normal", "balanced", "R", strike, 3, 2)
        good_ball = _common_trait_pitch_modifier(("full_count_filter",), "normal", "balanced", "R", ball, 3, 2)
        bad_ball = _common_trait_pitch_modifier(("full_count_chaser",), "normal", "balanced", "R", ball, 3, 2)
        self.assertGreater(good_strike.zone_swing_delta, 0.0); self.assertLess(good_ball.chase_delta, 0.0); self.assertGreater(bad_ball.chase_delta, 0.0)


class CommonTraitRegressionTests(unittest.TestCase):
    def test_non_trait_player_is_exact_legacy_path(self):
        player = neutral_player(); pitcher = PitcherProfile(103.0, 98.0, 105.0, "R")
        for seed in range(1, 300):
            new_rng = RNG(seed); old_rng = RNG(seed)
            self.assertEqual(simulate_plate_appearance_outcome(player, pitcher, new_rng), legacy_reference(player, pitcher, old_rng))
            self.assertEqual(new_rng.get_state(), old_rng.get_state())

    def test_legacy_trait_player_is_exact_legacy_path(self):
        player = neutral_player(); player.traits = [trait_from_key("fastball_specialist")]; pitcher = PitcherProfile(100.0, 100.0, 100.0, "L")
        for seed in range(1, 200):
            new_rng = RNG(seed); old_rng = RNG(seed)
            self.assertEqual(simulate_plate_appearance_outcome(player, pitcher, new_rng), legacy_reference(player, pitcher, old_rng))
            self.assertEqual(new_rng.get_state(), old_rng.get_state())

    def test_common_trait_same_seed_is_deterministic(self):
        player = neutral_player(); player.traits = [trait_from_key("two_strike_compact"), trait_from_key("fastball_timing_read")]
        pitcher = PitcherProfile(100.0, 100.0, 100.0, "R")
        for seed in range(1, 150):
            a_rng = RNG(seed); b_rng = RNG(seed)
            self.assertEqual(simulate_plate_appearance_outcome(player, pitcher, a_rng), simulate_plate_appearance_outcome(player, pitcher, b_rng))
            self.assertEqual(a_rng.get_state(), b_rng.get_state())

    def test_gameplay_code_has_no_common_trait_id_branches(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "src" / "simulation.py").read_text(encoding="utf-8") + (root / "src" / "hitting" / "trait_engine.py").read_text(encoding="utf-8")
        for trait_id in load_trait_catalog().by_id:
            self.assertNotIn(f'has_trait(p.traits, "{trait_id}")', text)
            self.assertNotIn(f'== "{trait_id}"', text)


if __name__ == "__main__": unittest.main()
