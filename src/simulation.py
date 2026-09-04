"""Pitch-by-pitch hitter simulation and compact game simulation."""
from __future__ import annotations
from dataclasses import dataclass
import math
from . import config
from .player import Player
from .records import BattingLine
from .rng import RNG
from .traits import has_trait
PA_RESULTS=('strikeout','walk','hit_by_pitch','out','single','double','triple','home_run')
def sigmoid(v:float)->float:
    if v>=60:return 1.
    if v<=-60:return 0.
    return 1./(1.+math.exp(-v))
def logistic_range(diff:float,low:float,high:float,scale:float)->float:return low+(high-low)*sigmoid(diff/scale)
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
    if rng.random()>=logistic_range(contact_eff-pitcher.movement,.20,.46,28.):return 'out'
    if rng.random()<logistic_range(power_eff-pitcher.movement,.030,.210,27.):return 'home_run'
    extra=logistic_range(power_eff-pitcher.movement,.12,.34,34.);roll=rng.random();triple=logistic_range(p.effective_stat('speed')-100.,.008,.055,30.)
    if roll<triple:return 'triple'
    if roll<triple+extra:return 'double'
    return 'single'
def simulate_plate_appearance(p:Player,pitcher:PitcherProfile,rng:RNG,pressure:bool=False)->str:
    balls=strikes=0;cond_c,cond_p=_condition_modifiers(p)
    for _ in range(24):
        if rng.random()<.0012:return 'hit_by_pitch'
        pitch_type='fastball' if rng.random()<.58 else 'breaking';zr=rng.random();zone='low' if zr<.28 else 'inside' if zr<.48 else 'other';high=pitch_type=='fastball' and pitcher.stuff>=104 and rng.random()<.55;is_strike=rng.random()<logistic_range(pitcher.control-100.,.43,.64,28.)
        discipline=p.effective_stat('discipline');swing=logistic_range(100.-discipline,.58,.78,45.) if is_strike else logistic_range(100.-discipline,.10,.38,30.)
        if rng.random()>=swing:
            if is_strike:
                strikes+=1
                if strikes>=3:return 'strikeout'
            else:
                balls+=1
                if balls>=4:return 'walk'
            continue
        trait=_trait_contact_modifier(p,pitcher,pitch_type,zone,high,strikes,pressure);contact=p.effective_stat('contact')+cond_c+trait;power=p.effective_stat('power')+cond_p+trait*.25
        if rng.random()>=logistic_range(contact-pitcher.stuff,.55,.95,30.):
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
    speed=p.effective_stat('speed');attempt=logistic_range(speed-100.,.015,.16,30.)
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
