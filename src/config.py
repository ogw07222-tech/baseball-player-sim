"""Prototype balance configuration for v0.4 / H3.2.1 production candidate.

DESIGN.md remains the game-design source of truth. Numeric values here are
provisional defaults that are validated with Monte Carlo simulation.
"""
from __future__ import annotations

STAT_MIN=0
STAT_NAMES=('contact','power','discipline','speed','defense','throwing','stamina','durability','mentality','talent')
HITTER_STAT_NAMES=tuple(n for n in STAT_NAMES if n!='talent')
POSITIONS=('C','1B','2B','3B','SS','LF','CF','RF','DH')
BATS_THROWS=('R/R','R/L','L/R','L/L','S/R','S/L')
START_AGE=18; START_YEAR=2026; SAVE_VERSION=3; SUPPORTED_SAVE_VERSIONS=(1,2,3)

# Shared neutral high-school stat shape. Player/NPC cohort overlays below move
# the resulting current-ability distribution without generating ability directly.
INITIAL_STAT_DISTRIBUTIONS={
    'contact':(69.,14.),'power':(65.,16.),'discipline':(63.,14.),
    'speed':(75.,18.),'defense':(70.,15.),'throwing':(70.,16.),
    'stamina':(78.,14.),'durability':(80.,16.),'mentality':(63.,18.),
}
# The protagonist is a notable draft prospect by default, but keeps a thicker
# shared talent/current-skill tail so low-start and instant-impact careers exist.
PLAYER_STARTING_STAT_BONUS=10.0
PLAYER_STARTING_SHARED_OFFSET_SD=8.0
# Generic high-school population stays lower and tighter than the protagonist.
NPC_STARTING_STAT_BONUS=0.0
NPC_STARTING_SHARED_OFFSET_SD=4.0
POSITION_ADJUSTMENTS={
    'SS':{'speed':8,'defense':10,'throwing':8,'power':-5},
    'CF':{'speed':10,'defense':8,'throwing':3},'1B':{'power':10,'speed':-12,'defense':-4},
    'C':{'throwing':10,'durability':8,'speed':-12},'3B':{'power':6,'throwing':7},
    '2B':{'contact':4,'defense':7,'speed':5},'LF':{'power':6,'throwing':5},
    'RF':{'power':6,'throwing':5},'DH':{'contact':5,'power':10,'defense':-15,'speed':-8},
}
TALENT_MIXTURE=((.85,85.,17.,35),(.12,125.,15.,90),(.025,160.,17.,120),(.005,205.,30.,150))
TRAIT_POSITIVE_SHARE=.50; TRAIT_DEFAULT_WEIGHT=1.; TRAIT_WEIGHTS={'fast_growth':.65,'slow_growth':.65,'injury_risk':.70,'clutch':.75}; TRAIT_EFFECT=8.

# Growth v0.3/v0.4 philosophy is retained: natural growth stays weak.
GROWTH_BASE_STDDEV=3.15
GROWTH_TALENT_REFERENCE=100.; GROWTH_TALENT_SCALE=.016
GROWTH_CURRENT_STAT_DAMPING=.0030
GROWTH_EXPLOSION_BASE_CHANCE=.009
GROWTH_EXPLOSION_TALENT_SCALE=.000055
GROWTH_EXPLOSION_MIN_BONUS=4; GROWTH_EXPLOSION_MAX_BONUS=13
AGE_GROWTH_BIAS={(0,22):2.0,(23,27):1.2,(28,31):.15,(32,35):-1.25,(36,200):-2.65}
AGING_MULTIPLIER={'contact':.80,'power':.95,'discipline':.35,'speed':1.55,'defense':1.05,'throwing':.90,'stamina':1.30,'durability':1.40,'mentality':.20}
DEVELOPMENT_PROFILE_WEIGHTS=(('early_bloomer',.20),('normal',.55),('late_bloomer',.20),('very_late_bloomer',.05))
DEVELOPMENT_PROFILE_AGE_BIAS={
 'early_bloomer':((18,22,.90),(23,24,.30),(25,27,-.80),(28,31,-1.40),(32,200,-.35)),
 'normal':((18,24,.10),(25,28,.25),(29,31,-1.15),(32,200,0.)),
 'late_bloomer':((18,23,-.60),(24,26,-.10),(27,29,.80),(30,30,.45),(31,33,-.45),(34,200,0.)),
 'very_late_bloomer':((18,24,-.90),(25,27,-.35),(28,31,.90),(32,32,.50),(33,34,-.20),(35,200,0.)),
}
EXPERIENCE_FIRST_PA_REFERENCE=450.; EXPERIENCE_FARM_PA_REFERENCE=380.; EXPERIENCE_MAX_MEAN_BONUS=.45; EXPERIENCE_LOW_PLAY_PENALTY=-.30
COACH_MEAN_DIVISOR=30.; COACH_STABILITY_VARIANCE_SCALE=.012; COACH_EXPERIMENT_VARIANCE_SCALE=.015; COACH_REPLACEMENT_CHANCE=.11
COACH_ARCHETYPES={
 'power':{'contact_development':-8,'power_development':26,'discipline_development':-6,'stability':-5,'experimentation':20},
 'precision':{'contact_development':24,'power_development':-8,'discipline_development':18,'stability':18,'experimentation':-8},
 'balanced':{'contact_development':8,'power_development':8,'discipline_development':8,'stability':10,'experimentation':2},
 'experimental':{'contact_development':5,'power_development':13,'discipline_development':-2,'stability':-15,'experimentation':30},
}
FIELDING_COACH_ARCHETYPES={
 'defense':{'defense_development':23,'throwing_development':10,'speed_development':5,'stability':14,'experimentation':-4},
 'arm':{'defense_development':6,'throwing_development':25,'speed_development':0,'stability':4,'experimentation':6},
 'athletic':{'defense_development':12,'throwing_development':2,'speed_development':18,'stability':2,'experimentation':12},
 'balanced':{'defense_development':8,'throwing_development':8,'speed_development':8,'stability':10,'experimentation':2},
}

HIGH_SCHOOL_TOURNAMENTS=('청룡기','황금사자기','대통령배','봉황대기'); HIGH_SCHOOL_PITCHER_LEVEL=(55,75)
KBO_FIRST_TEAM_GAMES=144; KBO_FARM_GAMES=120
KBO_TEAMS=(
 {'name':'KIA 타이거즈','first_team_level':101,'farm_level':83,'depth':100},
 {'name':'삼성 라이온즈','first_team_level':100,'farm_level':82,'depth':99},
 {'name':'LG 트윈스','first_team_level':103,'farm_level':84,'depth':104},
 {'name':'두산 베어스','first_team_level':100,'farm_level':83,'depth':101},
 {'name':'KT 위즈','first_team_level':100,'farm_level':82,'depth':99},
 {'name':'SSG 랜더스','first_team_level':101,'farm_level':82,'depth':100},
 {'name':'롯데 자이언츠','first_team_level':99,'farm_level':81,'depth':98},
 {'name':'한화 이글스','first_team_level':101,'farm_level':84,'depth':103},
 {'name':'NC 다이노스','first_team_level':99,'farm_level':82,'depth':98},
 {'name':'키움 히어로즈','first_team_level':96,'farm_level':80,'depth':91},
)
POSITION_COMPETITION={'C':4,'1B':1,'2B':3,'3B':2,'SS':5,'LF':0,'CF':4,'RF':1,'DH':-2}
SLUMP_BASE_CHANCE_PER_GAME=.0040; HOT_STREAK_BASE_CHANCE_PER_GAME=.0045; FORM_MIN_GAMES=4; FORM_MAX_GAMES=18; FORM_CONTACT_DELTA=7; FORM_POWER_DELTA=5
INJURY_BASE_CHANCE_PER_GAME=.00135; FATIGUE_PER_GAME_BASE=7.; FATIGUE_REST_RECOVERY=12.

# Draft performance normalization. Values are frozen career-layer calibration
# assumptions for the H3.2.1 high-school environment, not H3.2.1 hitting math.
HIGH_SCHOOL_PERFORMANCE_RELIABILITY_PA=45.0
HIGH_SCHOOL_PERFORMANCE_BASELINES={
    'obp':(.200,.080,1.0),
    'iso':(.053,.065,1.0),
    'hr_rate':(.010,.018,1.0),
    'bb_rate':(.049,.041,1.0),
    'k_rate':(.208,.073,-1.0),
    'baserunning':(0.000,.025,1.0),
}
OVERALL_HITTER_PERFORMANCE_WEIGHTS={'obp':.30,'iso':.20,'hr_rate':.12,'bb_rate':.12,'k_rate':.16,'baserunning':.10}
# Catcher is intentionally absent. Its receiving/framing/blocking/game-calling
# model is pending and uses an explicit legacy fallback in draft_scoring.py.
POSITION_PERFORMANCE_WEIGHTS={
    '1B':{'obp':.28,'iso':.30,'hr_rate':.24,'bb_rate':.08,'k_rate':.07,'baserunning':.03},
    'LF':{'obp':.28,'iso':.28,'hr_rate':.22,'bb_rate':.09,'k_rate':.08,'baserunning':.05},
    'RF':{'obp':.28,'iso':.28,'hr_rate':.22,'bb_rate':.09,'k_rate':.08,'baserunning':.05},
    'DH':{'obp':.27,'iso':.31,'hr_rate':.25,'bb_rate':.08,'k_rate':.07,'baserunning':.02},
    '2B':{'obp':.30,'iso':.12,'hr_rate':.06,'bb_rate':.15,'k_rate':.20,'baserunning':.17},
    'SS':{'obp':.30,'iso':.10,'hr_rate':.05,'bb_rate':.15,'k_rate':.21,'baserunning':.19},
    'CF':{'obp':.29,'iso':.12,'hr_rate':.07,'bb_rate':.13,'k_rate':.19,'baserunning':.20},
    '3B':{'obp':.28,'iso':.23,'hr_rate':.15,'bb_rate':.11,'k_rate':.13,'baserunning':.10},
}
CATCHER_LEGACY_PERFORMANCE_WEIGHTS={'obp':.30,'iso':.20,'hr_rate':.12,'bb_rate':.14,'k_rate':.18,'baserunning':.06}
DRAFT_WEIGHTS={'performance':.80,'scouting':.10,'position':.06,'health':.02,'context':.02,'current_ability':0.0}
DRAFT_COMPONENT_REFERENCE=100.0
DRAFT_COMPONENT_SCALE=15.0
DRAFT_SCORE_CENTER=83.0
DRAFT_SCORE_SPREAD=48.25
DRAFT_RANDOM_SD=3.0
DRAFT_THRESHOLDS={'round1':105.,'round2_3':97.,'round4_7':86.8,'round8_11':76.2}
POSITION_DRAFT_VALUE={'C':9,'SS':10,'CF':7,'2B':5,'3B':4,'RF':2,'LF':1,'1B':0,'DH':-4}

FIRST_TEAM_PLAY_BASELINE=92.; FARM_PLAY_BASELINE=71.; CALLUP_COMPETITION_OFFSET=5.; FIRST_TEAM_INITIAL_OFFSET=5.
RETIREMENT_HARD_AGE=45

# In-season event scheduler v0.4.
EVENT_BASE_CHANCE_PER_GAME=.0155
EVENT_PRESEASON_CHANCE=.78
EVENT_MIN_GAP_GAMES=13
EVENT_RARITY_WEIGHTS={'common':1.0,'uncommon':.72,'rare':.38,'major_breakthrough':1.00,'legendary_breakthrough':.80}
AUTO_EVENT_RISK_WEIGHTS={'stable':.40,'medium':.35,'risky':.25}
EVENT_CATEGORY_TARGETS={'training':(.55,.70),'performance':(.15,.25),'injury':(.05,.15),'breakthrough':(.05,.12)}
EVENT_COOLDOWN_DEFAULT=42
MAJOR_BREAKTHROUGH_TARGET_PER_SEASON=.25
LEGENDARY_BREAKTHROUGH_MAX_PER_SEASON=.05
BREAKTHROUGH_AFFINITY_WEIGHTS=((.25,.12),(.55,.18),(1.0,.45),(1.45,.18),(2.0,.06),(2.8,.01))
ESTABLISHED_FIRST_TEAM_PA=500
ESTABLISHED_FIRST_TEAM_ABILITY_FLOOR=82.
ESTABLISHED_DEMOTION_MARGIN=22.
REGULAR_DEMOTION_MARGIN=13.
