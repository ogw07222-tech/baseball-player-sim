import unittest

from src.growth import apply_season_growth
from src.player import Player
from src.rng import RNG
from src.stats import PlayerStats


class GrowthTests(unittest.TestCase):
    def test_growth_is_reproducible_with_seed(self):
        stats = PlayerStats(80, 80, 80, 80, 80, 80, 80, 80, 80, 100)
        a = Player("A", 20, PlayerStats(**stats.as_dict()))
        b = Player("B", 20, PlayerStats(**stats.as_dict()))
        result_a = apply_season_growth(a, RNG(77))
        result_b = apply_season_growth(b, RNG(77))
        self.assertEqual(result_a.deltas, result_b.deltas)
        self.assertEqual(result_a.explosion, result_b.explosion)

    def test_season_growth_advances_age_and_records_history(self):
        player = Player.random("A", RNG(9))
        before = player.age
        result = apply_season_growth(player, RNG(10))
        self.assertEqual(player.age, before + 1)
        self.assertEqual(result.age_after, before + 1)
        self.assertEqual(len(player.growth_history), 1)

    def test_decline_never_pushes_stats_below_zero(self):
        low = PlayerStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 50)
        player = Player("Old", 40, low)
        for year in range(10):
            apply_season_growth(player, RNG(year))
        self.assertTrue(all(value >= 0 for value in player.stats.as_dict().values()))


if __name__ == "__main__":
    unittest.main()
