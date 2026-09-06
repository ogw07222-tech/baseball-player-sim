from __future__ import annotations

import argparse
import bisect
import csv
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from src.hitting.model import HitterSnapshot
from src.pitching.model import PitcherStats
from tools.pitcher_joint_v3 import calibrate as v3
from tools.pitcher_joint_v3.adapter import JointWeights, PitcherJointV3Adapter
from tools.pitcher_joint_v3.targets import SEARCH_RANGES


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def hitter_from_row(row: dict[str, str]) -> HitterSnapshot:
    hand = "L" if row.get("bats_throws", "R").startswith("L") else "R"
    return HitterSnapshot(float(row["gp_contact"]), float(row["gp_power"]), float(row["gp_discipline"]), float(row["gp_speed"]), hand, "balanced")


def pitcher_from_row(row: dict[str, str]) -> PitcherStats:
    return PitcherStats(
        velocity=int(round(float(row["raw_velocity"]))),
        stuff=int(round(float(row["raw_stuff"]))),
        control=int(round(float(row["raw_control"]))),
        breaking=int(round(float(row["raw_breaking"]))),
        stamina=100, resilience=100, talent=100,
    )


def cumulative_weights(rows: list[dict[str, str]], field: str) -> tuple[list[float], float]:
    out=[]; total=0.0
    for row in rows:
        w=max(0.0,float(row[field])); total+=w; out.append(total)
    if total <= 0: raise ValueError("non-positive total sampling weight")
    return out,total


def pick_weighted(rows, cumulative, total, rng):
    x=rng.random()*total
    return rows[bisect.bisect_right(cumulative,x)]


def sim(weights: JointWeights, hitters, pitchers, pa: int, seed: int) -> dict[str,float]:
    hc,ht=cumulative_weights(hitters,"first_team_PA")
    pc,pt=cumulative_weights(pitchers,"weight")
    choose=random.Random(seed ^ 0xA17E); rng=random.Random(seed ^ 0xC0DE)
    counts=Counter(); balls=Counter(); hard=0
    for _ in range(pa):
        hr=pick_weighted(hitters,hc,ht,choose); pr=pick_weighted(pitchers,pc,pt,choose)
        h=hitter_from_row(hr); p=pitcher_from_row(pr)
        o=PitcherJointV3Adapter(p,weights).make_engine(h,100.0,rng).simulate_plate_appearance()
        counts[o.result]+=1
        if o.batted_ball is not None:
            balls[o.batted_ball.ball_type]+=1
            hard += int(o.batted_ball.exit_quality >= .75)
    return v3.metrics(counts,balls,pa,hard)


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--population-dir",default="reports")
    ap.add_argument("--candidates",type=int,default=60)
    ap.add_argument("--search-pa",type=int,default=100000)
    ap.add_argument("--top",type=int,default=5)
    ap.add_argument("--validation-pa",type=int,default=1000000)
    ap.add_argument("--seeds",type=int,default=5)
    ap.add_argument("--diag-pa",type=int,default=300000)
    ap.add_argument("--seed",type=int,default=261406)
    args=ap.parse_args(); d=Path(args.population_dir)
    summary=json.loads((d/"kbo_first_team_population_summary.json").read_text())
    if summary["gate"] != "KBO_FIRST_TEAM_POPULATION_CONTRACT_READY":
        result={"gate":"PITCHER_JOINT_CALIBRATION_V4_NOT_RUN","reason":"first-team population contract not READY"}
        (d/"pitcher_joint_v4_first_team_final.json").write_text(json.dumps(result,indent=2)); print(json.dumps(result)); return
    hitters=load_csv(d/"kbo_generated_first_team_hitter_population.csv")
    pitchers=load_csv(d/"kbo_generated_first_team_pitcher_population.csv")
    r=random.Random(args.seed)
    candidates=[JointWeights()]+[JointWeights(**{k:r.uniform(*bounds) for k,bounds in SEARCH_RANGES.items()}) for _ in range(args.candidates-1)]
    searched=[]
    for w in candidates:
        m=sim(w,hitters,pitchers,args.search_pa,args.seed+11)
        searched.append((v3.loss(m),w,m))
    searched.sort(key=lambda x:x[0])
    validated=[]
    for rank,(search_loss,w,_) in enumerate(searched[:args.top],1):
        runs=[sim(w,hitters,pitchers,args.validation_pa,args.seed+1000+s) for s in range(args.seeds)]
        mean=v3.avg_runs(runs)
        validated.append({"rank":rank,"search_loss":search_loss,"weights":w.as_dict(),"metrics":mean,"loss":v3.loss(mean),"passed_tolerances":v3.pass_tol(mean),"seed_sd":{k:statistics.pstdev(x[k] for x in runs) for k in ("AVG","OBP","SLG","BB%","K%","HR%")}})
    validated.sort(key=lambda x:x["loss"]); best=validated[0]
    bestw=JointWeights(**best["weights"])
    diagnostics=v3.diagnostics(bestw,args.diag_pa,args.seed+9000)
    semantics=v3.semantic(diagnostics)
    archetypes=v3.archetypes(bestw,args.diag_pa,args.seed+10000)
    extreme=v3.extreme_safe(bestw)
    joint_ready=best["passed_tolerances"] and all(semantics.values()) and extreme
    final={
        "gate":"PITCHER_JOINT_CALIBRATION_V4_READY" if joint_ready else "PITCHER_JOINT_CALIBRATION_V4_NOT_READY",
        "population_contract":summary["gate"],
        "hitter_sampling":"production CareerEngine first-team PA weighted",
        "pitcher_sampling":summary["pitcher"]["usage_weighting"],
        "velocity":"frozen Velocity v2 physical path; not searched",
        "best":best,"semantic_gates":semantics,"diagnostics":diagnostics,"archetypes":archetypes,"extreme_safe":extreme,
        "search":{"candidates":args.candidates,"search_pa":args.search_pa,"top":args.top,"validation_pa":args.validation_pa,"seeds":args.seeds,"diag_pa":args.diag_pa},
    }
    (d/"pitcher_joint_v4_first_team_final.json").write_text(json.dumps(final,indent=2))
    with (d/"pitcher_joint_v4_first_team_candidates.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["rank","loss","passed_tolerances","w_control_zone","w_stuff_quality","w_stuff_contact","w_breaking_contact","w_breaking_quality","AVG","OBP","SLG","BB%","K%","HR%","BABIP"]
        cw=csv.DictWriter(f,fieldnames=fields);cw.writeheader()
        for x in validated:
            row={"rank":x["rank"],"loss":x["loss"],"passed_tolerances":x["passed_tolerances"],**x["weights"],**{k:x["metrics"][k] for k in ("AVG","OBP","SLG","BB%","K%","HR%","BABIP")}}
            cw.writerow(row)
    lines=["# Pitcher Joint v4 — First-Team Population Rerun","",f"Gate: `{final['gate']}`","",f"Hitter sampling: {final['hitter_sampling']}",f"Pitcher sampling: {final['pitcher_sampling']}","","## Best metrics"]
    lines += [f"- {k}: {v:.6f}" for k,v in best["metrics"].items() if isinstance(v,(int,float))]
    lines += ["","## Semantic gates"]+[f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in semantics.items()]
    (d/"pitcher_joint_v4_first_team_summary.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"gate":final["gate"],"best":best,"semantics":semantics},indent=2))


if __name__=="__main__": main()
