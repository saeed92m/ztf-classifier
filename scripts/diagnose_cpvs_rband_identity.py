"""Discover r-band archive identity evidence for the CPVS Seq 615170/615172 lead.

This is a bounded, read-only scan. It never rewrites SourceIDs or CPVS membership.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import statistics
import subprocess
import tempfile
import zipfile
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

ZENODO_MD5 = "daa7bc45c67579253eebe6b1c09dfbd9"
EXPECTED_ARCHIVE_SHA256 = "48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74"
EXPECTED_MEMBER_SHA256 = "78df6d0b22099a7e5c6e74b897682c6ab94f90d5f9e887d4b0b3b152514e50fe"
EXPECTED_MEMBER_SIZE = 6175667360
EXPECTED_MEMBER_ROWS = 109971576
EXPECTED_TABLE2_SHA256 = "2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881"
EXPECTED_TABLE2_SIZE = 178986858
EXPECTED_TABLE2_RECORDS = 781602
EXPECTED_README_SHA256 = "e57991d9e086155b9da14eaca7a6abc46a876a2dce58b397a90c915ec309e24a"
EXPECTED_README_SIZE = 12990
FIRST_DISCOVERY_REFERENCE = {
    "workflow_run_id": 42311975704,
    "artifact_id": 13550020720,
    "artifact_zip_sha256": "0d64d338998fc62694d0cc4527ed9cf95544bda5156168ab642ca3731602c80b",
    "report_sha256": "2c31b258dffddc3eff0cd6cdc70bb7bf743e180608004b4b808ec06d6710f3e8",
}
SECOND_DISCOVERY_REFERENCE = {
    "workflow_run_id": 42311984342,
    "artifact_id": 13548792994,
    "artifact_zip_sha256": "1f9342ba5b8b1fcc9fde17d4b24ff79a0eb00b45d386fb0487a5700662275d1e",
    "report_sha256": "2c31b258dffddc3eff0cd6cdc70bb7bf743e180608004b4b808ec06d6710f3e8",
    "interpretation": "Independent second run reproduced the first run's archive hash, member CRC, extracted member SHA-256, size, row count and target/orphan summaries. Member hash is an internal reproducibility reference, not a Zenodo-published checksum.",
}
G_BAND_ORPHAN = {
    "source_id": 615172,
    "row_count": 132,
    "ra_median_deg": 307.3656934,
    "dec_median_deg": -13.4214107,
    "gmag_mean": 14.88604545,
    "hjd_min": 58254.44022,
    "hjd_max": 58657.48608,
}
ZENODO_SOURCE = "https://zenodo.org/records/3886372"
TABLE2_TARGET = {
    "source_id": 615170,
    "ztf_name": "ZTFJ202927.75-132516.6",
    "ra_deg": 307.36563,
    "dec_deg": -13.42128,
    "gmag": 14.886,
    "rmag": 14.736,
    "ng": 132,
    "nr": 113,
}
FIELDS = ("SourceID", "RAdeg", "DEdeg", "HJD", "rmag", "e_rmag", "r_flag")


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    ra1_rad, dec1_rad, ra2_rad, dec2_rad = map(
        math.radians, (ra1, dec1, ra2, dec2)
    )
    sin_dec = math.sin((dec2_rad - dec1_rad) / 2.0)
    sin_ra = math.sin((ra2_rad - ra1_rad) / 2.0)
    haversine = sin_dec**2 + math.cos(dec1_rad) * math.cos(dec2_rad) * sin_ra**2
    angle = 2.0 * math.asin(min(1.0, math.sqrt(max(0.0, haversine))))
    return math.degrees(angle) * 3600.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"row_count": 0}
    return {
        "row_count": len(rows),
        "ra_median_deg": statistics.median(row["ra_deg"] for row in rows),
        "dec_median_deg": statistics.median(row["dec_deg"] for row in rows),
        "hjd_min": min(row["hjd"] for row in rows),
        "hjd_max": max(row["hjd"] for row in rows),
        "rmag_mean": statistics.fmean(row["rmag"] for row in rows),
        "rmag_median": statistics.median(row["rmag"] for row in rows),
        "e_rmag_min": min(row["e_rmag"] for row in rows),
        "e_rmag_max": max(row["e_rmag"] for row in rows),
        "r_flag_counts": dict(sorted(Counter(row["r_flag"] for row in rows).items())),
        "nearest_coordinate_separation_arcsec": min(
            row["separation_arcsec"] for row in rows
        ),
    }



def parse_readme(
    path: Path,
    *,
    expected_sha256: str | None = EXPECTED_README_SHA256,
    expected_size: int | None = EXPECTED_README_SIZE,
) -> dict[str, Any]:
    size = path.stat().st_size
    sha256 = digest_file(path, "sha256")
    content = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^\s*ztf2r\.dat\s+\d+\s+(\d+)", content, re.MULTILINE)
    errors = []
    if not match:
        errors.append("CDS ReadMe does not contain a ztf2r.dat row count")
        readme_rows = None
    else:
        readme_rows = int(match.group(1))
    if expected_sha256 and sha256 != expected_sha256:
        errors.append(f"CDS ReadMe SHA-256 mismatch: {sha256}")
    if expected_size is not None and size != expected_size:
        errors.append(f"CDS ReadMe size mismatch: {size} != {expected_size}")
    return {
        "source_url": "http://vizier.nao.ac.jp/ftp/cats/J/ApJS/249/18/ReadMe",
        "size_bytes": size,
        "sha256": sha256,
        "published_ztf2r_rows": readme_rows,
        "validation_errors": errors,
    }


def parse_table2(
    path: Path,
    *,
    expected_sha256: str | None = EXPECTED_TABLE2_SHA256,
    expected_size: int | None = EXPECTED_TABLE2_SIZE,
    expected_records: int | None = EXPECTED_TABLE2_RECORDS,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    size = path.stat().st_size
    sha256 = digest_file(path, "sha256")
    rows: dict[int, dict[str, Any]] = {}
    errors = []
    record_count = 0
    with path.open("r", encoding="ascii", errors="strict") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            record_count += 1
            if len(line.rstrip("\r\n")) < 140:
                errors.append(f"Table 2 line {line_number} is shorter than 140 columns")
                continue
            try:
                seq = int(line[23:29])
                ra_deg = float(line[30:39])
                dec_deg = float(line[40:49])
                rmag = float(line[96:102])
                nr = int(line[136:140])
            except ValueError:
                errors.append(f"Table 2 line {line_number} has invalid fixed-width fields")
                continue
            if seq in rows:
                errors.append(f"Duplicate Table 2 Seq {seq}")
                continue
            rows[seq] = {
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "rmag": rmag,
                "nr": nr,
            }
    if expected_sha256 and sha256 != expected_sha256:
        errors.append(f"Table 2 SHA-256 mismatch: {sha256}")
    if expected_size is not None and size != expected_size:
        errors.append(f"Table 2 size mismatch: {size} != {expected_size}")
    if expected_records is not None and record_count != expected_records:
        errors.append(
            f"Table 2 record count mismatch: {record_count} != {expected_records}"
        )
    if len(rows) != record_count:
        errors.append(f"Table 2 unique Seq count mismatch: {len(rows)} != {record_count}")
    return rows, {
        "source_url": "http://vizier.nao.ac.jp/ftp/cats/J/ApJS/249/18/table2.dat.gz",
        "size_bytes": size,
        "sha256": sha256,
        "record_count": record_count,
        "unique_seq_count": len(rows),
        "sum_nr": sum(row["nr"] for row in rows.values()),
        "validation_errors": errors,
    }


def reconcile_counts(
    table2: dict[int, dict[str, Any]],
    actual_counts: Counter[int],
    archive_rows: int,
    readme_rows: int | None,
    mismatch_output: Path,
) -> dict[str, Any]:
    expected_total = sum(row["nr"] for row in table2.values())
    actual_for_table2 = sum(actual_counts.get(seq, 0) for seq in table2)
    mismatches = []
    deficit_rows = 0
    surplus_rows = 0
    missing_seq_count = 0
    with mismatch_output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(
            ["status", "Seq", "Table2_Nr", "Archive_rows", "delta", "RAdeg", "DEdeg", "rmag"]
        )
        for seq, reference in sorted(table2.items()):
            expected = reference["nr"]
            actual = actual_counts.get(seq, 0)
            delta = actual - expected
            if delta == 0:
                continue
            mismatches.append(
                {
                    "seq": seq,
                    "expected_nr": expected,
                    "actual_rows": actual,
                    "delta": delta,
                    "ra_deg": reference["ra_deg"],
                    "dec_deg": reference["dec_deg"],
                    "rmag": reference["rmag"],
                }
            )
            if delta < 0:
                deficit_rows += -delta
            else:
                surplus_rows += delta
            if expected > 0 and actual == 0:
                missing_seq_count += 1
            writer.writerow(
                ["COUNT_MISMATCH", seq, expected, actual, delta,
                 reference["ra_deg"], reference["dec_deg"], reference["rmag"]]
            )
        archive_only = {
            seq: count for seq, count in actual_counts.items() if seq not in table2
        }
        for seq, actual in sorted(archive_only.items()):
            writer.writerow(["ARCHIVE_ONLY_SEQ", seq, "", actual, actual, "", "", ""])

    top_mismatches = sorted(
        mismatches, key=lambda row: (abs(row["delta"]), row["seq"]), reverse=True
    )[:50]
    top_archive_only = [
        {"seq": seq, "archive_rows": count}
        for seq, count in sorted(
            archive_only.items(), key=lambda item: (item[1], item[0]), reverse=True
        )[:50]
    ]
    return {
        "table2_unique_seq_count": len(table2),
        "table2_sum_nr": expected_total,
        "archive_total_rows": archive_rows,
        "archive_rows_for_table2_seq": actual_for_table2,
        "archive_only_seq_count": len(archive_only),
        "archive_only_rows": sum(archive_only.values()),
        "archive_minus_table2_sum_nr": archive_rows - expected_total,
        "table2_seq_net_delta": actual_for_table2 - expected_total,
        "matched_seq_count": len(table2) - len(mismatches),
        "mismatched_seq_count": len(mismatches),
        "deficit_seq_count": sum(row["delta"] < 0 for row in mismatches),
        "surplus_seq_count": sum(row["delta"] > 0 for row in mismatches),
        "missing_seq_count": missing_seq_count,
        "sum_deficit_rows": deficit_rows,
        "sum_surplus_rows": surplus_rows,
        "net_delta_for_table2_seq": surplus_rows - deficit_rows,
        "published_readme_r_rows": readme_rows,
        "archive_minus_readme_rows": (
            archive_rows - readme_rows if readme_rows is not None else None
        ),
        "table2_sum_nr_minus_readme_rows": (
            expected_total - readme_rows if readme_rows is not None else None
        ),
        "readme_count_matches_table2_sum_nr": (
            expected_total == readme_rows if readme_rows is not None else None
        ),
        "readme_count_matches_archive_rows": (
            archive_rows == readme_rows if readme_rows is not None else None
        ),
        "mismatch_tsv": str(mismatch_output),
        "top_mismatches_by_absolute_delta": top_mismatches,
        "top_archive_only_seq_ids": top_archive_only,
    }

def scan_archive(
    archive_path: Path,
    *,
    table2_path: Path,
    readme_path: Path,
    mismatch_output: Path,
    target_seq: int = TABLE2_TARGET["source_id"],
    orphan_seq: int = 615172,
    expected_archive_md5: str | None = ZENODO_MD5,
    expected_archive_sha256: str | None = EXPECTED_ARCHIVE_SHA256,
    expected_data_sha256: str | None = EXPECTED_MEMBER_SHA256,
    expected_data_size: int | None = EXPECTED_MEMBER_SIZE,
    expected_total_rows: int | None = EXPECTED_MEMBER_ROWS,
    expected_table2_sha256: str | None = EXPECTED_TABLE2_SHA256,
    expected_table2_size: int | None = EXPECTED_TABLE2_SIZE,
    expected_table2_records: int | None = EXPECTED_TABLE2_RECORDS,
    expected_readme_sha256: str | None = EXPECTED_README_SHA256,
    expected_readme_size: int | None = EXPECTED_README_SIZE,
    spatial_radius_arcsec: float = 2.0,
) -> dict[str, Any]:
    archive_md5 = digest_file(archive_path, "md5")
    archive_sha256 = digest_file(archive_path, "sha256")
    errors: list[str] = []
    warnings: list[str] = []
    if expected_archive_md5 and archive_md5 != expected_archive_md5:
        errors.append(f"Zenodo archive MD5 mismatch: {archive_md5}")
    if expected_archive_sha256 and archive_sha256 != expected_archive_sha256:
        errors.append(f"Zenodo archive SHA-256 mismatch: {archive_sha256}")
    readme_report = parse_readme(
        readme_path,
        expected_sha256=expected_readme_sha256,
        expected_size=expected_readme_size,
    )
    errors.extend(readme_report["validation_errors"])
    table2, table2_report = parse_table2(
        table2_path,
        expected_sha256=expected_table2_sha256,
        expected_size=expected_table2_size,
        expected_records=expected_table2_records,
    )
    errors.extend(table2_report["validation_errors"])

    with zipfile.ZipFile(archive_path) as archive:
        members = [
            name for name in archive.namelist()
            if Path(name).name == "ztf2r" and "__MACOSX" not in name
        ]
        if len(members) != 1:
            raise ValueError(f"Expected exactly one ztf2r member, found {members!r}")
        member = members[0]
        info = archive.getinfo(member)
        expected_crc = info.CRC
        member_metadata = {
            "central_directory_file_size": info.file_size,
            "central_directory_compressed_size": info.compress_size,
            "compression_method": info.compress_type,
        }

    if shutil.which("unzip") is None:
        raise RuntimeError("Info-ZIP 'unzip' is required for this archive")

    selected: dict[int, list[dict[str, Any]]] = {}
    actual_counts: Counter[int] = Counter()
    data_hash = hashlib.sha256()
    data_size = 0
    actual_crc = 0
    data_rows = 0
    malformed_rows = 0
    field_counts: Counter[int] = Counter()
    parse_samples: list[str] = []

    with tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            ["unzip", "-p", str(archive_path), member],
            stdout=subprocess.PIPE,
            stderr=stderr_file,
        )
        if process.stdout is None:
            raise RuntimeError("unzip did not provide stdout")
        for raw_line in process.stdout:
            data_hash.update(raw_line)
            data_size += len(raw_line)
            actual_crc = zlib.crc32(raw_line, actual_crc)
            line = raw_line.decode("utf-8", errors="replace")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = next(csv.reader([line], delimiter=","))
            if fields and fields[0].strip().lower() == "sourceid":
                continue
            data_rows += 1
            field_counts[len(fields)] += 1
            if len(fields) != len(FIELDS):
                malformed_rows += 1
                if len(parse_samples) < 5:
                    parse_samples.append(
                        f"row {data_rows}: expected 7 fields, got {len(fields)}"
                    )
                continue
            try:
                source_id = int(fields[0])
                values = {
                    "ra_deg": float(fields[1]),
                    "dec_deg": float(fields[2]),
                    "hjd": float(fields[3]),
                    "rmag": float(fields[4]),
                    "e_rmag": float(fields[5]),
                    "r_flag": fields[6].strip(),
                }
            except (TypeError, ValueError):
                malformed_rows += 1
                if len(parse_samples) < 5:
                    parse_samples.append(f"row {data_rows}: invalid numeric field")
                continue
            if not all(
                math.isfinite(values[key])
                for key in ("ra_deg", "dec_deg", "hjd", "rmag", "e_rmag")
            ):
                malformed_rows += 1
                continue

            actual_counts[source_id] += 1
            separation = angular_separation_arcsec(
                TABLE2_TARGET["ra_deg"], TABLE2_TARGET["dec_deg"],
                values["ra_deg"], values["dec_deg"],
            )
            if (
                source_id in (target_seq, orphan_seq)
                or separation <= spatial_radius_arcsec
            ):
                values["separation_arcsec"] = separation
                selected.setdefault(source_id, []).append(values)

        process.stdout.close()
        unzip_returncode = process.wait()
        stderr_file.seek(0)
        unzip_stderr = stderr_file.read().decode("utf-8", errors="replace").strip()

    data_sha256 = data_hash.hexdigest()
    actual_crc &= 0xFFFFFFFF
    crc_verified = actual_crc == expected_crc
    archive_size_modulo_matches = info.file_size == data_size % (2**32)
    if unzip_returncode:
        errors.append(
            f"Info-ZIP exit code {unzip_returncode}: {unzip_stderr[-500:]}"
        )
    if expected_total_rows is not None and data_rows != expected_total_rows:
        errors.append(
            f"Data row count mismatch: {data_rows} != {expected_total_rows}"
        )
    if malformed_rows:
        errors.append(f"Malformed data rows: {malformed_rows}")
    if expected_data_size is not None and data_size != expected_data_size:
        errors.append(
            f"Extracted member size mismatch: {data_size} != {expected_data_size}"
        )
    if expected_data_sha256 and data_sha256 != expected_data_sha256:
        errors.append(f"Extracted member SHA-256 mismatch: {data_sha256}")

    target_rows = selected.get(target_seq, [])
    orphan_rows = selected.get(orphan_seq, [])
    candidate_summaries = [
        {
            "source_id": source_id,
            **summarize(rows),
            "is_target_seq": source_id == target_seq,
            "is_orphan_seq": source_id == orphan_seq,
        }
        for source_id, rows in sorted(selected.items())
    ]
    spatial_candidates = [
        candidate for candidate in candidate_summaries
        if candidate["nearest_coordinate_separation_arcsec"] <= spatial_radius_arcsec
    ]
    orphan_summary = summarize(orphan_rows)
    target_summary = summarize(target_rows)
    if orphan_summary.get("row_count"):
        orphan_summary["median_coordinate_separation_arcsec"] = angular_separation_arcsec(
            orphan_summary["ra_median_deg"],
            orphan_summary["dec_median_deg"],
            TABLE2_TARGET["ra_deg"],
            TABLE2_TARGET["dec_deg"],
        )
        orphan_summary["rmag_mean_delta_from_table2"] = (
            orphan_summary["rmag_mean"] - TABLE2_TARGET["rmag"]
        )
    else:
        orphan_summary["median_coordinate_separation_arcsec"] = None
        orphan_summary["rmag_mean_delta_from_table2"] = None

    reconciliation = reconcile_counts(
        table2,
        actual_counts,
        data_rows,
        readme_report["published_ztf2r_rows"],
        mismatch_output,
    )
    if (
        reconciliation["archive_minus_readme_rows"] != 0
        or reconciliation["table2_sum_nr_minus_readme_rows"] != 0
    ):
        warnings.append(
            "CDS ReadMe r-band record count differs from the Table 2 Nr sum and "
            "the checksum-pinned Zenodo archive."
        )
    if reconciliation["mismatched_seq_count"] or reconciliation["archive_only_seq_count"]:
        warnings.append(
            "Per-Seq r-band counts differ from Table 2 Nr; review the complete mismatch TSV."
        )
    if not archive_size_modulo_matches:
        warnings.append(
            "The central-directory 32-bit size field does not equal the streamed size modulo 2^32."
        )

    r_table2_separation = orphan_summary.get("median_coordinate_separation_arcsec")
    g_table2_separation = angular_separation_arcsec(
        G_BAND_ORPHAN["ra_median_deg"],
        G_BAND_ORPHAN["dec_median_deg"],
        TABLE2_TARGET["ra_deg"],
        TABLE2_TARGET["dec_deg"],
    )
    g_r_separation = None
    if orphan_summary.get("row_count"):
        g_r_separation = angular_separation_arcsec(
            G_BAND_ORPHAN["ra_median_deg"],
            G_BAND_ORPHAN["dec_median_deg"],
            orphan_summary["ra_median_deg"],
            orphan_summary["dec_median_deg"],
        )
    hjd_overlap = bool(
        orphan_summary.get("row_count")
        and max(G_BAND_ORPHAN["hjd_min"], orphan_summary["hjd_min"])
        <= min(G_BAND_ORPHAN["hjd_max"], orphan_summary["hjd_max"])
    )
    cross_band_identity = bool(
        target_summary.get("row_count") == 0
        and orphan_summary.get("row_count") == TABLE2_TARGET["nr"]
        and orphan_seq not in table2
        and r_table2_separation is not None
        and r_table2_separation <= 1.0
        and g_table2_separation <= 1.0
        and g_r_separation is not None
        and g_r_separation <= 0.2
        and abs(G_BAND_ORPHAN["gmag_mean"] - TABLE2_TARGET["gmag"]) <= 0.01
        and abs(orphan_summary.get("rmag_mean_delta_from_table2", math.inf)) <= 0.01
        and hjd_overlap
    )

    if not errors and warnings:
        status = "DISCOVERY_COMPLETE_WITH_SOURCE_DISCREPANCIES"
    elif errors:
        status = "FAILED_VALIDATION"
    else:
        status = "DISCOVERY_COMPLETE"

    return {
        "status": status,
        "validation_errors": errors,
        "warnings": warnings,
        "source": {
            "record": ZENODO_SOURCE,
            "doi": "10.5281/zenodo.3886372",
            "archive": "ztf2r.zip",
            "expected_md5": expected_archive_md5,
        },
        "archive": {
            "filename": archive_path.name,
            "size_bytes": archive_path.stat().st_size,
            "md5": archive_md5,
            "sha256": archive_sha256,
            "md5_verified": (
                expected_archive_md5 is None or archive_md5 == expected_archive_md5
            ),
            "expected_sha256": expected_archive_sha256,
            "sha256_verified": (
                expected_archive_sha256 is None or archive_sha256 == expected_archive_sha256
            ),
            "zip_member_crc32_expected": f"{expected_crc:08x}",
            "zip_member_crc32_actual": f"{actual_crc:08x}",
            "zip_member_crc32_matches": crc_verified,
            "member_metadata": {
                **member_metadata,
                "central_directory_size_modulo_2_32_matches_actual": archive_size_modulo_matches,
                "central_directory_size_interpretation": (
                    "32-bit central-directory size equals the full streamed size modulo 2^32"
                    if archive_size_modulo_matches
                    else "central-directory size does not match streamed size modulo 2^32"
                ),
            },
            "unzip_returncode": unzip_returncode,
            "unzip_stderr": unzip_stderr,
        },
        "extracted_member": {
            "name": member,
            "size_bytes": data_size,
            "sha256": data_sha256,
            "expected_size_bytes": expected_data_size,
            "expected_sha256": expected_data_sha256,
            "expected_rows": expected_total_rows,
            "first_discovery_reference": FIRST_DISCOVERY_REFERENCE,
            "second_discovery_reference": SECOND_DISCOVERY_REFERENCE,
            "pinned_integrity_verified": (
                expected_data_sha256 is not None and expected_data_size is not None
                and expected_total_rows is not None
                and data_sha256 == expected_data_sha256
                and data_size == expected_data_size
                and data_rows == expected_total_rows
                and crc_verified
            ),
        },
        "table2_source": table2_report,
        "readme_source": readme_report,
        "scan": {
            "data_rows": data_rows,
            "expected_data_rows": expected_total_rows,
            "malformed_rows": malformed_rows,
            "field_count_distribution": {
                str(key): value for key, value in sorted(field_counts.items())
            },
            "parse_error_samples": parse_samples,
            "target_seq": target_seq,
            "orphan_seq": orphan_seq,
            "spatial_radius_arcsec": spatial_radius_arcsec,
        },
        "table2_target": {
            "catalog_reference": TABLE2_TARGET,
            "parsed_row": table2.get(target_seq),
        },
        "target_seq_summary": target_summary,
        "orphan_seq_summary": orphan_summary,
        "cross_band_identity_diagnostic": {
            "g_orphan_reference": G_BAND_ORPHAN,
            "g_median_coordinate_separation_from_table2_arcsec": g_table2_separation,
            "r_median_coordinate_separation_from_table2_arcsec": r_table2_separation,
            "g_r_median_coordinate_separation_arcsec": g_r_separation,
            "g_mean_magnitude_delta_from_table2": G_BAND_ORPHAN["gmag_mean"] - TABLE2_TARGET["gmag"],
            "r_mean_magnitude_delta_from_table2": orphan_summary.get("rmag_mean_delta_from_table2"),
            "hjd_ranges_overlap": hjd_overlap,
            "interpretation": (
                "STRONG_CROSS_BAND_IDENTITY_LEAD" if cross_band_identity
                else "CROSS_BAND_IDENTITY_NOT_CONFIRMED"
            ),
            "no_automatic_source_id_remap": True,
        },
        "source_count_reconciliation": reconciliation,
        "nearby_source_ids": spatial_candidates,
        "limitations": [
            "The extracted-member hash, byte count and row count are pinned to the first source-backed scan as internal reproducibility references, not Zenodo-published checksums.",
            "The CDS ReadMe r-band row count differs from the checksum-pinned archive stream and the Table 2 Nr sum; this remains a source metadata discrepancy.",
            "The 2-arcsecond search radius is a candidate-retrieval bound, not an identity rule.",
            "A cross-band identity lead is not an automatic SourceID correction.",
            "Per-Seq count mismatches require review before any SourceID mapping decision.",
            "This archive audit does not explain the 11,602 candidate-only CPVS membership residuals.",
            "No CPVS selector, threshold, model, feature set, taxonomy or frozen v0.2.0 artifact is changed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--table2", type=Path, required=True)
    parser.add_argument("--readme", type=Path, required=True)
    parser.add_argument("--mismatches-output", type=Path, required=True)
    parser.add_argument("--target-seq", type=int, default=TABLE2_TARGET["source_id"])
    parser.add_argument("--orphan-seq", type=int, default=615172)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = scan_archive(
        args.archive,
        table2_path=args.table2,
        readme_path=args.readme,
        mismatch_output=args.mismatches_output,
        target_seq=args.target_seq,
        orphan_seq=args.orphan_seq,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if report["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
