"""Re-derive CPVS SNR selection for the fixed samples and all 11,602 residual IDs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import tempfile
import zipfile
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

SNR_FACTOR = 1.0857362047581296
LN10_OVER_2P5 = math.log(10.0) / 2.5
G_THRESHOLD = 2.5
R_THRESHOLD = 3.0

ARCHIVES = {
    "g": {
        "member": "ztf2g",
        "md5": "850fcef561dd7407fbe8e19e99100d7a",
        "sha256": "47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9",
        "member_sha256": "366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16",
        "member_size": 5034066142,
        "member_rows": 89697393,
        "member_crc32": "d2f33aa0",
        "threshold": G_THRESHOLD,
    },
    "r": {
        "member": "ztf2r",
        "md5": "daa7bc45c67579253eebe6b1c09dfbd9",
        "sha256": "48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74",
        "member_sha256": "78df6d0b22099a7e5c6e74b897682c6ab94f90d5f9e887d4b0b3b152514e50fe",
        "member_size": 6175667360,
        "member_rows": 109971576,
        "member_crc32": "225495a0",
        "threshold": R_THRESHOLD,
    },
}

ARTIFACT_REFERENCE = {
    "workflow_run_id": 41367972395,
    "artifact_id": 13108147605,
    "artifact_zip_sha256": "130f3db65827afd83f5050e7eb91eb1cf7f6432e85456fd16586c8000a9aa6be",
    "files": {
        "candidate_only_11602_object_provenance.tsv": {
            "sha256": "35305bb61558660cebd439152691d5e008ee89fb8a88a52726de052c2015ac21",
            "size_bytes": 1753019,
        },
        "fixed_sample_100.tsv": {
            "sha256": "baf94d168b59b682d113015c8ab15a1d2e6ec414cb82e29875a13358f0e5b25b",
            "size_bytes": 12634,
        },
        "fixed_sample_1000.tsv": {
            "sha256": "0a713379eb274d380f7a399d4a719cd3572113d6dc5184442124f8a9e59ed340",
            "size_bytes": 124564,
        },
        "four_field_only_55.tsv": {
            "sha256": "b7f712910467616919f616dfd5f9ddb94a4c6b819f973469eeeb704fae0e1ab6",
            "size_bytes": 7063,
        },
    },
}


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_float(value: Any) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def is_positive(value: Any) -> bool:
    number = parse_float(value)
    return number is not None and number > 0


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if not rows:
        raise ValueError(f"No records in TSV: {path}")
    return rows


def parse_photometry_line(raw_line: bytes) -> list[str]:
    """Parse one seven-column Zenodo row without assuming unquoted commas."""
    text = raw_line.decode("utf-8", errors="strict").rstrip("\r\n")
    if "\t" in text:
        return [value.strip() for value in text.split("\t")]
    if "," in text:
        return [value.strip() for value in next(csv.reader([text], delimiter=","))]
    return text.split()


def verify_artifact_inputs(paths: dict[str, Path]) -> dict[str, Any]:
    """Verify all TSV inputs against the retained workflow artifact manifest."""
    observed = {}
    errors = []
    for name, path in paths.items():
        expected = ARTIFACT_REFERENCE["files"][name]
        size = path.stat().st_size
        sha256 = digest_file(path, "sha256")
        observed[name] = {"size_bytes": size, "sha256": sha256}
        if size != expected["size_bytes"] or sha256 != expected["sha256"]:
            errors.append(
                f"{name} integrity mismatch: size={size}, sha256={sha256}"
            )
    return {"files": observed, "validation_errors": errors}


def metadata_record(row: dict[str, str], source: str) -> dict[str, Any]:
    source_id = int(row["SourceID"])
    gmag = parse_float(row.get("gmag"))
    rmag = parse_float(row.get("rmag"))
    per_g = parse_float(row.get("Per-g"))
    per_r = parse_float(row.get("Per-r"))
    mean_pair = gmag is not None and gmag > 0 and rmag is not None and rmag > 0
    period_pair = per_g is not None and per_g > 0 and per_r is not None and per_r > 0
    return {
        "source_id": source_id,
        "ztf_name": row.get("ZTF") or row.get("ZTFID"),
        "gmag": gmag,
        "rmag": rmag,
        "common_period": parse_float(row.get("Per")),
        "period_g": per_g,
        "period_r": per_r,
        "table2_ng": int(row["Ng"]) if row.get("Ng", "").strip() else None,
        "table2_nr": int(row["Nr"]) if row.get("Nr", "").strip() else None,
        "candidate": parse_bool(row.get("candidate")),
        "table4_member": parse_bool(row.get("Table4_member")),
        "mean_magnitude_pair_positive": mean_pair,
        "band_period_pair_positive": period_pair,
        "four_field_positive": mean_pair and period_pair,
        "stored_four_field_positive": parse_bool(row.get("four_field_positive")),
        "stored_mean_pair_positive": parse_bool(row.get("mean_magnitude_pair_positive")),
        "stored_period_pair_positive": parse_bool(row.get("band_period_pair_positive")),
        "strata": {source} | ({row["stratum"]} if row.get("stratum") else set()),
        "sample_100": source == "sample_100",
        "sample_1000": source == "sample_1000",
        "candidate_only": source == "candidate_only",
        "four_field_only": source == "four_field_only",
        "historical_g_snr": parse_bool(row.get("g_snr")),
        "historical_r_snr": parse_bool(row.get("r_snr")),
        "historical_g_qualifying_detections": (
            int(row["g_qualifying_detections"])
            if row.get("g_qualifying_detections", "").strip()
            else None
        ),
        "historical_r_qualifying_detections": (
            int(row["r_qualifying_detections"])
            if row.get("r_qualifying_detections", "").strip()
            else None
        ),
    }


def load_metadata(
    candidate_only_path: Path,
    sample_100_path: Path,
    sample_1000_path: Path,
    four_field_only_path: Path,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    metadata: dict[int, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    inputs = [
        ("candidate_only", candidate_only_path),
        ("sample_100", sample_100_path),
        ("sample_1000", sample_1000_path),
        ("four_field_only", four_field_only_path),
    ]
    input_counts = {}
    for source, path in inputs:
        rows = read_tsv(path)
        input_counts[source] = len(rows)
        for row in rows:
            record = metadata_record(row, source)
            source_id = record["source_id"]
            if source_id not in metadata:
                metadata[source_id] = record
                continue
            existing = metadata[source_id]
            for key in (
                "gmag",
                "rmag",
                "common_period",
                "period_g",
                "period_r",
                "table2_ng",
                "table2_nr",
                "candidate",
                "table4_member",
            ):
                previous = existing.get(key)
                current = record.get(key)
                if previous is not None and current is not None and previous != current:
                    conflicts.append(
                        {"source_id": source_id, "field": key,
                         "first": previous, "next": current}
                    )
                elif previous is None and current is not None:
                    existing[key] = current
            existing["strata"].update(record["strata"])
            existing["sample_100"] = existing["sample_100"] or record["sample_100"]
            existing["sample_1000"] = existing["sample_1000"] or record["sample_1000"]
            existing["candidate_only"] = (
                existing["candidate_only"] or record["candidate_only"]
            )
            existing["four_field_only"] = (
                existing["four_field_only"] or record["four_field_only"]
            )
            for key in (
                "historical_g_snr",
                "historical_r_snr",
                "historical_g_qualifying_detections",
                "historical_r_qualifying_detections",
            ):
                if record.get(key) is not None:
                    existing[key] = record[key]

    return metadata, {
        "input_record_counts": input_counts,
        "unique_source_ids": len(metadata),
        "metadata_conflicts": conflicts,
    }


def empty_band_metrics() -> dict[str, Any]:
    return {
        "raw_row_count": 0,
        "valid_photometry_rows": 0,
        "invalid_mag_rows": 0,
        "zero_magerr_rows": 0,
        "negative_magerr_rows": 0,
        "nonfinite_magerr_rows": 0,
        "qualifying_detections_approximate": 0,
        "qualifying_detections_exact": 0,
        "qualifying_detections_inverse_error": 0,
        "max_snr_approximate": None,
        "max_snr_exact": None,
        "minimum_qualifying_magerr": None,
        "qualifying_flag_counts": Counter(),
        "all_flag_counts": Counter(),
    }


def scan_band_archive(
    archive_path: Path,
    band: str,
    source_ids: set[int],
) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    config = ARCHIVES[band]
    errors: list[str] = []
    archive_md5 = digest_file(archive_path, "md5")
    archive_sha256 = digest_file(archive_path, "sha256")
    if archive_md5 != config["md5"]:
        errors.append(f"{band}-archive MD5 mismatch: {archive_md5}")
    if archive_sha256 != config["sha256"]:
        errors.append(f"{band}-archive SHA-256 mismatch: {archive_sha256}")

    with zipfile.ZipFile(archive_path) as archive:
        members = [
            name for name in archive.namelist()
            if Path(name).name == config["member"] and "__MACOSX" not in name
        ]
        if len(members) != 1:
            raise ValueError(f"Expected one {config['member']} member, found {members}")
        member_name = members[0]
        info = archive.getinfo(member_name)
        expected_crc = info.CRC
        central_size = info.file_size

    metrics = {source_id: empty_band_metrics() for source_id in source_ids}
    data_hash = hashlib.sha256()
    data_size = 0
    data_rows = 0
    malformed_rows = 0
    field_counts: Counter[int] = Counter()
    actual_crc = 0

    with tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            ["unzip", "-p", str(archive_path), member_name],
            stdout=subprocess.PIPE,
            stderr=stderr_file,
        )
        assert process.stdout is not None
        for raw_line in process.stdout:
            data_hash.update(raw_line)
            data_size += len(raw_line)
            actual_crc = zlib.crc32(raw_line, actual_crc)
            if not raw_line.strip() or raw_line.lstrip().startswith(b"#"):
                continue
            try:
                fields = parse_photometry_line(raw_line)
            except (UnicodeDecodeError, csv.Error):
                malformed_rows += 1
                continue
            field_counts[len(fields)] += 1
            if len(fields) != 7:
                malformed_rows += 1
                continue
            try:
                source_id = int(fields[0].strip())
            except ValueError:
                malformed_rows += 1
                continue
            data_rows += 1
            if source_id not in source_ids:
                continue

            item = metrics[source_id]
            item["raw_row_count"] += 1
            mag = parse_float(fields[4])
            magerr = parse_float(fields[5])
            flag_text = fields[6].strip()
            item["all_flag_counts"][flag_text] += 1

            if mag is None or mag == 0:
                item["invalid_mag_rows"] += 1
            if magerr is None:
                item["nonfinite_magerr_rows"] += 1
                continue
            if magerr == 0:
                item["zero_magerr_rows"] += 1
                continue
            if magerr < 0:
                item["negative_magerr_rows"] += 1
                continue
            if mag is None or mag == 0:
                continue

            item["valid_photometry_rows"] += 1
            snr_approx = SNR_FACTOR / magerr
            try:
                snr_exact = 1.0 / math.expm1(magerr * LN10_OVER_2P5)
            except (OverflowError, ZeroDivisionError):
                snr_exact = 0.0
            snr_inverse = 1.0 / magerr
            item["max_snr_approximate"] = max(
                item["max_snr_approximate"] or 0.0, snr_approx
            )
            item["max_snr_exact"] = max(item["max_snr_exact"] or 0.0, snr_exact)

            if snr_approx >= config["threshold"]:
                item["qualifying_detections_approximate"] += 1
                current = item["minimum_qualifying_magerr"]
                item["minimum_qualifying_magerr"] = (
                    magerr if current is None else min(current, magerr)
                )
                item["qualifying_flag_counts"][flag_text] += 1
            if snr_exact >= config["threshold"]:
                item["qualifying_detections_exact"] += 1
            if snr_inverse >= config["threshold"]:
                item["qualifying_detections_inverse_error"] += 1

        returncode = process.wait()
        stderr_file.seek(0)
        unzip_stderr = stderr_file.read().decode("utf-8", errors="replace")

    member_sha256 = data_hash.hexdigest()
    crc_verified = (actual_crc & 0xFFFFFFFF) == expected_crc
    size_modulo_matches = central_size == data_size % (2**32)
    if returncode:
        errors.append(f"Info-ZIP exit code {returncode}: {unzip_stderr[-500:]}")
    if member_sha256 != config["member_sha256"]:
        errors.append(f"{band}-member SHA-256 mismatch: {member_sha256}")
    if data_size != config["member_size"]:
        errors.append(f"{band}-member size mismatch: {data_size}")
    if data_rows != config["member_rows"]:
        errors.append(f"{band}-member row count mismatch: {data_rows}")
    if f"{actual_crc & 0xFFFFFFFF:08x}" != config["member_crc32"]:
        errors.append(
            f"{band}-member CRC mismatch: {actual_crc & 0xFFFFFFFF:08x}"
        )
    if malformed_rows:
        errors.append(f"{band}-member contains {malformed_rows} malformed rows")

    for item in metrics.values():
        item["qualifying_flag_counts"] = dict(item["qualifying_flag_counts"])
        item["all_flag_counts"] = dict(item["all_flag_counts"])
        if item["raw_row_count"] == 0:
            item["passes_approximate_snr"] = None
            item["passes_exact_snr"] = None
            item["passes_inverse_error_snr"] = None
        else:
            item["passes_approximate_snr"] = (
                item["qualifying_detections_approximate"] > 0
            )
            item["passes_exact_snr"] = item["qualifying_detections_exact"] > 0
            item["passes_inverse_error_snr"] = (
                item["qualifying_detections_inverse_error"] > 0
            )

    return {
        "band": band,
        "archive_path": archive_path.name,
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_md5": archive_md5,
        "archive_sha256": archive_sha256,
        "member_name": member_name,
        "central_directory_crc32": f"{expected_crc:08x}",
        "actual_stream_crc32": f"{actual_crc & 0xFFFFFFFF:08x}",
        "crc_verified": crc_verified,
        "central_directory_size_32bit": central_size,
        "stream_size_modulo_2_32_matches": size_modulo_matches,
        "member_sha256": member_sha256,
        "member_size_bytes": data_size,
        "member_rows": data_rows,
        "field_count_distribution": dict(field_counts),
        "malformed_rows": malformed_rows,
        "unzip_returncode": returncode,
        "validation_errors": errors,
        "pinned_integrity_verified": not errors,
        "threshold": config["threshold"],
    }, metrics


def confusion_summary(rows: list[dict[str, Any]], prediction_key: str) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    unknown = 0
    for row in rows:
        actual = row.get("table4_member")
        predicted = row.get(prediction_key)
        if actual is None:
            unknown += 1
        elif predicted is None:
            unknown += 1
        elif predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1
    return {
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "unknown": unknown,
    }


def build_object_rows(
    metadata: dict[int, dict[str, Any]],
    g_metrics: dict[int, dict[str, Any]],
    r_metrics: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []
    for source_id, meta in sorted(metadata.items()):
        g = g_metrics[source_id]
        r = r_metrics[source_id]
        g_pass = g["passes_approximate_snr"]
        r_pass = r["passes_approximate_snr"]
        raw_candidate = (
            None if g_pass is None or r_pass is None else bool(g_pass and r_pass)
        )
        row = {
            **meta,
            "strata": sorted(meta["strata"]),
            "g": g,
            "r": r,
            "rederived_candidate": raw_candidate,
            "rederived_candidate_and_four_field": (
                None
                if raw_candidate is None
                else raw_candidate and meta["four_field_positive"]
            ),
            "matches_historical_candidate": (
                None
                if raw_candidate is None or meta["candidate"] is None
                else raw_candidate == meta["candidate"]
            ),
            "matches_table4_with_snr_only": (
                None
                if raw_candidate is None or meta["table4_member"] is None
                else raw_candidate == meta["table4_member"]
            ),
            "matches_table4_with_four_field_gate": (
                (raw_candidate and meta["four_field_positive"])
                == meta["table4_member"]
                if meta["table4_member"] is not None else None
            ),
            "g_row_count_matches_table2": (
                g["raw_row_count"] == meta["table2_ng"]
                if meta["table2_ng"] is not None else None
            ),
            "r_row_count_matches_table2": (
                r["raw_row_count"] == meta["table2_nr"]
                if meta["table2_nr"] is not None else None
            ),
        }
        results.append(row)
    return results


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(rows),
        "g_snr_pass": sum(row["g"]["passes_approximate_snr"] is True for row in rows),
        "g_snr_fail": sum(row["g"]["passes_approximate_snr"] is False for row in rows),
        "g_snr_unknown": sum(row["g"]["passes_approximate_snr"] is None for row in rows),
        "r_snr_pass": sum(row["r"]["passes_approximate_snr"] is True for row in rows),
        "r_snr_fail": sum(row["r"]["passes_approximate_snr"] is False for row in rows),
        "r_snr_unknown": sum(row["r"]["passes_approximate_snr"] is None for row in rows),
        "both_snr_pass": sum(row["rederived_candidate"] is True for row in rows),
        "both_snr_fail": sum(row["rederived_candidate"] is False for row in rows),
        "both_snr_unknown": sum(row["rederived_candidate"] is None for row in rows),
        "both_snr_and_four_field": sum(
            row["rederived_candidate_and_four_field"] is True for row in rows
        ),
        "both_snr_and_four_field_unknown": sum(
            row["rederived_candidate_and_four_field"] is None for row in rows
        ),
        "table4_members": sum(row["table4_member"] is True for row in rows),
        "g_row_count_matches_table2": sum(
            row["g_row_count_matches_table2"] is True for row in rows
        ),
        "r_row_count_matches_table2": sum(
            row["r_row_count_matches_table2"] is True for row in rows
        ),
        "matches_table4_with_snr_only": sum(
            row["matches_table4_with_snr_only"] is True for row in rows
        ),
        "matches_table4_with_four_field_gate": sum(
            row["matches_table4_with_four_field_gate"] is True for row in rows
        ),
        "candidate_rederived_vs_table4": confusion_summary(
            rows, "rederived_candidate"
        ),
        "candidate_rederived_and_four_field_vs_table4": confusion_summary(
            rows, "rederived_candidate_and_four_field"
        ),
    }


def write_objects_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "SourceID", "ZTF", "strata", "candidate", "Table4_member",
        "four_field_positive", "gmag", "rmag", "Per", "Per-g", "Per-r",
        "Ng", "Nr", "g_rows", "g_valid", "g_qualifying_approx",
        "g_qualifying_exact", "g_max_snr_approx", "g_pass_approx",
        "g_row_count_match", "r_rows", "r_valid", "r_qualifying_approx",
        "r_qualifying_exact", "r_max_snr_approx", "r_pass_approx",
        "r_row_count_match", "rederived_candidate", "matches_historical_candidate",
        "matches_table4_with_four_field_gate",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "SourceID": row["source_id"],
                    "ZTF": row["ztf_name"],
                    "strata": ",".join(row["strata"]),
                    "candidate": row["candidate"],
                    "Table4_member": row["table4_member"],
                    "four_field_positive": row["four_field_positive"],
                    "gmag": row["gmag"],
                    "rmag": row["rmag"],
                    "Per": row["common_period"],
                    "Per-g": row["period_g"],
                    "Per-r": row["period_r"],
                    "Ng": row["table2_ng"],
                    "Nr": row["table2_nr"],
                    "g_rows": row["g"]["raw_row_count"],
                    "g_valid": row["g"]["valid_photometry_rows"],
                    "g_qualifying_approx": row["g"]["qualifying_detections_approximate"],
                    "g_qualifying_exact": row["g"]["qualifying_detections_exact"],
                    "g_max_snr_approx": row["g"]["max_snr_approximate"],
                    "g_pass_approx": row["g"]["passes_approximate_snr"],
                    "g_row_count_match": row["g_row_count_matches_table2"],
                    "r_rows": row["r"]["raw_row_count"],
                    "r_valid": row["r"]["valid_photometry_rows"],
                    "r_qualifying_approx": row["r"]["qualifying_detections_approximate"],
                    "r_qualifying_exact": row["r"]["qualifying_detections_exact"],
                    "r_max_snr_approx": row["r"]["max_snr_approximate"],
                    "r_pass_approx": row["r"]["passes_approximate_snr"],
                    "r_row_count_match": row["r_row_count_matches_table2"],
                    "rederived_candidate": row["rederived_candidate"],
                    "matches_historical_candidate": row["matches_historical_candidate"],
                    "matches_table4_with_four_field_gate": row[
                        "matches_table4_with_four_field_gate"
                    ],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--g-archive", type=Path, required=True)
    parser.add_argument("--r-archive", type=Path, required=True)
    parser.add_argument("--candidate-only", type=Path, required=True)
    parser.add_argument("--sample-100", type=Path, required=True)
    parser.add_argument("--sample-1000", type=Path, required=True)
    parser.add_argument("--four-field-only", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--objects-output", type=Path, required=True)
    args = parser.parse_args()

    input_integrity = verify_artifact_inputs(
        {
            "candidate_only_11602_object_provenance.tsv": args.candidate_only,
            "fixed_sample_100.tsv": args.sample_100,
            "fixed_sample_1000.tsv": args.sample_1000,
            "four_field_only_55.tsv": args.four_field_only,
        }
    )
    if input_integrity["validation_errors"]:
        raise ValueError("; ".join(input_integrity["validation_errors"]))

    metadata, input_report = load_metadata(
        args.candidate_only,
        args.sample_100,
        args.sample_1000,
        args.four_field_only,
    )
    input_report["artifact_integrity"] = input_integrity
    if input_report["metadata_conflicts"]:
        raise ValueError("Conflicting source metadata across retained audit inputs")
    source_ids = set(metadata)
    g_report, g_metrics = scan_band_archive(args.g_archive, "g", source_ids)
    r_report, r_metrics = scan_band_archive(args.r_archive, "r", source_ids)
    object_rows = build_object_rows(metadata, g_metrics, r_metrics)

    candidate_only_rows = [
        row for row in object_rows if row["candidate_only"]
    ]
    sample_100_rows = [row for row in object_rows if row["sample_100"]]
    sample_1000_rows = [row for row in object_rows if row["sample_1000"]]
    control_rows = [
        row for row in object_rows if row["four_field_only"]
    ]
    period_only_rows = [
        row for row in candidate_only_rows
        if row["mean_magnitude_pair_positive"]
        and not row["band_period_pair_positive"]
    ]
    magnitude_only_rows = [
        row for row in candidate_only_rows
        if row["band_period_pair_positive"]
        and not row["mean_magnitude_pair_positive"]
    ]

    report = {
        "schema_version": "1.0",
        "status": (
            "SOURCE_INTEGRITY_FAILED"
            if g_report["validation_errors"] or r_report["validation_errors"]
            else "RAW_SNR_SAMPLE_REDERIVATION_COMPLETE"
        ),
        "scientific_validation_status": "NOT_VALIDATED",
        "objective": (
            "Independently rederive raw g/r SNR for all 11,602 candidate-only IDs "
            "and fixed 100-/1,000-object samples from the checksum-pinned Zenodo archives."
        ),
        "artifact_reference": ARTIFACT_REFERENCE,
        "input_manifest": input_report,
        "input_artifact_integrity": input_integrity,
        "thresholds": {
            "g_approximate_snr": G_THRESHOLD,
            "r_approximate_snr": R_THRESHOLD,
            "snr_magnitude_error_factor": SNR_FACTOR,
            "selection_rule": (
                "At least one valid non-zero-magnitude row with approximate SNR "
                ">=2.5 in g and >=3.0 in r. Flags are reported, not filtered."
            ),
        },
        "archive_integrity": {"g": g_report, "r": r_report},
        "sample_summaries": {
            "candidate_only_11602": summarize_group(candidate_only_rows),
            "fixed_sample_100": summarize_group(sample_100_rows),
            "fixed_sample_1000": summarize_group(sample_1000_rows),
            "four_field_only_55_controls": summarize_group(control_rows),
            "candidate_only_17_mean_magnitudes_complete_periods_incomplete": (
                summarize_group(period_only_rows)
            ),
            "candidate_only_5_periods_complete_magnitudes_incomplete": (
                summarize_group(magnitude_only_rows)
            ),
        },
        "candidate_only_snr_unknowns": [
            {
                "source_id": row["source_id"],
                "ztf_name": row["ztf_name"],
                "g_raw_rows": row["g"]["raw_row_count"],
                "r_raw_rows": row["r"]["raw_row_count"],
                "g_snr_status": row["g"]["passes_approximate_snr"],
                "r_snr_status": row["r"]["passes_approximate_snr"],
            }
            for row in candidate_only_rows
            if row["rederived_candidate"] is None
        ],
        "candidate_only_archive_rowcount_mismatches": [
            {
                "source_id": row["source_id"],
                "ztf_name": row["ztf_name"],
                "g_raw_rows": row["g"]["raw_row_count"],
                "r_raw_rows": row["r"]["raw_row_count"],
                "table2_ng": row["table2_ng"],
                "table2_nr": row["table2_nr"],
                "g_row_count_matches_table2": row["g_row_count_matches_table2"],
                "r_row_count_matches_table2": row["r_row_count_matches_table2"],
            }
            for row in candidate_only_rows
            if row["g_row_count_matches_table2"] is False
            or row["r_row_count_matches_table2"] is False
        ],
        "candidate_only_snr_disagreements": [
            {
                "source_id": row["source_id"],
                "ztf_name": row["ztf_name"],
                "g_pass": row["g"]["passes_approximate_snr"],
                "r_pass": row["r"]["passes_approximate_snr"],
                "historical_g_snr": row["historical_g_snr"],
                "historical_r_snr": row["historical_r_snr"],
                "g_qualifying_detections": row["g"]["qualifying_detections_approximate"],
                "r_qualifying_detections": row["r"]["qualifying_detections_approximate"],
                "g_row_count_matches_table2": row["g_row_count_matches_table2"],
                "r_row_count_matches_table2": row["r_row_count_matches_table2"],
            }
            for row in candidate_only_rows
            if row["rederived_candidate"] is False
            and row["candidate"] is True
        ],
        "metadata_field_gate_disagreements": [
            {
                "source_id": row["source_id"],
                "ztf_name": row["ztf_name"],
                "mean_magnitude_pair_positive": row["mean_magnitude_pair_positive"],
                "band_period_pair_positive": row["band_period_pair_positive"],
                "common_period": row["common_period"],
                "gmag": row["gmag"],
                "rmag": row["rmag"],
                "period_g": row["period_g"],
                "period_r": row["period_r"],
                "g_snr_pass": row["g"]["passes_approximate_snr"],
                "r_snr_pass": row["r"]["passes_approximate_snr"],
            }
            for row in period_only_rows + magnitude_only_rows
        ],
        "object_result_count": len(object_rows),
        "four_field_only_control_count": len(control_rows),
        "limitations": [
            "Zero raw rows in a band are UNKNOWN, not an SNR failure; confusion matrices exclude unknown predictions.",
            "This is a raw-photometry diagnostic for the fixed samples and the 11,602 residual IDs, not a full 781,602-object candidate reconstruction.",
            "The SNR selector is reproduced as an explicit diagnostic; it is not silently substituted for the publisher's full method.",
            "Nonzero flags are reported. No flag filter is applied.",
            "No SourceID remapping, selector change, threshold change or frozen v0.2.0 baseline change is made.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.objects_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_objects_tsv(args.objects_output, object_rows)
    print(json.dumps({
        "status": report["status"],
        "object_result_count": report["object_result_count"],
        "candidate_only": report["sample_summaries"]["candidate_only_11602"],
        "fixed_sample_1000": report["sample_summaries"]["fixed_sample_1000"],
        "g_integrity_errors": g_report["validation_errors"],
        "r_integrity_errors": r_report["validation_errors"],
        "output": str(args.output),
        "objects_output": str(args.objects_output),
    }, indent=2))
    return 1 if report["status"] == "SOURCE_INTEGRITY_FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
