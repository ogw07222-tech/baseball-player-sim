from src.hitting.baserunning import GameState,steal_attempt_probability,steal_success_probability,first_to_third_probability,second_to_home_probability,dp_completion_probability
from src.hitting import parameters as P


def _state():return GameState(inning=8,outs=1,score_diff=0,first_occupied=True,second_occupied=False)

def _value(speed):
    st=_state();a=steal_attempt_probability(speed,st);s=steal_success_probability(speed,st)
    return a*(s*P.SB_RUN_VALUE+(1-s)*P.CS_RUN_VALUE)+P.FIRST_TO_THIRD_OPP_RATE*first_to_third_probability(speed)*P.FIRST_TO_THIRD_VALUE+P.SECOND_TO_HOME_OPP_RATE*second_to_home_probability(speed)*P.SECOND_TO_HOME_VALUE+P.DP_OPP_RATE*(1-dp_completion_probability(speed))*P.DP_AVOIDED_VALUE

def test_speed_steal_monotonic():
    assert steal_attempt_probability(80,_state())<steal_attempt_probability(100,_state())<steal_attempt_probability(125,_state())
    assert steal_success_probability(80,_state())<steal_success_probability(100,_state())<steal_success_probability(125,_state())

def test_speed_xbt_monotonic():
    assert first_to_third_probability(80)<first_to_third_probability(100)<first_to_third_probability(125)
    assert second_to_home_probability(80)<second_to_home_probability(100)<second_to_home_probability(125)

def test_speed_dp_avoidance_monotonic():
    assert 1-dp_completion_probability(80)<1-dp_completion_probability(100)<1-dp_completion_probability(125)

def test_speed_total_value_monotonic():assert _value(80)<_value(100)<_value(125)
def test_speed_high_end_not_flat():assert _value(124)-_value(118)>0.0005

def test_speed_not_pathologically_overpowered():
    st=_state();assert steal_success_probability(150,st)<.95
    assert first_to_third_probability(150)<.90
    assert second_to_home_probability(150)<.92
    assert 1-dp_completion_probability(150)<.90
