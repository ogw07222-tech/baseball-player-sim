import unittest

from src.player import Player
from src.rng import RNG


class PlayerTests(unittest.TestCase):
    def test_same_seed_reproduces_random_player(self):
        a = Player.random("A", RNG(1234))
        b = Player.random("A", RNG(1234))
        self.assertEqual(a.age, b.age)
        self.assertEqual(a.stats.as_dict(), b.stats.as_dict())
        self.assertEqual([t.key for t in a.traits], [t.key for t in b.traits])

    def test_stats_are_non_negative_and_unbounded_by_design(self):
        player = Player.random("A", RNG(1))
        self.assertTrue(all(value >= 0 for value in player.stats.as_dict().values()))
        player.stats.apply_delta("power", 500)
        self.assertGreater(player.stats.power, 100)

    def test_advance_age(self):
        player = Player.random("A", RNG(2))
        before = player.age
        player.advance_age()
        self.assertEqual(player.age, before + 1)


if __name__ == "__main__":
    unittest.main()
