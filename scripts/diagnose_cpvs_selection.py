"""Diagnose CPVS 730k selection semantics against the published VizieR membership."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from audit_cpvs_membership import read_parent_catalog, read_vizier_rows
from ztf_classifier.validation.derivation import _iter_rows


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parent", type=Path, required=True)
    p.add_argument("--g", type=Path, required=True)
    p.add_argument("--r", type=Path, required=True)
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    published_rows = read_vizier_rows(a.published)
    parent_rows = read_parent_catalog(a.parent)
    parent = set(parent_rows)
    if len(parent) != 781_602:
        raise ValueError(f"expected 781602 parent Seq/SourceIDs, got {len(parent)}")
    name_to_ids: dict[str, list[int]] = {}
    for source_id, name in parent_rows.items():
        name_to_ids.setdefault(name, []).append(source_id)
    duplicate_parent_names = sorted(name for name, ids in name_to_ids.items() if len(ids) != 1)
    published_names = set(published_rows.values())
    missing_published_names = sorted(published_names - set(name_to_ids))
    if duplicate_parent_names or missing_published_names:
        raise ValueError(
            "published-to-parent ZTF-name crosswalk is not unique: "
            f"duplicate_parent_names={len(duplicate_parent_names)}, "
            f"published_names_missing_from_parent={len(missing_published_names)}"
        )
    published = {name_to_ids[name][0] for name in published_names}
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
    report = {
        "membership_comparison_basis": "published ZTF names crosswalked to explicit Table2 Seq/SourceID values",
        "parent_sourceid_count": len(parent),
        "published_object_count": len(published),
        "published_names_missing_from_parent_count": len(missing_published_names),
    }
    for name, ids in predicates.items():
        report[name] = {
            "count": len(ids),
            "published_intersection": len(ids & published),
            "candidate_only": len(ids - published),
            "published_only": len(published - ids),
        }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
