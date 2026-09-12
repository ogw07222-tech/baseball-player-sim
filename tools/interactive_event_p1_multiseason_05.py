from __future__ import annotations
import json, statistics
from tools.interactive_event_p1_validation_05 import make_engine, DummyProvider, support_matrix
from src.production_advance import ProductionAdvanceService
from src.interactive_events import event_state_for_engine
from src.interactive_event_effects import UnsupportedInteractiveEffect

SEEDS=200
SEASONS=4
BASE=20270912

def quant(xs,p):
    ys=sorted(xs); i=round((len(ys)-1)*p); return ys[i]

rows=[]
_, support, _ = support_matrix()
for i in range(SEEDS):
    e=make_engine(BASE+i)
    per=[]
    for season_idx in range(SEASONS):
        s=ProductionAdvanceService(e,game_provider=DummyProvider())
        generated=0
        for _ in range(144):
            s.advance_one_game(); generated += len(s.drain_generated_interactive_events())
            for ev in list(s.pending_interactive_events):
                choices=support.get(ev.event_type,())
                if choices:
                    try:s.resolve_interactive_event(ev.event_id,choices[0])
                    except UnsupportedInteractiveEffect:pass
        pending=[x.event_type for x in event_state_for_engine(e).pending]
        per.append({"year":e.year,"generated":generated,"pending_count":len(pending),"pending_types":pending})
        s.finalize_season(); s.start_next_season()
    rows.append(per)

by_season=[]
for j in range(SEASONS):
    gen=[r[j]['generated'] for r in rows]; pend=[r[j]['pending_count'] for r in rows]
    by_season.append({
        "season_index":j+1,
        "generated_mean":statistics.fmean(gen),"generated_median":statistics.median(gen),"generated_zero_rate":sum(x==0 for x in gen)/SEEDS,
        "pending_mean":statistics.fmean(pend),"pending_median":statistics.median(pend),"pending_at_3_rate":sum(x>=3 for x in pend)/SEEDS,
    })
final_pending=[r[-1]['pending_count'] for r in rows]
all_final_types={}
for r in rows:
    for t in r[-1]['pending_types']:all_final_types[t]=all_final_types.get(t,0)+1
result={"seeds":SEEDS,"seasons_per_seed":SEASONS,"by_season":by_season,"final_pending_type_counts":all_final_types,
        "final_pending_at_3_rate":sum(x>=3 for x in final_pending)/SEEDS,
        "examples_at_3":[r for r in rows if r[-1]['pending_count']>=3][:5]}
print(json.dumps(result,ensure_ascii=False,indent=2))
open('interactive-event-p1-multiseason.json','w').write(json.dumps(result,ensure_ascii=False,indent=2))
