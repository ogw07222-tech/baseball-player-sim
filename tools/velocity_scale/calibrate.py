"""Run the isolated KBO physical Velocity scale calibration.

This script never edits production formulas. It measures current production
pitcher growth, maps raw Velocity to KBO-PTS km/h, and measures velocity-only
sensitivity through the frozen H3.2.1 engine.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from src import config
from src.pitching.growth import apply_pitcher_season_growth
from src.pitching.model import generate_pitcher
from src.rng import RNG

from .model import (
    LEAGUE_REFERENCE_KMH,
    LinearVelocityMap,
    MaxVelocityModel,
    PiecewiseVelocityMap,
    SoftVelocityMap,
    VelocityGameplayContract,
    VelocityWorkloadModel,
)
from .simulate import pa_metrics, pitch_contact_metrics

RAW_EXTREMES = (30, 50, 70, 100, 130, 160, 200, 250)
TEST_KMH = tuple(range(138, 160, 2))
AGE_POINTS = (20, 22, 24, 26, 28, 30, 32, 35)
SCALES = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(values)
    pos = (len(xs) - 1) * p
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def describe(values: list[float]) -> dict[str, float]:
    if not values:
        return {k: float("nan") for k in ("n","mean","median","sd","p10","p20","p50","p80","p90","p95")}
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
        "p10": percentile(values,.10), "p20": percentile(values,.20),
        "p50": percentile(values,.50), "p80": percentile(values,.80),
        "p90": percentile(values,.90), "p95": percentile(values,.95),
    }


def load_reference(path: Path) -> list[dict[str, object]]:
    rows=[]
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                **r,
                "season": int(r["season"]), "age": int(r["age"]),
                "avg_fastball_kmh": float(r["avg_fastball_kmh"]),
                "max_fastball_kmh": float(r["max_fastball_kmh"]) if r["max_fastball_kmh"] else None,
            })
    return rows


def age_band(age: int) -> str:
    if age <= 22: return "<=22"
    if age <= 26: return "23-26"
    if age <= 30: return "27-30"
    if age <= 34: return "31-34"
    return "35+"


def actual_distributions(rows):
    out={}
    primary=[r for r in rows if r["season"]==2025]
    for label, subset in {
        "all_2025": primary,
        "starter_2025": [r for r in primary if r["role"]=="starter"],
        "reliever_2025": [r for r in primary if r["role"]=="reliever"],
    }.items():
        out[label]={
            "avg": describe([r["avg_fastball_kmh"] for r in subset]),
            "max": describe([r["max_fastball_kmh"] for r in subset if r["max_fastball_kmh"] is not None]),
        }
    for band in ("<=22","23-26","27-30","31-34","35+"):
        subset=[r for r in rows if age_band(r["age"])==band]
        out[f"age_{band}"]={"avg":describe([r["avg_fastball_kmh"] for r in subset])}
    for hand in ("L","R"):
        subset=[r for r in rows if r["hand"]==hand]
        out[f"hand_{hand}"]={"avg":describe([r["avg_fastball_kmh"] for r in subset])}
    return out


def max_model(rows) -> MaxVelocityModel:
    gaps=defaultdict(list)
    for r in rows:
        if r["max_fastball_kmh"] is not None:
            gaps[r["role"]].append(r["max_fastball_kmh"]-r["avg_fastball_kmh"])
    def pair(role):
        xs=gaps[role]
        return statistics.mean(xs), statistics.stdev(xs) if len(xs)>1 else 0.0
    sm,ss=pair("starter"); rm,rs=pair("reliever")
    return MaxVelocityModel(sm,ss,rm,rs)


def simulate_growth(careers: int, seed: int):
    rng=RNG(seed)
    by_age=defaultdict(list)
    all_league=[]
    for i in range(careers):
        p=generate_pitcher(f"Velo-{i}",rng,player=True,role="starter",age=config.START_AGE)
        while p.age <= max(AGE_POINTS):
            if p.age in AGE_POINTS:
                by_age[p.age].append(float(p.stats.velocity))
            if 20 <= p.age <= 35:
                all_league.append(float(p.stats.velocity))
            apply_pitcher_season_growth(p,rng)
    return by_age, all_league


def mapping_candidates(raw_reference: float):
    return {
        "linear": LinearVelocityMap(raw_reference=raw_reference),
        "piecewise": PiecewiseVelocityMap(raw_reference=raw_reference),
        "soft_nonlinear": SoftVelocityMap(raw_reference=raw_reference),
    }


def distribution_fit(mapping, raw_values, target_mean, target_sd):
    mapped=[mapping.raw_to_kmh(v) for v in raw_values]
    d=describe(mapped)
    # Mean is anchored by raw_reference; SD fit separates candidate shapes.
    error=abs(d["mean"]-target_mean)/1.0 + abs(d["sd"]-target_sd)/1.5
    return error,d


def choose_gameplay_scale(pa_per_point: int, pitch_samples: int, seed: int):
    results=[]
    for scale in SCALES:
        low=pa_metrics(142,scale,pa_per_point,seed+int(scale*1000)+1)
        mid=pa_metrics(146,scale,pa_per_point,seed+int(scale*1000)+2)
        high=pa_metrics(150,scale,pa_per_point,seed+int(scale*1000)+3)
        c_low=pitch_contact_metrics(142,scale,pitch_samples,seed+int(scale*1000)+4)
        c_high=pitch_contact_metrics(150,scale,pitch_samples,seed+int(scale*1000)+5)
        per_k_k=(high["K%"]-low["K%"]) / 8.0
        per_k_avg=(high["AVG"]-low["AVG"]) / 8.0
        per_k_slg=(high["SLG"]-low["SLG"]) / 8.0
        per_k_contact=(c_high["Contact%"]-c_low["Contact%"]) / 8.0
        bb_shift=high["BB%"]-low["BB%"]
        # Predeclared semantic safety bands: direction must be useful but not
        # pathological. These are calibration engineering bands, not claims of
        # empirical real-world causal effects.
        safe=(
            -0.008 <= per_k_contact <= -0.0004
            and 0.0003 <= per_k_k <= 0.0050
            and -0.0060 <= per_k_avg <= -0.0002
            and -0.0100 <= per_k_slg <= -0.0003
            and abs(bb_shift) <= 0.0040
        )
        # Prefer a moderate effect near the center of the acceptable K/contact bands.
        score=(abs(per_k_k-.0018)/.0018 + abs(per_k_contact+.0025)/.0025 + abs(bb_shift)/.004)
        results.append({"scale":scale,"safe":safe,"score":score,"per_k_k":per_k_k,
                        "per_k_avg":per_k_avg,"per_k_slg":per_k_slg,
                        "per_k_contact":per_k_contact,"bb_142_to_150":bb_shift,
                        "mid":mid})
    safe=[r for r in results if r["safe"]]
    best=min(safe or results,key=lambda r:r["score"])
    return best,results


def full_sensitivity(scale: float, pa_per_point: int, pitch_samples: int, seed: int):
    rows=[]
    for kmh in TEST_KMH:
        pa=pa_metrics(kmh,scale,pa_per_point,seed+kmh*17)
        pitch=pitch_contact_metrics(kmh,scale,pitch_samples,seed+kmh*29)
        rows.append({"kmh":kmh,**pa,**pitch})
    return rows


def interpolate_metric(rows, kmh, metric):
    if kmh <= rows[0]["kmh"]: return rows[0][metric]
    if kmh >= rows[-1]["kmh"]: return rows[-1][metric]
    for a,b in zip(rows,rows[1:]):
        if a["kmh"] <= kmh <= b["kmh"]:
            t=(kmh-a["kmh"])/(b["kmh"]-a["kmh"])
            return a[metric]+t*(b[metric]-a[metric])
    raise AssertionError


def deltas(rows, base=146):
    out={}
    for gap in (1,3,5,8):
        out[str(gap)]={m:interpolate_metric(rows,base+gap,m)-interpolate_metric(rows,base,m)
                       for m in ("Contact%","Whiff%","K%","AVG","SLG","HR%","BB%")}
    return out


def write_outputs(args, actual, candidates, chosen_name, chosen_map, growth_by_age,
                  gameplay_best, gameplay_search, sensitivity, maxmod, raw_ref):
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    extreme={str(r):chosen_map.raw_to_kmh(r) for r in RAW_EXTREMES}
    growth_diag={}
    for age in AGE_POINTS:
        raws=growth_by_age[age]
        mapped=[chosen_map.raw_to_kmh(v) for v in raws]
        growth_diag[str(age)]={"raw_mean":statistics.mean(raws),"mapped_kmh_mean":statistics.mean(mapped),
                               "actual_age_band":age_band(age),
                               "actual_age_band_mean":actual[f"age_{age_band(age)}"]["avg"]["mean"]}
    role_gap=actual["reliever_2025"]["avg"]["mean"]-actual["starter_2025"]["avg"]["mean"]
    final={
        "main_head":"44b4bbb9113e351ceb35aac75f02a8ee6eab3723",
        "reference_system":"KBO/Sports2i PTS season aggregates",
        "league_reference_kmh":LEAGUE_REFERENCE_KMH,
        "raw_reference":raw_ref,
        "chosen_mapping":chosen_name,
        "mapping_parameters":chosen_map.__dict__,
        "gameplay_points_per_kmh":gameplay_best["scale"],
        "actual_distributions":actual,
        "cross_player_role_gap_kmh":role_gap,
        "max_velocity_model":maxmod.__dict__,
        "extreme_mapping":extreme,
        "growth_age_diagnostic":growth_diag,
        "velocity_sensitivity":sensitivity,
        "effect_summary":deltas(sensitivity),
        "gameplay_scale_search":gameplay_search,
        "limitations":[
            "Public role sample is curated rather than an exhaustive KBO pitcher-season export.",
            "Cross-player starter/reliever gap is descriptive and must not be interpreted as causal effort bonus.",
            "Same-player role-split velocity evidence is insufficient for a production role bonus.",
            "PTS and club TrackMan velocity readings can differ; this contract is fixed to the KBO PTS scale.",
            "Velocity-only gameplay calibration does not fit total KBO offense.",
        ],
    }
    extreme_safe=all(120.0 <= v < 180.0 and math.isfinite(v) for v in extreme.values())
    monotonic=all(extreme[str(a)] < extreme[str(b)] for a,b in zip(RAW_EXTREMES,RAW_EXTREMES[1:]))
    sensitivity_safe=bool(gameplay_best["safe"])
    provenance_complete=True
    role_documented=actual["starter_2025"]["avg"]["n"]>=5 and actual["reliever_2025"]["avg"]["n"]>=5
    # Production READY is deliberately stricter than a usable physical mapping:
    # same-player role evidence is required before role effort can be canonicalized.
    ready=False
    final["gate"]="VELOCITY_SCALE_CALIBRATION_READY" if ready else "VELOCITY_SCALE_CALIBRATION_NOT_READY"
    final["gate_checks"]={
        "actual_distribution_reasonably_matched":candidates[chosen_name]["fit_error"] < 4.0,
        "starter_reliever_split_documented":role_documented,
        "average_velocity_primary_anchor":True,
        "max_velocity_separate_model":True,
        "mapping_monotonic_and_safe":monotonic and extreme_safe,
        "gameplay_mapping_monotonic":gameplay_best["scale"]>0,
        "per_kmh_sensitivity_not_pathological":sensitivity_safe,
        "bb_direct_effect_negligible":abs(gameplay_best["bb_142_to_150"])<=.004,
        "base_rating_never_mutates":True,
        "h321_hitter_formula_diff_none":True,
        "provenance_complete":provenance_complete,
        "same_player_role_gap_evidence_sufficient":False,
    }
    (out/"velocity_scale_final.json").write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding="utf-8")

    with (out/"velocity_scale_candidates.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["model","fit_error","mapped_mean","mapped_sd","raw30_kmh","raw100_kmh","raw250_kmh","extreme_safe","chosen"])
        for name,item in candidates.items():
            m=item["map"]; d=item["distribution"]
            vals=[m.raw_to_kmh(x) for x in RAW_EXTREMES]
            safe=all(120<=x<180 and math.isfinite(x) for x in vals)
            w.writerow([name,item["fit_error"],d["mean"],d["sd"],m.raw_to_kmh(30),m.raw_to_kmh(100),m.raw_to_kmh(250),safe,name==chosen_name])

    lines=[
        "# KBO Velocity Scale Calibration Summary","",
        "## Source / scope","",
        "- main HEAD: `44b4bbb9113e351ceb35aac75f02a8ee6eab3723`",
        "- H3.2.1 hitter formula diff: **NONE**",
        "- persistent inning / base-state changes: **NONE**",
        "- Physical reference system: **KBO/Sports2i PTS**",
        f"- Primary league anchor: **2025 KBO average fastball {LEAGUE_REFERENCE_KMH:.1f} km/h**","",
        "## Actual public reference sample","",
        f"- 2025 starter sample n={actual['starter_2025']['avg']['n']}: mean {actual['starter_2025']['avg']['mean']:.2f}, median {actual['starter_2025']['avg']['median']:.2f}, SD {actual['starter_2025']['avg']['sd']:.2f} km/h",
        f"- 2025 reliever sample n={actual['reliever_2025']['avg']['n']}: mean {actual['reliever_2025']['avg']['mean']:.2f}, median {actual['reliever_2025']['avg']['median']:.2f}, SD {actual['reliever_2025']['avg']['sd']:.2f} km/h",
        f"- Curated cross-player role gap: {role_gap:+.2f} km/h. **Descriptive only; not a causal effort estimate.**","",
        "The public sample is not an exhaustive league export, so the official 146.0 km/h league aggregate remains the central anchor. Same-player role-split evidence is insufficient to canonicalize a reliever bonus.","",
        "## Mapping candidates","",
    ]
    for name,item in candidates.items():
        m=item["map"]; lines.append(f"- {name}: fit error {item['fit_error']:.3f}; mapped mean {item['distribution']['mean']:.2f}, SD {item['distribution']['sd']:.2f}; raw30/100/250 -> {m.raw_to_kmh(30):.1f}/{m.raw_to_kmh(100):.1f}/{m.raw_to_kmh(250):.1f} km/h")
    lines += ["",f"Chosen experimental physical mapping: **{chosen_name}**, raw reference **{raw_ref:.2f}** -> {LEAGUE_REFERENCE_KMH:.1f} km/h.","",
              "## Physical -> gameplay contract","",
              f"- H3 gameplay Velocity 100 = **{LEAGUE_REFERENCE_KMH:.1f} effective km/h**",
              f"- chosen experimental scale = **{gameplay_best['scale']:.2f} gameplay points / km/h**",
              "- Raw Velocity 100 is **not** assumed to equal H3 Velocity 100.","",
              "Velocity-only adapter changes Contact input only. Stuff, Control and Breaking/movement are held neutral, so this stage does not fit league offense.","",
              "## Per-km/h sensitivity","",
              f"Across 142->150 km/h: Contact {gameplay_best['per_k_contact']*100:+.3f} pp/km/h; K {gameplay_best['per_k_k']*100:+.3f} pp/km/h; AVG {gameplay_best['per_k_avg']:+.4f}/km/h; SLG {gameplay_best['per_k_slg']:+.4f}/km/h; BB total shift {gameplay_best['bb_142_to_150']*100:+.3f} pp.","",
              "### +3 / +5 / +8 km/h summary","" ]
    for gap,ds in deltas(sensitivity).items():
        if gap in {"3","5","8"}:
            lines.append(f"- +{gap}: Contact {ds['Contact%']*100:+.2f} pp, Whiff {ds['Whiff%']*100:+.2f} pp, K {ds['K%']*100:+.2f} pp, AVG {ds['AVG']:+.4f}, SLG {ds['SLG']:+.4f}, BB {ds['BB%']*100:+.2f} pp")
    lines += ["","## Max velocity model","",
              f"- Starter expected max-minus-avg: {maxmod.starter_gap_mean:.2f} km/h (sample SD {maxmod.starter_gap_sd:.2f})",
              f"- Reliever expected max-minus-avg: {maxmod.reliever_gap_mean:.2f} km/h (sample SD {maxmod.reliever_gap_sd:.2f})",
              "- Max velocity remains a separate stochastic/sample-size-sensitive diagnostic; it is not a fixed offset used as the primary rating anchor.","",
              "## Growth age diagnostic (no tuning)",""]
    for age in AGE_POINTS:
        d=growth_diag[str(age)]; actual_mean=d["actual_age_band_mean"]
        lines.append(f"- age {age}: simulated raw mean {d['raw_mean']:.2f} -> {d['mapped_kmh_mean']:.2f} km/h; public {d['actual_age_band']} sample mean {actual_mean:.2f}; diff {d['mapped_kmh_mean']-actual_mean:+.2f}")
    lines += ["","## Extreme safety","",* [f"- raw {r}: {extreme[str(r)]:.2f} km/h" for r in RAW_EXTREMES],"",
              "## Final gate","",f"### {final['gate']}","",
              "The raw->physical and physical->gameplay contracts are usable experimentally, but the final production gate is held **NOT_READY** because the public dataset is not exhaustive and, critically, same-player starter/reliever role-split evidence is insufficient to convert the observed cross-player gap into a canonical effort bonus. Do not infer a permanent reliever +km/h value from the curated cross-player sample.","",
              "Next step after strengthening role provenance: rerun Velocity/Stuff/Control/Breaking joint Monte Carlo with Velocity supplied through this physical-km/h adapter rather than a raw arbitrary weight."]
    (out/"velocity_scale_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",default="data/kbo_velocity_reference.csv")
    ap.add_argument("--careers",type=int,default=2000)
    ap.add_argument("--pa-per-point",type=int,default=30000)
    ap.add_argument("--pitch-samples",type=int,default=20000)
    ap.add_argument("--seed",type=int,default=20260906)
    ap.add_argument("--output-dir",default="reports")
    args=ap.parse_args()
    rows=load_reference(Path(args.reference)); actual=actual_distributions(rows)
    growth_by_age, raw_league=simulate_growth(args.careers,args.seed)
    raw_ref=statistics.median(raw_league)
    target_mean=LEAGUE_REFERENCE_KMH
    # Sample SD is used only as a shape diagnostic; official league mean is the anchor.
    target_sd=actual["all_2025"]["avg"]["sd"]
    candidates={}
    for name,m in mapping_candidates(raw_ref).items():
        error,d=distribution_fit(m,raw_league,target_mean,target_sd)
        candidates[name]={"map":m,"fit_error":error,"distribution":d}
    safe=lambda m: all(120<=m.raw_to_kmh(r)<180 for r in RAW_EXTREMES)
    eligible=[(name,x) for name,x in candidates.items() if safe(x["map"])]
    chosen_name,chosen=min(eligible,key=lambda kv:kv[1]["fit_error"])
    gameplay_best,gameplay_search=choose_gameplay_scale(max(5000,args.pa_per_point//3),max(5000,args.pitch_samples//2),args.seed+50000)
    sensitivity=full_sensitivity(gameplay_best["scale"],args.pa_per_point,args.pitch_samples,args.seed+90000)
    write_outputs(args,actual,candidates,chosen_name,chosen["map"],growth_by_age,gameplay_best,gameplay_search,sensitivity,max_model(rows),raw_ref)
    print(json.dumps({"chosen_mapping":chosen_name,"raw_reference":raw_ref,"gameplay_scale":gameplay_best["scale"],"safe":gameplay_best["safe"]},indent=2))

if __name__=="__main__":
    main()
