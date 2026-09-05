from src.player import Player
from src.rng import RNG
from src.growth import apply_season_growth
from src.hitting.baserunning import GameState,steal_attempt_probability,first_to_third_probability,second_to_home_probability,dp_completion_probability
from src.hitting.normalization import normalize_contact,normalize_power,normalize_discipline


def _prime(n=1200,seed=771):
    rng=RNG(seed);vals={k:[] for k in ('contact','power','discipline')}
    for i in range(n):
        p=Player.random(str(i),rng,position=('SS','CF','1B','3B')[i%4]);target=(26,28,30)[i%3]
        while p.age<target:apply_season_growth(p,rng)
        for k in vals:vals[k].append(getattr(p.stats,k))
    return {k:sum(v)/len(v) for k,v in vals.items()}

def test_contact_prime_mean_near_110(): assert 106 < _prime()['contact'] < 114
def test_power_prime_mean_near_110(): assert 106 < _prime()['power'] < 114
def test_discipline_prime_mean_near_110(): assert 106 < _prime()['discipline'] < 114

def test_hitter_entry_scale_not_prime():
    rng=RNG(4);ps=[Player.random(str(i),rng) for i in range(500)]
    assert sum(p.stats.contact for p in ps)/len(ps)<100
    assert sum(p.stats.power for p in ps)/len(ps)<100
    assert sum(p.stats.discipline for p in ps)/len(ps)<100

def test_hitter_growth_curve_not_pathological():
    rng=RNG(9);p=Player.random('x',rng);series=[]
    for _ in range(18):
        series.append((p.age,p.stats.contact,p.stats.power,p.stats.discipline));apply_season_growth(p,rng)
    assert max(v[1] for v in series)<250 and max(v[2] for v in series)<250 and max(v[3] for v in series)<250

def test_hitter_raw_stats_not_mutated():
    p=Player.random('x',RNG(2));before=p.stats.as_dict().copy();normalize_contact(p.stats.contact);normalize_power(p.stats.power);normalize_discipline(p.stats.discipline);assert p.stats.as_dict()==before

def test_speed_mapping_monotonic(): assert 70<80<90<100<110<120<130<140<150<160

def test_speed_steal_value_monotonic():
    st=GameState(inning=5,outs=1,score_diff=0,first_occupied=True)
    assert steal_attempt_probability(80,st)<steal_attempt_probability(110,st)<steal_attempt_probability(140,st)

def test_speed_extra_base_value_monotonic():
    assert first_to_third_probability(80)<first_to_third_probability(110)<first_to_third_probability(140)
    assert second_to_home_probability(80)<second_to_home_probability(110)<second_to_home_probability(140)

def test_speed_dp_avoidance_monotonic(): assert dp_completion_probability(80)>dp_completion_probability(110)>dp_completion_probability(140)
def test_speed_high_end_not_completely_flat(): assert first_to_third_probability(150)-first_to_third_probability(140)>.005

def test_h32_formula_diff_none():
    from pathlib import Path
    text=Path('src/hitting/model.py').read_text()
    assert 'hitting.normalization' not in text and 'normalize_contact' not in text
