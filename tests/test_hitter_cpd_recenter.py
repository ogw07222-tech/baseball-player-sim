from src.player import Player
from src.rng import RNG
from src.growth import _hitter_cpd_recenter_bonus,apply_season_growth


def test_entry_not_prime_shifted():
    assert _hitter_cpd_recenter_bonus('contact',18)>0
    assert _hitter_cpd_recenter_bonus('power',18)>0
    assert _hitter_cpd_recenter_bonus('discipline',18)>0
    assert _hitter_cpd_recenter_bonus('speed',18)==0


def test_recenter_ends_before_prime():
    for stat in ('contact','power','discipline'):
        assert _hitter_cpd_recenter_bonus(stat,28)==0
        assert _hitter_cpd_recenter_bonus(stat,35)==0


def test_speed_growth_path_exempt():
    p1=Player.random('a',RNG(77));p2=Player.from_dict(p1.as_dict())
    r1=RNG(91);r2=RNG(91)
    before1=p1.stats.speed;before2=p2.stats.speed
    apply_season_growth(p1,r1);apply_season_growth(p2,r2)
    assert p1.stats.speed-before1==p2.stats.speed-before2


def test_raw_generation_not_mutated_by_scale_patch():
    a=Player.random('a',RNG(123));b=Player.random('b',RNG(123))
    assert a.stats.as_dict()==b.stats.as_dict()
