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


def id_set_sha256(values: set[str]) -> str:
    payload = "".join(f"{value}\n" for value in sorted(values, key=int)).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def records(
    path: pathlib.Path, expected_lrecl: int, *, allow_trailing_pad: bool = False
):
    raw = path.read_bytes()
    lines = raw.splitlines()
    # CDS fixed-width files can omit trailing blank bytes. Publisher MRT files
    # retain a final pad byte. Keep source bytes unchanged in both cases.
    rows = [line for line in lines if line[:22].strip().startswith(b"ZTF")]
    lengths = Counter(map(len, rows))
    if not rows:
        raise ValueError(f"{path}: no data records")
    if any(len(row) < 29 for row in rows):
        raise ValueError(f"{path}: record shorter than required ID fields")
    if allow_trailing_pad:
        allowed_lengths = {expected_lrecl, expected_lrecl + 1}
        invalid_lengths = [len(row) for row in rows if len(row) not in allowed_lengths]
        if invalid_lengths:
            raise ValueError(
                f"{path}: unexpected publisher record lengths; "
                f"allowed={sorted(allowed_lengths)}, observed={Counter(invalid_lengths)}"
            )
        if any(len(row) == expected_lrecl + 1 and row[-1:] != b" " for row in rows):
            raise ValueError(f"{path}: publisher pad byte is not an ASCII space")
    elif any(len(row) > expected_lrecl for row in rows):
        raise ValueError(f"{path}: raw CDS record exceeds Lrecl={expected_lrecl}")
    return raw, rows, lengths


def field(row: bytes, start: int, end: int) -> str:
    return row[start:end].decode("ascii", errors="strict").strip()


def load_table2(path: pathlib.Path, *, allow_trailing_pad: bool = False):
    raw, rows, lengths = records(
        path, LRECL["table2"], allow_trailing_pad=allow_trailing_pad
    )
    by_name: dict[str, dict[str, str]] = {}
    by_seq: dict[str, str] = {}
    for n, row in enumerate(rows, 1):
        if len(row) < 216:
            raise ValueError(f"Table2 row {n}: truncated record ({len(row)} bytes)")
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


def load_table4(path: pathlib.Path, *, allow_trailing_pad: bool = False):
    raw, rows, lengths = records(
        path, LRECL["table4"], allow_trailing_pad=allow_trailing_pad
    )
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
        raise ValueError(
            f"Expected exactly one {name} below {root}, found {len(matches)}"
        )
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


def is_positive_field(value: object) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def hash_rank(seed: str, value: str) -> str:
    return hashlib.sha256((seed + ":" + value).encode("utf-8")).hexdigest()


def sample_ids(groups: dict[str, set[str]], n: int, seed: str):
    required = {
        "reference_candidate",
        "candidate_only",
        "four_field_only",
        "reference_only",
        "parent_neither",
    }
    missing = required - groups.keys()
    if missing:
        raise ValueError(f"Sample groups missing required strata: {sorted(missing)}")

    # Deliberately oversample discrepancy populations. The 1,000-object design
    # includes all 55 four-field-only controls when that full population exists.
    # This is a diagnostic sample, not a prevalence estimator.
    quotas = {
        "reference_candidate": int(round(n * 0.50)),
        "candidate_only": int(round(n * 0.25)),
        "four_field_only": min(
            len(groups["four_field_only"]), max(10, int(round(n * 0.055)))
        ),
        "reference_only": min(
            len(groups["reference_only"]),
            max(1, int(round(n * 0.05))) if groups["reference_only"] else 0,
        ),
    }
    quotas["parent_neither"] = n - sum(quotas.values())
    if quotas["parent_neither"] < 0:
        raise ValueError(f"Sample {n}: stratum quotas exceed requested sample size")

    selected = []
    for group in ("reference_candidate", "candidate_only", "four_field_only", "reference_only"):
        quota = quotas[group]
        ordered = sorted(groups[group], key=lambda x: hash_rank(seed + ":" + group, x))
        if len(ordered) < quota:
            raise ValueError(
                f"Sample {n}: {group} has {len(ordered)} objects, needs {quota}"
            )
        selected.extend((value, group) for value in ordered[:quota])
    ordered_neither = sorted(
        groups["parent_neither"],
        key=lambda x: hash_rank(seed + ":parent_neither", x),
    )
    if len(ordered_neither) < quotas["parent_neither"]:
        raise ValueError(
            f"Sample {n}: parent_neither has {len(ordered_neither)} objects, "
            f"needs {quotas['parent_neither']}"
        )
    selected.extend(
        (value, "parent_neither")
        for value in ordered_neither[: quotas["parent_neither"]]
    )
    if len(selected) != n or len({x for x, _ in selected}) != n:
        raise ValueError(f"Sample {n}: invalid sample cardinality or duplicate IDs")
    return sorted(selected, key=lambda item: hash_rank(seed + ":output", item[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=pathlib.Path)
    ap.add_argument("--zenodo", required=True, type=pathlib.Path)
    ap.add_argument("--publisher", required=True, type=pathlib.Path)
    ap.add_argument("--heavy", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    t2_path = args.raw / "table2.dat"
    t4_path = args.raw / "table4.dat"
    t2_readme = args.raw / "table2.ReadMe"
    t4_readme = args.raw / "table4.ReadMe"
    t2_gzip = args.raw / "table2.dat.gz"
    t4_gzip = args.raw / "table4.dat.gz"
    publisher_t2_path = find_one(args.publisher, "table2.mrt.txt")
    publisher_t4_path = find_one(args.publisher, "table4.mrt.txt")

    # Hash the exact raw CDS payloads, compressed archives, ReadMe files,
    # and retained original publisher MRT files before parsing.
    hash_paths = [
        t2_path,
        t4_path,
        t2_readme,
        t4_readme,
        t2_gzip,
        t4_gzip,
        publisher_t2_path,
        publisher_t4_path,
    ]
    hashes = {
        str(p.relative_to(args.raw))
        if p.is_relative_to(args.raw)
        else f"publisher/{p.name}": {"bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in hash_paths
    }
    (out / "raw_source_hashes.json").write_text(
        json.dumps(
            {"retrieved_utc": datetime.now(timezone.utc).isoformat(), "files": hashes},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    t2_raw, t2_rows, t2_lengths, t2_by_name, t2_by_seq = load_table2(t2_path)
    t4_raw, t4_rows, t4_lengths, t4_rows_parsed = load_table4(t4_path)
    _, publisher_t2_rows, publisher_t2_lengths, _, _ = load_table2(
        publisher_t2_path, allow_trailing_pad=True
    )
    _, publisher_t4_rows, publisher_t4_lengths, _ = load_table4(
        publisher_t4_path, allow_trailing_pad=True
    )
    if len(t2_rows) != EXPECTED["table2"]:
        raise ValueError(f"Table2 count {len(t2_rows)} != {EXPECTED['table2']}")
    if len(t4_rows) != EXPECTED["table4"]:
        raise ValueError(f"Table4 count {len(t4_rows)} != {EXPECTED['table4']}")
    if len(publisher_t2_rows) != len(t2_rows) or len(publisher_t4_rows) != len(t4_rows):
        raise ValueError("Publisher MRT and raw CDS record counts differ")
    t2_publisher_mismatches = [
        i
        for i, (raw_row, publisher_row) in enumerate(zip(t2_rows, publisher_t2_rows), 1)
        if publisher_row[: LRECL["table2"]] != raw_row.ljust(LRECL["table2"], b" ")
    ]
    t4_publisher_mismatches = [
        i
        for i, (raw_row, publisher_row) in enumerate(zip(t4_rows, publisher_t4_rows), 1)
        if publisher_row[: LRECL["table4"]] != raw_row.ljust(LRECL["table4"], b" ")
    ]

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
    if len(candidate_only_records) != len(
        diagnostics.get("candidate_only_all_objects", [])
    ):
        raise ValueError(
            "Duplicate source_id in candidate_only_all_objects diagnostics"
        )

    parent_set = set(t2_by_seq)
    four_field_set = {
        sid
        for sid, ztf in t2_by_seq.items()
        if all(
            is_positive_field(t2_by_name[ztf].get(field, ""))
            for field in ("gmag", "rmag", "Per-g", "Per-r")
        )
    }
    table2_seq_gaps = sorted(
        set(range(1, 781605)) - {int(value) for value in parent_set}
    )
    table4_seq_sha256 = id_set_sha256(table4_seq)
    zenodo_seq_sha256 = id_set_sha256(zenodo_set)
    candidate_seq_sha256 = id_set_sha256(candidate_set)
    candidate_only = candidate_set - table4_seq
    reference_only = table4_seq - candidate_set
    intersection = table4_seq & candidate_set
    candidate_four_field = candidate_set & four_field_set
    four_field_only = four_field_set - candidate_set - table4_seq
    parent_neither = parent_set - (table4_seq | candidate_set | four_field_set)
    empirical_conjunction_exact_match = candidate_four_field == table4_seq
    residual_field_partition = Counter()
    for sid in candidate_only:
        row = t2_by_name[t2_by_seq[sid]]
        magnitude_pair = all(
            is_positive_field(row.get(field, "")) for field in ("gmag", "rmag")
        )
        period_pair = all(
            is_positive_field(row.get(field, "")) for field in ("Per-g", "Per-r")
        )
        if not magnitude_pair and not period_pair:
            residual_field_partition["both_pairs_incomplete"] += 1
        elif magnitude_pair and not period_pair:
            residual_field_partition["magnitudes_complete_periods_incomplete"] += 1
        elif not magnitude_pair and period_pair:
            residual_field_partition["periods_complete_magnitudes_incomplete"] += 1
        else:
            residual_field_partition["all_four_fields_positive"] += 1
    zenodo_vs_table4 = {
        "table4_only": table4_seq - zenodo_set,
        "zenodo_only": zenodo_set - table4_seq,
    }

    # Candidate-only object-level provenance from retained heavy-run diagnostics.
    residual_path = out / "candidate_only_11602_object_provenance.tsv"
    residual_fields = [
        "SourceID",
        "Table4_member",
        "Zenodo_member",
        "candidate",
        "mean_magnitude_pair_positive",
        "band_period_pair_positive",
        "four_field_positive",
        "ZTF",
        "Type",
        "gmag",
        "rmag",
        "Per-g",
        "Per-r",
        "Per",
        "Ng",
        "Nr",
        "R2-g",
        "R2-r",
        "g_qualifying_detections",
        "r_qualifying_detections",
        "g_snr",
        "r_snr",
        "g_qualifying_flag_or",
        "r_qualifying_flag_or",
        "g_smallest_qualifying_error",
        "r_smallest_qualifying_error",
    ]
    with residual_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=residual_fields, delimiter="\t", lineterminator="\n"
        )
        w.writeheader()
        for sid in sorted(candidate_only, key=lambda x: int(x)):
            item = candidate_only_records.get(sid, {})
            p = item.get("parent", {})
            g = item.get("g", {})
            r = item.get("r", {})
            ztf = t2_by_seq.get(sid, "")
            w.writerow(
                {
                    "SourceID": sid,
                    "Table4_member": False,
                    "Zenodo_member": sid in zenodo_set,
                    "candidate": True,
                    "mean_magnitude_pair_positive": all(
                        is_positive_field(t2_by_name[ztf].get(field, ""))
                        for field in ("gmag", "rmag")
                    ),
                    "band_period_pair_positive": all(
                        is_positive_field(t2_by_name[ztf].get(field, ""))
                        for field in ("Per-g", "Per-r")
                    ),
                    "four_field_positive": sid in four_field_set,
                    "ZTF": ztf,
                    "Type": p.get("type", t2_by_name.get(ztf, {}).get("Type", "")),
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
                    "g_smallest_qualifying_error": g.get(
                        "smallest_qualifying_error", ""
                    ),
                    "r_smallest_qualifying_error": r.get(
                        "smallest_qualifying_error", ""
                    ),
                }
            )

    # Preserve all 55 four-field-positive controls outside the SNR candidate set.
    four_field_only_path = out / "four_field_only_55.tsv"
    four_field_fields = [
        "SourceID",
        "Table4_member",
        "Zenodo_member",
        "candidate",
        "four_field_positive",
        "ZTF",
        "Type",
        "gmag",
        "rmag",
        "Per-g",
        "Per-r",
        "Per",
        "Ng",
        "Nr",
        "R2-g",
        "R2-r",
    ]
    with four_field_only_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=four_field_fields, delimiter="\t", lineterminator="\n"
        )
        w.writeheader()
        for sid in sorted(four_field_only, key=lambda x: int(x)):
            ztf = t2_by_seq[sid]
            row = t2_by_name[ztf]
            w.writerow(
                {
                    "SourceID": sid,
                    "Table4_member": sid in table4_seq,
                    "Zenodo_member": sid in zenodo_set,
                    "candidate": sid in candidate_set,
                    "four_field_positive": sid in four_field_set,
                    "ZTF": ztf,
                    "Type": row["Type"],
                    "gmag": row["gmag"],
                    "rmag": row["rmag"],
                    "Per-g": row["Per-g"],
                    "Per-r": row["Per-r"],
                    "Per": row["Per"],
                    "Ng": row["Ng"],
                    "Nr": row["Nr"],
                    "R2-g": row["R2-g"],
                    "R2-r": row["R2-r"],
                }
            )

    # Fresh deterministic stratified samples from the full parent population.
    groups = {
        "reference_candidate": intersection,
        "candidate_only": candidate_only,
        "four_field_only": four_field_only,
        "reference_only": reference_only,
        "parent_neither": parent_neither,
    }
    sample_seed = "ztf-cpvs-fixed-object-sample-v2"
    sample_quotas = {}
    for n in (100, 1000):
        sample = sample_ids(groups, n, sample_seed)
        sample_quotas[str(n)] = dict(Counter(stratum for _, stratum in sample))
        with (out / f"fixed_sample_{n}.tsv").open(
            "w", encoding="utf-8", newline=""
        ) as f:
            fields = [
                "SourceID",
                "stratum",
                "Table4_member",
                "Zenodo_member",
                "candidate",
                "mean_magnitude_pair_positive",
                "band_period_pair_positive",
                "four_field_positive",
                "ZTF",
                "Type",
                "gmag",
                "rmag",
                "Per-g",
                "Per-r",
                "Ng",
                "Nr",
            ]
            w = csv.DictWriter(
                f, fieldnames=fields, delimiter="\t", lineterminator="\n"
            )
            w.writeheader()
            for sid, stratum in sample:
                ztf = t2_by_seq[sid]
                p = t2_by_name[ztf]
                w.writerow(
                    {
                        "SourceID": sid,
                        "stratum": stratum,
                        "Table4_member": sid in table4_seq,
                        "Zenodo_member": sid in zenodo_set,
                        "candidate": sid in candidate_set,
                        "mean_magnitude_pair_positive": all(
                            is_positive_field(p.get(field, ""))
                            for field in ("gmag", "rmag")
                        ),
                        "band_period_pair_positive": all(
                            is_positive_field(p.get(field, ""))
                            for field in ("Per-g", "Per-r")
                        ),
                        "four_field_positive": sid in four_field_set,
                        "ZTF": ztf,
                        "Type": p["Type"],
                        "gmag": p["gmag"],
                        "rmag": p["rmag"],
                        "Per-g": p["Per-g"],
                        "Per-r": p["Per-r"],
                        "Ng": p["Ng"],
                        "Nr": p["Nr"],
                    }
                )

    source_crosswalk_pass = (
        len(t2_rows) == EXPECTED["table2"]
        and len(t4_rows) == EXPECTED["table4"]
        and not unmapped
        and not direct_id_mismatches
        and len(table4_seq) == EXPECTED["table4"]
        and not t2_publisher_mismatches
        and not t4_publisher_mismatches
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

    def is_missing(value: object) -> bool:
        return value is None or str(value).strip().lower() in {
            "",
            "nan",
            "none",
            "null",
        }

    def as_number(value: object):
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    with residual_path.open("r", encoding="utf-8", newline="") as f:
        residual_rows = list(csv.DictReader(f, delimiter="\t"))

    def quantiles(values: list[float]):
        ordered = sorted(values)
        return {
            "count": len(ordered),
            "min": min(ordered) if ordered else None,
            "median": statistics.median(ordered) if ordered else None,
            "p90_nearest_rank": ordered[round((len(ordered) - 1) * 0.90)]
            if ordered
            else None,
            "max": max(ordered) if ordered else None,
        }

    residual_summary = {
        "object_count": len(residual_rows),
        "g_snr_true_count": sum(row["g_snr"] == "True" for row in residual_rows),
        "r_snr_true_count": sum(row["r_snr"] == "True" for row in residual_rows),
        "missing_parent_fields": {
            key: sum(is_missing(row.get(key)) for row in residual_rows)
            for key in ("gmag", "rmag", "Per-g", "Per-r")
        },
        "both_mean_magnitudes_present": sum(
            not is_missing(row["gmag"]) and not is_missing(row["rmag"])
            for row in residual_rows
        ),
        "both_band_periods_present": sum(
            not is_missing(row["Per-g"]) and not is_missing(row["Per-r"])
            for row in residual_rows
        ),
        "g_qualifying_detections": quantiles(
            [
                as_number(row["g_qualifying_detections"])
                for row in residual_rows
                if as_number(row["g_qualifying_detections"]) is not None
            ]
        ),
        "r_qualifying_detections": quantiles(
            [
                as_number(row["r_qualifying_detections"])
                for row in residual_rows
                if as_number(row["r_qualifying_detections"]) is not None
            ]
        ),
        "objects_with_nonzero_qualifying_flag_or": {
            "g": sum(
                as_number(row["g_qualifying_flag_or"]) not in (None, 0)
                for row in residual_rows
            ),
            "r": sum(
                as_number(row["r_qualifying_flag_or"]) not in (None, 0)
                for row in residual_rows
            ),
        },
        "parent_zero_detection_counts": {
            "Ng_zero": sum(as_number(row["Ng"]) == 0 for row in residual_rows),
            "Nr_zero": sum(as_number(row["Nr"]) == 0 for row in residual_rows),
        },
    }
    output_artifacts = [
        crosswalk_path,
        residual_path,
        four_field_only_path,
        out / "fixed_sample_100.tsv",
        out / "fixed_sample_1000.tsv",
    ]
    output_artifact_hashes = {
        item.name: {"bytes": item.stat().st_size, "sha256": sha256(item)}
        for item in output_artifacts
    }

    report = {
        "status": overall_status,
        "source_crosswalk_status": "PASS" if source_crosswalk_pass else "FAIL",
        "zenodo_membership_status": "PASS" if zenodo_exact_match else "FAIL",
        "candidate_reproduction_status": "PASS" if candidate_exact_match else "FAIL",
        "candidate_diagnostics_coverage": {
            "missing_residual_diagnostics_count": len(candidate_diagnostics_missing),
            "missing_residual_diagnostics_examples": sorted(
                candidate_diagnostics_missing, key=lambda x: int(x)
            )[:20],
            "extra_residual_diagnostics_count": len(candidate_diagnostics_extra),
            "extra_residual_diagnostics_examples": sorted(
                candidate_diagnostics_extra, key=lambda x: int(x)
            )[:20],
        },
        "scope_note": "Inputs are the original CDS fixed-width tables from the official NAOJ VizieR mirror, with byte-for-byte row comparison against original IOP/AAS publisher MRT files. Candidate membership is historical evidence from workflow run 38635891449; this job does not re-download or re-derive the 179M light-curve rows.",
        "primary_source_urls": {
            "table2_cds": "https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJS/249/18/table2.dat",
            "table4_cds": "https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJ/932/118/table4.dat",
            "table2_naoj_mirror": "http://vizier.nao.ac.jp/ftp/cats/J/ApJS/249/18/table2.dat.gz",
            "table4_naoj_mirror": "http://vizier.nao.ac.jp/ftp/cats/J/ApJ/932/118/table4.dat.gz",
        },
        "source_files": hashes,
        "membership_set_hashes": {
            "table4_sorted_seq_sha256": table4_seq_sha256,
            "zenodo_sorted_sourceid_sha256": zenodo_seq_sha256,
            "candidate_sorted_sourceid_sha256": candidate_seq_sha256,
            "candidate_only_sorted_sourceid_sha256": id_set_sha256(candidate_only),
            "reference_only_sorted_sourceid_sha256": id_set_sha256(reference_only),
            "table2_missing_seq_values_in_1_to_781604": table2_seq_gaps,
        },
        "candidate_only_diagnostic_summary": residual_summary,
        "output_artifact_hashes": output_artifact_hashes,
        "record_validation": {
            "table2_records": len(t2_rows),
            "table2_expected": EXPECTED["table2"],
            "table2_record_length_distribution": dict(sorted(t2_lengths.items())),
            "table4_records": len(t4_rows),
            "table4_expected": EXPECTED["table4"],
            "table4_record_length_distribution": dict(sorted(t4_lengths.items())),
            "publisher_table2_record_length_distribution": dict(
                sorted(publisher_t2_lengths.items())
            ),
            "publisher_table4_record_length_distribution": dict(
                sorted(publisher_t4_lengths.items())
            ),
        },
        "publisher_vs_raw_cds_row_comparison": {
            "table2_exact_data_rows": len(t2_rows) - len(t2_publisher_mismatches),
            "table2_mismatched_rows": len(t2_publisher_mismatches),
            "table2_mismatch_examples": t2_publisher_mismatches[:20],
            "table4_exact_data_rows": len(t4_rows) - len(t4_publisher_mismatches),
            "table4_mismatched_rows": len(t4_publisher_mismatches),
            "table4_mismatch_examples": t4_publisher_mismatches[:20],
            "comparison_rule": "publisher MRT bytes [0:Lrecl] must equal the raw CDS .dat record right-padded with ASCII spaces to Lrecl; source files are not modified",
        },
        "identifier_crosswalk": {
            "table2_unique_ZTF": len(t2_by_name),
            "table2_unique_Seq": len(t2_by_seq),
            "table4_unique_ZTF": len(t4_rows_parsed),
            "table4_unmapped_ZTF_count": len(unmapped),
            "table4_unmapped_ZTF_examples": unmapped[:20],
            "table4_ID_equals_parent_Seq_count": len(t4_rows_parsed)
            - len(direct_id_mismatches),
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
            "four_field_parent_count": len(four_field_set),
            "candidate_four_field_intersection_count": len(candidate_four_field),
            "candidate_intersection_four_field_equals_table4": empirical_conjunction_exact_match,
            "four_field_only_non_candidate_count": len(four_field_only),
            "four_field_only_sorted_sourceid_sha256": id_set_sha256(four_field_only),
            "candidate_only_field_partition": dict(sorted(residual_field_partition.items())),
            "parent_neither_after_four_field_partition_count": len(parent_neither),
            "parent_neither_count": len(parent_neither),
        },
        "artifacts": {
            "crosswalk_tsv": crosswalk_path.name,
            "candidate_only_object_provenance_tsv": residual_path.name,
            "four_field_only_tsv": four_field_only_path.name,
            "samples": ["fixed_sample_100.tsv", "fixed_sample_1000.tsv"],
        },
        "reproducibility": {
            "sample_seed": sample_seed,
            "sample_method": "SHA-256 rank within five explicit membership/diagnostic strata; diagnostic oversampling, not a prevalence estimator",
            "sample_strata": sample_quotas,
        },
        "limitations": [
            "The CDS .dat files were retrieved unchanged from the official NAOJ VizieR mirror because the primary CDS host timed out in this environment; both original CDS URLs and mirror URLs are recorded.",
            "The publisher MRT comparison right-pads only the in-memory raw CDS record for comparison. The raw source files remain unchanged.",
            "Zenodo membership and candidate comparisons use retained workflow artifacts; the 89,697,393-row-per-band light curves are not re-downloaded in this job.",
            "The historical candidate set is not a fresh derivation from the current PR head.",
            "A successful identifier crosswalk does not prove that the scientific selection method was reproduced.",
        ],
    }
    (out / "reconciliation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (out / "reconciliation_report.md").write_text(
        "# CPVS raw CDS and publisher reconciliation\n\n"
        f"- Overall status: **{report['status']}**\n"
        f"- Raw Table 2 records: {len(t2_rows):,}\n"
        f"- Raw Table 4 records: {len(t4_rows):,}\n"
        f"- Table 4 unmapped ZTF names: {len(unmapped):,}\n"
        f"- Table 4 ID vs Table 2 SourceID mismatches: {len(direct_id_mismatches):,}\n"
        f"- Raw CDS vs publisher MRT row mismatches: {len(t2_publisher_mismatches):,} (Table 2), {len(t4_publisher_mismatches):,} (Table 4)\n"
        f"- Table 4 vs Zenodo exact membership: {zenodo_exact_match}\n"
        f"- Historical candidate count: {len(candidate_set):,}\n"
        f"- Candidate-only residuals: {len(candidate_only):,}\n"
        f"- Reference-only residuals: {len(reference_only):,}\n"
        f"- Four-field parent rows: {len(four_field_set):,}\n"
        f"- Candidate intersection with four-field set: {len(candidate_four_field):,}\n"
        f"- Empirical conjunction equals Table 4: {empirical_conjunction_exact_match}\n"
        f"- Four-field-only non-candidates: {len(four_field_only):,}\n\n"
        "See reconciliation_report.json, raw_source_hashes.json, the full crosswalk, "
        "candidate-only provenance, the 55-object four-field-only control set, "
        "and deterministic 100/1,000-object stratified samples.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
