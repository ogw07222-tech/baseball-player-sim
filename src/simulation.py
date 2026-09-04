"""Pitch-by-pitch hitter simulation and compact game simulation.

Experimental H2 hitting candidate. Frozen for validation.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from . import config
from .player import Player
from .records import BattingLine
from .rng import RNG
from .traits import has_trait

PA_RESULTS=('strikeout','walk','hit_by_pitch','out','single','double','triple','home_run')

# Frozen H2 candidate parameters.
HITTING_STAT_REFERENCE=100.0
CONTACT_EFFECT_SCALE=1.6
POWER_EFFECT_SCALE=1.4
DISCIPLINE_EFFECT_SCALE=2.5
SPEED_EFFECT_SCALE=1.0
CONTACT_DIMINISH=45.0
POWER_DIMINISH=110.0
DISCIPLINE_DIMINISH=75.0
SPEED_DIMINISH=9999.0
ZONE_SWING_LOW=.569
ZONE_SWING_HIGH=.769
ZONE_SWING_SCALE=36.0
ZONE_SWING_CENTER=-8.0
CHASE_LOW=.010
CHASE_HIGH=.411
CHASE_SCALE=27.0
CHASE_CENTER=-8.0
CONTACT_PROB_LOW=.533
CONTACT_PROB_HIGH=.933
CONTACT_PROB_SCALE=30.0
CONTACT_PROB_CENTER=-5.0
TWO_STRIKE_MISS_FOUL_WEIGHT=.007
TWO_STRIKE_MISS_FOUL_CAP=.35
HR_BASE=.0395
HR_LOW=.001
HR_HIGH=.22
HR_UP_SCALE=130.0
HR_DOWN_SCALE=12.0
BIP_LOW=.15
BIP_HIGH=.454
BIP_SCALE=28.0
BIP_CONTACT_WEIGHT=.45
BIP_POWER_WEIGHT=.60
BIP_POWER_THRESHOLD=20.0
EXTRA_BASE=.23
EXTRA_LOW=.02
EXTRA_HIGH=.50
EXTRA_UP_SCALE=150.0
EXTRA_DOWN_SCALE=12.0

def sigmoid(v:float)->float:
    if v>=60:return 1.
    if v<=-60:return 0.
    return 1./(1.+math.exp(-v))

def logistic_range(diff:float,low:float,high:float,scale:float)->float:
    return low+(high-low)*sigmoid(diff/scale)

def _soft_delta(raw:float,scale:float,diminish:float)->float:
    d=raw-HITTING_STAT_REFERENCE
    if d>0:d=diminish*math.log1p(d/diminish)
    return d*scale

def effective_hitting_stat(raw:float,stat_name:str)->float:
    params={'contact':(CONTACT_EFFECT_SCALE,CONTACT_DIMINISH),'power':(POWER_EFFECT_SCALE,POWER_DIMINISH),'discipline':(DISCIPLINE_EFFECT_SCALE,DISCIPLINE_DIMINISH),'speed':(SPEED_EFFECT_SCALE,SPEED_DIMINISH)}
    scale,diminish=params[stat_name]
    return HITTING_STAT_REFERENCE+_soft_delta(raw,scale,diminish)

def anchored_probability(diff:float,base:float,low:float,high:float,up_scale:float,down_scale:float)->float:
    if diff>=0:return base+(high-base)*(1-math.exp(-diff/up_scale))
    return low+(base-low)*math.exp(diff/down_scale)

@dataclass(frozen=True)
class PitcherProfile:
    stuff:float;control:float;movement:float;handedness:str
    @classmethod
    def from_level(cls,level:float,rng:RNG)->'PitcherProfile':return cls(rng.gauss(level,7.5),rng.gauss(level,8.),rng.gauss(level,7.),'L' if rng.random()<.28 else 'R')

def _trait_contact_modifier(p:Player,pitcher:PitcherProfile,pitch_type:str,zone:str,high_velocity:bool,strikes:int,pressure:bool)->float:
    e=config.TRAIT_EFFECT;d=0.
    if pitch_type=='fastball':d+=e if has_trait(p.traits,'fastball_specialist') else 0.;d-=e if has_trait(p.traits,'fastball_weakness') else 0.
    else:d+=e if has_trait(p.traits,'breaking_ball_response') else 0.;d-=e if has_trait(p.traits,'breaking_ball_weakness') else 0.
    if high_velocity:d+=e if has_trait(p.traits,'high_velocity_strength') else 0.;d-=e if has_trait(p.traits,'high_velocity_weakness') else 0.
    if zone=='low':d+=e if has_trait(p.traits,'low_pitch_strength') else 0.;d-=e if has_trait(p.traits,'low_pitch_weakness') else 0.
    if zone=='inside':d+=e if has_trait(p.traits,'inside_pitch_strength') else 0.;d-=e if has_trait(p.traits,'inside_pitch_weakness') else 0.
    if pitcher.handedness=='L':d+=e if has_trait(p.traits,'vs_lhp_strength') else 0.;d-=e if has_trait(p.traits,'vs_lhp_weakness') else 0.
    else:d+=e if has_trait(p.traits,'vs_rhp_strength') else 0.;d-=e if has_trait(p.traits,'vs_rhp_weakness') else 0.
    if strikes==2 and has_trait(p.traits,'two_strike_strength'):d+=e*.75
    if pressure:d+=e if has_trait(p.traits,'clutch') else 0.;d-=e if has_trait(p.traits,'pressure_weakness') else 0.
    return d

def _condition_modifiers(p:Player)->tuple[float,float]:
    c=q=0.
    if p.form=='slump':c-=config.FORM_CONTACT_DELTA;q-=config.FORM_POWER_DELTA
    elif p.form=='hot':c+=config.FORM_CONTACT_DELTA*.75;q+=config.FORM_POWER_DELTA*.75
    fatigue=max(0.,p.fatigue-55.)/7.
    return c-fatigue,q-fatigue*.8

def _ball_in_play_result(p:Player,pitcher:PitcherProfile,contact_eff:float,power_eff:float,rng:RNG)->str:
    pdiff=power_eff-pitcher.movement
    if rng.random()<anchored_probability(pdiff,HR_BASE,HR_LOW,HR_HIGH,HR_UP_SCALE,HR_DOWN_SCALE):return 'home_run'
    bip_diff=(contact_eff-100.)*BIP_CONTACT_WEIGHT+max(0.,power_eff-100.-BIP_POWER_THRESHOLD)*BIP_POWER_WEIGHT-(pitcher.movement-100.)
    if rng.random()>=logistic_range(bip_diff,BIP_LOW,BIP_HIGH,BIP_SCALE):return 'out'
    extra=anchored_probability(pdiff,EXTRA_BASE,EXTRA_LOW,EXTRA_HIGH,EXTRA_UP_SCALE,EXTRA_DOWN_SCALE)
    roll=rng.random();speed=effective_hitting_stat(p.effective_stat('speed'),'speed');triple=logistic_range(speed-100.,.008,.055,30.)
    if roll<triple:return 'triple'
    if roll<triple+extra:return 'double'
    return 'single'

def simulate_plate_appearance(p:Player,pitcher:PitcherProfile,rng:RNG,pressure:bool=False)->str:
    balls=strikes=0;cond_c,cond_p=_condition_modifiers(p);discipline=effective_hitting_stat(p.effective_stat('discipline'),'discipline')
    for _ in range(24):
        if rng.random()<.0012:return 'hit_by_pitch'
        pitch_type='fastball' if rng.random()<.58 else 'breaking';zr=rng.random();zone='low' if zr<.28 else 'inside' if zr<.48 else 'other';high=pitch_type=='fastball' and pitcher.stuff>=104 and rng.random()<.55;is_strike=rng.random()<logistic_range(pitcher.control-100.,.43,.64,28.)
        swing=logistic_range((discipline-100.)-ZONE_SWING_CENTER,ZONE_SWING_LOW,ZONE_SWING_HIGH,ZONE_SWING_SCALE) if is_strike else logistic_range((100.-discipline)-CHASE_CENTER,CHASE_LOW,CHASE_HIGH,CHASE_SCALE)
        if rng.random()>=swing:
            if is_strike:
                strikes+=1
                if strikes>=3:return 'strikeout'
            else:
                balls+=1
                if balls>=4:return 'walk'
            continue
        trait=_trait_contact_modifier(p,pitcher,pitch_type,zone,high,strikes,pressure);contact=effective_hitting_stat(p.effective_stat('contact'),'contact')+cond_c+trait;power=effective_hitting_stat(p.effective_stat('power'),'power')+cond_p+trait*.25
        if rng.random()>=logistic_range((contact-pitcher.stuff)-CONTACT_PROB_CENTER,CONTACT_PROB_LOW,CONTACT_PROB_HIGH,CONTACT_PROB_SCALE):
            if strikes==2 and discipline>100.:
                protect=min(TWO_STRIKE_MISS_FOUL_CAP,(discipline-100.)*TWO_STRIKE_MISS_FOUL_WEIGHT)
                if rng.random()<protect:continue
            strikes+=1
            if strikes>=3:return 'strikeout'
            continue
        foul=.34 if strikes<2 else .49
        if rng.random()<foul:
            if strikes<2:strikes+=1
            continue
        return _ball_in_play_result(p,pitcher,contact,power,rng)
    return 'out'

def _run_rbi_values(result:str,rng:RNG)->tuple[int,int]:
    if result=='home_run':rbi=1+(1 if rng.random()<.32 else 0)+(1 if rng.random()<.14 else 0);return 1,rbi
    if result in {'double','triple'}:return (1 if rng.random()<.28 else 0,1 if rng.random()<.48 else 0)
    if result=='single':return (1 if rng.random()<.20 else 0,1 if rng.random()<.30 else 0)
    if result in {'walk','hit_by_pitch'}:return (1 if rng.random()<.10 else 0,0)
    return 0,0

def _maybe_steal(p:Player,line:BattingLine,reached:bool,rng:RNG)->None:
    if not reached:return
    speed=effective_hitting_stat(p.effective_stat('speed'),'speed');attempt=logistic_range(speed-100.,.015,.16,30.)
    if has_trait(p.traits,'steal_sense'):attempt*=1.30
    if rng.random()>=attempt:return
    success=logistic_range(speed-100.,.56,.88,28.)
    if has_trait(p.traits,'steal_sense'):success=min(.94,success+.06)
    if rng.random()<success:line.SB+=1
    else:line.CS+=1

def simulate_player_game(p:Player,opponent_level:float,rng:RNG,line:BattingLine,pa_count:int|None=None)->None:
    pitcher=PitcherProfile.from_level(opponent_level,rng);line.G+=1;appearances=pa_count if pa_count is not None else rng.weighted_choice(((3,.12),(4,.58),(5,.25),(6,.05)))
    for i in range(appearances):
        result=simulate_plate_appearance(p,pitcher,rng,pressure=i>=3 and rng.random()<.28);runs,rbi=_run_rbi_values(result,rng);line.record_pa(result,runs=runs,rbi=rbi);_maybe_steal(p,line,result in {'single','walk','hit_by_pitch'},rng)
