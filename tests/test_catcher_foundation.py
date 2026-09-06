import math
from pathlib import Path
import statistics
import unittest

from src.catcher import CATCHER_ARCHETYPES
from src.growth import apply_season_growth
from src.player import Player
from src.rng import RNG


class CatcherAbilityFoundationTests(unittest.TestCase):
    def test_catcher_position_supported(self):
        player = Player.random("Catcher", RNG(1), position="C")
        self.assertEqual(player.position, "C")

    def test_catcher_has_game_calling(self):
        player = Player.random("Catcher", RNG(2), position="C")
        self.assertGreater(player.stats.game_calling, 0)
        self.assertGreater(player.stats.defense, 0)
        self.assertGreater(player.stats.throwing, 0)
        self.assertIsNotNone(player.catcher_archetype)

    def test_non_catcher_backward_compatible(self):
        player = Player.random("Shortstop", RNG(3), position="SS")
        self.assertEqual(player.stats.game_calling, 0)
        self.assertIsNone(player.catcher_archetype)

    def test_old_save_without_game_calling_loads(self):
        source = Player.random("Legacy", RNG(4), position="SS").as_dict()
        stats = dict(source["stats"])
        stats.pop("game_calling", None)
        source["stats"] = stats
        source.pop("catcher_archetype", None)
        loaded = Player.from_dict(source)
        self.assertEqual(loaded.stats.game_calling, 0)
        self.assertIsNone(loaded.catcher_archetype)

    def test_game_calling_roundtrip_save(self):
        source = Player.random("Catcher", RNG(5), position="C")
        loaded = Player.from_dict(source.as_dict())
        self.assertEqual(loaded.stats.game_calling, source.stats.game_calling)
        self.assertEqual(loaded.catcher_archetype, source.catcher_archetype)

    def test_catcher_generation_distribution(self):
        rng = RNG(20260906)
        values = [Player.random(f"C{i}", rng, position="C") for i in range(100_000)]
        for name in ("defense", "throwing", "game_calling"):
            samples = [getattr(player.stats, name) for player in values]
            self.assertGreater(statistics.mean(samples), 70.0)
            self.assertLess(statistics.mean(samples), 105.0)
            self.assertGreater(statistics.pstdev(samples), 8.0)
            self.assertLess(statistics.pstdev(samples), 25.0)
            self.assertLess(sum(value >= 170 for value in samples) / len(samples), 0.001)
            self.assertEqual(sum(value >= 200 for value in samples), 0)

    def test_catcher_archetype_diversity(self):
        rng = RNG(77)
        by_type = {entry[0]: [] for entry in CATCHER_ARCHETYPES}
        for i in range(20_000):
            player = Player.random(f"C{i}", rng, position="C")
            by_type[player.catcher_archetype].append(player)
        self.assertTrue(all(len(players) > 1_000 for players in by_type.values()))
        means = {
            key: (
                statistics.mean(p.stats.defense for p in players),
                statistics.mean(p.stats.throwing for p in players),
                statistics.mean(p.stats.game_calling for p in players),
            )
            for key, players in by_type.items()
        }
        self.assertGreater(means["defensive"][0], means["offensive"][0] + 7.0)
        self.assertGreater(means["strong_arm"][1], means["balanced"][1] + 4.0)
        self.assertGreater(means["game_manager"][2], means["balanced"][2] + 4.0)

    def test_game_calling_growth_foundation(self):
        player = Player.random("Catcher", RNG(8), position="C")
        before = player.stats.game_calling
        result = apply_season_growth(player, RNG(9))
        self.assertIn("game_calling", result.deltas)
        self.assertEqual(player.stats.game_calling - before, result.deltas["game_calling"])

    def test_no_hitting_formula_changes(self):
        protected = (
            "src/hitting/model.py",
            "src/hitting/parameters.py",
            "src/hitting/baserunning.py",
            "src/hitting/normalization.py",
        )
        for path in protected:
            target = Path(path)
            if target.exists():
                self.assertNotIn("game_calling", target.read_text(encoding="utf-8").lower())

    def test_no_pitching_formula_changes(self):
        pitching = Path("src/pitching")
        if pitching.exists():
            for target in pitching.glob("*.py"):
                self.assertNotIn("game_calling", target.read_text(encoding="utf-8").lower())

    def test_no_inning_engine_changes(self):
        for path in ("src/inning.py", "src/game_provider.py", "src/stat_aggregation.py", "src/time_advance.py"):
            target = Path(path)
            if target.exists():
                self.assertNotIn("game_calling", target.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
