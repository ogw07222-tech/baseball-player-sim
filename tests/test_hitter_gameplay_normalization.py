from src.hitting.normalization import *
from src.hitting.model import HitterSnapshot,PitcherSnapshot,HittingEngine
from src.player import Player
from src.rng import RNG


def test_hitter_raw_stats_not_mutated():
    p=Player.random('x',RNG(1)); before=p.stats.as_dict().copy(); normalize_hitter(p.stats.contact,p.stats.power,p.stats.discipline,p.stats.speed); assert p.stats.as_dict()==before

def test_contact_reference_maps_to_gameplay_neutral(): assert abs(normalize_contact(CONTACT_RAW_REFERENCE)-100)<1e-9
def test_power_reference_maps_to_gameplay_neutral(): assert abs(normalize_power(POWER_RAW_REFERENCE)-100)<1e-9
def test_discipline_reference_maps_to_gameplay_neutral(): assert abs(normalize_discipline(DISCIPLINE_RAW_REFERENCE)-100)<1e-9

def test_contact_mapping_monotonic(): assert normalize_contact(70)<normalize_contact(110)<normalize_contact(150)
def test_power_mapping_monotonic(): assert normalize_power(70)<normalize_power(110)<normalize_power(150)
def test_discipline_mapping_monotonic(): assert normalize_discipline(70)<normalize_discipline(110)<normalize_discipline(150)

def _pa(rawc=110,rawp=110,rawd=110,n=35000,seed=9):
    rng=RNG(seed); c={}
    for _ in range(n):
        h=HitterSnapshot(normalize_contact(rawc),normalize_power(rawp),normalize_discipline(rawd),normalize_speed(110))
        r=HittingEngine(h,PitcherSnapshot(),100,rng).simulate_plate_appearance().result;c[r]=c.get(r,0)+1
    hits=sum(c.get(k,0) for k in ('single','double','triple','home_run'));ab=n-c.get('walk',0);tb=c.get('single',0)+2*c.get('double',0)+3*c.get('triple',0)+4*c.get('home_run',0)
    return hits/ab,tb/ab,c.get('walk',0)/n,c.get('strikeout',0)/n

def test_contact_elite_separation():
    a=_pa(rawc=140,seed=51);b=_pa(rawc=150,seed=51);assert b[0]>a[0] and b[3]<a[3]
def test_power_elite_separation():
    a=_pa(rawp=140,seed=52);b=_pa(rawp=150,seed=52);assert b[1]>a[1]
def test_discipline_elite_separation():
    a=_pa(rawd=140,seed=53);b=_pa(rawd=150,seed=53);assert b[2]>a[2]

def test_low_rating_stability():
    for x in (30,50,70,80):
        vals=(normalize_contact(x),normalize_power(x),normalize_discipline(x));assert all(-100<v<300 for v in vals)
def test_extreme_rating_stability():
    for x in (30,50,70,90,110,130,150,180,200,250):
        assert all(abs(v)<500 for v in (normalize_contact(x),normalize_power(x),normalize_discipline(x),normalize_speed(x)))
def test_raw_to_gameplay_ratio_not_pathological(): assert 4<=normalize_contact(120)-normalize_contact(110)<=12

def test_contact_identity_preserved():
    lo=_pa(rawc=100,seed=61);hi=_pa(rawc=120,seed=61);assert hi[0]>lo[0] and abs(hi[2]-lo[2])<.02
def test_power_identity_preserved():
    lo=_pa(rawp=100,seed=62);hi=_pa(rawp=120,seed=62);assert hi[1]>lo[1] and abs(hi[2]-lo[2])<.02
def test_discipline_identity_preserved():
    lo=_pa(rawd=100,seed=63);hi=_pa(rawd=120,seed=63);assert hi[2]>lo[2]
