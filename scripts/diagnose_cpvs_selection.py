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
)


def parent_catalog_metadata(
    path: Path, metadata_path: Path | None = None
) -> dict[int, dict[str, Any]]:
    """Read fixed-width Table 2 metadata or an authoritative named-column TSV.

    The Zenodo text mirror can collapse blank fixed-width fields, so token offsets
    are not reliable for optional columns. When metadata_path is supplied, use the
    named-column VizieR export. These fields remain diagnostic-only.
    """
    if metadata_path is not None:
        lines = metadata_path.read_text(encoding="utf-8", errors="replace").splitlines()
        header_index = None
        header = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            candidate = stripped[1:].strip() if stripped.startswith("#") else stripped
            columns = [item.strip() for item in candidate.split("\t")]
            normalized = {name.lower() for name in columns}
            if {"seq", "gmag", "rmag", "ng", "nr", "type"}.issubset(normalized):
                header_index = index
                header = columns
                break
        if header_index is None:
            raise ValueError(
                f"metadata TSV lacks named Seq/gmag/rmag/Ng/Nr/Type columns: {metadata_path}"
            )
        indexes = {name.strip().lower(): index for index, name in enumerate(header)}

        def value_at(values: list[str], name: str) -> str:
            index = indexes[name]
            return values[index].strip() if index < len(values) else ""

        def to_float(value: str) -> float:
            try:
                result = float(value)
                return result if math.isfinite(result) else float("nan")
            except (TypeError, ValueError):
                return float("nan")

        def to_int(value: str) -> int:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return -1

        def named_value(values: list[str], *names: str) -> str:
            for name in names:
                index = indexes.get(name.lower())
                if index is not None and index < len(values):
                    return values[index].strip()
            return ""

        metadata: dict[int, dict[str, Any]] = {}
        for line in lines[header_index + 1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            values = line.split("\t")
            source_id = to_int(value_at(values, "seq"))
            if source_id < 0:
                continue
            metadata[source_id] = {
                "type": value_at(values, "type") or "UNKNOWN",
                "ng": to_int(value_at(values, "ng")),
                "nr": to_int(value_at(values, "nr")),
                "gmag": to_float(value_at(values, "gmag")),
                "rmag": to_float(value_at(values, "rmag")),
                "period": to_float(named_value(values, "per")),
                "per_g": to_float(named_value(values, "per-g", "per_g")),
                "per_r": to_float(named_value(values, "per-r", "per_r")),
                "r2_g": to_float(named_value(values, "r2-g", "r2_g")),
                "r2_r": to_float(named_value(values, "r2-r", "r2_r")),
                "gamp": to_float(named_value(values, "gamp")),
                "ramp": to_float(named_value(values, "ramp")),
                "fap_g": to_float(named_value(values, "log(fap-g)", "log_fap_g")),
                "fap_r": to_float(named_value(values, "log(fap-r)", "log_fap_r")),
            }
        if not metadata:
            raise ValueError(f"metadata TSV contained no valid Seq rows: {metadata_path}")
        return metadata

    metadata: dict[int, dict[str, Any]] = {}
    for line in _iter_parent_lines(path):
        identity = _parse_cpvs_table2_identity(line)
        if identity is None:
            continue
        source_id = int(identity[1])
        ng = nr = -1
        gmag = rmag = float("nan")
        period = per_g = per_r = float("nan")
        r2_g = r2_r = gamp = ramp = fap_g = fap_r = float("nan")
        variable_type = ""

        def parse_int(value: str, default: int) -> int:
            try:
                return int(value.strip())
            except (TypeError, ValueError):
                return default

        def parse_float(value: str, default: float = float("nan")) -> float:
            try:
                return float(value.strip())
            except (TypeError, ValueError):
                return default

        # Parse each fixed-width field independently. A blank optional field
        # must not discard valid g/r magnitudes, Ng/Nr, or Type from the row.
        if len(line) >= 216 and line[23:29].strip() == identity[1]:
            period = parse_float(line[50:61])
            gmag = parse_float(line[89:95])
            rmag = parse_float(line[96:102])
            per_g = parse_float(line[103:116])
            per_r = parse_float(line[117:130])
            ng = parse_int(line[131:135], -1)
            nr = parse_int(line[136:140], -1)
            r2_g = parse_float(line[167:173])
            r2_r = parse_float(line[174:180])
            gamp = parse_float(line[181:186])
            ramp = parse_float(line[187:192])
            fap_g = parse_float(line[193:201])
            fap_r = parse_float(line[202:210])
            variable_type = line[211:216].strip()
        else:
            # Whitespace-tokenized mirror: locate Seq rather than relying on
            # an absolute token index (the object name may be one or two tokens).
            fields = line.strip().split()
            try:
                seq_index = next(i for i, value in enumerate(fields) if value == identity[1])
            except StopIteration:
                seq_index = -1
            if seq_index >= 0:
                period = parse_float(fields[seq_index + 3]) if len(fields) > seq_index + 3 else period
                gmag = parse_float(fields[seq_index + 7]) if len(fields) > seq_index + 7 else gmag
                rmag = parse_float(fields[seq_index + 8]) if len(fields) > seq_index + 8 else rmag
                per_g = parse_float(fields[seq_index + 9]) if len(fields) > seq_index + 9 else per_g
                per_r = parse_float(fields[seq_index + 10]) if len(fields) > seq_index + 10 else per_r
                ng = parse_int(fields[seq_index + 11], -1) if len(fields) > seq_index + 11 else ng
                nr = parse_int(fields[seq_index + 12], -1) if len(fields) > seq_index + 12 else nr
                r2_g = parse_float(fields[seq_index + 17]) if len(fields) > seq_index + 17 else r2_g
                r2_r = parse_float(fields[seq_index + 18]) if len(fields) > seq_index + 18 else r2_r
                gamp = parse_float(fields[seq_index + 19]) if len(fields) > seq_index + 19 else gamp
                ramp = parse_float(fields[seq_index + 20]) if len(fields) > seq_index + 20 else ramp
                fap_g = parse_float(fields[seq_index + 21]) if len(fields) > seq_index + 21 else fap_g
                fap_r = parse_float(fields[seq_index + 22]) if len(fields) > seq_index + 22 else fap_r
                variable_type = fields[seq_index + 23] if len(fields) > seq_index + 23 else variable_type

        metadata[source_id] = {
            "type": variable_type or "UNKNOWN",
            "ng": ng,
            "nr": nr,
            "gmag": gmag,
            "rmag": rmag,
            "period": period,
            "per_g": per_g,
            "per_r": per_r,
            "r2_g": r2_g,
            "r2_r": r2_r,
            "gamp": gamp,
            "ramp": ramp,
            "fap_g": fap_g,
            "fap_r": fap_r,
        }
    return metadata


def has_finite_nonzero_mean_magnitudes(metadata: dict[str, Any]) -> bool:
    """Return true only when both parent mean magnitudes are finite and nonzero.

    NaN compares unequal to zero in Python, so a simple not-equal-to-zero test
    incorrectly classifies missing magnitudes as present.
    """
    gmag = metadata.get("gmag", float("nan"))
    rmag = metadata.get("rmag", float("nan"))
    return (
        isinstance(gmag, (int, float))
        and isinstance(rmag, (int, float))
        and math.isfinite(gmag)
        and math.isfinite(rmag)
        and gmag != 0.0
        and rmag != 0.0
    )

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
            "snr_exact": False,
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
        # Exact inverse of the magnitude-error transform, retained as a diagnostic
        # until validated against the published selection semantics.
        snr_exact = 1.0 / math.expm1(err * math.log(10.0) / 2.5)
        snr1 = 1.0 / err
        item["mag206_only"] |= mag <= 20.6
        item["snr1"] |= snr1 >= threshold
        item["snr_exact"] |= snr_exact >= threshold
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
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    published = read_vizier(args.published, args.parent)
    parent = {int(source_id) for source_id in _source_ids(args.parent, None)}
    if len(parent) != 781_602:
        raise ValueError(f"expected 781602 parent SourceIDs, got {len(parent)}")
    catalog_metadata = parent_catalog_metadata(args.parent, args.metadata)
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
        "exact_magnitude_error_snr_diagnostic": {
            oid for oid in parent if g[oid]["snr_exact"] and r[oid]["snr_exact"]
        },
        "baseline_plus_nonzero_parent_mean_magnitudes_diagnostic": {
            oid for oid in parent
            if g[oid]["snr"] and r[oid]["snr"]
            and has_finite_nonzero_mean_magnitudes(catalog_metadata[oid])
        },
        "exact_snr_plus_nonzero_parent_mean_magnitudes_diagnostic": {
            oid for oid in parent
            if g[oid]["snr_exact"] and r[oid]["snr_exact"]
            and has_finite_nonzero_mean_magnitudes(catalog_metadata[oid])
        },
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
            "parent_mean_magnitude_quality": {
                partition: {
                    "gmag_zero": sum(catalog_metadata[oid]["gmag"] == 0.0 for oid in ids),
                    "rmag_zero": sum(catalog_metadata[oid]["rmag"] == 0.0 for oid in ids),
                    "gmag_or_rmag_zero": sum(
                        catalog_metadata[oid]["gmag"] == 0.0
                        or catalog_metadata[oid]["rmag"] == 0.0
                        for oid in ids
                    ),
                    "gmag_or_rmag_unknown": sum(
                        not math.isfinite(catalog_metadata[oid]["gmag"])
                        or not math.isfinite(catalog_metadata[oid]["rmag"])
                        for oid in ids
                    ),
                }
                for partition, ids in (
                    ("candidate_only", candidate_only),
                    ("published_intersection", published_intersection),
                )
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
    # Enumerate the residual candidate-only objects after the strongest
    # source-backed metadata hypothesis. This is evidence collection only: do
    # not use this report to silently change the scientific selection policy.
    nonzero_mean_mag_ids = {
        oid for oid in candidate_only
        if has_finite_nonzero_mean_magnitudes(catalog_metadata[oid])
    }
    report["candidate_only_residual_analysis"] = {
        "candidate_only_count": len(candidate_only),
        "both_parent_mean_magnitudes_nonzero_count": len(nonzero_mean_mag_ids),
        "both_parent_mean_magnitudes_zero_or_one_zero_count": (
            len(candidate_only) - len(nonzero_mean_mag_ids)
        ),
        "candidate_only_with_zero_ng_or_nr_count": sum(
            catalog_metadata[oid]["ng"] == 0 or catalog_metadata[oid]["nr"] == 0
            for oid in candidate_only
        ),
        "both_mean_magnitudes_nonzero_objects": [
            {
                "source_id": oid,
                "gmag": catalog_metadata[oid]["gmag"],
                "rmag": catalog_metadata[oid]["rmag"],
                "period": catalog_metadata[oid]["period"],
                "per_g": catalog_metadata[oid]["per_g"],
                "per_r": catalog_metadata[oid]["per_r"],
                "r2_g": catalog_metadata[oid]["r2_g"],
                "r2_r": catalog_metadata[oid]["r2_r"],
                "gamp": catalog_metadata[oid]["gamp"],
                "ramp": catalog_metadata[oid]["ramp"],
                "fap_g": catalog_metadata[oid]["fap_g"],
                "fap_r": catalog_metadata[oid]["fap_r"],
                "ng": catalog_metadata[oid]["ng"],
                "nr": catalog_metadata[oid]["nr"],
                "type": catalog_metadata[oid]["type"],
                "g_qualifying_detections": g[oid]["qualifying_detections"],
                "r_qualifying_detections": r[oid]["qualifying_detections"],
                "g_qualifying_flag_or": g[oid]["qualifying_flag_or"],
                "r_qualifying_flag_or": r[oid]["qualifying_flag_or"],
            }
            for oid in sorted(nonzero_mean_mag_ids)
        ],
        "zero_mean_magnitude_source_id_sample": [
            oid for oid in sorted(candidate_only - nonzero_mean_mag_ids)[:100]
        ],
        "warning": (
            "Diagnostic only. Nonzero parent mean magnitudes are not an accepted "
            "selection criterion unless supported by the source methodology."
        ),
    }

    # Full ID-level evidence enables auditing every extra candidate, not only samples.
    report["candidate_only_all_objects"] = [
        {
            "source_id": oid,
            "parent": catalog_metadata[oid],
            "g": {key: g[oid][key] for key in (
                "qualifying_detections", "qualifying_flag_or",
                "qualifying_flag_nonzero", "brightest_qualifying_mag",
                "smallest_qualifying_error", "snr", "snr_exact", "snr1",
            )},
            "r": {key: r[oid][key] for key in (
                "qualifying_detections", "qualifying_flag_or",
                "qualifying_flag_nonzero", "brightest_qualifying_mag",
                "smallest_qualifying_error", "snr", "snr_exact", "snr1",
            )},
            "parent_mean_magnitudes_nonzero": (
                has_finite_nonzero_mean_magnitudes(catalog_metadata[oid])
            ),
        }
        for oid in sorted(candidate_only)
    ]

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
