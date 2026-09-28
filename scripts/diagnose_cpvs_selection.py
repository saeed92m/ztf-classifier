"""Diagnose CPVS 730k selection semantics against the published VizieR membership."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scripts.audit_cpvs_membership import read_vizier
from ztf_classifier.validation.derivation import _iter_rows


def band_metrics(path: Path, parent: set[str], error_key: str, mag_key: str):
    metrics = {oid: {"snr": False, "snr1": False, "mag206": False} for oid in parent}
    threshold = 2.5 if error_key == "e_gmag" else 3.0
    for row in _iter_rows(path, required_columns=("SourceID", error_key, mag_key)):
        oid = row.get("SourceID", "").strip()
        if oid not in metrics:
            continue
        try:
            err = float(row.get(error_key, ""))
            mag = float(row.get(mag_key, ""))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(err) or err <= 0 or not math.isfinite(mag) or mag == 0:
            continue
        snr = 1.0857362047581296 / err
        snr1 = 1.0 / err
        metrics[oid]["snr"] |= snr >= threshold
        metrics[oid]["snr1"] |= snr1 >= threshold
        metrics[oid]["mag206"] |= mag <= 20.6 and snr >= threshold
    return metrics


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--g", type=Path, required=True)
    p.add_argument("--r", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    published = read_vizier(a.published)
    parent = {str(i) for i in range(1, 781605)}
    g = band_metrics(a.g, parent, "e_gmag", "gmag")
    r = band_metrics(a.r, parent, "e_rmag", "rmag")
    predicates = {
        "baseline_1p085": {o for o in parent if g[o]["snr"] and r[o]["snr"]},
        "baseline_1p0": {o for o in parent if g[o]["snr1"] and r[o]["snr1"]},
        "baseline_plus_mag206": {o for o in parent if g[o]["mag206"] and r[o]["mag206"]},
    }
    report = {}
    for name, ids in predicates.items():
        report[name] = {
            "count": len(ids),
            "published_intersection": len(ids & published),
            "candidate_only": len(ids - published),
            "published_only": len(published - ids),
        }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
