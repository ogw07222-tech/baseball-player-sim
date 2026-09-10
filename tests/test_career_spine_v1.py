import tempfile
import unittest
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.career_story import (
    CAREER_ONCE,
    record_observational_event,
    render_career_news,
)
from src.persistence import load_game, save_game
from src.player import Player
from src.rng import RNG


class CareerSpineV1Tests(unittest.TestCase):
    def make_engine(self, seed: int = 400) -> CareerEngine:
        rng = RNG(seed)
        player = Player.random("Spine", rng, "SS", "R/R", 1)
        return CareerEngine(player, rng)

    def test_draft_result_and_pro_entry_are_recorded_exactly_once(self):
        engine = self.make_engine(401)
        result = engine.evaluate_draft()
        expected = "draft_selected" if result.round is not None else "draft_undrafted_entry"
        ids = [entry["event_id"] for entry in engine.player.career_history]
        self.assertEqual(ids.count(expected), 1)
        self.assertEqual(ids.count("pro_entry"), 1)

        engine.evaluate_draft()
        ids = [entry["event_id"] for entry in engine.player.career_history]
        self.assertEqual(ids.count(expected), 1)
        self.assertEqual(ids.count("pro_entry"), 1)

    def test_observational_record_has_zero_gameplay_mutation_and_no_rng_use(self):
        engine = self.make_engine(402)
        player = engine.player
        player.team = "테스트"
        before_stats = player.stats.as_dict()
        before_fatigue = player.fatigue
        before_injury = player.injury
        before_form = (player.form, player.form_games_remaining)
        before_traits = [trait.key for trait in player.traits]
        before_modifiers = dict(player.season_modifiers)
        before_rng = engine.rng.get_state()

        entry = record_observational_event(
            player,
            event_id="pro_entry",
            year=engine.year,
            career_stage="PRO_ENTRY",
            kind="entry",
            importance="major",
            dedupe_key="test:pro_entry",
            trigger="test authoritative state",
            eligibility="test",
            repeat_contract=CAREER_ONCE,
            facts={"team": player.team, "status": "test"},
        )

        self.assertIsNotNone(entry)
        self.assertEqual(player.stats.as_dict(), before_stats)
        self.assertEqual(player.fatigue, before_fatigue)
        self.assertIs(player.injury, before_injury)
        self.assertEqual((player.form, player.form_games_remaining), before_form)
        self.assertEqual([trait.key for trait in player.traits], before_traits)
        self.assertEqual(player.season_modifiers, before_modifiers)
        self.assertEqual(engine.rng.get_state(), before_rng)
        self.assertEqual(entry["effects"], [])

    def test_callup_and_demotion_mirror_authoritative_transitions_without_duplicates(self):
        engine = self.make_engine(403)
        engine.evaluate_draft()
        session = engine.start_pro_season()

        for name in (
            "contact",
            "power",
            "discipline",
            "speed",
            "defense",
            "throwing",
            "stamina",
            "durability",
            "mentality",
        ):
            setattr(engine.player.stats, name, 250)
        session.current_level = "FARM"
        engine.player.roster_level = "FARM"
        session.games_completed = 10
        engine.rng.gauss = lambda *_args: 0.0
        engine.rng.random = lambda: 0.0

        engine._reconsider_roster(session)
        self.assertEqual(session.current_level, "FIRST")
        self.assertEqual(engine.player.roster_level, "FIRST")
        callups = [
            entry
            for entry in engine.player.career_history
            if entry["event_id"] == "first_team_callup"
        ]
        self.assertEqual(len(callups), 1)
        self.assertEqual(callups[0]["facts"]["from_level"], "FARM")
        self.assertEqual(callups[0]["facts"]["to_level"], "FIRST")

        engine._record_roster_transition(session, "FARM", "FIRST")
        callups = [
            entry
            for entry in engine.player.career_history
            if entry["event_id"] == "first_team_callup"
        ]
        self.assertEqual(len(callups), 1)

        for name in (
            "contact",
            "power",
            "discipline",
            "speed",
            "defense",
            "throwing",
            "stamina",
            "durability",
            "mentality",
        ):
            setattr(engine.player.stats, name, 1)
        session.games_completed = 20
        session.record.first_team.PA = 30
        session.current_level = "FIRST"
        engine.player.roster_level = "FIRST"

        engine._reconsider_roster(session)
        self.assertEqual(session.current_level, "FARM")
        self.assertEqual(engine.player.roster_level, "FARM")
        demotions = [
            entry
            for entry in engine.player.career_history
            if entry["event_id"] == "farm_demotion"
        ]
        self.assertEqual(len(demotions), 1)
        self.assertEqual(demotions[0]["facts"]["from_level"], "FIRST")
        self.assertEqual(demotions[0]["facts"]["to_level"], "FARM")

    def test_first_team_debut_is_career_once(self):
        engine = self.make_engine(404)
        engine.evaluate_draft()
        session = engine.start_pro_season()
        session.current_level = "FIRST"
        engine.player.roster_level = "FIRST"
        session.games_completed = 12
        session.record.first_team.G = 1
        engine.player.debut_year = engine.year

        engine._record_first_team_debut_if_needed(session)
        engine._record_first_team_debut_if_needed(session)
        debuts = [
            entry
            for entry in engine.player.career_history
            if entry["event_id"] == "first_team_debut"
        ]
        self.assertEqual(len(debuts), 1)
        self.assertEqual(debuts[0]["game_number"], 12)

    def test_save_load_round_trip_preserves_career_history(self):
        engine = self.make_engine(405)
        engine.evaluate_draft()
        expected = list(engine.player.career_history)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_game(path, engine)
            loaded = load_game(path)
        self.assertEqual(loaded.player.career_history, expected)

    def test_old_player_payload_without_career_history_loads_empty(self):
        engine = self.make_engine(406)
        payload = engine.player.as_dict()
        payload.pop("career_history")
        restored = Player.from_dict(payload)
        self.assertEqual(restored.career_history, [])

    def test_same_seed_same_actions_produce_identical_history(self):
        def history(seed: int):
            engine = self.make_engine(seed)
            engine.evaluate_draft()
            old_preseason = config.EVENT_PRESEASON_CHANCE
            old_game = config.EVENT_BASE_CHANCE_PER_GAME
            try:
                config.EVENT_PRESEASON_CHANCE = 0.0
                config.EVENT_BASE_CHANCE_PER_GAME = 0.0
                engine.advance_pro_games(40)
            finally:
                config.EVENT_PRESEASON_CHANCE = old_preseason
                config.EVENT_BASE_CHANCE_PER_GAME = old_game
            return engine.player.career_history

        self.assertEqual(history(407), history(407))

    def test_auto_and_interactive_flags_do_not_change_factual_history_when_state_matches(self):
        def history(seed: int, stop_on_event: bool):
            engine = self.make_engine(seed)
            engine.evaluate_draft()
            old_preseason = config.EVENT_PRESEASON_CHANCE
            old_game = config.EVENT_BASE_CHANCE_PER_GAME
            try:
                config.EVENT_PRESEASON_CHANCE = 0.0
                config.EVENT_BASE_CHANCE_PER_GAME = 0.0
                engine.advance_pro_games(40, stop_on_event=stop_on_event)
            finally:
                config.EVENT_PRESEASON_CHANCE = old_preseason
                config.EVENT_BASE_CHANCE_PER_GAME = old_game
            return engine.player.career_history

        self.assertEqual(history(408, False), history(408, True))

    def test_template_rendering_is_deterministic_and_rng_free(self):
        rng = RNG(409)
        before = rng.get_state()
        facts = {"team": "테스트", "round": 1, "pick": 3}
        first = render_career_news("draft_selected", "선수", facts)
        second = render_career_news("draft_selected", "선수", facts)
        self.assertEqual(first, second)
        self.assertEqual(rng.get_state(), before)


if __name__ == "__main__":
    unittest.main()
