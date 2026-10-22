#!/usr/bin/env python3
"""Verify the CPVS four-field parent-metadata predicate as a diagnostic only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


FIELDS = ("gmag", "rmag", "Per-g", "Per-r")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def positive_finite(value: Any) -> bool:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def read_candidate_ids(path: Path) -> set[int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "SourceID" not in reader.fieldnames:
            raise ValueError(f"candidate file lacks SourceID header: {path}")
        result = set()
        for row in reader:
            raw = (row.get("SourceID") or "").strip()
            if not raw:
                continue
            try:
                result.add(int(raw))
            except ValueError as exc:
                raise ValueError(f"invalid candidate SourceID {raw!r}") from exc
    return result


def read_parent_metadata(path: Path) -> dict[int, dict[str, str]]:
    with path.open(encoding="utf-8", errors="replace") as handle:
        lines = [line for line in handle if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError(f"empty parent metadata file: {path}")
    reader = csv.DictReader(lines, delimiter="\t")
    required = {"Seq", *FIELDS}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError(f"parent metadata missing required columns: {required}")
    result: dict[int, dict[str, str]] = {}
    for row in reader:
        raw = (row.get("Seq") or "").strip()
        if not raw or set(raw) == {"-"}:
            # VizieR TSV exports include a dashed separator row after the header.
            continue
        try:
            source_id = int(raw)
        except ValueError as exc:
            raise ValueError(f"invalid parent Seq {raw!r}") from exc
        if source_id in result:
            raise ValueError(f"duplicate parent Seq {source_id}")
        result[source_id] = {field: (row.get(field) or "").strip() for field in FIELDS}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-metadata", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--selection-diagnostics", type=Path, required=True)
    parser.add_argument("--membership-audit", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    selection_raw = args.selection_diagnostics.read_bytes()
    audit_raw = args.membership_audit.read_bytes()
    parent = read_parent_metadata(args.parent_metadata)
    candidates = read_candidate_ids(args.candidates)
    selection = json.loads(selection_raw)
    audit = json.loads(audit_raw)

    candidate_only_rows = selection.get("candidate_only_all_objects")
    if not isinstance(candidate_only_rows, list):
        raise ValueError("selection diagnostics lack candidate_only_all_objects")
    candidate_only_ids = {int(row["source_id"]) for row in candidate_only_rows}
    if len(candidate_only_ids) != len(candidate_only_rows):
        raise ValueError("duplicate SourceID in candidate-only diagnostic list")
    if not candidate_only_ids.issubset(candidates):
        raise ValueError("candidate-only diagnostic IDs are not a subset of candidates")
    if not candidates.issubset(parent):
        raise ValueError("candidate IDs include values absent from parent metadata")
    filtered = {
        source_id
        for source_id in candidates
        if all(positive_finite(parent[source_id].get(field, "")) for field in FIELDS)
    }
    expected_published = candidates - candidate_only_ids
    if int(audit.get("candidate_count", len(candidates))) != len(candidates):
        raise ValueError("candidate count differs from membership audit")
    if int(audit.get("candidate_only_count", len(candidate_only_ids))) != len(candidate_only_ids):
        raise ValueError("candidate-only count differs from membership audit")
    if int(audit.get("published_only_count", 0)) != 0:
        raise ValueError("published-only IDs exist; candidate-minus-extras is not the reference set")
    if len(expected_published) != int(audit.get("published_count", len(expected_published))):
        raise ValueError("candidate minus extras does not equal the published count")

    exact_match = filtered == expected_published
    if not exact_match:
        raise ValueError(
            "four-field diagnostic does not equal candidate set minus crosswalk-confirmed extras"
        )

    positive_counts = {
        field: sum(positive_finite(values.get(field, "")) for values in parent.values())
        for field in FIELDS
    }
    valid_all_four = {
        source_id
        for source_id, values in parent.items()
        if all(positive_finite(values.get(field, "")) for field in FIELDS)
    }
    dispositions = {}
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    csv_fields = [
        "SourceID", "gmag", "rmag", "Per-g", "Per-r",
        "gmag_positive", "rmag_positive", "Per-g_positive", "Per-r_positive",
        "both_mean_magnitudes_positive", "both_band_periods_positive",
        "all_four_fields_positive", "diagnostic_disposition",
    ]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for source_id in sorted(candidate_only_ids):
            values = parent[source_id]
            flags = {field: positive_finite(values.get(field, "")) for field in FIELDS}
            means = flags["gmag"] and flags["rmag"]
            periods = flags["Per-g"] and flags["Per-r"]
            if not means and not periods:
                disposition = "both_pairs_incomplete"
            elif means and not periods:
                disposition = "mean_magnitudes_valid_period_pair_incomplete"
            elif periods and not means:
                disposition = "period_pair_valid_mean_magnitudes_incomplete"
            else:
                disposition = "all_four_valid"
            dispositions[disposition] = dispositions.get(disposition, 0) + 1
            writer.writerow({
                "SourceID": source_id,
                **values,
                **{f"{field}_positive": flags[field] for field in FIELDS},
                "both_mean_magnitudes_positive": means,
                "both_band_periods_positive": periods,
                "all_four_fields_positive": all(flags.values()),
                "diagnostic_disposition": disposition,
            })

    report = {
        "schema_version": "1.0",
        "diagnostic_only": True,
        "production_selection_changed": False,
        "candidate_count": len(candidates),
        "parent_metadata_count": len(parent),
        "published_count_from_crosswalk_audit": int(audit.get("published_count", 0)),
        "candidate_only_count": len(candidate_only_ids),
        "published_only_count_from_crosswalk_audit": int(audit.get("published_only_count", 0)),
        "four_field_filtered_candidate_count": len(filtered),
        "four_field_filtered_candidate_only_count": len(filtered & candidate_only_ids),
        "four_field_filtered_set_equals_published_reference": exact_match,
        "positive_finite_count_by_parent_field": positive_counts,
        "parent_rows_with_all_four_fields_positive": len(valid_all_four),
        "candidate_only_partition": dispositions,
        "input_sha256": {
            "parent_metadata_tsv": sha256(args.parent_metadata),
            "candidate_tsv": sha256(args.candidates),
            "selection_diagnostics_json": sha256(args.selection_diagnostics),
            "membership_audit_json": sha256(args.membership_audit),
        },
        "interpretation": (
            "Exact membership under the four-field validity predicate is reproduced. "
            "This does not prove the publisher used this predicate; do not adopt it in "
            "production without method/source evidence or author clarification."
        ),
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
