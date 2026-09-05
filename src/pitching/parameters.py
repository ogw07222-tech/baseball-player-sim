"""Validated pitcher-foundation production constants.

Promoted from tools/balance_lab/pitching at commit 4e16feb4. No H3.2.1 hitter
constants are modified here.
"""
PITCHER_STATS=("velocity","stuff","control","breaking","stamina","resilience")
ABILITY_WEIGHTS={"velocity":.14,"stuff":.25,"control":.22,"breaking":.18,"stamina":.12,"resilience":.09}
BASE_MEANS={"velocity":68.6,"stuff":67.6,"control":67.6,"breaking":66.6,"stamina":70.6,"resilience":70.6}
BASE_SDS={"velocity":10.,"stuff":10.,"control":11.,"breaking":11.,"stamina":12.,"resilience":10.}
PLAYER_BONUS=9.5; PLAYER_SHARED_SD=7.5; NPC_SHARED_SD=4.0
ARCHETYPE_WEIGHTS=(("power",.18),("command",.18),("breaking",.16),("workhorse",.16),("wild_flamethrower",.12),("balanced",.20))
ARCHETYPE_ADJUSTMENTS={
 "power":{"velocity":12,"stuff":8,"control":-8,"breaking":-2},
 "command":{"control":12,"breaking":6,"velocity":-4},
 "breaking":{"breaking":14,"stuff":6,"velocity":-2,"control":-2},
 "workhorse":{"stamina":15,"resilience":12,"stuff":-2,"velocity":-2},
 "wild_flamethrower":{"velocity":16,"stuff":10,"control":-14,"breaking":-3,"stamina":-2},
 "balanced":{},
}
NEUTRAL_BB=.0807; NEUTRAL_K=.213; NEUTRAL_HR=.0275; NEUTRAL_AVG=.261
STARTER_DRAIN=1.0; RELIEVER_DRAIN=1.38; RELIEVER_VELOCITY_BONUS=4.0; RELIEVER_STUFF_BONUS=4.0
STARTER_PITCH_BASE=82.; STARTER_PITCH_STAMINA=.25; RELIEVER_PITCH_BASE=18.; RELIEVER_PITCH_STAMINA=.07
RECOVERY_STARTER_FACTOR=.90; RECOVERY_RELIEVER_FACTOR=.55; RECOVERY_BASE=12.; RECOVERY_RESILIENCE=.08
PERFORMANCE_RELIABILITY_BF=100.0
PERFORMANCE_BASELINES={"k_rate":(.213,.060,1.),"bb_rate":(.081,.040,-1.),"hr_rate":(.0275,.018,-1.),"fip":(4.00,1.00,-1.)}
PERFORMANCE_WEIGHTS={"starter":{"k_rate":.25,"bb_rate":.22,"hr_rate":.18,"fip":.20,"workload":.15},"reliever":{"k_rate":.31,"bb_rate":.25,"hr_rate":.19,"fip":.20,"workload":.05}}
WORKLOAD_BASELINE={"starter":27.0,"reliever":4.3}; WORKLOAD_SD={"starter":7.0,"reliever":1.8}
PITCHER_AGING_MULTIPLIER={"velocity":1.25,"stuff":.90,"control":.45,"breaking":.60,"stamina":1.10,"resilience":.65}
