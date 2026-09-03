"""Data-driven career events. Choices reshape probability distributions, not guaranteed outcomes."""
from __future__ import annotations
from dataclasses import dataclass, field
from . import config
from .growth import GrowthModifiers
from .player import InjuryStatus, Player
from .records import SeasonRecord
from .rng import RNG
from .traits import has_trait, trait_from_key, traits_conflict

@dataclass(frozen=True)
class Outcome:
    id:str; name:str; weight:float; quality:int=0
    stat_ranges:dict[str,tuple[int,int]]=field(default_factory=dict)
    growth_means:dict[str,float]=field(default_factory=dict)
    variance_multiplier:float=1.0; explosion_multiplier:float=1.0
    injury:tuple[str,int,int]|None=None
    fatigue_delta:float=0.0; trait_add:str|None=None; trait_remove:str|None=None

@dataclass(frozen=True)
class EventChoice:
    id:str; name:str; risk:str; outcomes:tuple[Outcome,...]

@dataclass(frozen=True)
class CareerEvent:
    id:str; name:str; description:str; rarity:str; condition:str; choices:tuple[EventChoice,...]

@dataclass(frozen=True)
class EventResolution:
    event_id:str; event_name:str; choice_id:str; choice_name:str; outcome_id:str; outcome_name:str
    stat_changes:dict[str,int]; trait_changes:tuple[str,...]; injury_change:str; growth_modifiers:GrowthModifiers

def O(id,name,w,q=0,stats=None,growth=None,var=1.,expl=1.,injury=None,fatigue=0.,trait_add=None,trait_remove=None):
    return Outcome(id,name,w,q,stats or {},growth or {},var,expl,injury,fatigue,trait_add,trait_remove)
def C(id,name,risk,*outcomes):return EventChoice(id,name,risk,tuple(outcomes))

def simple_event(id,name,description,condition,focus):
    return CareerEvent(id,name,description,'common',condition,(
        C('stable','안정적으로 유지','stable',O('steady','안정',.72,1,growth={focus:.18},var=.88),O('flat','정체',.28,0,var=.92)),
        C('medium','변화를 시도','medium',O('good','성공',.56,1,stats={focus:(0,2)},growth={focus:.35},var=1.02),O('mixed','혼합',.32,0,var=1.06),O('bad','실패',.12,-1,stats={focus:(-2,0)},var=1.10)),
        C('risky','전면 개조','risky',O('breakthrough','대성공',.18,2,stats={focus:(2,5)},growth={focus:.55},var=1.28,expl=1.18),O('upside','성공',.32,1,stats={focus:(0,3)},var=1.20),O('messy','실패',.30,-1,stats={focus:(-3,0)},var=1.30),O('collapse','대실패',.20,-2,stats={focus:(-5,-2)},var=1.38)),
    ))

HAMSTRING=CareerEvent('hamstring_warning','햄스트링 이상 징후','햄스트링에 이상이 느껴집니다. 계속 뛰거나 재활을 선택할 수 있습니다.','uncommon','healthy_or_minor',(
    C('play_through','참고 계속 출전한다','risky',
      O('great','대성공',.15,2,{'mentality':(6,12),'durability':(2,5),'power':(2,5)},{'contact':.40,'power':.60},1.25,1.40,('clear',0,0)),
      O('success','성공',.50,1,{'mentality':(1,3)},{'contact':.15,'power':.20},1.15,1.08),
      O('failure','실패',.22,-1,{'durability':(-5,-2)},var=1.22,injury=('보통',15,45)),
      O('disaster','대실패',.13,-2,{'speed':(-6,-2),'power':(-4,-1),'durability':(-7,-3)},var=1.30,injury=('중상',60,150))),
    C('rehab','재활 치료를 받는다','stable',
      O('great','매우 좋은 회복',.12,2,{'durability':(2,4),'stamina':(1,3)},{'durability':.20},.78,.70,('경미',8,16)),
      O('success','정상 회복',.50,1,{'durability':(0,2)},var=.82,expl=.75,injury=('경미',12,24)),
      O('neutral','예상대로 회복',.35,0,var=.85,expl=.75,injury=('경미',18,30)),
      O('failure','회복 지연',.03,-1,{'stamina':(-2,0)},var=.90,expl=.80,injury=('보통',28,45))))
)

BATTING_FORM=simple_event('batting_form','타격폼 변경','타격폼 유지/수정/전면 개조를 선택합니다.','always','contact')
BULK_UP=CareerEvent('bulk_up','벌크업','장타를 위해 체형 변화를 시도할 수 있습니다.','uncommon','under_32',(
    C('maintain','현재 체형 유지','stable',O('steady','유지',1.,0,growth={'speed':.05,'durability':.05},var=.94)),
    C('gradual','점진적 벌크업','medium',O('good','성공',.55,1,{'power':(1,3),'speed':(-1,0)},{'power':.35,'durability':.10}),O('neutral','변화 적음',.35,0,growth={'power':.15},var=1.02),O('strain','부담',.10,-1,{'speed':(-3,-1),'durability':(-2,0)},var=1.08)),
    C('aggressive','강한 벌크업','risky',O('slugger','대성공',.22,2,{'power':(3,7),'speed':(-2,0)},{'power':.55},1.22,1.12),O('power_gain','파워 상승',.33,1,{'power':(1,4),'speed':(-3,-1)},var=1.17),O('sluggish','민첩성 저하',.27,-1,{'speed':(-5,-2),'defense':(-2,0)},var=1.22),O('injured','부상',.18,-2,{'durability':(-4,-1),'speed':(-4,-1)},var=1.28,injury=('보통',15,50))))
)
FARM_DEVELOPMENT=CareerEvent('farm_development','2군 장기체류','2군에서 훈련 방향을 정합니다.','common','farm_heavy',(
    C('contact','컨택 집중','medium',O('develop','성과',.72,1,growth={'contact':.65,'discipline':.12,'power':-.12},var=.98),O('flat','정체',.28,0,growth={'contact':.15})),
    C('power','장타 집중','medium',O('develop','성과',.68,1,growth={'power':.72,'contact':-.12},var=1.06),O('flat','정체',.32,0,growth={'power':.15},var=1.06)),
    C('defense','수비 집중','medium',O('develop','성과',.72,1,growth={'defense':.62,'throwing':.32},var=.97),O('flat','정체',.28,0,growth={'defense':.12},var=.99)),
    C('maintain','현재 훈련 유지','stable',O('steady','유지',1.,0,growth={'contact':.08,'power':.08,'defense':.08},var=.90))))
WINTER_TRAINING=CareerEvent('winter_training','겨울 훈련','오프시즌 훈련 방향을 선택합니다.','common','always',tuple(
    [C(k,n,'medium',O('good','훈련 성과',.72,1,growth={stat:.60},var=1.0),O('flat','평범',.28,0,growth={stat:.12})) for k,n,stat in (
        ('contact','컨택','contact'),('power','파워','power'),('discipline','선구안','discipline'),('defense','수비','defense'),('baserun','주루','speed'))]
    +[C('rest','휴식','stable',O('fresh','충분히 회복',.86,1,{'stamina':(0,2),'durability':(0,2)},{'contact':-.08,'power':-.08},.80,fatigue=-40),O('rust','감각 저하',.14,-1,{'contact':(-1,0)},var=.85,fatigue=-30))]
))
COACH_CONFLICT=simple_event('coach_conflict','코치와의 의견 충돌','코치와 훈련 방식에 대한 의견 차이가 생겼습니다.','always','discipline')
SLUMP_RESPONSE=simple_event('slump_response','슬럼프 대응','부진이 이어지고 있습니다. 대응 방식을 선택합니다.','slump_or_bad_year','mentality')
INJURY_RETURN=CareerEvent('injury_return','부상 복귀 시점','복귀 시점을 결정합니다.','rare','injured',(
    C('early','조기 복귀','risky',O('fine','문제 없이 복귀',.34,1,{'mentality':(1,3)},var=1.10,injury=('clear',0,0)),O('setback','재발',.46,-1,{'durability':(-3,-1)},var=1.18,injury=('보통',20,55)),O('major','큰 재발',.20,-2,{'durability':(-6,-2),'speed':(-4,-1)},var=1.25,injury=('중상',60,130))),
    C('normal','정상 복귀','medium',O('fine','정상 복귀',.72,1,var=.98,injury=('clear',0,0)),O('delay','약간 지연',.25,0,var=1.0,injury=('경미',5,15)),O('setback','가벼운 재발',.03,-1,var=1.04,injury=('보통',15,35))),
    C('full','완전 회복 후 복귀','stable',O('strong','완전 회복',.58,1,{'durability':(1,3)},var=.82,injury=('clear',0,0)),O('fine','안정 복귀',.40,0,var=.84,injury=('clear',0,0)),O('slow','회복 지연',.02,-1,var=.86,injury=('경미',5,12))))
)

EVENT_CATALOG=(HAMSTRING,BATTING_FORM,BULK_UP,FARM_DEVELOPMENT,WINTER_TRAINING,COACH_CONFLICT,SLUMP_RESPONSE,INJURY_RETURN)
EVENT_BY_ID={e.id:e for e in EVENT_CATALOG}

def _eligible(event:CareerEvent,player:Player,record:SeasonRecord)->bool:
    c=event.condition
    if c=='always':return True
    if c=='under_32':return player.age<=31
    if c=='healthy_or_minor':return player.injury is None or player.injury.severity=='경미'
    if c=='farm_heavy':return record.farm.PA>=180 and record.first_team.PA<180
    if c=='slump_or_bad_year':return player.form=='slump' or (record.first_team.PA>=80 and record.first_team.OPS<.680)
    if c=='injured':return player.injury is not None
    return False

def choose_season_events(player:Player,record:SeasonRecord,rng:RNG)->list[CareerEvent]:
    target=rng.weighted_choice(config.EVENTS_PER_SEASON_WEIGHTS)
    eligible=[e for e in EVENT_CATALOG if _eligible(e,player,record)];selected=[]
    while eligible and len(selected)<target:
        e=rng.weighted_choice([(x,config.EVENT_RARITY_WEIGHTS[x.rarity]) for x in eligible]);selected.append(e);eligible.remove(e)
    return selected

def auto_choose(event:CareerEvent,player:Player,rng:RNG)->EventChoice:
    weighted=[]
    for c in event.choices:
        w=config.AUTO_EVENT_RISK_WEIGHTS.get(c.risk,.33)
        if c.risk=='risky':w*=max(.75,min(1.25,.92+(player.stats.mentality-70)/350))
        weighted.append((c,w))
    return rng.weighted_choice(weighted)

def _outcome_weight(o:Outcome,choice:EventChoice,player:Player)->float:
    w=o.weight; talent=max(-.18,min(.22,(player.stats.talent-100)/450))
    if o.quality>0:w*=1+talent*.55
    elif o.quality<0:w*=1-talent*.35
    if choice.risk=='risky':
        mental=max(-.15,min(.15,(player.stats.mentality-70)/300))
        if o.quality>0:w*=1+mental
        elif o.quality<0:w*=1-mental*.6
    if has_trait(player.traits,'fast_growth') and o.quality>0:w*=1.08
    if has_trait(player.traits,'slow_growth') and o.quality>0:w*=.94
    if has_trait(player.traits,'injury_risk') and o.injury and o.injury[0] not in {'clear','경미'}:w*=1.12
    if has_trait(player.traits,'quick_recovery') and o.injury and o.injury[0] in {'clear','경미'}:w*=1.10
    if has_trait(player.traits,'volatile') and abs(o.quality)>=2:w*=1.14
    if has_trait(player.traits,'consistent') and abs(o.quality)>=2:w*=.84
    return max(.0001,w)

def resolve_event(event:CareerEvent,choice:EventChoice,player:Player,rng:RNG,year:int)->EventResolution:
    outcome=rng.weighted_choice([(o,_outcome_weight(o,choice,player)) for o in choice.outcomes]);changes={}
    for stat,(lo,hi) in outcome.stat_ranges.items():
        delta=rng.randint(lo,hi);before=getattr(player.stats,stat);after=player.stats.apply_delta(stat,delta);changes[stat]=after-before
    trait_changes=[]
    if outcome.trait_add:
        t=trait_from_key(outcome.trait_add)
        if t not in player.traits and not any(traits_conflict(t,x) for x in player.traits):player.traits.append(t);trait_changes.append('+'+t.key)
    if outcome.trait_remove:
        for t in list(player.traits):
            if t.key==outcome.trait_remove:player.traits.remove(t);trait_changes.append('-'+t.key);break
    injury_change='none'
    if outcome.injury:
        severity,lo,hi=outcome.injury
        if severity=='clear':player.injury=None;injury_change='cleared'
        else:
            games=rng.randint(lo,hi);player.injury=InjuryStatus(f'{event.name} 후 {severity} 부상',severity,games);injury_change=f'{severity}:{games}'
            player.injury_history.append({'year':year,'age':player.age,'name':player.injury.name,'severity':severity,'games':games,'source':'event'})
    player.fatigue=max(0.,min(100.,player.fatigue+outcome.fatigue_delta))
    mods=GrowthModifiers(dict(outcome.growth_means),outcome.variance_multiplier,outcome.explosion_multiplier)
    result=EventResolution(event.id,event.name,choice.id,choice.name,outcome.id,outcome.name,changes,tuple(trait_changes),injury_change,mods)
    player.event_history.append({'year':year,'age':player.age,'event_id':event.id,'event_name':event.name,'chosen_option':choice.id,'chosen_option_name':choice.name,'result':outcome.id,'result_name':outcome.name,'choice_risk':choice.risk,'outcome_quality':outcome.quality,'stat_changes':dict(changes),'trait_changes':list(trait_changes),'injury_changes':injury_change})
    return result
