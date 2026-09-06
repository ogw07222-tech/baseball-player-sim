from __future__ import annotations

"""Broad-spectrum hitter inference entrypoint.

Reuses the validated candidate-search implementation. Only the fit target for
small/medium samples is replaced by the fixed-prior shrunk rates prepared by
broad_spectrum.py. Original observed stats remain in output/report columns.
"""

from tools.kbo_rating_inference import infer_hitters as base

_original=base.actual_metrics


def _broad_actual(row):
    out=_original(row)
    for key in ("AVG","OBP","SLG","BB_pct","K_pct","HR_pct","BABIP"):
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
