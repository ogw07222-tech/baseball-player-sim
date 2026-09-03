"""Prototype balance configuration. Numeric values remain provisional."""
from __future__ import annotations

STAT_MIN=0
STAT_NAMES=('contact','power','discipline','speed','defense','throwing','stamina','durability','mentality','talent')
HITTER_STAT_NAMES=tuple(n for n in STAT_NAMES if n!='talent')
POSITIONS=('C','1B','2B','3B','SS','LF','CF','RF','DH')
BATS_THROWS=('R/R','R/L','L/R','L/L','S/R','S/L')
START_AGE=18; START_YEAR=2026; SAVE_VERSION=2; SUPPORTED_SAVE_VERSIONS=(1,2)
INITIAL_STAT_DISTRIBUTIONS={'contact':(58.,14.),'power':(52.,16.),'discipline':(50.,14.),'speed':(68.,18.),'defense':(60.,15.),'throwing':(62.,16.),'stamina':(72.,14.),'durability':(75.,16.),'mentality':(52.,18.)}
POSITION_ADJUSTMENTS={'SS':{'speed':8,'defense':10,'throwing':8,'power':-5},'CF':{'speed':10,'defense':8,'throwing':3},'1B':{'power':10,'speed':-12,'defense':-4},'C':{'throwing':10,'durability':8,'speed':-12},'3B':{'power':6,'throwing':7},'2B':{'contact':4,'defense':7,'speed':5},'LF':{'power':6,'throwing':5},'RF':{'power':6,'throwing':5},'DH':{'contact':5,'power':10,'defense':-15,'speed':-8}}
TALENT_MIXTURE=((.85,85.,17.,35),(.12,125.,15.,90),(.025,160.,17.,120),(.005,205.,30.,150))
TRAIT_POSITIVE_SHARE=.50; TRAIT_DEFAULT_WEIGHT=1.; TRAIT_WEIGHTS={'fast_growth':.65,'slow_growth':.65,'injury_risk':.70,'clutch':.75}; TRAIT_EFFECT=8.

# Growth v0.3: natural growth is intentionally weak; other systems shape the distribution.
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
 {'name':'KIA 타이거즈','first_team_level':101,'farm_level':83,'depth':100},{'name':'삼성 라이온즈','first_team_level':100,'farm_level':82,'depth':99},{'name':'LG 트윈스','first_team_level':103,'farm_level':84,'depth':104},{'name':'두산 베어스','first_team_level':100,'farm_level':83,'depth':101},{'name':'KT 위즈','first_team_level':100,'farm_level':82,'depth':99},{'name':'SSG 랜더스','first_team_level':101,'farm_level':82,'depth':100},{'name':'롯데 자이언츠','first_team_level':99,'farm_level':81,'depth':98},{'name':'한화 이글스','first_team_level':101,'farm_level':84,'depth':103},{'name':'NC 다이노스','first_team_level':99,'farm_level':82,'depth':98},{'name':'키움 히어로즈','first_team_level':96,'farm_level':80,'depth':91})
POSITION_COMPETITION={'C':4,'1B':1,'2B':3,'3B':2,'SS':5,'LF':0,'CF':4,'RF':1,'DH':-2}
SLUMP_BASE_CHANCE_PER_GAME=.0040; HOT_STREAK_BASE_CHANCE_PER_GAME=.0045; FORM_MIN_GAMES=4; FORM_MAX_GAMES=18; FORM_CONTACT_DELTA=7; FORM_POWER_DELTA=5
INJURY_BASE_CHANCE_PER_GAME=.0016; FATIGUE_PER_GAME_BASE=7.; FATIGUE_REST_RECOVERY=12.
DRAFT_WEIGHTS={'current_ability':.34,'scouted_talent':.28,'performance':.25,'position':.08,'health':.05}
DRAFT_THRESHOLDS={'round1':98.,'round2_3':90.,'round4_7':80.,'round8_11':70.}
DRAFT_SCORE_OFFSET=5.5
POSITION_DRAFT_VALUE={'C':9,'SS':10,'CF':7,'2B':5,'3B':4,'RF':2,'LF':1,'1B':0,'DH':-4}
FIRST_TEAM_PLAY_BASELINE=92.; FARM_PLAY_BASELINE=63.; CALLUP_COMPETITION_OFFSET=14.; FIRST_TEAM_INITIAL_OFFSET=10.
RETIREMENT_HARD_AGE=45

EVENTS_PER_SEASON_WEIGHTS=((1,.35),(2,.50),(3,.15)); EVENT_RARITY_WEIGHTS={'common':1.0,'uncommon':.55,'rare':.20,'career_defining':.035}
AUTO_EVENT_RISK_WEIGHTS={'stable':.40,'medium':.35,'risky':.25}
HAMSTRING_PLAY_THROUGH_WEIGHTS={'great':.08,'success':.42,'failure':.35,'disaster':.15}
HAMSTRING_REHAB_WEIGHTS={'great':.20,'success':.55,'neutral':.22,'failure':.03}
