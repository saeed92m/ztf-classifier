"""Diagnose CPVS selection semantics against the published VizieR membership.

All metrics in this module are diagnostic only. They must not silently change
the production selection predicate or be used to tune membership cardinality.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from audit_cpvs_membership import _iter_parent_lines, read_vizier
except ModuleNotFoundError:  # pytest imports this file as scripts.diagnose_cpvs_selection
    from scripts.audit_cpvs_membership import _iter_parent_lines, read_vizier
from ztf_classifier.validation.derivation import (
    _iter_rows,
    _parse_cpvs_table2_identity,
    _source_ids,
    _split_fields,
)


def parent_catalog_metadata(path: Path) -> dict[int, dict[str, Any]]:
    """Read CPVS Type/Ng/Nr from fixed-width or tokenized Table2 rows."""
    metadata: dict[int, dict[str, Any]] = {}
    for line in _iter_parent_lines(path):
        identity = _parse_cpvs_table2_identity(line)
        if identity is None:
            continue
        source_id = int(identity[1])
        fields = _split_fields(line)
        offset = (
            1
            if len(fields) >= 3
            and fields[0].upper() == "ZTF"
            and fields[1].upper().startswith("J")
            else 0
        )
        try:
            ng = int(fields[offset + 12])
            nr = int(fields[offset + 13])
            variable_type = fields[offset + 24].strip()
        except (IndexError, ValueError):
            # Do not manufacture class/detection metadata when the source row
            # cannot be parsed against the documented Table2 column order.
            ng = nr = -1
            variable_type = "UNKNOWN"
        metadata[source_id] = {
            "type": variable_type or "UNKNOWN",
            "ng": ng,
            "nr": nr,
        }
    return metadata

def membership_by_type(
    ids: set[int], metadata: dict[int, dict[str, Any]]
) -> dict[str, int]:
    counts = Counter(
        str(metadata[oid]["type"]) for oid in ids if oid in metadata
    )
    return dict(sorted(counts.items()))


def band_metrics(path: Path, parent: set[int], error_key: str, mag_key: str):
    """Summarize per-source qualifying detections and flag/magnitude/error evidence."""
    metrics = {
        oid: {
            "snr": False,
            "snr1": False,
            "mag206": False,
            "mag206_only": False,
            "snr_flag0": False,
            "snr_flag_lt_32768": False,
            "qualifying_detections": 0,
            "qualifying_flag_or": 0,
            "qualifying_flag_nonzero": 0,
            "brightest_qualifying_mag": None,
            "smallest_qualifying_error": None,
        }
        for oid in parent
    }
    threshold = 2.5 if error_key == "e_gmag" else 3.0
    flag_candidates = (
        ("g_flag", "catflags", "flag")
        if error_key == "e_gmag"
        else ("r_flag", "catflags", "flag")
    )
    for row in _iter_rows(path, required_columns=("SourceID", error_key, mag_key)):
        try:
            oid = int(row.get("SourceID", "").strip())
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

        item = metrics[oid]
        snr = 1.0857362047581296 / err
        snr1 = 1.0 / err
        item["mag206_only"] |= mag <= 20.6
        item["snr1"] |= snr1 >= threshold
        if snr < threshold:
            continue

        item["snr"] = True
        item["qualifying_detections"] += 1
        item["brightest_qualifying_mag"] = (
            mag if item["brightest_qualifying_mag"] is None
            else max(item["brightest_qualifying_mag"], mag)
        )
        item["smallest_qualifying_error"] = (
            err if item["smallest_qualifying_error"] is None
            else min(item["smallest_qualifying_error"], err)
        )
        item["mag206"] |= mag <= 20.6

        flag_key_map = {key.strip().lower(): key for key in row}
        flag_key = next(
            (flag_key_map[name] for name in flag_candidates if name in flag_key_map),
            None,
        )
        if flag_key is not None:
            try:
                flag = int(float(row.get(flag_key, "")))
            except (TypeError, ValueError):
                flag = -1
            if flag >= 0:
                item["qualifying_flag_or"] |= flag
                item["qualifying_flag_nonzero"] += int(flag != 0)
            if flag == 0:
                item["snr_flag0"] = True
            if 0 <= flag < 32768:
                item["snr_flag_lt_32768"] = True
    return metrics


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def summarize_group(ids: set[int], g: dict[int, dict[str, Any]], r: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Provide interpretable per-band evidence for a membership partition."""
    result: dict[str, Any] = {"object_count": len(ids), "bands": {}}
    for band_name, values in (("g", g), ("r", r)):
        band = [values[oid] for oid in ids]
        detection_counts = [int(item["qualifying_detections"]) for item in band]
        flags = Counter(str(item["qualifying_flag_or"]) for item in band)
        bright_mags = [
            float(item["brightest_qualifying_mag"])
            for item in band if item["brightest_qualifying_mag"] is not None
        ]
        min_errors = [
            float(item["smallest_qualifying_error"])
            for item in band if item["smallest_qualifying_error"] is not None
        ]
        nonzero = sum(int(item["qualifying_flag_nonzero"] > 0) for item in band)
        result["bands"][band_name] = {
            "objects_with_qualifying_detections": sum(n > 0 for n in detection_counts),
            "qualifying_detections_per_object": {
                "min": min(detection_counts) if detection_counts else None,
                "p50": percentile(detection_counts, 0.50),
                "p90": percentile(detection_counts, 0.90),
                "p99": percentile(detection_counts, 0.99),
                "max": max(detection_counts) if detection_counts else None,
            },
            "objects_with_any_nonzero_qualifying_flag": nonzero,
            "qualifying_flag_or_top20": flags.most_common(20),
            "brightest_qualifying_magnitude": {
                "p10": percentile(bright_mags, 0.10),
                "p50": percentile(bright_mags, 0.50),
                "p90": percentile(bright_mags, 0.90),
            },
            "smallest_qualifying_magnitude_error": {
                "p10": percentile(min_errors, 0.10),
                "p50": percentile(min_errors, 0.50),
                "p90": percentile(min_errors, 0.90),
            },
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--g", type=Path, required=True)
    parser.add_argument("--r", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    published = read_vizier(args.published, args.parent)
    parent = {int(source_id) for source_id in _source_ids(args.parent, None)}
    if len(parent) != 781_602:
        raise ValueError(f"expected 781602 parent SourceIDs, got {len(parent)}")
    catalog_metadata = parent_catalog_metadata(args.parent)
    if len(catalog_metadata) != len(parent):
        raise ValueError(
            "parent metadata/SourceID coverage mismatch: "
            f"{len(catalog_metadata)} metadata rows for {len(parent)} SourceIDs"
        )

    g = band_metrics(args.g, parent, "e_gmag", "gmag")
    r = band_metrics(args.r, parent, "e_rmag", "rmag")
    predicates = {
        "baseline_1p085": {oid for oid in parent if g[oid]["snr"] and r[oid]["snr"]},
        "baseline_1p0": {oid for oid in parent if g[oid]["snr1"] and r[oid]["snr1"]},
        "baseline_plus_mag206": {
            oid for oid in parent if g[oid]["mag206"] and r[oid]["mag206"]
        },
        "baseline_plus_rmag206": {
            oid for oid in parent
            if g[oid]["snr"] and r[oid]["snr"] and r[oid]["mag206_only"]
        },
        "baseline_flag_zero_detection_each_band_diagnostic": {
            oid for oid in parent if g[oid]["snr_flag0"] and r[oid]["snr_flag0"]
        },
        "baseline_flag_below_32768_each_band_diagnostic": {
            oid for oid in parent
            if g[oid]["snr_flag_lt_32768"] and r[oid]["snr_flag_lt_32768"]
        },
    }
    baseline = predicates["baseline_1p085"]
    candidate_only = baseline - published
    published_intersection = baseline & published
    published_only = published - baseline

    report: dict[str, Any] = {
        "diagnostic_only": True,
        "selection_policy_changed": False,
        "band_summary": {
            "g": {
                "snr_qualified_objects": sum(item["snr"] for item in g.values()),
                "snr_qualified_flag_zero_objects": sum(item["snr_flag0"] for item in g.values()),
            },
            "r": {
                "snr_qualified_objects": sum(item["snr"] for item in r.values()),
                "snr_qualified_flag_zero_objects": sum(item["snr_flag0"] for item in r.values()),
            },
        },
        "membership_partitions": {
            "candidate_only": summarize_group(candidate_only, g, r),
            "published_and_candidate": summarize_group(published_intersection, g, r),
            "published_only": summarize_group(published_only, g, r),
        },
        "parent_catalog_context_diagnostic_only": {
            "class_counts": {
                "candidate": membership_by_type(baseline, catalog_metadata),
                "candidate_only": membership_by_type(candidate_only, catalog_metadata),
                "published_intersection": membership_by_type(
                    published_intersection, catalog_metadata
                ),
                "published_only": membership_by_type(published_only, catalog_metadata),
                "published_reference": membership_by_type(published, catalog_metadata),
            },
            "parent_ng_nr_counts": {
                "candidate_only": {
                    "ng_zero": sum(
                        catalog_metadata[oid]["ng"] == 0 for oid in candidate_only
                    ),
                    "nr_zero": sum(
                        catalog_metadata[oid]["nr"] == 0 for oid in candidate_only
                    ),
                    "ng_or_nr_unknown": sum(
                        catalog_metadata[oid]["ng"] < 0
                        or catalog_metadata[oid]["nr"] < 0
                        for oid in candidate_only
                    ),
                },
                "published_intersection": {
                    "ng_zero": sum(
                        catalog_metadata[oid]["ng"] == 0 for oid in published_intersection
                    ),
                    "nr_zero": sum(
                        catalog_metadata[oid]["nr"] == 0 for oid in published_intersection
                    ),
                    "ng_or_nr_unknown": sum(
                        catalog_metadata[oid]["ng"] < 0
                        or catalog_metadata[oid]["nr"] < 0
                        for oid in published_intersection
                    ),
                },
            },
        },
        "candidate_only_sample_by_source_id": [
            {
                "source_id": oid,
                "g": {key: g[oid][key] for key in (
                    "qualifying_detections", "qualifying_flag_or",
                    "brightest_qualifying_mag", "smallest_qualifying_error",
                )},
                "r": {key: r[oid][key] for key in (
                    "qualifying_detections", "qualifying_flag_or",
                    "brightest_qualifying_mag", "smallest_qualifying_error",
                )},
            }
            for oid in sorted(candidate_only)[:100]
        ],
    }
    for name, ids in predicates.items():
        report[name] = {
            "count": len(ids),
            "published_intersection": len(ids & published),
            "candidate_only": len(ids - published),
            "published_only": len(published - ids),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
