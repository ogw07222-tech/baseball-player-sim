from functools import lru_cache
from statistics import mean
from src.player import Player
from src.rng import RNG
from src.growth import _hitter_cpd_recenter_bonus,apply_season_growth
from src import config

@lru_cache(maxsize=1)
def _prime_means():
    rng=RNG(70707);snap={'contact':[],'power':[],'discipline':[]};n=3000
    players=[Player.random(f'T{i}',rng,position=config.POSITIONS[i%len(config.POSITIONS)]) for i in range(n)]
    for target in (26,28,30):
        while players[0].age<target:
            for p in players:apply_season_growth(p,rng)
        for stat in snap:snap[stat].extend(getattr(p.stats,stat) for p in players)
    return {k:mean(v) for k,v in snap.items()}

def test_contact_prime_mean_near_110():assert 108<=_prime_means()['contact']<=112
def test_power_prime_mean_near_110():assert 108<=_prime_means()['power']<=112
def test_discipline_prime_mean_near_110():assert 108<=_prime_means()['discipline']<=112

def test_entry_not_prime():
    rng=RNG(8181);ps=[Player.random(f'E{i}',rng,position=config.POSITIONS[i%len(config.POSITIONS)]) for i in range(1000)]
    assert mean(p.stats.contact for p in ps)<95 and mean(p.stats.power for p in ps)<95 and mean(p.stats.discipline for p in ps)<95

def test_growth_curve_sane():
    rng=RNG(9090);ps=[Player.random(f'G{i}',rng,position=config.POSITIONS[i%len(config.POSITIONS)]) for i in range(1000)];entry=mean(p.stats.contact for p in ps)
    while ps[0].age<28:
        for p in ps:apply_season_growth(p,rng)
    prime=mean(p.stats.contact for p in ps)
    while ps[0].age<38:
        for p in ps:apply_season_growth(p,rng)
    late=mean(p.stats.contact for p in ps)
    assert prime>entry+20 and late<prime

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
    p1=Player.random('a',RNG(77));p2=Player.from_dict(p1.as_dict());r1=RNG(91);r2=RNG(91);before1=p1.stats.speed;before2=p2.stats.speed
    apply_season_growth(p1,r1);apply_season_growth(p2,r2);assert p1.stats.speed-before1==p2.stats.speed-before2

def test_raw_generation_not_mutated_by_scale_patch():
    a=Player.random('a',RNG(123));b=Player.random('b',RNG(123));assert a.stats.as_dict()==b.stats.as_dict()
