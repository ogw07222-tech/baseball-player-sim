import unittest

from src.rng import RNG
from src.traits import generate_random_traits, traits_conflict


class TraitTests(unittest.TestCase):
    def test_generation_never_returns_conflicting_traits(self):
        for seed in range(500):
            traits = generate_random_traits(RNG(seed))
            for i, left in enumerate(traits):
                for right in traits[i + 1:]:
                    self.assertFalse(traits_conflict(left, right))


if __name__ == "__main__":
    unittest.main()
