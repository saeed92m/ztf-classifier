"""Diagnose CPVS 730k selection semantics against the published VizieR membership."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from audit_cpvs_membership import read_vizier
from ztf_classifier.validation.derivation import _iter_rows, _source_ids


def band_metrics(path: Path, parent: set[int], error_key: str, mag_key: str):
    metrics = {
        oid: {"snr": False, "snr1": False, "mag206": False, "mag206_only": False}
        for oid in parent
    }
    threshold = 2.5 if error_key == "e_gmag" else 3.0
    for row in _iter_rows(path, required_columns=("SourceID", error_key, mag_key)):
        raw_oid = row.get("SourceID", "").strip()
        try:
            oid = int(raw_oid)
        except (TypeError, ValueError):
            continue
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
        metrics[oid]["mag206_only"] |= mag <= 20.6
    return metrics


def _json_safe(value: Any) -> Any:
    """Convert non-finite floats to JSON null without altering finite values.

    Missing source metadata can be represented internally as NaN. Standard JSON
    has no NaN/Infinity literals, so normalize only at the serialization boundary
    and retain strict encoding as a regression guard.
    """
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g", type=Path, required=True)
    p.add_argument("--r", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    published = read_vizier(a.published)
    parent = {int(source_id) for source_id in _source_ids(a.parent, None)}
    if len(parent) != 781_602:
        raise ValueError(f"expected 781602 parent SourceIDs, got {len(parent)}")
    g = band_metrics(a.g, parent, "e_gmag", "gmag")
    r = band_metrics(a.r, parent, "e_rmag", "rmag")
    predicates = {
        "baseline_1p085": {o for o in parent if g[o]["snr"] and r[o]["snr"]},
        "baseline_1p0": {o for o in parent if g[o]["snr1"] and r[o]["snr1"]},
        "baseline_plus_mag206": {
            o for o in parent if g[o]["mag206"] and r[o]["mag206"]
        },
        "baseline_plus_rmag206": {
            o for o in parent if g[o]["snr"] and r[o]["snr"] and r[o]["mag206_only"]
        },
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
    report_json = (
        json.dumps(_json_safe(report), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    a.output.write_text(report_json, encoding="utf-8")
    print(report_json, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
