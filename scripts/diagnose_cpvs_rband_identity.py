#!/usr/bin/env python3
"""Discover r-band archive identity evidence for the CPVS Seq 615170/615172 lead.

This is a bounded, read-only scan. It never rewrites SourceIDs or CPVS membership.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
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
ZENODO_SOURCE = "https://zenodo.org/records/3886372"
TABLE2_TARGET = {
    "source_id": 615170,
    "ztf_name": "ZTFJ202927.75-132516.6",
    "ra_deg": 307.36563,
    "dec_deg": -13.42128,
    "gmag": 14.886,
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


def scan_archive(
    archive_path: Path,
    *,
    target_seq: int = TABLE2_TARGET["source_id"],
    orphan_seq: int = 615172,
    expected_archive_md5: str | None = ZENODO_MD5,
    expected_data_sha256: str | None = None,
    expected_data_size: int | None = None,
    expected_total_rows: int | None = None,
    spatial_radius_arcsec: float = 2.0,
) -> dict[str, Any]:
    archive_md5 = digest_file(archive_path, "md5")
    archive_sha256 = digest_file(archive_path, "sha256")
    errors: list[str] = []
    if expected_archive_md5 and archive_md5 != expected_archive_md5:
        errors.append(f"Zenodo archive MD5 mismatch: {archive_md5}")

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
    identity_lead = bool(
        orphan_summary.get("row_count") == TABLE2_TARGET["nr"]
        and orphan_summary.get("nearest_coordinate_separation_arcsec", math.inf)
        <= 1.0
    )

    return {
        "status": "FAILED_VALIDATION" if errors else "DISCOVERY_COMPLETE",
        "validation_errors": errors,
        "source": {
            "record": ZENODO_SOURCE,
            "doi": "10.5281/zenodo.3886372",
            "archive": "ztf2r.zip",
            "expected_md5": expected_archive_md5,
        },
        "archive": {
            "filename": archive_path.name,
            "md5": archive_md5,
            "sha256": archive_sha256,
            "md5_verified": (
                expected_archive_md5 is None or archive_md5 == expected_archive_md5
            ),
            "zip_member_crc32_expected": f"{expected_crc:08x}",
            "zip_member_crc32_actual": f"{actual_crc:08x}",
            "zip_member_crc32_matches": crc_verified,
            "member_metadata": member_metadata,
            "unzip_returncode": unzip_returncode,
            "unzip_stderr": unzip_stderr,
        },
        "extracted_member": {
            "name": member,
            "size_bytes": data_size,
            "sha256": data_sha256,
            "expected_size_bytes": expected_data_size,
            "expected_sha256": expected_data_sha256,
            "independent_member_hash_pinned": (
                expected_data_sha256 is not None and expected_data_size is not None
            ),
            "pinned_integrity_verified": (
                expected_data_sha256 is not None
                and expected_data_size is not None
                and data_sha256 == expected_data_sha256
                and data_size == expected_data_size
            ),
        },
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
        "table2_target": TABLE2_TARGET,
        "target_seq_summary": target_summary,
        "orphan_seq_summary": orphan_summary,
        "comparison": {
            "target_seq_rows_match_table2_nr": (
                target_summary.get("row_count") == TABLE2_TARGET["nr"]
            ),
            "orphan_seq_rows_match_table2_nr": (
                orphan_summary.get("row_count") == TABLE2_TARGET["nr"]
            ),
            "orphan_seq_nearest_separation_arcsec": orphan_summary.get(
                "nearest_coordinate_separation_arcsec"
            ),
            "orphan_seq_matches_table2_nr_and_within_one_arcsec": identity_lead,
            "interpretation": (
                "STRONG_R_BAND_IDENTITY_LEAD"
                if identity_lead else "R_BAND_IDENTITY_NOT_CONFIRMED"
            ),
            "nearby_source_ids": spatial_candidates,
        },
        "warnings": (
            ["ZIP CRC does not match. The archive checksum and extracted-member hash/size are reported separately."]
            if not crc_verified else []
        ),
        "limitations": [
            "This is a discovery scan. The extracted-member SHA-256, byte count and row count are not pinned until this first result is reviewed.",
            "The 2-arcsecond search radius is a candidate-retrieval bound, not an identity rule.",
            "A coordinate match is not an automatic SourceID correction.",
            "This targeted scan does not reconcile every r-band SourceID against Table 2 Nr.",
            "This scan does not explain the 11,602 candidate-only CPVS membership residuals.",
            "No CPVS selector, threshold, model, feature set, taxonomy or frozen v0.2.0 artifact is changed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--target-seq", type=int, default=TABLE2_TARGET["source_id"])
    parser.add_argument("--orphan-seq", type=int, default=615172)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = scan_archive(
        args.archive, target_seq=args.target_seq, orphan_seq=args.orphan_seq
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if report["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
