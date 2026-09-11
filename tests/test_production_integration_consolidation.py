import hashlib
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from src import config
from src.career import CareerEngine
from src.persistence import load_game, save_game
from src.pitcher_usage_game_provider import DynamicPitcherGameProvider
from src.player import Player
from src.production_advance import (
    ProductionAdvancePipelineState,
    ProductionAdvanceService,
)
from src.rng import RNG
from src.stats import PlayerStats


PROTECTED_BLOBS = {
    "src/hitting/model.py": "2718635ccb9e53fbed63f0d5d5ba2ad7c17ac8e1",
    "src/hitting/parameters.py": "3876b4221f53b7d4b7cc6069d9425004fc9f311a",
    "src/hitting/baserunning.py": "2a383ce61fb6938ae30973be210159baa1d76726",
    "src/hitting/defense.py": "279f6282ef41c53e709839dbbe791e16836eaf53",
}


def _git_blob_sha(path: str) -> str:
    data = Path(path).read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _career(seed: int) -> CareerEngine:
    team = str(config.KBO_TEAMS[0]["name"])
    player = Player(
        name="Integration User",
        age=24,
        stats=PlayerStats(100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
        position="SS",
        team=team,
        roster_level="FIRST",
    )
    player.draft_info = {
        "team": team,
        "round": 1,
        "pick": 1,
        "status": "지명",
        "scouting_score": 110.0,
        "scouted_talent": 100,
    }
    engine = CareerEngine(player, RNG(seed))
    engine.phase = "PRO"
    return engine


class ProductionIntegrationConsolidationTests(unittest.TestCase):
    def test_canonical_advance_uses_dynamic_pitcher_provider(self):
        service = ProductionAdvanceService(_career(1))
        self.assertIsInstance(
            service.game_provider.game_provider,
            DynamicPitcherGameProvider,
        )
        self.assertIsInstance(service.state, ProductionAdvancePipelineState)
        self.assertTrue(service.state.team_record_supported)

    def test_week_advance_is_exact_composition(self):
        bulk_engine = _career(20260906)
        repeated_engine = _career(20260906)
        bulk = ProductionAdvanceService(bulk_engine)
        repeated = ProductionAdvanceService(repeated_engine)
        dates = bulk.schedule.game_dates(
            bulk.state.current_date,
            bulk.state.current_date + timedelta(days=7),
        )
        bulk.advance_one_week()
        for _ in dates:
            repeated.advance_one_game()
        self.assertEqual(bulk.state.as_dict(), repeated.state.as_dict())
        self.assertEqual(bulk.state.team_record, repeated.state.team_record)
        self.assertEqual(
            bulk.state.team_wins + bulk.state.team_losses + bulk.state.team_ties,
            len(dates),
        )
        self.assertTrue(bulk.state.team_record_supported)
        self.assertEqual(
            bulk_engine.pitcher_usage_state.as_dict(),
            repeated_engine.pitcher_usage_state.as_dict(),
        )
        self.assertEqual(
            bulk_engine.start_pro_season().games_completed,
            repeated_engine.start_pro_season().games_completed,
        )

    def test_month_advance_is_exact_composition(self):
        bulk_engine = _career(20260907)
        repeated_engine = _career(20260907)
        bulk = ProductionAdvanceService(bulk_engine)
        repeated = ProductionAdvanceService(repeated_engine)
        start = bulk.state.current_date
        expected_dates = bulk.schedule.game_dates(
            start,
            start.replace(month=4, day=30),
        )
        bulk.advance_one_month()
        for _ in expected_dates:
            repeated.advance_one_game()
        self.assertEqual(bulk.state.as_dict(), repeated.state.as_dict())
        self.assertEqual(bulk.state.team_record, repeated.state.team_record)
        self.assertEqual(
            bulk.state.team_wins + bulk.state.team_losses + bulk.state.team_ties,
            len(expected_dates),
        )
        self.assertTrue(bulk.state.team_record_supported)
        self.assertEqual(
            bulk_engine.pitcher_usage_state.as_dict(),
            repeated_engine.pitcher_usage_state.as_dict(),
        )

    def test_production_team_record_save_roundtrip(self):
        engine = _career(404)
        service = ProductionAdvanceService(engine)
        service.advance_one_week()
        expected = dict(service.state.team_record)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "team-record.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["advance_state"]["team_record"], expected)
            loaded = load_game(path)
            self.assertIsInstance(
                loaded.advance_state,
                ProductionAdvancePipelineState,
            )
            self.assertEqual(loaded.advance_state.team_record, expected)

    def test_old_advance_state_without_team_record_loads_as_unsupported(self):
        engine = _career(405)
        service = ProductionAdvanceService(engine)
        service.advance_one_game()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["advance_state"].pop("team_record", None)
            old_path = Path(tmp) / "legacy-advance.json"
            old_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_game(old_path)
            self.assertIsInstance(
                loaded.advance_state,
                ProductionAdvancePipelineState,
            )
            self.assertFalse(loaded.advance_state.team_record_supported)
            self.assertEqual(loaded.advance_state.team_wins, 0)
            self.assertEqual(loaded.advance_state.team_losses, 0)
            self.assertEqual(loaded.advance_state.team_ties, 0)

    def test_optional_save_state_and_game_calling_are_backward_compatible(self):
        engine = _career(77)
        service = ProductionAdvanceService(engine)
        service.advance_one_game()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "new.json"
            save_game(path, engine)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("advance_state", payload)
            self.assertIn("pitcher_usage_state", payload)
            stats = dict(payload["player"]["stats"])
            self.assertIn("game_calling", stats)

            payload.pop("advance_state", None)
            payload.pop("pitcher_usage_state", None)
            payload["player"]["stats"].pop("game_calling", None)
            payload["player"].pop("catcher_archetype", None)
            old_path = Path(tmp) / "old.json"
            old_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_game(old_path)
            self.assertFalse(hasattr(loaded, "advance_state"))
            self.assertFalse(hasattr(loaded, "pitcher_usage_state"))
            self.assertEqual(loaded.player.stats.game_calling, 0)

    def test_protected_h32_formula_blobs_unchanged(self):
        for path, expected in PROTECTED_BLOBS.items():
            self.assertEqual(_git_blob_sha(path), expected, path)


if __name__ == "__main__":
    unittest.main()