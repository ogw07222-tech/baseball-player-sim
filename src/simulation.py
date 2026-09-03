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
def sigmoid(value:float)->float:
    if value>=60:return 1.0
    if value<=-60:return 0.0
    return 1.0/(1.0+math.exp(-value))
def logistic_range(diff:float,low:float,high:float,scale:float)->float:return low+(high-low)*sigmoid(diff/scale)
@dataclass(frozen=True)
class PitcherProfile:
    stuff:float; control:float; movement:float; handedness:str
    @classmethod
    def from_level(cls,level:float,rng:RNG)->'PitcherProfile':return cls(rng.gauss(level,7.5),rng.gauss(level,8.0),rng.gauss(level,7.0),'L' if rng.random()<.28 else 'R')
def _trait_contact_modifier(player,pitcher,pitch_type,zone,high_velocity,strikes,pressure):
    e=config.TRAIT_EFFECT; d=0.
    if pitch_type=='fastball': d+=e if has_trait(player.traits,'fastball_specialist') else 0; d-=e if has_trait(player.traits,'fastball_weakness') else 0
    else: d+=e if has_trait(player.traits,'breaking_ball_response') else 0; d-=e if has_trait(player.traits,'breaking_ball_weakness') else 0
    if high_velocity:d+=e if has_trait(player.traits,'high_velocity_strength') else 0;d-=e if has_trait(player.traits,'high_velocity_weakness') else 0
    if zone=='low':d+=e if has_trait(player.traits,'low_pitch_strength') else 0;d-=e if has_trait(player.traits,'low_pitch_weakness') else 0
    if zone=='inside':d+=e if has_trait(player.traits,'inside_pitch_strength') else 0;d-=e if has_trait(player.traits,'inside_pitch_weakness') else 0
    if pitcher.handedness=='L':d+=e if has_trait(player.traits,'vs_lhp_strength') else 0;d-=e if has_trait(player.traits,'vs_lhp_weakness') else 0
    else:d+=e if has_trait(player.traits,'vs_rhp_strength') else 0;d-=e if has_trait(player.traits,'vs_rhp_weakness') else 0
    if strikes==2 and has_trait(player.traits,'two_strike_strength'):d+=e*.75
    if pressure:d+=e if has_trait(player.traits,'clutch') else 0;d-=e if has_trait(player.traits,'pressure_weakness') else 0
    return d
def _condition_modifiers(player):
    contact=power=0.
    if player.form=='slump':contact-=config.FORM_CONTACT_DELTA;power-=config.FORM_POWER_DELTA
    elif player.form=='hot':contact+=config.FORM_CONTACT_DELTA*.75;power+=config.FORM_POWER_DELTA*.75
    f=max(0.,player.fatigue-55.)/7.;return contact-f,power-f*.8
def _ball_in_play_result(player,pitcher,contact_eff,power_eff,rng):
    if rng.random()>=logistic_range(contact_eff-pitcher.movement,.20,.46,28.):return 'out'
    if rng.random()<logistic_range(power_eff-pitcher.movement,.030,.210,27.):return 'home_run'
    extra=logistic_range(power_eff-pitcher.movement,.12,.34,34.);roll=rng.random();triple=logistic_range(player.stats.speed-100.,.008,.055,30.)
    if roll<triple:return 'triple'
    if roll<triple+extra:return 'double'
    return 'single'
def simulate_plate_appearance(player:Player,pitcher:PitcherProfile,rng:RNG,pressure:bool=False)->str:
    balls=strikes=0;cc,cp=_condition_modifiers(player)
    for _ in range(24):
        if rng.random()<.0012:return 'hit_by_pitch'
        pt='fastball' if rng.random()<.58 else 'breaking';zr=rng.random();zone='low' if zr<.28 else 'inside' if zr<.48 else 'other';hv=pt=='fastball' and pitcher.stuff>=104 and rng.random()<.55
        strike=rng.random()<logistic_range(pitcher.control-100.,.43,.64,28.);disc=player.stats.discipline;swing=logistic_range(100.-disc,.58,.78,45.) if strike else logistic_range(100.-disc,.10,.38,30.)
        if rng.random()>=swing:
            if strike:
                strikes+=1
                if strikes>=3:return 'strikeout'
            else:
                balls+=1
                if balls>=4:return 'walk'
            continue
        tm=_trait_contact_modifier(player,pitcher,pt,zone,hv,strikes,pressure);ce=player.stats.contact+cc+tm;pe=player.stats.power+cp+tm*.25
        if rng.random()>=logistic_range(ce-pitcher.stuff,.55,.95,30.):
            strikes+=1
            if strikes>=3:return 'strikeout'
            continue
        foul=.34 if strikes<2 else .49
        if rng.random()<foul:
            if strikes<2:strikes+=1
            continue
        return _ball_in_play_result(player,pitcher,ce,pe,rng)
    return 'out'
def _run_rbi_values(result,rng):
    if result=='home_run':return 1,1+(1 if rng.random()<.32 else 0)+(1 if rng.random()<.14 else 0)
    if result in {'double','triple'}:return (1 if rng.random()<.28 else 0,1 if rng.random()<.48 else 0)
    if result=='single':return (1 if rng.random()<.20 else 0,1 if rng.random()<.30 else 0)
    if result in {'walk','hit_by_pitch'}:return (1 if rng.random()<.10 else 0,0)
    return 0,0
def _maybe_steal(player,line,reached,rng):
    if not reached:return
    attempt=logistic_range(player.stats.speed-100.,.015,.16,30.)*(1.30 if has_trait(player.traits,'steal_sense') else 1.)
    if rng.random()>=attempt:return
    success=logistic_range(player.stats.speed-100.,.56,.88,28.)+(0.06 if has_trait(player.traits,'steal_sense') else 0)
    if rng.random()<min(.94,success):line.SB+=1
    else:line.CS+=1
def simulate_player_game(player:Player,opponent_level:float,rng:RNG,line:BattingLine,pa_count:int|None=None)->None:
    pitcher=PitcherProfile.from_level(opponent_level,rng);line.G+=1;apps=pa_count if pa_count is not None else rng.weighted_choice(((3,.12),(4,.58),(5,.25),(6,.05)))
    for i in range(apps):
        result=simulate_plate_appearance(player,pitcher,rng,pressure=i>=3 and rng.random()<.28);runs,rbi=_run_rbi_values(result,rng);line.record_pa(result,runs,rbi);_maybe_steal(player,line,result in {'single','walk','hit_by_pitch'},rng)
