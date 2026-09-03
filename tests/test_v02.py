import math
import tempfile
import unittest
from pathlib import Path

from src.career import CareerEngine
from src.growth import apply_season_growth
from src.persistence import load_game, save_game
from src.player import Player
from src.records import BattingLine
from src.rng import RNG
from src.simulation import PA_RESULTS, PitcherProfile, simulate_plate_appearance
from src.stats import PlayerStats
from src.traits import generate_random_traits, traits_conflict


class V02PrototypeTests(unittest.TestCase):
    def test_player_generation_and_seed_reproducibility(self):
        a = Player.random("A", RNG(1234), "SS", "R/R", 3)
        b = Player.random("A", RNG(1234), "SS", "R/R", 3)
        self.assertEqual(a.stats.as_dict(), b.stats.as_dict())
        self.assertEqual([t.key for t in a.traits], [t.key for t in b.traits])
        self.assertTrue(all(v >= 0 for v in a.stats.as_dict().values()))

    def test_stats_are_unbounded(self):
        stats = PlayerStats(1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
        stats.apply_delta("power", 500)
        self.assertEqual(stats.power, 501)

    def test_trait_count_and_conflicts(self):
        for count in range(4):
            traits = generate_random_traits(RNG(100 + count), count)
            self.assertEqual(len(traits), count)
            self.assertEqual(len({t.key for t in traits}), count)
            for i, left in enumerate(traits):
                for right in traits[i + 1:]:
                    self.assertFalse(traits_conflict(left, right))

    def test_growth_and_aging(self):
        young = Player("Y", 20, PlayerStats(80, 80, 80, 80, 80, 80, 80, 80, 80, 100))
        r1 = apply_season_growth(young, RNG(77))
        self.assertEqual(young.age, 21)
        old = Player("O", 39, PlayerStats(110, 110, 110, 110, 110, 110, 110, 110, 110, 100))
        r2 = apply_season_growth(old, RNG(4))
        self.assertLess(sum(r2.deltas.values()), 0)
        self.assertTrue(all(v >= 0 for v in old.stats.as_dict().values()))
        self.assertIsInstance(r1.explosion, bool)

    def test_record_math(self):
        line = BattingLine(G=10, PA=20, AB=16, H=8, doubles=2, triples=1, HR=1, BB=3, HBP=1)
        self.assertAlmostEqual(line.AVG, 0.5)
        self.assertAlmostEqual(line.OBP, 0.6)
        self.assertAlmostEqual(line.SLG, 15 / 16)
        self.assertAlmostEqual(line.OPS, 0.6 + 15 / 16)

    def test_plate_appearance_engine(self):
        player = Player.random("A", RNG(1), "CF", "L/R", 2)
        pitcher = PitcherProfile(100, 100, 100, "R")
        results = [simulate_plate_appearance(player, pitcher, RNG(seed)) for seed in range(50)]
        self.assertTrue(all(result in PA_RESULTS for result in results))

    def test_draft_runs(self):
        rng = RNG(123)
        player = Player.random("A", rng, "SS", "R/R", 2)
        engine = CareerEngine(player, rng)
        draft = engine.evaluate_draft()
        self.assertIn(draft.status, {"지명", "미지명 육성선수 계약"})
        self.assertIsNotNone(player.team)
        self.assertIn("scouted_talent", player.draft_info)

    def test_save_load_round_trip_and_midseason_state(self):
        rng = RNG(777)
        player = Player.random("A", rng, "2B", "S/R", 3)
        engine = CareerEngine(player, rng)
        engine.evaluate_draft()
        engine.advance_pro_games(37)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "save.json"
            save_game(path, engine)
            loaded = load_game(path)
            self.assertEqual(engine.player.as_dict(), loaded.player.as_dict())
            self.assertEqual(37, loaded.current_session.games_completed)
            self.assertAlmostEqual(engine.rng.random(), loaded.rng.random())

    def test_full_career_smoke(self):
        rng = RNG(20260903)
        player = Player.random("Smoke", rng, "SS", "R/R", 3)
        engine = CareerEngine(player, rng)
        engine.run_to_retirement()
        self.assertEqual(engine.phase, "RETIRED")
        self.assertGreaterEqual(len(player.seasons), 1)
        self.assertTrue(all(v >= 0 for v in player.stats.as_dict().values()))
        career = player.first_team_career()
        self.assertTrue(all(math.isfinite(v) for v in (career.AVG, career.OBP, career.SLG, career.OPS)))


if __name__ == "__main__":
    unittest.main()
