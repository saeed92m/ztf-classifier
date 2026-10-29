#!/usr/bin/env python3
"""Reconstruct the published CPVS detection-threshold membership from source photometry.

Standard-library only. The primary threshold uses the conventional relation
sigma_mag = (2.5 / ln(10)) / SNR. Flag==0 is measured as a separate sensitivity
variant; it is not silently imposed on the primary interpretation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import zipfile
from collections import Counter
from pathlib import Path

EXPECTED_PARENT_ROWS = 781_602
EXPECTED_PUBLISHED = 730_184
EXPECTED_TABLE2_LINES = 781_636
EXPECTED_METADATA_LINES = 34
SEQ_MIN_EXPECTED = 1
SEQ_MAX_EXPECTED = 781_604
MAG_ERROR_FACTOR = 2.5 / math.log(10.0)
G_SNR_THRESHOLD = 2.5
R_SNR_THRESHOLD = 3.0
G_MAX_MAGERR = MAG_ERROR_FACTOR / G_SNR_THRESHOLD
R_MAX_MAGERR = MAG_ERROR_FACTOR / R_SNR_THRESHOLD


class AuditError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_ids(values) -> str:
    payload = "".join(f"{x}\n" for x in sorted(values)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def find_member(zip_path: Path, candidates: set[str]) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        files = [n for n in zf.namelist() if not n.endswith("/")]
        exact = [n for n in files if Path(n).name in candidates]
        if len(exact) != 1:
            raise AuditError(
                f"{zip_path.name}: expected exactly one member basename in "
                f"{sorted(candidates)}, found {exact[:10]} (members={files[:10]})"
            )
        return exact[0]


def read_table2(zip_path: Path):
    member = find_member(zip_path, {"Table2.txt", "table2.dat"})
    seq_to_name = {}
    name_to_seq = {}
    s4 = set()
    null_counts = Counter()
    metadata = []
    source_lines = 0
    record_lengths = []
    with zipfile.ZipFile(zip_path) as zf, zf.open(member) as stream:
        for line_number, raw in enumerate(stream, start=1):
            source_lines += 1
            line = raw.decode("ascii", errors="strict").rstrip("\r\n")
            name = line[:22].strip() if len(line) >= 22 else ""
            seq_text = line[23:29].strip() if len(line) >= 29 else ""
            is_record = (
                len(line) >= 129
                and name.upper().startswith("ZTF")
                and seq_text.isdigit()
            )
            if not is_record:
                metadata.append({"line": line_number, "length": len(line), "preview": line[:120]})
                continue

            seq = int(seq_text)
            if seq in seq_to_name:
                raise AuditError(f"Duplicate Table2 Seq {seq} at source line {line_number}")
            if not (SEQ_MIN_EXPECTED <= seq <= SEQ_MAX_EXPECTED):
                raise AuditError(f"Table2 Seq out of expected range: {seq}")
            if name in name_to_seq:
                raise AuditError(f"Duplicate Table2 ZTF name {name!r}")
            seq_to_name[seq] = name
            name_to_seq[name] = seq
            record_lengths.append(len(line))

            # The Zenodo source records are not fully consistent with the byte
            # widths printed in the header. These are the observed data spans:
            # gmag 90-95, rmag 97-102, Per-g 104-116, Per-r 117-129.
            raw_fields = {
                "gmag": line[89:95],
                "rmag": line[96:102],
                "per_g": line[103:116],
                "per_r": line[116:129],
            }
            values = {}
            for field, raw_value in raw_fields.items():
                value = raw_value.strip()
                if not value:
                    values[field] = None
                    null_counts[field] += 1
                    continue
                try:
                    number = float(value.replace("D", "E").replace("d", "e"))
                except ValueError as exc:
                    raise AuditError(
                        f"Non-numeric Table2 {field} at source line {line_number}: {raw_value!r}"
                    ) from exc
                if not math.isfinite(number) or number == 0.0:
                    values[field] = None
                    null_counts[field] += 1
                else:
                    values[field] = number
            if all(values[k] is not None and values[k] > 0 for k in ("gmag", "rmag", "per_g", "per_r")):
                s4.add(seq)

    if source_lines != EXPECTED_TABLE2_LINES:
        raise AuditError(f"Table2 source lines {source_lines}; expected {EXPECTED_TABLE2_LINES}")
    if len(metadata) != EXPECTED_METADATA_LINES or [x["line"] for x in metadata] != list(range(1, EXPECTED_METADATA_LINES + 1)):
        raise AuditError("Table2 metadata/header contract changed; refusing to skip unrecognized lines")
    if len(seq_to_name) != EXPECTED_PARENT_ROWS:
        raise AuditError(f"Table2 records {len(seq_to_name)}; expected {EXPECTED_PARENT_ROWS}")
    if min(seq_to_name) != SEQ_MIN_EXPECTED or max(seq_to_name) != SEQ_MAX_EXPECTED:
        raise AuditError("Table2 Seq min/max differs from the pinned source contract")
    return {
        "member": member,
        "seq_to_name": seq_to_name,
        "name_to_seq": name_to_seq,
        "four_field_ids": s4,
        "null_counts": dict(sorted(null_counts.items())),
        "metadata": metadata,
        "source_lines": source_lines,
        "record_lengths": record_lengths,
    }


def read_published(zip_path: Path):
    member = find_member(zip_path, {"1st_layer.csv"})
    names = set()
    rows = 0
    with zipfile.ZipFile(zip_path) as zf, zf.open(member) as stream:
        import io
        text = io.TextIOWrapper(stream, encoding="utf-8", newline="")
        reader = csv.DictReader(text)
        if not reader.fieldnames or "ID" not in reader.fieldnames:
            raise AuditError(f"{member}: missing required CSV column 'ID'")
        for row in reader:
            rows += 1
            name = (row.get("ID") or "").strip()
            if not name:
                raise AuditError(f"{member}: empty ID at data row {rows}")
            names.add(name)
    if rows != EXPECTED_PUBLISHED or len(names) != EXPECTED_PUBLISHED:
        raise AuditError(
            f"Published membership rows/unique IDs={rows}/{len(names)}; expected {EXPECTED_PUBLISHED}"
        )
    return member, names, rows


def split_fields(raw: bytes) -> list[str]:
    text = raw.decode("ascii", errors="strict").strip()
    if not text:
        return []
    if "," in text:
        return [part.strip() for part in next(csv.reader([text]))]
    return text.split()


def scan_photometry(zip_path: Path, band: str, target_ids: set[int]):
    if band == "g":
        member_candidates = {"ztf2g", "ztf2g.dat", "ztf2g.txt", "ztf2g.csv"}
        threshold = G_MAX_MAGERR
    elif band == "r":
        member_candidates = {"ztf2r", "ztf2r.dat", "ztf2r.txt", "ztf2r.csv"}
        threshold = R_MAX_MAGERR
    else:
        raise ValueError(band)

    member = find_member(zip_path, member_candidates)
    qualifying_any = set()
    qualifying_flag0 = set()
    rows = 0
    malformed = 0
    source_ids_seen = set()
    flag_counts = Counter()
    invalid_error_rows = 0
    target_stats = {
        sid: {
            "rows": 0, "valid_error_rows": 0,
            "min_magerr_any": None, "min_magerr_flag0": None,
            "pass_snr_any": False, "pass_snr_flag0": False,
            "flags_seen": Counter(),
        }
        for sid in target_ids
    }

    with zipfile.ZipFile(zip_path) as zf, zf.open(member) as stream:
        for line_number, raw in enumerate(stream, start=1):
            if not raw.strip():
                continue
            fields = split_fields(raw)
            if fields and fields[0].lower() == "sourceid" and line_number == 1:
                continue
            if len(fields) < 7:
                malformed += 1
                if malformed > 0:
                    raise AuditError(f"{member}: malformed row {line_number}, {len(fields)} fields")
            try:
                sid = int(fields[0])
                magerr = float(fields[5])
                flag = int(float(fields[6]))
            except (ValueError, IndexError) as exc:
                raise AuditError(f"{member}: cannot parse row {line_number}: {raw[:160]!r}") from exc
            rows += 1
            source_ids_seen.add(sid)
            flag_counts[str(flag)] += 1
            valid = math.isfinite(magerr) and magerr > 0
            passes = valid and magerr <= threshold
            passes_flag0 = passes and flag == 0
            if valid:
                if passes:
                    qualifying_any.add(sid)
                if passes_flag0:
                    qualifying_flag0.add(sid)
            else:
                invalid_error_rows += 1

            if sid in target_stats:
                item = target_stats[sid]
                item["rows"] += 1
                item["flags_seen"][str(flag)] += 1
                if valid:
                    item["valid_error_rows"] += 1
                    old = item["min_magerr_any"]
                    item["min_magerr_any"] = magerr if old is None else min(old, magerr)
                    if flag == 0:
                        old0 = item["min_magerr_flag0"]
                        item["min_magerr_flag0"] = magerr if old0 is None else min(old0, magerr)
                item["pass_snr_any"] = item["pass_snr_any"] or passes
                item["pass_snr_flag0"] = item["pass_snr_flag0"] or passes_flag0

    return {
        "member": member,
        "rows": rows,
        "malformed_rows": malformed,
        "invalid_error_rows": invalid_error_rows,
        "source_ids_seen": source_ids_seen,
        "qualifying_any": qualifying_any,
        "qualifying_flag0": qualifying_flag0,
        "flag_counts": dict(sorted(flag_counts.items())),
        "target_stats": target_stats,
        "magerr_threshold": threshold,
    }


def write_ids(path: Path, ids: set[int]):
    path.write_text("".join(f"{sid}\n" for sid in sorted(ids)), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table2-zip", type=Path)
    parser.add_argument("--published-zip", type=Path)
    parser.add_argument("--g-zip", type=Path)
    parser.add_argument("--r-zip", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        assert math.isclose(G_MAX_MAGERR, 1.0857362047581296 / 2.5)
        assert math.isclose(R_MAX_MAGERR, 1.0857362047581296 / 3.0)
        assert split_fields(b"1, 2, 3, 4, 5, 0.2, 0") == ["1", "2", "3", "4", "5", "0.2", "0"]
        assert split_fields(b"1 2 3 4 5 0.2 0") == ["1", "2", "3", "4", "5", "0.2", "0"]
        print(json.dumps({"self_test": "PASS", "g_magerr_max": G_MAX_MAGERR, "r_magerr_max": R_MAX_MAGERR}))
        return 0

    required = (args.table2_zip, args.published_zip, args.g_zip, args.r_zip)
    if any(path is None for path in required):
        parser.error("provide --table2-zip, --published-zip, --g-zip, and --r-zip (or --self-test)")
    for path in required:
        if not path.is_file():
            raise AuditError(f"Input file does not exist: {path}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    table2 = read_table2(args.table2_zip)
    member, published_names, published_rows = read_published(args.published_zip)
    name_to_seq = table2["name_to_seq"]
    unmapped_names = sorted(published_names - set(name_to_seq))
    if unmapped_names:
        raise AuditError(f"{len(unmapped_names)} published names do not map to Table2; examples={unmapped_names[:10]}")
    published_ids = {name_to_seq[name] for name in published_names}
    if len(published_ids) != EXPECTED_PUBLISHED:
        raise AuditError("Published name-to-Seq mapping is not one-to-one")

    s4 = table2["four_field_ids"]
    s4_only = s4 - published_ids
    published_only_s4 = published_ids - s4
    g = scan_photometry(args.g_zip, "g", s4_only)
    r = scan_photometry(args.r_zip, "r", s4_only)

    # Primary interpretation: at least one threshold-passing detection in each band.
    snr_any = g["qualifying_any"] & r["qualifying_any"]
    snr_flag0 = g["qualifying_flag0"] & r["qualifying_flag0"]
    variants = {
        "snr_threshold_any_flag": snr_any,
        "snr_threshold_flag_zero_only": snr_flag0,
    }
    comparisons = {}
    for label, candidate_ids in variants.items():
        candidate_only = candidate_ids - published_ids
        published_only = published_ids - candidate_ids
        comparisons[label] = {
            "candidate_count": len(candidate_ids),
            "intersection": len(candidate_ids & published_ids),
            "candidate_only": len(candidate_only),
            "published_only": len(published_only),
            "candidate_only_sha256_sorted_seq": sha256_ids(candidate_only),
            "published_only_sha256_sorted_seq": sha256_ids(published_only),
            "exact_set_match": candidate_ids == published_ids,
        }
        write_ids(args.out_dir / f"{label}_candidate_only_seq.txt", candidate_only)
        write_ids(args.out_dir / f"{label}_published_only_seq.txt", published_only)

    target_details = []
    for sid in sorted(s4_only):
        target_details.append({
            "Seq": sid,
            "ZTF_ID": table2["seq_to_name"][sid],
            "g_rows": g["target_stats"][sid]["rows"],
            "g_min_magerr_any": g["target_stats"][sid]["min_magerr_any"],
            "g_min_magerr_flag0": g["target_stats"][sid]["min_magerr_flag0"],
            "g_pass_2p5sigma_any_flag": g["target_stats"][sid]["pass_snr_any"],
            "g_pass_2p5sigma_flag0_only": g["target_stats"][sid]["pass_snr_flag0"],
            "r_rows": r["target_stats"][sid]["rows"],
            "r_min_magerr_any": r["target_stats"][sid]["min_magerr_any"],
            "r_min_magerr_flag0": r["target_stats"][sid]["min_magerr_flag0"],
            "r_pass_3sigma_any_flag": r["target_stats"][sid]["pass_snr_any"],
            "r_pass_3sigma_flag0_only": r["target_stats"][sid]["pass_snr_flag0"],
        })
    with (args.out_dir / "four_field_only_snr_details.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(target_details[0]) if target_details else ["Seq", "ZTF_ID"])
        writer.writeheader()
        writer.writerows(target_details)

    table2_ids = set(table2["seq_to_name"])
    report = {
        "status": "EXACT_SNR_RULE_REPRODUCTION" if any(x["exact_set_match"] for x in comparisons.values()) else "SNR_RULE_NOT_EXACTLY_REPRODUCED",
        "scientific_scope": "Independent full-source audit of the published 730,184-member subset against Chen et al. CPVS single-exposure photometry.",
        "threshold_definition": {
            "paper_rule": "at least one 2.5-sigma g-band detection and at least one 3-sigma r-band detection",
            "magnitude_error_relation": "SNR = (2.5 / ln(10)) / magnitude_error",
            "g_snr_min": G_SNR_THRESHOLD,
            "r_snr_min": R_SNR_THRESHOLD,
            "g_magerr_max": G_MAX_MAGERR,
            "r_magerr_max": R_MAX_MAGERR,
            "flag_policy": "Both any-flag and flag==0 variants are reported; primary variant does not silently apply a flag filter.",
        },
        "source_files": {
            "table2_zip": {"name": args.table2_zip.name, "bytes": args.table2_zip.stat().st_size, "sha256": sha256_file(args.table2_zip)},
            "published_zip": {"name": args.published_zip.name, "bytes": args.published_zip.stat().st_size, "sha256": sha256_file(args.published_zip)},
            "g_zip": {"name": args.g_zip.name, "bytes": args.g_zip.stat().st_size, "sha256": sha256_file(args.g_zip)},
            "r_zip": {"name": args.r_zip.name, "bytes": args.r_zip.stat().st_size, "sha256": sha256_file(args.r_zip)},
        },
        "table2": {
            "member": table2["member"],
            "source_lines": table2["source_lines"],
            "metadata_lines": len(table2["metadata"]),
            "record_count": len(table2_ids),
            "unique_seq": len(table2_ids),
            "seq_min": min(table2_ids),
            "seq_max": max(table2_ids),
            "seq_gaps": max(table2_ids) - min(table2_ids) + 1 - len(table2_ids),
            "four_field_count": len(s4),
            "four_field_only": len(s4_only),
            "published_only_under_four_field_rule": len(published_only_s4),
            "four_field_only_sha256_sorted_seq": sha256_ids(s4_only),
            "null_field_counts": table2["null_counts"],
            "record_length_min": min(table2["record_lengths"]),
            "record_length_max": max(table2["record_lengths"]),
        },
        "published_membership": {
            "member": member,
            "csv_rows": published_rows,
            "unique_names": len(published_names),
            "unique_mapped_seq": len(published_ids),
            "unmapped_names": len(unmapped_names),
        },
        "photometry": {
            "g": {
                "member": g["member"], "rows": g["rows"],
                "source_ids_seen": len(g["source_ids_seen"]),
                "source_ids_outside_table2": len(g["source_ids_seen"] - table2_ids),
                "invalid_error_rows": g["invalid_error_rows"],
                "flag_counts": g["flag_counts"],
                "qualifying_any_flag": len(g["qualifying_any"]),
                "qualifying_flag_zero_only": len(g["qualifying_flag0"]),
                "target_55_source_ids_seen": sum(g["target_stats"][sid]["rows"] > 0 for sid in s4_only),
            },
            "r": {
                "member": r["member"], "rows": r["rows"],
                "source_ids_seen": len(r["source_ids_seen"]),
                "source_ids_outside_table2": len(r["source_ids_seen"] - table2_ids),
                "invalid_error_rows": r["invalid_error_rows"],
                "flag_counts": r["flag_counts"],
                "qualifying_any_flag": len(r["qualifying_any"]),
                "qualifying_flag_zero_only": len(r["qualifying_flag0"]),
                "target_55_source_ids_seen": sum(r["target_stats"][sid]["rows"] > 0 for sid in s4_only),
            },
        },
        "membership_comparisons": comparisons,
        "four_field_only_photometry": {
            "count": len(target_details),
            "g_threshold_failures_any_flag": sum(not row["g_pass_2p5sigma_any_flag"] for row in target_details),
            "r_threshold_failures_any_flag": sum(not row["r_pass_3sigma_any_flag"] for row in target_details),
            "fails_either_threshold_any_flag": sum(not (row["g_pass_2p5sigma_any_flag"] and row["r_pass_3sigma_any_flag"]) for row in target_details),
            "g_threshold_failures_flag_zero_only": sum(not row["g_pass_2p5sigma_flag0_only"] for row in target_details),
            "r_threshold_failures_flag_zero_only": sum(not row["r_pass_3sigma_flag0_only"] for row in target_details),
            "fails_either_threshold_flag_zero_only": sum(not (row["g_pass_2p5sigma_flag0_only"] and row["r_pass_3sigma_flag0_only"]) for row in target_details),
        },
    }
    out_path = args.out_dir / "cpvs_snr_membership_report.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_ids(args.out_dir / "four_field_only_seq.txt", s4_only)
    write_ids(args.out_dir / "four_field_published_only_seq.txt", published_only_s4)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"REPORT_PATH={out_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuditError, OSError, zipfile.BadZipFile) as exc:
        print(f"AUDIT_BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
