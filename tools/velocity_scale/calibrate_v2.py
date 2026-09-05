"""Second-pass velocity calibration with a 119-pitcher 2025 distribution anchor."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

from . import calibrate as C
from .simulate import pa_metrics, pitch_contact_metrics

SCALES=(0.5,0.75,1.0,1.25,1.5,2.0,2.5,3.0,3.5,4.0,5.0)


def load_distribution(path: Path) -> list[float]:
    with path.open(encoding="utf-8",newline="") as f:
        return [float(r["avg_fastball_kmh"]) for r in csv.DictReader(f)]


def choose_scale(pa_n:int,pitch_n:int,seed:int):
    results=[]
    for scale in SCALES:
        # Common random numbers make the velocity contrast much less noisy.
        pa_seed=seed+int(scale*1000)
        pitch_seed=seed+100000+int(scale*1000)
        low=pa_metrics(142,scale,pa_n,pa_seed)
        mid=pa_metrics(146,scale,pa_n,pa_seed)
        high=pa_metrics(150,scale,pa_n,pa_seed)
        cl=pitch_contact_metrics(142,scale,pitch_n,pitch_seed)
        ch=pitch_contact_metrics(150,scale,pitch_n,pitch_seed)
        pk=(high["K%"]-low["K%"]) / 8
        pav=(high["AVG"]-low["AVG"]) / 8
        psl=(high["SLG"]-low["SLG"]) / 8
        pc=(ch["Contact%"]-cl["Contact%"]) / 8
        bb=high["BB%"]-low["BB%"]
        safe=(-.008<=pc<=-.0004 and .0003<=pk<=.005 and -.006<=pav<=-.0002
              and -.010<=psl<=-.0003 and abs(bb)<=.004)
        score=abs(pk-.0018)/.0018+abs(pc+.0025)/.0025+abs(bb)/.004
        results.append({"scale":scale,"safe":safe,"score":score,"per_k_k":pk,
                        "per_k_avg":pav,"per_k_slg":psl,"per_k_contact":pc,
                        "bb_142_to_150":bb,"mid":mid})
    safe=[r for r in results if r["safe"]]
    return min(safe or results,key=lambda r:r["score"]),results


def sensitivity(scale:float,pa_n:int,pitch_n:int,seed:int):
    rows=[]
    for kmh in C.TEST_KMH:
        rows.append({"kmh":kmh,
                     **pa_metrics(kmh,scale,pa_n,seed),
                     **pitch_contact_metrics(kmh,scale,pitch_n,seed+1)})
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",default="data/kbo_velocity_reference.csv")
    ap.add_argument("--distribution-reference",default="data/kbo_velocity_distribution_2025.csv")
    ap.add_argument("--careers",type=int,default=2000)
    ap.add_argument("--pa-per-point",type=int,default=30000)
    ap.add_argument("--pitch-samples",type=int,default=20000)
    ap.add_argument("--seed",type=int,default=20260906)
    ap.add_argument("--output-dir",default="reports")
    args=ap.parse_args()

    detailed=C.load_reference(Path(args.reference))
    actual=C.actual_distributions(detailed)
    dist=load_distribution(Path(args.distribution_reference))
    actual["qualifying_2025"]={"avg":C.describe(dist),"source":"2025 pitchers at >=30% regulation innings"}

    by_age,raw=C.simulate_growth(args.careers,args.seed)
    raw_ref=statistics.median(raw)
    candidates={}
    for name,m in C.mapping_candidates(raw_ref).items():
        err,d=C.distribution_fit(m,raw,C.LEAGUE_REFERENCE_KMH,actual["qualifying_2025"]["avg"]["sd"])
        candidates[name]={"map":m,"fit_error":err,"distribution":d}
    eligible=[(n,x) for n,x in candidates.items()
              if all(120<=x["map"].raw_to_kmh(r)<180 for r in C.RAW_EXTREMES)]
    chosen_name,chosen=min(eligible,key=lambda kv:kv[1]["fit_error"])

    best,search=choose_scale(max(8000,args.pa_per_point//2),max(8000,args.pitch_samples//2),args.seed+50000)
    sens=sensitivity(best["scale"],args.pa_per_point,args.pitch_samples,args.seed+90000)
    C.write_outputs(args,actual,candidates,chosen_name,chosen["map"],by_age,best,search,sens,C.max_model(detailed),raw_ref)

    out=Path(args.output_dir)
    final_path=out/"velocity_scale_final.json"
    final=json.loads(final_path.read_text(encoding="utf-8"))
    final["qualifying_distribution_2025"]=actual["qualifying_2025"]
    final["distribution_sample_size"]=len(dist)
    final["velocity_scale_search_range"]=[min(SCALES),max(SCALES)]
    final_path.write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding="utf-8")

    d=actual["qualifying_2025"]["avg"]
    addition=(
        "\n## 2025 broad velocity distribution anchor\n\n"
        f"The secondary public table contains **{int(d['n'])} pitchers at >=30% of regulation innings**: "
        f"mean {d['mean']:.2f}, median {d['median']:.2f}, SD {d['sd']:.2f}, "
        f"P10/P20/P50/P80/P90/P95 = {d['p10']:.2f}/{d['p20']:.2f}/{d['p50']:.2f}/"
        f"{d['p80']:.2f}/{d['p90']:.2f}/{d['p95']:.2f} km/h. "
        "The official 146.0 km/h all-league aggregate remains the primary center anchor; this 119-pitcher table is used for distribution-shape validation.\n"
    )
    summary=out/"velocity_scale_summary.md"
    summary.write_text(summary.read_text(encoding="utf-8")+addition,encoding="utf-8")
    print(json.dumps({"chosen_mapping":chosen_name,"raw_reference":raw_ref,
                      "gameplay_scale":best["scale"],"safe":best["safe"],
                      "distribution_n":len(dist)},indent=2))

if __name__=="__main__":
    main()
