"""Diagnose CPVS 730k selection semantics against the published VizieR membership."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

if __package__:
    from .audit_cpvs_membership import (
        read_parent_catalog,
        read_parent_metadata_fields,
        read_vizier_rows,
    )
else:
    from audit_cpvs_membership import (
        read_parent_catalog,
        read_parent_metadata_fields,
        read_vizier_rows,
    )

from ztf_classifier.validation.derivation import _iter_rows


def _exact_snr_from_mag_error(error: float) -> float:
    """Diagnostic alternative: invert the magnitude/flux-error relation."""
    if not math.isfinite(error) or error <= 0:
        return float("nan")
    try:
        denominator = math.expm1(0.4 * math.log(10.0) * error)
    except OverflowError:
        return 0.0
    return 1.0 / denominator if denominator > 0 else float("inf")


def _positive_finite(value: object) -> bool:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def band_metrics(path: Path, parent: set[int], error_key: str, mag_key: str):
    metrics = {
        oid: {
            "snr": False,
            "snr1": False,
            "snr_exact": False,
            "mag206": False,
            "mag206_exact": False,
            "mag206_only": False,
        }
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
        snr_exact = _exact_snr_from_mag_error(err)
        metrics[oid]["snr"] |= snr >= threshold
        metrics[oid]["snr1"] |= snr1 >= threshold
        metrics[oid]["snr_exact"] |= snr_exact >= threshold
        metrics[oid]["mag206"] |= mag <= 20.6 and snr >= threshold
        metrics[oid]["mag206_exact"] |= mag <= 20.6 and snr_exact >= threshold
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
    parent_metadata = read_parent_metadata_fields(a.parent)
    parent = set(parent_rows)
    if set(parent_metadata) != parent:
        raise ValueError(
            "parent metadata Seq namespace differs from the parent identity catalog: "
            f"metadata={len(parent_metadata)}, identity={len(parent)}"
        )
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
        "baseline_exact_nonlinear_snr": {
            o for o in parent if g[o]["snr_exact"] and r[o]["snr_exact"]
        },
        "baseline_exact_nonlinear_snr_plus_mag206": {
            o for o in parent if g[o]["mag206_exact"] and r[o]["mag206_exact"]
        },
        "baseline_plus_mag206": {
            o for o in parent if g[o]["mag206"] and r[o]["mag206"]
        },
        "baseline_plus_rmag206": {
            o for o in parent if g[o]["snr"] and r[o]["snr"] and r[o]["mag206_only"]
        },
        "baseline_plus_positive_parent_metadata_diagnostic": {
            oid
            for oid in parent
            if g[oid]["snr"]
            and r[oid]["snr"]
            and all(
                _positive_finite(parent_metadata[oid].get(field))
                for field in ("gmag", "rmag", "Per-g", "Per-r")
            )
        },
    }
    report = {
        "membership_comparison_basis": "published ZTF names crosswalked to explicit Table2 Seq/SourceID values",
        "parent_sourceid_count": len(parent),
        "published_object_count": len(published),
        "published_names_missing_from_parent_count": len(missing_published_names),
    }
    metadata_positive_counts = {
        field: sum(
            _positive_finite(values.get(field))
            for values in parent_metadata.values()
        )
        for field in ("gmag", "rmag", "Per-g", "Per-r")
    }
    valid_all_four_metadata = {
        oid
        for oid, values in parent_metadata.items()
        if all(
            _positive_finite(values.get(field))
            for field in ("gmag", "rmag", "Per-g", "Per-r")
        )
    }
    report["parent_metadata_validity_diagnostic"] = {
        "schema_available": len(parent_metadata) == len(parent),
        "parent_rows": len(parent_metadata),
        "positive_finite_count_by_field": metadata_positive_counts,
        "all_four_positive_finite_count": len(valid_all_four_metadata),
        "interpretation": (
            "diagnostic only; not an accepted production rule without source-method evidence"
        ),
    }
    for name, ids in predicates.items():
        report[name] = {
            "count": len(ids),
            "published_intersection": len(ids & published),
            "candidate_only": len(ids - published),
            "published_only": len(published - ids),
            "exact_membership_match": ids == published,
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
