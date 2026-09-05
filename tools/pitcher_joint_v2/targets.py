"""Frozen 2025 KBO offense targets/tolerances reused from pitcher calibration v1."""
KBO_TARGETS={
 'AVG':0.2616021705,'OBP':0.3384956950,'SLG':0.3887313600,'OPS':0.7272270551,
 'BB%':0.0914886778,'K%':0.1968712051,'HR%':0.0212693764,'1B%':0.1639759983,
 '2B%':0.0400564326,'3B%':0.0037145510,'BABIP':0.3122366267,
}
TOLERANCES={'AVG':0.010,'OBP':0.010,'SLG':0.020,'BB%':0.010,'K%':0.015,'HR%':0.005,'1B%':0.010,'2B%':0.004,'3B%':0.0015,'BABIP':0.012}
OBJECTIVE_WEIGHTS={'AVG':1.0,'OBP':1.0,'SLG':1.0,'BB%':1.0,'K%':1.0,'HR%':1.0,'1B%':.75,'2B%':.75,'3B%':.5,'BABIP':.75}
# Minimal semantic search set. Velocity is deliberately absent/frozen.
SEARCH_RANGES={
 'w_control_zone':(.40,2.50),
 'w_stuff_quality':(.05,.80),
 'w_stuff_contact':(0.0,.25),
 'w_breaking_contact':(.03,.70),
 'w_breaking_quality':(.03,.60),
}
