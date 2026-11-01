#!/usr/bin/env python3
"""Byte-preserving CDS CPVS Table 2 / Table 4 reconciliation.

The original publisher MRT files are read as bytes. Hashes are calculated before parsing.
Identifiers remain strings. No selector or production artifact is modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import statistics
from collections import Counter
from datetime import datetime, timezone

EXPECTED = {"table2": 781_602, "table4": 730_184}
LRECL = {"table2": 228, "table4": 63}


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def records(path: pathlib.Path, expected_lrecl: int):
    raw = path.read_bytes()
    lines = raw.splitlines()
    # Publisher MRT files contain a descriptive header. Select only catalog
    # records. Keep the original record bytes and whitespace unchanged.
    rows = [line for line in lines if line[:22].strip().startswith(b"ZTF")]
    lengths = Counter(map(len, rows))
    if not rows:
        raise ValueError(f"{path}: no data records")
    if any(len(row) < 29 for row in rows):
        raise ValueError(f"{path}: record shorter than required ID fields")
    if any(len(row) > expected_lrecl for row in rows):
        raise ValueError(f"{path}: record longer than expected Lrecl={expected_lrecl}")
    return raw, rows, lengths

def field(row: bytes, start: int, end: int) -> str:
    return row[start:end].decode("ascii", errors="strict").strip()


def load_table2(path: pathlib.Path):
    raw, rows, lengths = records(path, LRECL["table2"])
    by_name: dict[str, dict[str, str]] = {}
    by_seq: dict[str, str] = {}
    for n, row in enumerate(rows, 1):
        name = field(row, 0, 22)
        seq = field(row, 23, 29)
        if not name or not name.startswith("ZTF"):
            raise ValueError(f"Table2 row {n}: invalid ZTF ID {name!r}")
        if not seq.isascii() or not seq.isdecimal():
            raise ValueError(f"Table2 row {n}: invalid Seq {seq!r}")
        if name in by_name:
            raise ValueError(f"Table2 row {n}: duplicate ZTF name {name}")
        if seq in by_seq:
            raise ValueError(f"Table2 row {n}: duplicate Seq {seq}")
        by_name[name] = {
            "SourceID": seq,
            "ZTF": name,
            "Per": field(row, 50, 61),
            "gmag": field(row, 89, 95),
            "rmag": field(row, 96, 102),
            "Per-g": field(row, 103, 116),
            "Per-r": field(row, 117, 130),
            "Ng": field(row, 131, 135),
            "Nr": field(row, 136, 140),
            "R2-g": field(row, 167, 173),
            "R2-r": field(row, 174, 180),
            "Type": field(row, 211, 216),
        }
        by_seq[seq] = name
    return raw, rows, lengths, by_name, by_seq


def load_table4(path: pathlib.Path):
    raw, rows, lengths = records(path, LRECL["table4"])
    parsed = []
    seen_names, seen_ids = set(), set()
    for n, row in enumerate(rows, 1):
        name = field(row, 0, 22)
        internal_id = field(row, 23, 29)
        if not name or not name.startswith("ZTF"):
            raise ValueError(f"Table4 row {n}: invalid ZTF name {name!r}")
        if not internal_id.isascii() or not internal_id.isdecimal():
            raise ValueError(f"Table4 row {n}: invalid ID {internal_id!r}")
        if name in seen_names:
            raise ValueError(f"Table4 row {n}: duplicate ZTF name {name}")
        if internal_id in seen_ids:
            raise ValueError(f"Table4 row {n}: duplicate internal ID {internal_id}")
        seen_names.add(name)
        seen_ids.add(internal_id)
        parsed.append({"ZTF": name, "Table4_ID": internal_id})
    return raw, rows, lengths, parsed


def find_one(root: pathlib.Path, name: str) -> pathlib.Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {name} below {root}, found {len(matches)}")
    return matches[0]


def read_id_set(path: pathlib.Path, header: str | None = None) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError(f"{path}: missing TSV header")
        key = header or reader.fieldnames[0]
        if key not in reader.fieldnames:
            raise ValueError(f"{path}: missing {key}; fields={reader.fieldnames}")
        return {str(row[key]).strip() for row in reader if row.get(key, "").strip()}


def read_candidate_ids(path: pathlib.Path) -> set[str]:
    vals = set()
    with path.open("r", encoding="utf-8-sig") as f:
        next(f, None)
        for line in f:
            value = line.strip().split("\t", 1)[0]
            if value:
                vals.add(value)
    return vals


def hash_rank(seed: str, value: str) -> str:
    return hashlib.sha256((seed + ":" + value).encode("utf-8")).hexdigest()


def sample_ids(groups: dict[str, set[str]], n: int, seed: str):
    # Fixed design: if reference-only objects exist, reserve 5% for them;
    # otherwise use the established 50/25/25 design.
    if groups["reference_only"]:
        fractions = {
            "reference_candidate": 0.45,
            "candidate_only": 0.25,
            "reference_only": 0.05,
            "parent_neither": 0.25,
        }
    else:
        fractions = {
            "reference_candidate": 0.50,
            "candidate_only": 0.25,
            "reference_only": 0.00,
            "parent_neither": 0.25,
        }
    quotas = {k: int(round(n * v)) for k, v in fractions.items()}
    # Keep the total exact. Allocate rounding remainder to the largest stratum.
    diff = n - sum(quotas.values())
    quotas["reference_candidate"] += diff
    selected = []
    for group, quota in quotas.items():
        ordered = sorted(groups[group], key=lambda x: hash_rank(seed + ":" + group, x))
        if len(ordered) < quota:
            raise ValueError(f"Sample {n}: {group} has {len(ordered)} objects, needs {quota}")
        selected.extend((value, group) for value in ordered[:quota])
    if len(selected) != n or len({x for x, _ in selected}) != n:
        raise ValueError(f"Sample {n}: invalid sample cardinality or duplicate IDs")
    return sorted(selected, key=lambda item: hash_rank(seed + ":output", item[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=pathlib.Path)
    ap.add_argument("--zenodo", required=True, type=pathlib.Path)
    ap.add_argument("--heavy", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    t2_path = args.raw / "table2.mrt.txt"
    t4_path = args.raw / "table4.mrt.txt"

    # Hash the original downloaded bytes before any parsing.
    hashes = {
        p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in [t2_path, t4_path]
    }
    (out / "raw_source_hashes.json").write_text(
        json.dumps({"retrieved_utc": datetime.now(timezone.utc).isoformat(),
                    "files": hashes}, indent=2) + "\n", encoding="utf-8"
    )

    t2_raw, t2_rows, t2_lengths, t2_by_name, t2_by_seq = load_table2(t2_path)
    t4_raw, t4_rows, t4_lengths, t4_rows_parsed = load_table4(t4_path)
    if len(t2_rows) != EXPECTED["table2"]:
        raise ValueError(f"Table2 count {len(t2_rows)} != {EXPECTED['table2']}")
    if len(t4_rows) != EXPECTED["table4"]:
        raise ValueError(f"Table4 count {len(t4_rows)} != {EXPECTED['table4']}")

    table4_seq, unmapped, direct_id_mismatches = set(), [], []
    crosswalk_path = out / "table4_to_table2_seq_crosswalk.tsv"
    with crosswalk_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["ZTF", "Table4_ID", "Table2_Seq", "Table4_ID_equals_Table2_Seq"])
        for row in t4_rows_parsed:
            parent = t2_by_name.get(row["ZTF"])
            if parent is None:
                unmapped.append(row["ZTF"])
                continue
            seq = parent["SourceID"]
            table4_seq.add(seq)
            same = row["Table4_ID"] == seq
            if not same:
                direct_id_mismatches.append((row["ZTF"], row["Table4_ID"], seq))
            w.writerow([row["ZTF"], row["Table4_ID"], seq, str(same).lower()])

    zenodo_path = find_one(args.zenodo, "published_membership_seq.tsv")
    zenodo_set = read_id_set(zenodo_path, "SourceID")
    candidate_path = find_one(args.heavy, "selected.tsv")
    candidate_set = read_candidate_ids(candidate_path)
    diagnostics_path = find_one(args.heavy, "selection_diagnostics.json")
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    candidate_only_records = {
        str(item["source_id"]): item
        for item in diagnostics.get("candidate_only_all_objects", [])
    }
    if len(candidate_only_records) != len(diagnostics.get("candidate_only_all_objects", [])):
        raise ValueError("Duplicate source_id in candidate_only_all_objects diagnostics")

    parent_set = set(t2_by_seq)
    candidate_only = candidate_set - table4_seq
    reference_only = table4_seq - candidate_set
    intersection = table4_seq & candidate_set
    parent_neither = parent_set - (table4_seq | candidate_set)
    zenodo_vs_table4 = {
        "table4_only": table4_seq - zenodo_set,
        "zenodo_only": zenodo_set - table4_seq,
    }

    # Candidate-only object-level provenance from retained heavy-run diagnostics.
    residual_path = out / "candidate_only_11602_object_provenance.tsv"
    residual_fields = [
        "SourceID", "Table4_member", "Zenodo_member", "candidate",
        "ZTF", "Type", "gmag", "rmag", "Per-g", "Per-r", "Per",
        "Ng", "Nr", "R2-g", "R2-r",
        "g_qualifying_detections", "r_qualifying_detections",
        "g_snr", "r_snr", "g_qualifying_flag_or", "r_qualifying_flag_or",
        "g_smallest_qualifying_error", "r_smallest_qualifying_error",
    ]
    with residual_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=residual_fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for sid in sorted(candidate_only, key=lambda x: int(x)):
            item = candidate_only_records.get(sid, {})
            p = item.get("parent", {})
            g = item.get("g", {})
            r = item.get("r", {})
            ztf = t2_by_seq.get(sid, "")
            w.writerow({
                "SourceID": sid, "Table4_member": False,
                "Zenodo_member": sid in zenodo_set, "candidate": True,
                "ZTF": ztf, "Type": p.get("type", t2_by_name.get(ztf, {}).get("Type", "")),
                "gmag": p.get("gmag", t2_by_name.get(ztf, {}).get("gmag", "")),
                "rmag": p.get("rmag", t2_by_name.get(ztf, {}).get("rmag", "")),
                "Per-g": p.get("per_g", t2_by_name.get(ztf, {}).get("Per-g", "")),
                "Per-r": p.get("per_r", t2_by_name.get(ztf, {}).get("Per-r", "")),
                "Per": p.get("period", t2_by_name.get(ztf, {}).get("Per", "")),
                "Ng": p.get("ng", t2_by_name.get(ztf, {}).get("Ng", "")),
                "Nr": p.get("nr", t2_by_name.get(ztf, {}).get("Nr", "")),
                "R2-g": p.get("r2_g", t2_by_name.get(ztf, {}).get("R2-g", "")),
                "R2-r": p.get("r2_r", t2_by_name.get(ztf, {}).get("R2-r", "")),
                "g_qualifying_detections": g.get("qualifying_detections", ""),
                "r_qualifying_detections": r.get("qualifying_detections", ""),
                "g_snr": g.get("snr_exact", g.get("snr", "")),
                "r_snr": r.get("snr_exact", r.get("snr", "")),
                "g_qualifying_flag_or": g.get("qualifying_flag_or", ""),
                "r_qualifying_flag_or": r.get("qualifying_flag_or", ""),
                "g_smallest_qualifying_error": g.get("smallest_qualifying_error", ""),
                "r_smallest_qualifying_error": r.get("smallest_qualifying_error", ""),
            })

    # Fresh deterministic stratified samples against raw Table4 membership.
    groups = {
        "reference_candidate": intersection,
        "candidate_only": candidate_only,
        "reference_only": reference_only,
        "parent_neither": parent_neither,
    }
    for n in (100, 1000):
        sample = sample_ids(groups, n, "ztf-cpvs-fixed-object-sample-v1")
        with (out / f"fixed_sample_{n}.tsv").open("w", encoding="utf-8", newline="") as f:
            fields = ["SourceID", "stratum", "Table4_member", "Zenodo_member", "candidate",
                      "ZTF", "Type", "gmag", "rmag", "Per-g", "Per-r", "Ng", "Nr"]
            w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
            w.writeheader()
            for sid, stratum in sample:
                ztf = t2_by_seq[sid]
                p = t2_by_name[ztf]
                w.writerow({
                    "SourceID": sid, "stratum": stratum,
                    "Table4_member": sid in table4_seq,
                    "Zenodo_member": sid in zenodo_set,
                    "candidate": sid in candidate_set,
                    "ZTF": ztf, "Type": p["Type"],
                    "gmag": p["gmag"], "rmag": p["rmag"],
                    "Per-g": p["Per-g"], "Per-r": p["Per-r"],
                    "Ng": p["Ng"], "Nr": p["Nr"],
                })

    source_crosswalk_pass = (
        len(t2_rows) == EXPECTED["table2"]
        and len(t4_rows) == EXPECTED["table4"]
        and not unmapped
        and not direct_id_mismatches
        and len(table4_seq) == EXPECTED["table4"]
    )
    zenodo_exact_match = table4_seq == zenodo_set
    candidate_exact_match = table4_seq == candidate_set
    candidate_diagnostics_missing = candidate_only - set(candidate_only_records)
    candidate_diagnostics_extra = set(candidate_only_records) - candidate_only

    if not source_crosswalk_pass:
        overall_status = "FAIL_SOURCE_IDENTIFIER_CROSSWALK"
    elif not zenodo_exact_match:
        overall_status = "FAIL_TABLE4_VS_ZENODO_MEMBERSHIP"
    elif not candidate_exact_match:
        overall_status = "UNRESOLVED_CANDIDATE_MEMBERSHIP_MISMATCH"
    else:
        overall_status = "PASS_EXACT_MEMBERSHIP_MATCH"

    report = {
        "status": overall_status,
        "source_crosswalk_status": "PASS" if source_crosswalk_pass else "FAIL",
        "zenodo_membership_status": "PASS" if zenodo_exact_match else "FAIL",
        "candidate_reproduction_status": "PASS" if candidate_exact_match else "FAIL",
        "candidate_diagnostics_coverage": {
            "missing_residual_diagnostics_count": len(candidate_diagnostics_missing),
            "missing_residual_diagnostics_examples": sorted(candidate_diagnostics_missing, key=lambda x: int(x))[:20],
            "extra_residual_diagnostics_count": len(candidate_diagnostics_extra),
            "extra_residual_diagnostics_examples": sorted(candidate_diagnostics_extra, key=lambda x: int(x))[:20],
        },
        "scope_note": "Inputs are the original publisher machine-readable tables from IOP/AAS. Candidate membership is historical evidence from workflow run 38635891449; this job does not re-download or re-derive the 179M light-curve rows.",
        "primary_source_urls": {
            "table2_mrt": "https://content.cld.iop.org/journals/0067-0049/249/1/18/revision1/apjsab9caet2_mrt.txt",
            "table4_mrt": "https://content.cld.iop.org/journals/0004-637X/932/2/118/revision1/apjac69d4t4_mrt.txt",
        },
        "source_files": hashes,
        "record_validation": {
            "table2_records": len(t2_rows), "table2_expected": EXPECTED["table2"],
            "table2_record_length_distribution": dict(sorted(t2_lengths.items())),
            "table4_records": len(t4_rows), "table4_expected": EXPECTED["table4"],
            "table4_record_length_distribution": dict(sorted(t4_lengths.items())),
        },
        "identifier_crosswalk": {
            "table2_unique_ZTF": len(t2_by_name),
            "table2_unique_Seq": len(t2_by_seq),
            "table4_unique_ZTF": len(t4_rows_parsed),
            "table4_unmapped_ZTF_count": len(unmapped),
            "table4_unmapped_ZTF_examples": unmapped[:20],
            "table4_ID_equals_parent_Seq_count": len(t4_rows_parsed) - len(direct_id_mismatches),
            "table4_ID_vs_parent_Seq_mismatch_count": len(direct_id_mismatches),
            "table4_ID_vs_parent_Seq_mismatch_examples": direct_id_mismatches[:20],
        },
        "membership_comparison": {
            "table4_seq_count": len(table4_seq),
            "zenodo_sourceid_count": len(zenodo_set),
            "table4_vs_zenodo_exact_match": zenodo_exact_match,
            "table4_only_vs_zenodo_count": len(zenodo_vs_table4["table4_only"]),
            "zenodo_only_vs_table4_count": len(zenodo_vs_table4["zenodo_only"]),
            "candidate_count_historical": len(candidate_set),
            "table4_intersection_candidate_count": len(intersection),
            "candidate_vs_table4_exact_match": candidate_exact_match,
            "candidate_only_count": len(candidate_only),
            "reference_only_count": len(reference_only),
            "parent_neither_count": len(parent_neither),
        },
        "artifacts": {
            "crosswalk_tsv": crosswalk_path.name,
            "candidate_only_object_provenance_tsv": residual_path.name,
            "samples": ["fixed_sample_100.tsv", "fixed_sample_1000.tsv"],
        },
        "reproducibility": {
            "sample_seed": "ztf-cpvs-fixed-object-sample-v1",
            "sample_method": "SHA-256 rank within explicit membership strata; no random-state dependence",
        },
        "limitations": [
            "The publisher MRT files are hashed before parsing. This run does not contain the CDS fixed-width .dat byte streams; it reconciles the publisher originals against the retained VizieR/Zenodo crosswalk evidence.",
            "Zenodo and candidate comparisons use retained workflow artifacts; the 89,697,393-row-per-band light curves are not re-downloaded in this job.",
            "The historical candidate set is not a fresh derivation from the current PR head.",
            "A membership match does not prove the scientific selection method was reproduced.",
        ],
    }
    (out / "reconciliation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (out / "reconciliation_report.md").write_text(
        "# CPVS original publisher MRT reconciliation\n\n"
        f"- Status: **{report['status']}**\n"
        f"- Table 2 publisher MRT records: {len(t2_rows):,}\n"
        f"- Table 4 publisher MRT records: {len(t4_rows):,}\n"
        f"- Table 4 unmapped ZTF names: {len(unmapped):,}\n"
        f"- Table 4 internal ID vs Table 2 SourceID mismatches: {len(direct_id_mismatches):,}\n"
        f"- Table 4 vs Zenodo exact membership: {table4_seq == zenodo_set}\n"
        f"- Historical candidate count: {len(candidate_set):,}\n"
        f"- Candidate-only residuals: {len(candidate_only):,}\n"
        f"- Reference-only residuals: {len(reference_only):,}\n\n"
        "See reconciliation_report.json, raw_source_hashes.json, the full crosswalk, "
        "candidate-only provenance, and deterministic 100/1,000-object samples.\n",
        encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
