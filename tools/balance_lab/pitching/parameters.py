"""Pitcher Balance-Lab calibration constants."""
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
