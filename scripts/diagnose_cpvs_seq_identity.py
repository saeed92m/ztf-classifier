#!/usr/bin/env python3
"""Verify a suspected CPVS Table 2 / Zenodo g-archive Seq mismatch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import zipfile
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_ARCHIVE_MD5 = "850fcef561dd7407fbe8e19e99100d7a"
EXPECTED_ARCHIVE_SHA256 = (
    "47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9"
)
EXPECTED_DATA_SHA256 = (
    "366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16"
)
EXPECTED_DATA_SIZE = 5_034_066_142
EXPECTED_TOTAL_G_ROWS = 89_697_393
TABLE2_TARGET = {
    "source_id": 615170,
    "ztf_name": "ZTFJ202927.75-132516.6",
    "ra_deg": 307.36563,
    "dec_deg": -13.42128,
    "gmag": 14.886,
    "ng": 132,
    "nr": 113,
}
SCHEMA = ["SourceID", "RAdeg", "DEdeg", "HJD", "gmag", "e_gmag", "g_flag"]


def file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def angular_separation_arcsec(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    ra1, dec1, ra2, dec2 = map(
        math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg)
    )
    cos_angle = (
        math.sin(dec1) * math.sin(dec2)
        + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    )
    return math.degrees(math.acos(min(1.0, max(-1.0, cos_angle)))) * 3600.0


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"row_count": 0}
    ra = [row["ra_deg"] for row in rows]
    dec = [row["dec_deg"] for row in rows]
    hjd = [row["hjd"] for row in rows]
    mag = [row["gmag"] for row in rows]
    error = [row["e_gmag"] for row in rows]
    flags = Counter(row["g_flag"] for row in rows)
    return {
        "row_count": len(rows),
        "ra_median_deg": statistics.median(ra),
        "dec_median_deg": statistics.median(dec),
        "ra_min_deg": min(ra),
        "ra_max_deg": max(ra),
        "dec_min_deg": min(dec),
        "dec_max_deg": max(dec),
        "hjd_min": min(hjd),
        "hjd_max": max(hjd),
        "gmag_mean": statistics.fmean(mag),
        "gmag_median": statistics.median(mag),
        "gmag_min": min(mag),
        "gmag_max": max(mag),
        "e_gmag_min": min(error),
        "e_gmag_max": max(error),
        "g_flag_counts": dict(sorted(flags.items())),
    }


def scan_archive(
    archive_path: Path,
    target_seq: int,
    orphan_seq: int,
    *,
    expected_archive_md5: str | None = EXPECTED_ARCHIVE_MD5,
    expected_archive_sha256: str | None = EXPECTED_ARCHIVE_SHA256,
    expected_data_sha256: str | None = EXPECTED_DATA_SHA256,
    expected_data_size: int | None = EXPECTED_DATA_SIZE,
    expected_total_rows: int | None = EXPECTED_TOTAL_G_ROWS,
    expected_ra_deg: float = TABLE2_TARGET["ra_deg"],
    expected_dec_deg: float = TABLE2_TARGET["dec_deg"],
    expected_gmag: float = TABLE2_TARGET["gmag"],
    expected_ng: int = TABLE2_TARGET["ng"],
) -> dict[str, Any]:
    archive_md5 = file_digest(archive_path, "md5")
    archive_sha256 = file_digest(archive_path, "sha256")
    if expected_archive_md5 is not None and archive_md5 != expected_archive_md5:
        raise ValueError(f"Zenodo g-archive MD5 mismatch: {archive_md5}")
    if (
        expected_archive_sha256 is not None
        and archive_sha256 != expected_archive_sha256
    ):
        raise ValueError(f"Zenodo g-archive SHA-256 mismatch: {archive_sha256}")

    matches: dict[int, list[dict[str, Any]]] = {
        target_seq: [],
        orphan_seq: [],
    }
    data_hash = hashlib.sha256()
    data_size = 0
    data_crc32 = 0
    malformed_rows = 0
    data_rows = 0
    field_count_distribution: Counter[int] = Counter()
    parse_error_samples: list[str] = []
    zip_crc32_expected = 0

    with zipfile.ZipFile(archive_path) as archive:
        members = [
            name
            for name in archive.namelist()
            if Path(name).name == "ztf2g" and "__MACOSX" not in name
        ]
        if len(members) != 1:
            raise ValueError(f"Expected one ztf2g member, found {members!r}")
        member = members[0]
        member_info = archive.getinfo(member)
        zip_crc32_expected = member_info.CRC
        with archive.open(member) as binary_stream:
            # Verify the member with independent SHA-256/size checks below.
            # Disable zipfile's CRC exception so a bad ZIP CRC field does not
            # prevent us from checking the full uncompressed byte stream.
            binary_stream._expected_crc = None
            header: list[str] | None = None
            for raw_line in binary_stream:
                data_hash.update(raw_line)
                data_size += len(raw_line)
                data_crc32 = zlib.crc32(raw_line, data_crc32)
                line = raw_line.decode("utf-8", errors="replace")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                data_rows += 1
                fields = next(csv.reader([line], delimiter=","))
                field_count_distribution[len(fields)] += 1
                if fields and fields[0].strip().lower() == "sourceid":
                    header = [value.strip() for value in fields]
                    data_rows -= 1
                    continue
                schema = header or SCHEMA
                if len(fields) != len(schema):
                    malformed_rows += 1
                    if len(parse_error_samples) < 5:
                        parse_error_samples.append(f"line {data_rows}: expected {len(schema)} fields, got {len(fields)}: {line[:240]!r}")
                    continue
                row = dict(zip(schema, fields, strict=True))
                try:
                    source_id = int(row["SourceID"])
                except (KeyError, TypeError, ValueError):
                    malformed_rows += 1
                    if len(parse_error_samples) < 5:
                        parse_error_samples.append(f"line {data_rows}: invalid SourceID: {line[:240]!r}")
                    continue
                if source_id not in matches:
                    continue
                try:
                    values = {
                        "ra_deg": float(row["RAdeg"]),
                        "dec_deg": float(row["DEdeg"]),
                        "hjd": float(row["HJD"]),
                        "gmag": float(row["gmag"]),
                        "e_gmag": float(row["e_gmag"]),
                        "g_flag": str(row["g_flag"]).strip(),
                    }
                except (KeyError, TypeError, ValueError):
                    malformed_rows += 1
                    continue
                if not all(
                    math.isfinite(values[key])
                    for key in ("ra_deg", "dec_deg", "hjd", "gmag", "e_gmag")
                ):
                    malformed_rows += 1
                    continue
                matches[source_id].append(values)

    observed_data_sha256 = data_hash.hexdigest()
    observed_crc32 = data_crc32 & 0xFFFFFFFF
    zip_crc_verified = observed_crc32 == zip_crc32_expected
    validation_errors: list[str] = []
    if expected_total_rows is not None and data_rows != expected_total_rows:
        validation_errors.append(f"Non-empty record count mismatch: {data_rows} != {expected_total_rows}")
    if malformed_rows:
        validation_errors.append(f"Found {malformed_rows} malformed ztf2g rows")
    if expected_data_size is not None and data_size != expected_data_size:
        validation_errors.append(f"Extracted ztf2g size mismatch: {data_size} != {expected_data_size}")
    if expected_data_sha256 is not None and observed_data_sha256 != expected_data_sha256:
        validation_errors.append("Extracted ztf2g SHA-256 mismatch: " + observed_data_sha256)

    target = _summary(matches[target_seq])
    orphan = _summary(matches[orphan_seq])
    separation = None
    magnitude_delta = None
    if orphan.get("row_count"):
        separation = angular_separation_arcsec(
            expected_ra_deg,
            expected_dec_deg,
            orphan["ra_median_deg"],
            orphan["dec_median_deg"],
        )
        magnitude_delta = orphan["gmag_mean"] - expected_gmag

    strong_match = bool(
        orphan.get("row_count") == expected_ng
        and separation is not None
        and separation <= 1.0
    )
    return {
        "status": (
            "FAILED_VALIDATION" if validation_errors else (
                "COMPLETED" if zip_crc_verified else "COMPLETED_WITH_ZIP_CRC_MISMATCH"
            )
        ),
        "validation_errors": validation_errors,
        "source": "Zenodo 10.5281/zenodo.3886372, ztf2g.zip",
        "archive": {
            "path_name": archive_path.name,
            "md5": archive_md5,
            "sha256": archive_sha256,
            "expected_md5": expected_archive_md5,
            "expected_sha256": expected_archive_sha256,
            "checksum_verified": (
                (expected_archive_md5 is None or archive_md5 == expected_archive_md5)
                and (
                    expected_archive_sha256 is None
                    or archive_sha256 == expected_archive_sha256
                )
            ),
            "zip_member_crc32_expected": f"{zip_crc32_expected:08x}",
            "zip_member_crc32_actual": f"{observed_crc32:08x}",
            "zip_crc_verified": zip_crc_verified,
        },
        "extracted_member": {
            "name": member,
            "size_bytes": data_size,
            "sha256": observed_data_sha256,
            "expected_size_bytes": expected_data_size,
            "expected_sha256": expected_data_sha256,
            "integrity_verified": (
                (expected_data_size is None or data_size == expected_data_size)
                and (
                    expected_data_sha256 is None
                    or observed_data_sha256 == expected_data_sha256
                )
            ),
        },
        "scan": {
            "data_rows": data_rows,
            "expected_data_rows": expected_total_rows,
            "malformed_rows": malformed_rows,
            "field_count_distribution": {str(k): v for k, v in sorted(field_count_distribution.items())},
            "parse_error_samples": parse_error_samples,
            "target_seq": target_seq,
            "orphan_seq": orphan_seq,
        },
        "table2_target": TABLE2_TARGET,
        "target_seq_summary": target,
        "orphan_seq_summary": orphan,
        "comparison": {
            "orphan_row_count_equals_table2_ng": (
                orphan.get("row_count") == expected_ng
            ),
            "orphan_median_coordinate_separation_arcsec": separation,
            "orphan_mean_gmag_delta_from_table2": magnitude_delta,
            "strong_coordinate_match_to_table2_target": strong_match,
            "interpretation": (
                "STRONG_IDENTITY_LEAD"
                if strong_match
                else "IDENTITY_NOT_CONFIRMED"
            ),
        },
        "warnings": (
            ["ZIP member CRC-32 does not match, but archive and extracted-member SHA-256/size checks passed."]
            if not zip_crc_verified
            else []
        ),
        "limitations": [
            "This diagnostic checks only the g-band archive.",
            "A coordinate match supports an archive-to-Table2 identity mapping but does not prove why the published 730184 membership differs from the 741786 reconstruction.",
            "The r-band archive and all other mismatched Seq values require separate checks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--target-seq", type=int, default=615170)
    parser.add_argument("--orphan-seq", type=int, default=615172)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = scan_archive(args.archive, args.target_seq, args.orphan_seq)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if report["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
