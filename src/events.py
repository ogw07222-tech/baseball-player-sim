"""In-season, data-driven career events for v0.4.

Choices reshape probability distributions. Event results are sampled only when
an event actually occurs in the career timeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from . import config
from .growth import GrowthModifiers
from .player import InjuryStatus, Player
from .rng import RNG
from .traits import has_trait, trait_from_key, traits_conflict

@dataclass(frozen=True)
class EventContext:
    year:int; game_number:int; season_phase:str; current_level:str; first_pa:int=0; farm_pa:int=0; coach_archetype:str='balanced'

@dataclass(frozen=True)
class Outcome:
    id:str;name:str;weight:float;quality:int=0
    stat_ranges:dict[str,tuple[int,int]]=field(default_factory=dict)
    temporary_ranges:dict[str,tuple[int,int]]=field(default_factory=dict)
    growth_means:dict[str,float]=field(default_factory=dict)
    variance_multiplier:float=1.;explosion_multiplier:float=1.
    injury:tuple[str,int,int]|None=None;fatigue_delta:float=0.;trait_add:str|None=None;trait_remove:str|None=None;form:str|None=None

@dataclass(frozen=True)
class EventChoice:
    id:str;name:str;risk:str;outcomes:tuple[Outcome,...]

@dataclass(frozen=True)
class CareerEvent:
    id:str;name:str;description:str;rarity:str;category:str;condition:str;choices:tuple[EventChoice,...]
    phases:tuple[str,...]=('early','mid','late');weight:float=1.;once_per_season:bool=True;cooldown_games:int=config.EVENT_COOLDOWN_DEFAULT;career_once:bool=False;coach_tags:tuple[str,...]=()
    @property
    def breakthrough_tier(self)->str|None:
        return self.rarity if self.rarity in {'major_breakthrough','legendary_breakthrough'} else None

@dataclass(frozen=True)
class EventResolution:
    event_id:str;event_name:str;choice_id:str;choice_name:str;outcome_id:str;outcome_name:str;quality:int
    stat_changes:dict[str,int];temporary_changes:dict[str,int];trait_changes:tuple[str,...];injury_change:str;growth_modifiers:GrowthModifiers
    ability_before:float;ability_after:float

def O(id,name,w,q=0,stats=None,temp=None,growth=None,var=1.,expl=1.,injury=None,fatigue=0.,trait_add=None,trait_remove=None,form=None)->Outcome:
    return Outcome(id,name,w,q,stats or {},temp or {},growth or {},var,expl,injury,fatigue,trait_add,trait_remove,form)
def C(id,name,risk,*outcomes)->EventChoice:return EventChoice(id,name,risk,tuple(outcomes))

def focus_event(id:str,name:str,description:str,focus:str,category:str='training',phases=('early','mid','late'),weight:float=1.,coach_tags=())->CareerEvent:
    return CareerEvent(id,name,description,'common',category,'always',(
        C('stable','기존 방식을 유지','stable',O('steady','안정',.75,1,growth={focus:.15},var=.90),O('flat','정체',.25,0,var=.94)),
        C('medium','부분적으로 수정','medium',O('good','성공',.58,1,stats={focus:(0,2)},temp={focus:(1,3)},growth={focus:.28}),O('mixed','적응 중',.30,0,temp={focus:(-1,1)},var=1.05),O('bad','실패',.12,-1,stats={focus:(-2,0)},temp={focus:(-2,0)},var=1.10)),
        C('risky','전면 개조','risky',O('breakthrough','대성공',.16,2,stats={focus:(2,5)},temp={focus:(3,6)},growth={focus:.48},var=1.25,expl=1.12),O('upside','성공',.34,1,stats={focus:(0,3)},temp={focus:(1,4)},var=1.18),O('messy','실패',.31,-1,stats={focus:(-3,0)},temp={focus:(-3,0)},var=1.28),O('collapse','대실패',.19,-2,stats={focus:(-5,-2)},temp={focus:(-5,-2)},var=1.36)),
    ),phases=tuple(phases),weight=weight,coach_tags=tuple(coach_tags))

WINTER_TRAINING=CareerEvent('winter_training','겨울 훈련','새 시즌을 앞두고 훈련 방향을 정합니다.','common','training','always',(
    C('contact','컨택 집중','medium',O('good','훈련 성과',.72,1,stats={'contact':(0,2)},growth={'contact':.50}),O('flat','평범',.28,0,growth={'contact':.10})),
    C('power','장타 집중','medium',O('good','훈련 성과',.70,1,stats={'power':(0,2)},growth={'power':.55}),O('flat','평범',.30,0,growth={'power':.10})),
    C('discipline','선구안 집중','medium',O('good','훈련 성과',.72,1,stats={'discipline':(0,2)},growth={'discipline':.50}),O('flat','평범',.28,0,growth={'discipline':.10})),
    C('defense','수비 집중','medium',O('good','훈련 성과',.72,1,stats={'defense':(0,2)},growth={'defense':.50}),O('flat','평범',.28,0,growth={'defense':.10})),
    C('rest','휴식','stable',O('fresh','충분히 회복',.86,1,stats={'stamina':(0,2),'durability':(0,2)},growth={'contact':-.08,'power':-.08},var=.80,fatigue=-40),O('rust','감각 저하',.14,-1,stats={'contact':(-1,0)},var=.86,fatigue=-30)),
),phases=('preseason',),weight=1.45,cooldown_games=144,coach_tags=('power','precision','balanced'))

BATTING_FORM=focus_event('batting_form','타격폼 변경','타격코치가 스윙 수정을 제안했습니다.','contact',weight=.90,coach_tags=('precision','experimental'))
DEFENSE_TRAINING=focus_event('defense_training','수비 집중 훈련','수비 코치가 집중 훈련을 제안했습니다.','defense',weight=.72)
VIDEO_ANALYSIS=CareerEvent('video_analysis','영상 분석','최근 타석 영상을 분석해 접근법을 조정합니다.','common','training','always',(
    C('keep','현재 접근 유지','stable',O('steady','안정',1.,0,growth={'discipline':.10},var=.92)),
    C('study','집중 분석','medium',O('read','패턴 파악',.68,1,stats={'discipline':(0,2)},temp={'contact':(1,3),'discipline':(1,3)},growth={'discipline':.30}),O('noise','정보 과부하',.32,-1,temp={'contact':(-2,0)},var=1.08)),
),phases=('mid','late'),weight=.72,coach_tags=('precision',))
BULK_UP=CareerEvent('bulk_up','벌크업','장타를 위해 체형 변화를 시도할 수 있습니다.','uncommon','training','under_32',(
    C('maintain','현재 체형 유지','stable',O('steady','유지',1.,0,growth={'speed':.05,'durability':.05},var=.94)),
    C('gradual','점진적 벌크업','medium',O('good','성공',.58,1,stats={'power':(1,3),'speed':(-1,0)},growth={'power':.30,'durability':.08}),O('neutral','변화 적음',.32,0,growth={'power':.12}),O('strain','부담',.10,-1,stats={'speed':(-3,-1),'durability':(-2,0)},var=1.08)),
    C('aggressive','강한 벌크업','risky',O('slugger','대성공',.20,2,stats={'power':(3,7),'speed':(-2,0)},temp={'power':(2,5)},growth={'power':.45},var=1.22),O('power_gain','파워 상승',.35,1,stats={'power':(1,4),'speed':(-3,-1)},var=1.17),O('sluggish','민첩성 저하',.28,-1,stats={'speed':(-5,-2),'defense':(-2,0)},var=1.22),O('injured','부상',.17,-2,stats={'durability':(-4,-1),'speed':(-4,-1)},injury=('보통',15,50),var=1.28)),
),phases=('preseason','early'),weight=.58,coach_tags=('power','experimental'))
FARM_DEVELOPMENT=CareerEvent('farm_development','2군 훈련 방향','2군에서 집중할 성장 방향을 정합니다.','common','training','farm_heavy',(
    C('contact','컨택 집중','medium',O('develop','성과',.72,1,stats={'contact':(0,2)},growth={'contact':.52,'discipline':.10,'power':-.10}),O('flat','정체',.28,0,growth={'contact':.12})),
    C('power','장타 집중','medium',O('develop','성과',.68,1,stats={'power':(0,3)},growth={'power':.58,'contact':-.10}),O('flat','정체',.32,0,growth={'power':.12})),
    C('defense','수비 집중','medium',O('develop','성과',.72,1,stats={'defense':(0,2)},growth={'defense':.50,'throwing':.25}),O('flat','정체',.28,0,growth={'defense':.10})),
    C('maintain','현재 훈련 유지','stable',O('steady','유지',1.,0,growth={'contact':.06,'power':.06,'defense':.06},var=.90)),
),phases=('mid','late'),weight=1.05,cooldown_games=55)
COACH_ADVICE=CareerEvent('coach_advice','코치의 집중 조언','현재 타격코치가 특정 훈련을 권합니다.','common','training','always',(
    C('follow','코치 방식을 따른다','medium',O('fit','잘 맞는다',.62,1,temp={'contact':(1,3),'power':(1,3)},growth={'contact':.18,'power':.18},var=.98),O('neutral','보통',.30,0,growth={'contact':.08}),O('mismatch','맞지 않는다',.08,-1,temp={'contact':(-2,0)},var=1.10)),
    C('own','자신의 방식을 유지한다','stable',O('steady','안정',.80,0,var=.91),O('self_discovery','자기 방식 발견',.20,1,stats={'mentality':(1,2)},growth={'discipline':.12})),
    C('experiment','새 방식을 시험한다','risky',O('jump','큰 성과',.20,2,stats={'contact':(1,4),'power':(1,4)},temp={'contact':(2,4)},var=1.25),O('good','성과',.32,1,temp={'contact':(1,3)},var=1.15),O('bad','혼란',.30,-1,temp={'contact':(-3,0)},var=1.25),O('collapse','폼 붕괴',.18,-2,stats={'contact':(-4,-1)},temp={'contact':(-5,-2)},form='slump',var=1.34)),
),phases=('early','mid'),weight=.90,coach_tags=('experimental','precision','power'))

GAME_APPROACH=CareerEvent('game_approach','경기 접근법 조정','최근 경기 흐름에 맞춰 타석 접근법을 바꿀 수 있습니다.','common','performance','always',(
    C('steady','기존 접근 유지','stable',O('steady','안정',1.,0,temp={'discipline':(0,1)},var=.94)),
    C('aggressive','공격적으로 간다','medium',O('hot','효과적',.55,1,temp={'power':(2,4),'discipline':(-1,0)}),O('neutral','보통',.30,0),O('chase','성급함',.15,-1,temp={'discipline':(-3,-1)})),
    C('selective','볼을 더 고른다','medium',O('read','선구안 향상',.58,1,temp={'discipline':(2,4),'contact':(1,2)}),O('passive','소극적',.20,-1,temp={'power':(-2,0)}),O('neutral','보통',.22,0)),
),phases=('early','mid','late'),weight=1.65)
SLUMP_RESPONSE=CareerEvent('slump_response','슬럼프 대응','부진이 이어지고 있습니다. 대응 방식을 선택합니다.','common','performance','slump',(
    C('play','계속 출전','risky',O('break','돌파',.28,2,stats={'mentality':(1,4)},temp={'contact':(2,5)},form='normal'),O('grind','버틴다',.34,1,stats={'mentality':(0,2)}),O('worse','악화',.38,-1,temp={'contact':(-3,0)},form='slump',var=1.15)),
    C('rest','잠시 휴식','stable',O('reset','회복',.70,1,fatigue=-35,form='normal'),O('slow','회복 지연',.30,0,fatigue=-20)),
    C('change','타격폼 수정','medium',O('fix','수정 성공',.48,1,stats={'contact':(0,2)},temp={'contact':(2,4)},form='normal'),O('mixed','혼합',.32,0),O('lost','더 흔들림',.20,-1,temp={'contact':(-3,-1)},form='slump')),
),phases=('mid','late'),weight=1.60,cooldown_games=35)

MOMENTUM_CHECK=CareerEvent('momentum_check','경기 흐름 점검','최근 경기 흐름에 맞춰 컨디션과 접근법을 재조정합니다.','common','performance','always',(
    C('steady','페이스 유지','stable',O('steady','안정',.78,1,temp={'contact':(0,2)},var=.93),O('flat','변화 없음',.22,0)),
    C('push','공격적 전환','medium',O('hot','상승세',.52,1,temp={'contact':(1,3),'power':(2,4)},form='hot'),O('neutral','보통',.31,0),O('press','과욕',.17,-1,temp={'discipline':(-3,-1)},form='slump')),
    C('reset','짧게 리셋','stable',O('fresh','회복',.72,1,fatigue=-25,form='normal'),O('quiet','효과 적음',.28,0,fatigue=-12)),
),phases=('mid','late'),weight=1.35,cooldown_games=40)

HAMSTRING=CareerEvent('hamstring_warning','햄스트링 이상 징후','햄스트링에 이상이 느껴집니다. 계속 뛰거나 재활을 선택할 수 있습니다.','uncommon','injury','healthy',(
    C('play_through','참고 계속 출전한다','risky',O('great','대성공',.15,3,stats={'mentality':(6,10),'durability':(2,4),'power':(2,4)},temp={'speed':(1,3)},growth={'contact':.30,'power':.40},injury=('clear',0,0),var=1.22,expl=1.10),O('success','문제 없이 버팀',.50,1,stats={'mentality':(1,4)},growth={'contact':.08,'power':.10},var=1.08),O('failure','악화',.22,-1,stats={'durability':(-3,-1)},injury=('보통',15,45),var=1.22),O('disaster','대실패',.13,-2,stats={'speed':(-5,-2),'power':(-3,-1),'durability':(-5,-2)},injury=('중상',60,150),var=1.32)),
    C('rehab','재활 치료를 받는다','stable',O('great','매우 좋은 회복',.14,2,stats={'durability':(2,4),'stamina':(1,3)},injury=('경미',8,16),var=.80),O('success','정상 회복',.53,1,stats={'durability':(0,2)},injury=('경미',12,24),var=.84),O('neutral','예상대로 회복',.30,0,injury=('경미',18,30),var=.87),O('failure','회복 지연',.03,-1,stats={'stamina':(-2,0)},injury=('보통',28,45),var=.90)),
),phases=('mid','late'),weight=1.10,cooldown_games=144)
INJURY_RETURN=CareerEvent('injury_return','부상 복귀 시점','복귀 시점을 결정합니다.','rare','injury','injured_returning',(
    C('early','조기 복귀','risky',O('fine','문제 없이 복귀',.34,1,stats={'mentality':(1,3)},injury=('clear',0,0)),O('setback','재발',.46,-1,stats={'durability':(-3,-1)},injury=('보통',20,55)),O('major','큰 재발',.20,-2,stats={'durability':(-6,-2),'speed':(-4,-1)},injury=('중상',60,130))),
    C('normal','정상 복귀','medium',O('fine','정상 복귀',.72,1,injury=('clear',0,0)),O('delay','약간 지연',.25,0,injury=('경미',5,15)),O('setback','가벼운 재발',.03,-1,injury=('보통',15,35))),
    C('full','완전 회복 후 복귀','stable',O('strong','완전 회복',.58,1,stats={'durability':(1,3)},injury=('clear',0,0),var=.84),O('fine','안정 복귀',.40,0,injury=('clear',0,0),var=.86),O('slow','회복 지연',.02,-1,injury=('경미',5,12))),
),phases=('early','mid','late'),weight=1.15,cooldown_games=144)

# Breakthrough events: stronger average upside, but not guaranteed success.
BATTING_MECHANICS_COMPLETE=CareerEvent('batting_mechanics_complete','대박 이벤트: 타격 메커니즘 완성','여러 시행착오 끝에 스윙 메커니즘이 맞아들어가기 시작합니다.','major_breakthrough','breakthrough','always',(
    C('refine','현재 감각을 다듬는다','stable',O('solid','확실한 진전',.72,1,stats={'contact':(3,7),'power':(2,6),'discipline':(1,4)},growth={'contact':.25,'power':.20}),O('small','작은 진전',.28,0,stats={'contact':(1,3)})),
    C('commit','완전히 체화한다','risky',O('career_jump','커리어 점프',.24,3,stats={'contact':(8,16),'power':(6,13),'discipline':(3,8)},temp={'contact':(2,5),'power':(2,5)},expl=1.25),O('big','큰 성장',.42,2,stats={'contact':(5,10),'power':(3,8),'discipline':(2,5)}),O('mixed','부분 성공',.24,1,stats={'contact':(2,5),'power':(1,4)}),O('lost','오버튜닝',.10,-1,stats={'contact':(-3,0),'power':(-2,1)},temp={'contact':(-3,0)})),
),phases=('mid','late'),weight=.48,career_once=False,cooldown_games=144,coach_tags=('precision','experimental'))
PHYSICAL_COMPLETION=CareerEvent('physical_completion','대박 이벤트: 피지컬 완성','젊은 시기의 신체 발달이 경기력으로 연결될 조짐을 보입니다.','major_breakthrough','breakthrough','young',(
    C('balanced','균형 있게 강화','medium',O('great','큰 성장',.50,2,stats={'power':(6,12),'stamina':(3,7),'throwing':(2,6)},temp={'power':(1,3)}),O('good','성장',.40,1,stats={'power':(3,7),'stamina':(2,5)}),O('strain','과부하',.10,-1,stats={'durability':(-3,0)})),
    C('max_power','파워에 집중','risky',O('monster','대성공',.22,3,stats={'power':(10,20),'stamina':(3,7),'speed':(-3,0)}),O('power','성공',.43,2,stats={'power':(6,12),'speed':(-2,0)}),O('heavy','둔화',.25,0,stats={'power':(3,7),'speed':(-5,-2)}),O('injury','부담',.10,-1,stats={'durability':(-4,-1)},injury=('보통',15,45))),
),phases=('preseason','early','mid'),weight=.82,career_once=True,coach_tags=('power',))
COACH_SYNERGY=CareerEvent('coach_synergy','대박 이벤트: 코치와 완벽한 궁합','현재 코치의 육성 방식이 선수와 놀랍도록 잘 맞습니다.','major_breakthrough','breakthrough','always',(
    C('trust','코치 플랜을 따른다','medium',O('click','궁합 폭발',.55,2,stats={'contact':(3,7),'power':(3,7),'discipline':(2,6)},growth={'contact':.65,'power':.65,'discipline':.55},var=.92),O('good','좋은 시너지',.38,1,stats={'contact':(1,4),'discipline':(1,4)},growth={'contact':.35,'discipline':.30}),O('overfit','과적응',.07,-1,temp={'contact':(-2,0)})),
),phases=('early','mid'),weight=.38,career_once=False,cooldown_games=144)
PERFECT_SWING=CareerEvent('perfect_swing','대박 이벤트: 완벽한 타격폼 발견','우연한 조정이 지금까지 가장 자연스러운 타격폼으로 이어집니다.','major_breakthrough','breakthrough','always',(
    C('keep','미세조정만 한다','stable',O('lock','폼 정착',.76,2,stats={'contact':(4,8),'power':(3,7)},temp={'contact':(2,4),'power':(1,3)}),O('good','좋은 변화',.24,1,stats={'contact':(2,5),'power':(1,4)})),
    C('rebuild','전면 개조한다','risky',O('elite','대성공',.20,3,stats={'contact':(8,14),'power':(7,14),'discipline':(3,7)},temp={'contact':(3,6),'power':(3,6)}),O('big','큰 성공',.38,2,stats={'contact':(5,9),'power':(4,9)}),O('okay','부분 성공',.27,1,stats={'contact':(2,5),'power':(1,4)}),O('collapse','폼 붕괴',.15,-2,stats={'contact':(-6,-2),'power':(-5,-1)},temp={'contact':(-5,-2)},form='slump')),
),phases=('mid','late'),weight=.78,career_once=True,coach_tags=('experimental',))
LATE_BLOOM=CareerEvent('late_bloom_explosion','대박 이벤트: 늦깎이 폭발','정체되어 있던 기술이 뒤늦게 연결되기 시작합니다.','major_breakthrough','breakthrough','late_bloom',(
    C('embrace','변화를 받아들인다','medium',O('burst','폭발 성장',.48,3,stats={'contact':(8,16),'power':(8,18)},growth={'contact':.35,'power':.40}),O('rise','큰 성장',.42,2,stats={'contact':(5,10),'power':(4,10)}),O('flash','반짝 효과',.10,0,temp={'contact':(2,5),'power':(2,5)})),
),phases=('mid','late'),weight=1.1,career_once=True)
POST_INJURY_AWAKENING=CareerEvent('post_injury_awakening','대박 이벤트: 부상 후 각성','부상과 재활을 거치며 경기 접근이 달라졌습니다.','major_breakthrough','breakthrough','post_injury',(
    C('new_way','새 방식을 유지한다','medium',O('awake','각성',.50,2,stats={'mentality':(5,10),'contact':(3,7),'discipline':(2,6)}),O('good','긍정적 변화',.42,1,stats={'mentality':(3,6),'contact':(1,4)}),O('hesitate','아직 불안',.08,-1,temp={'contact':(-2,0)})),
),phases=('mid','late'),weight=.62,career_once=True)
GENERATIONAL_BLOOM=CareerEvent('generational_talent_bloom','전설적 이벤트: 세대급 재능 개화','숨겨져 있던 최상위 재능이 한꺼번에 실전 능력으로 연결됩니다.','legendary_breakthrough','breakthrough','high_talent',(
    C('commit','재능을 완전히 밀어붙인다','risky',O('legend','전설적 개화',.30,4,stats={'contact':(10,18),'power':(10,20),'discipline':(6,12),'defense':(3,8)},trait_add='fast_growth'),O('star','스타급 성장',.48,3,stats={'contact':(7,13),'power':(7,14),'discipline':(4,9)}),O('partial','부분 개화',.18,1,stats={'contact':(3,7),'power':(3,7)}),O('overreach','과욕',.04,-1,stats={'contact':(-3,0),'power':(-3,0)})),
),phases=('mid','late'),weight=.75,career_once=True)
MIRACLE_BREAKOUT=CareerEvent('miracle_breakout','전설적 이벤트: 예상 밖의 완성','낮은 평가를 뒤집는 비정상적으로 큰 기술적 도약의 기회가 찾아옵니다.','legendary_breakthrough','breakthrough','miracle_candidate',(
    C('chance','기회를 잡는다','risky',O('miracle','기적의 완성',.22,4,stats={'contact':(10,20),'power':(8,18),'discipline':(6,12),'mentality':(4,9)}),O('huge','대성공',.38,3,stats={'contact':(7,13),'power':(6,12),'discipline':(3,8)}),O('good','성공',.28,2,stats={'contact':(4,8),'power':(3,7)}),O('miss','기회 상실',.12,-1,stats={'mentality':(-3,0)})),
),phases=('mid','late'),weight=.52,career_once=True)

EVENT_CATALOG=(WINTER_TRAINING,BATTING_FORM,DEFENSE_TRAINING,VIDEO_ANALYSIS,BULK_UP,FARM_DEVELOPMENT,COACH_ADVICE,GAME_APPROACH,SLUMP_RESPONSE,MOMENTUM_CHECK,HAMSTRING,INJURY_RETURN,BATTING_MECHANICS_COMPLETE,PHYSICAL_COMPLETION,COACH_SYNERGY,PERFECT_SWING,LATE_BLOOM,POST_INJURY_AWAKENING,GENERATIONAL_BLOOM,MIRACLE_BREAKOUT)
EVENT_BY_ID={e.id:e for e in EVENT_CATALOG}

def eligible(event:CareerEvent,player:Player,ctx:EventContext)->bool:
    if ctx.season_phase not in event.phases:return False
    c=event.condition
    if c=='always':return True
    if c=='under_32':return player.age<=31
    if c=='healthy':return player.injury is None
    if c=='farm_heavy':return ctx.farm_pa>=120 and ctx.first_pa<160 and ctx.current_level=='FARM'
    if c=='slump':return player.form=='slump'
    if c=='injured_returning':return player.injury is not None and player.injury.games_remaining<=12
    if c=='young':return player.age<=23
    if c=='late_bloom':return player.age>=27 and player.development_profile in {'late_bloomer','very_late_bloomer'}
    if c=='post_injury':return player.injury is None and bool(player.injury_history) and player.age>=22
    if c=='high_talent':return player.stats.talent>=145
    if c=='miracle_candidate':return player.stats.current_ability()<100 and 23<=player.age<=34
    return False

def event_weight(event:CareerEvent,player:Player,ctx:EventContext)->float:
    w=event.weight*config.EVENT_RARITY_WEIGHTS[event.rarity]
    coach=ctx.coach_archetype
    if event.coach_tags and coach in event.coach_tags:w*=1.35
    if coach=='experimental' and any(c.risk=='risky' for c in event.choices):w*=1.12
    if event.id=='late_bloom_explosion' and player.development_profile=='very_late_bloomer':w*=1.45
    if event.breakthrough_tier:
        w*=max(.15,min(3.0,player.breakthrough_affinity))
        if not event.career_once:
            repeats=sum(1 for x in player.event_history if x.get('event_id')==event.id)
            w*=.55**repeats
        if player.stats.talent>120:w*=1+min(.18,(player.stats.talent-120)/500)
    return max(.0001,w)

def auto_choose(event:CareerEvent,player:Player,rng:RNG)->EventChoice:
    weighted=[]
    for c in event.choices:
        w=config.AUTO_EVENT_RISK_WEIGHTS.get(c.risk,.33)
        if c.risk=='risky':w*=max(.72,min(1.28,.92+(player.stats.mentality-70)/320))
        weighted.append((c,w))
    return rng.weighted_choice(weighted)

def _outcome_weight(o:Outcome,choice:EventChoice,player:Player)->float:
    w=o.weight;tal=max(-.18,min(.22,(player.stats.talent-100)/450))
    if o.quality>0:w*=1+tal*.55
    elif o.quality<0:w*=1-tal*.35
    if choice.risk=='risky':
        mental=max(-.16,min(.16,(player.stats.mentality-70)/300))
        if o.quality>0:w*=1+mental
        elif o.quality<0:w*=1-mental*.6
    if has_trait(player.traits,'fast_growth') and o.quality>0:w*=1.08
    if has_trait(player.traits,'slow_growth') and o.quality>0:w*=.94
    if has_trait(player.traits,'injury_risk') and o.injury and o.injury[0] not in {'clear','경미'}:w*=1.12
    if has_trait(player.traits,'quick_recovery') and o.injury and o.injury[0] in {'clear','경미'}:w*=1.10
    if has_trait(player.traits,'volatile') and abs(o.quality)>=2:w*=1.14
    if has_trait(player.traits,'consistent') and abs(o.quality)>=2:w*=.84
    return max(.0001,w)

def resolve_event(event:CareerEvent,choice:EventChoice,player:Player,rng:RNG,year:int,context:EventContext|None=None)->EventResolution:
    ability_before=player.stats.current_ability();outcome=rng.weighted_choice([(o,_outcome_weight(o,choice,player)) for o in choice.outcomes]);changes={};temps={}
    for stat,(lo,hi) in outcome.stat_ranges.items():
        delta=rng.randint(lo,hi);before=getattr(player.stats,stat);after=player.stats.apply_delta(stat,delta);changes[stat]=after-before
    for stat,(lo,hi) in outcome.temporary_ranges.items():
        delta=rng.randint(lo,hi);player.add_season_modifier(stat,delta);temps[stat]=delta
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
            games=rng.randint(lo,hi);player.injury=InjuryStatus(f'{event.name} 후 {severity} 부상',severity,games);injury_change=f'{severity}:{games}';player.injury_history.append({'year':year,'age':player.age,'name':player.injury.name,'severity':severity,'games':games,'source':'event'})
    player.fatigue=max(0.,min(100.,player.fatigue+outcome.fatigue_delta))
    if outcome.form:
        player.form=outcome.form;player.form_games_remaining=max(player.form_games_remaining,8 if outcome.form!='normal' else 0)
    mods=GrowthModifiers(dict(outcome.growth_means),outcome.variance_multiplier,outcome.explosion_multiplier);ability_after=player.stats.current_ability()
    ctx=context or EventContext(year,0,'offseason',player.roster_level)
    entry={'year':year,'age':player.age,'game_number':ctx.game_number,'season_phase':ctx.season_phase,'event_id':event.id,'event_name':event.name,'rarity':event.rarity,'category':event.category,'breakthrough_tier':event.breakthrough_tier,'choice':choice.id,'chosen_option':choice.id,'choice_name':choice.name,'choice_risk':choice.risk,'outcome':outcome.id,'result':outcome.id,'outcome_name':outcome.name,'outcome_quality':outcome.quality,'stat_changes':dict(changes),'temporary_effects':dict(temps),'trait_changes':list(trait_changes),'injury_changes':injury_change,'ability_before':round(ability_before,4),'ability_after':round(ability_after,4)}
    player.event_history.append(entry)
    return EventResolution(event.id,event.name,choice.id,choice.name,outcome.id,outcome.name,outcome.quality,changes,temps,tuple(trait_changes),injury_change,mods,ability_before,ability_after)
