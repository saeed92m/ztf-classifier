"""Trace every CPVS candidate-only SourceID to parent and per-epoch source records.

Diagnostic only: this tool does not change selection thresholds or acceptance criteria.
It emits (1) one object-level provenance row per candidate-only ID, (2) one JSONL
record per parsed g/r epoch for those IDs, and (3) a hash manifest and count-drift report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from audit_cpvs_membership import (
    _iter_parent_lines,
    read_parent_name_to_sourceid,
    read_selected,
    read_vizier,
)
from ztf_classifier.validation.derivation import (
    _iter_rows,
    _parse_cpvs_table2_identity,
    _path_member_matches_header,
    _snr_from_mag_error,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files(path: Path, required: tuple[str, ...]) -> list[Path]:
    if path.is_file():
        return [path]
    suffixes = {".csv", ".txt", ".dat", ".json", ".gz", ""}
    return sorted(
        item for item in path.rglob("*")
        if item.is_file()
        and item.suffix.lower() in suffixes
        and _path_member_matches_header(item, required)
    )


def parent_records(path: Path) -> tuple[dict[int, dict[str, object]], dict[str, int]]:
    name_to_id = read_parent_name_to_sourceid(path)
    id_to_name = {source_id: name for name, source_id in name_to_id.items()}
    records: dict[int, dict[str, object]] = {}
    for line_number, line in enumerate(_iter_parent_lines(path), start=1):
        identity = _parse_cpvs_table2_identity(line)
        if identity is None:
            continue
        name, raw_id = identity
        source_id = int(raw_id)
        records[source_id] = {
            "parent_record_line": line_number,
            "parent_record_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
            "parent_record_raw": line.rstrip("\r\n"),
            "ztf_name_normalized": name,
        }
    if set(records) != set(id_to_name):
        raise ValueError("Parent record trace does not cover the full SourceID mapping")
    return records, id_to_name


def trace_band(
    root: Path,
    *,
    band: str,
    parent_ids: set[int],
    extras: set[int],
    output_jsonl,
) -> dict[int, dict[str, object]]:
    error_key = "e_gmag" if band == "g" else "e_rmag"
    mag_key = "gmag" if band == "g" else "rmag"
    flag_key = "g_flag" if band == "g" else "r_flag"
    sigma = 2.5 if band == "g" else 3.0
    required = ("SourceID", error_key, mag_key)
    metrics: dict[int, dict[str, object]] = {}
    for source_path in source_files(root, required):
        rel = str(source_path)
        for parsed_row_index, row in enumerate(_iter_rows(source_path, required_columns=required), start=1):
            raw_id = (row.get("SourceID") or row.get("sourceid") or "").strip()
            try:
                source_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if source_id not in parent_ids:
                continue
            item = metrics.setdefault(source_id, {
                "row_count": 0,
                "snr_qualified_row_count": 0,
                "production_qualifying_row_count": 0,
                "production_qualifying_valid_magnitude_row_count": 0,
                "snr_qualified_valid_magnitude_row_count": 0,
                "valid_magnitude_row_count": 0,
                "same_row_snr_and_valid_magnitude_count": 0,
                "first_snr_qualified_row": None,
                "best_snr_row": None,
                "flag_values_on_qualifying_rows": Counter(),
            })
            item["row_count"] += 1
            try:
                magnitude = float(row.get(mag_key, ""))
            except (TypeError, ValueError):
                magnitude = float("nan")
            try:
                error = float(row.get(error_key, ""))
            except (TypeError, ValueError):
                error = float("nan")
            valid_mag = math.isfinite(magnitude) and magnitude != 0.0
            snr = _snr_from_mag_error(row.get(error_key, ""))
            snr_pass = math.isfinite(snr) and snr >= sigma
            if valid_mag:
                item["valid_magnitude_row_count"] += 1
            # Production currently tests snr < threshold; NaN < threshold is False,
            # so non-finite SNR values can incorrectly pass this branch.
            production_pass = not (snr < sigma)
            if production_pass:
                item["production_qualifying_row_count"] += 1
            if snr_pass:
                item["snr_qualified_row_count"] += 1
                if item["first_snr_qualified_row"] is None:
                    item["first_snr_qualified_row"] = {
                        "file": rel, "parsed_row_index": parsed_row_index,
                        "hjd": row.get("HJD"), "magnitude": row.get(mag_key),
                        "magnitude_error": row.get(error_key), "snr": snr,
                        "flag": row.get(flag_key),
                    }
                best = item["best_snr_row"]
                if best is None or snr > best["snr"]:
                    item["best_snr_row"] = {
                        "file": rel, "parsed_row_index": parsed_row_index,
                        "hjd": row.get("HJD"), "magnitude": row.get(mag_key),
                        "magnitude_error": row.get(error_key), "snr": snr,
                        "flag": row.get(flag_key),
                    }
                item["flag_values_on_qualifying_rows"][str(row.get(flag_key, ""))] += 1
            if snr_pass and valid_mag:
                item["same_row_snr_and_valid_magnitude_count"] += 1
                item["snr_qualified_valid_magnitude_row_count"] += 1
            if production_pass and valid_mag:
                item["production_qualifying_valid_magnitude_row_count"] += 1
            if source_id in extras:
                record = {
                    "source_id": source_id,
                    "band": band,
                    "source_file": rel,
                    "parsed_row_index": parsed_row_index,
                    "hjd": row.get("HJD"),
                    "magnitude": row.get(mag_key),
                    "magnitude_error": row.get(error_key),
                    "snr": snr if math.isfinite(snr) else None,
                    "snr_threshold": sigma,
                    "snr_pass": snr_pass,
                    "production_snr_predicate_pass": bool(production_pass),
                    "magnitude_finite_nonzero": bool(valid_mag),
                    "same_row_qualifies": bool(snr_pass and valid_mag),
                    "production_same_row_qualifies": bool(production_pass and valid_mag),
                    "flag": row.get(flag_key),
                    "raw_parsed_row": row,
                }
                output_jsonl.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--g", type=Path, required=True)
    parser.add_argument("--r", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--code-version", required=True)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    parent_meta, name_by_id = parent_records(args.parent)
    parent_ids = set(parent_meta)
    candidate = read_selected(args.candidate)
    published = read_vizier(args.published, args.parent)
    if len(parent_ids) != 781_602 or len(published) != 730_184:
        raise ValueError(f"Unexpected parent/reference sizes: {len(parent_ids)}/{len(published)}")
    if not candidate <= parent_ids:
        raise ValueError("Candidate IDs are not a subset of parent SourceIDs")

    candidate_only = candidate - published
    published_only = published - candidate
    with (out / "cpvs_candidate_only_epoch_provenance.jsonl").open("w", encoding="utf-8") as ledger:
        g_metrics = trace_band(args.g, band="g", parent_ids=parent_ids, extras=candidate_only, output_jsonl=ledger)
        r_metrics = trace_band(args.r, band="r", parent_ids=parent_ids, extras=candidate_only, output_jsonl=ledger)

    # The published implementation uses object-level intersection of SNR-qualified
    # IDs and IDs with any finite non-zero magnitude. This alternate rowwise set is
    # reported for diagnosis only; neither set is asserted to be scientifically correct.
    g_production = {oid for oid, m in g_metrics.items() if m["production_qualifying_row_count"]}
    r_production = {oid for oid, m in r_metrics.items() if m["production_qualifying_row_count"]}
    g_production_valid = {oid for oid, m in g_metrics.items() if m["production_qualifying_valid_magnitude_row_count"]}
    r_production_valid = {oid for oid, m in r_metrics.items() if m["production_qualifying_valid_magnitude_row_count"]}
    g_rowwise = {oid for oid, m in g_metrics.items() if m["same_row_snr_and_valid_magnitude_count"]}
    r_rowwise = {oid for oid, m in r_metrics.items() if m["same_row_snr_and_valid_magnitude_count"]}
    production_predicate = (g_production & r_production & g_production_valid & r_production_valid) & parent_ids
    rowwise = g_rowwise & r_rowwise & parent_ids
    production_only = sorted(production_predicate - rowwise)
    rowwise_only = sorted(rowwise - production_predicate)
    actual_vs_recomputed = sorted(candidate ^ production_predicate, key=int)

    summary_path = out / "cpvs_candidate_only_provenance.tsv"
    fields = [
        "SourceID", "ZTF_name", "parent_record_line", "parent_record_sha256",
        "g_rows", "g_snr_rows", "g_valid_mag_rows", "g_same_row_qualified_rows",
        "g_first_snr_row", "g_best_snr_row",
        "r_rows", "r_snr_rows", "r_production_rows", "r_production_valid_mag_rows", "r_valid_mag_rows", "r_same_row_qualified_rows",
        "r_first_snr_row", "r_best_snr_row",
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for oid in sorted(candidate_only):
            p = parent_meta[oid]
            g = g_metrics.get(oid, {})
            r = r_metrics.get(oid, {})
            writer.writerow({
                "SourceID": oid,
                "ZTF_name": name_by_id[oid],
                "parent_record_line": p["parent_record_line"],
                "parent_record_sha256": p["parent_record_sha256"],
                "g_rows": g.get("row_count", 0),
                "g_snr_rows": g.get("snr_qualified_row_count", 0),
                "g_production_rows": g.get("production_qualifying_row_count", 0),
                "g_production_valid_mag_rows": g.get("production_qualifying_valid_magnitude_row_count", 0),
                "g_valid_mag_rows": g.get("valid_magnitude_row_count", 0),
                "g_same_row_qualified_rows": g.get("same_row_snr_and_valid_magnitude_count", 0),
                "g_first_snr_row": json.dumps(g.get("first_snr_qualified_row"), sort_keys=True),
                "g_best_snr_row": json.dumps(g.get("best_snr_row"), sort_keys=True),
                "r_rows": r.get("row_count", 0),
                "r_snr_rows": r.get("snr_qualified_row_count", 0),
                "r_production_rows": r.get("production_qualifying_row_count", 0),
                "r_production_valid_mag_rows": r.get("production_qualifying_valid_magnitude_row_count", 0),
                "r_valid_mag_rows": r.get("valid_magnitude_row_count", 0),
                "r_same_row_qualified_rows": r.get("same_row_snr_and_valid_magnitude_count", 0),
                "r_first_snr_row": json.dumps(r.get("first_snr_qualified_row"), sort_keys=True),
                "r_best_snr_row": json.dumps(r.get("best_snr_row"), sort_keys=True),
            })

    hashes = {}
    for label, path, required in (
        ("parent", args.parent, ()),
        ("candidate", args.candidate, ()),
        ("published", args.published, ()),
    ):
        hashes[label] = {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)}
    for label, root, required in (("g_lightcurves", args.g, ("SourceID", "e_gmag", "gmag")), ("r_lightcurves", args.r, ("SourceID", "e_rmag", "rmag"))):
        files = source_files(root, required)
        hashes[label] = [{
            "path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)
        } for path in files]

    ledger_path = out / "cpvs_candidate_only_epoch_provenance.jsonl"
    report = {
        "schema_version": 1,
        "status": "UNRESOLVED" if candidate_only or published_only else "REFERENCE_MEMBERSHIP_MATCH",
        "diagnostic_only": True,
        "code_version": args.code_version,
        "counts": {
            "parent_ids": len(parent_ids), "published_ids": len(published),
            "candidate_ids": len(candidate), "intersection": len(candidate & published),
            "candidate_only": len(candidate_only), "published_only": len(published_only),
            "production_predicate_count": len(production_predicate),
            "strict_finite_snr_rowwise_predicate_count": len(rowwise),
            "production_only_count": len(production_only),
            "strict_rowwise_only_count": len(rowwise_only),
            "candidate_vs_recomputed_production_xor_count": len(actual_vs_recomputed),
        },
        "predicate_drift": {
            "production_only_source_ids": production_only,
            "strict_rowwise_only_source_ids": rowwise_only,
            "candidate_vs_recomputed_production_xor_source_ids": actual_vs_recomputed,
            "production_definition": "mimics current _qualified_ids: not (snr < threshold); this incorrectly treats NaN SNR as passing, then requires finite non-zero magnitude on that same row",
            "strict_rowwise_definition": "finite SNR >= threshold AND finite non-zero magnitude on the same row, independently in both bands",
            "code_root_cause": "Python NaN comparison: NaN < threshold is False, so the current negative-only guard accepts non-finite SNR. Verify the exact real IDs in this ledger.",
            "scientific_disposition": "This NaN guard is a code defect if the traced IDs confirm it; it does not explain the remaining candidate-only membership mismatch.",
        },
        "published_only_source_ids": sorted(published_only),
        "input_hashes": hashes,
        "outputs": {
            summary_path.name: {"sha256": sha256(summary_path), "size_bytes": summary_path.stat().st_size},
            ledger_path.name: {"sha256": sha256(ledger_path), "size_bytes": ledger_path.stat().st_size},
        },
        "parent_record_note": "parent line and SHA-256 refer to the exact decoded Table2 source line; source file hash is in input_hashes.parent",
        "validation": {
            "candidate_matches_recomputed_production_predicate": len(actual_vs_recomputed) == 0,
            "candidate_production_xor_ids": actual_vs_recomputed,
        },
        "epoch_record_note": "parsed_row_index is the ordinal among parser-emitted data rows in the named source file, not the physical byte line number",
    }
    report_path = out / "cpvs_provenance_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], indent=2, sort_keys=True))
    print(json.dumps(report["predicate_drift"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
