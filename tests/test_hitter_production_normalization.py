from src.player import Player
from src.rng import RNG
from src.simulation import _hitter_snapshot,PitcherProfile,simulate_plate_appearance
from src.hitting.normalization import normalize_hitter,normalize_speed
from src.records import BattingLine
from src.simulation import _maybe_compat_steal


def test_production_snapshot_uses_normalization():
    p=Player.random('n',RNG(41));s=_hitter_snapshot(p);g=normalize_hitter(p.effective_stat('contact'),p.effective_stat('power'),p.effective_stat('discipline'),p.effective_stat('speed'))
    assert (s.contact,s.power,s.discipline,s.speed)==(g.contact,g.power,g.discipline,g.speed)

def test_raw_not_mutated_by_production_pa():
    p=Player.random('n',RNG(42));before=p.stats.as_dict().copy();simulate_plate_appearance(p,PitcherProfile(100,100,100,'R'),RNG(99));assert p.stats.as_dict()==before

def test_production_normalization_deterministic():
    p=Player.random('n',RNG(43));a=[simulate_plate_appearance(p,PitcherProfile(100,100,100,'R'),RNG(i)) for i in range(40)];b=[simulate_plate_appearance(p,PitcherProfile(100,100,100,'R'),RNG(i)) for i in range(40)];assert a==b

def test_save_round_trip_preserves_only_raw_stats():
    p=Player.random('n',RNG(44));d=p.as_dict();assert 'gameplay_stats' not in d and 'gameplay_rating' not in d;restored=Player.from_dict(d);assert restored.stats.as_dict()==p.stats.as_dict()

def test_compat_steal_uses_normalized_speed_without_mutation():
    p=Player.random('n',RNG(45));p.stats.speed=140;before=p.stats.speed;line=BattingLine();_maybe_compat_steal(p,line,'single',RNG(77),0,4);assert p.stats.speed==before and normalize_speed(before)>100
