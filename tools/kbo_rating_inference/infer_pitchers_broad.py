from __future__ import annotations

"""Broad-spectrum pitcher inference entrypoint with fixed BF shrinkage targets."""

from tools.kbo_rating_inference import infer_pitchers as base

_original=base.actual_metrics


def _broad_actual(row):
    out=_original(row)
    for key in ("K_pct","BB_pct","HR_pct","OPP_AVG","OPP_SLG","BABIP"):
        name="shrunk_"+key
        raw=row.get(name,"")
        if str(raw).strip() not in {"","nan","NaN"}:
            try:out[key]=float(raw)
            except ValueError:pass
    return out


def main():
    base.actual_metrics=_broad_actual
    base.main()

if __name__=="__main__":main()
