#!/usr/bin/env python3
"""Source-backed CPVS Seq identity probe using Info-ZIP extraction."""

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

EXPECTED_ARCHIVE_MD5 = "850fcef561dd7407fbe8e19e99100d7a"
EXPECTED_ARCHIVE_SHA256 = "47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9"
EXPECTED_DATA_SHA256 = "366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16"
EXPECTED_DATA_SIZE = 5_034_066_142
EXPECTED_TOTAL_ROWS = 89_697_393
TABLE2 = {
    "source_id": 615170,
    "ztf_name": "ZTFJ202927.75-132516.6",
    "ra_deg": 307.36563,
    "dec_deg": -13.42128,
    "gmag": 14.886,
    "ng": 132,
    "nr": 113,
}
FIELDS = ("SourceID", "RAdeg", "DEdeg", "HJD", "gmag", "e_gmag", "g_flag")


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    value = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    return math.degrees(math.acos(min(1.0, max(-1.0, value)))) * 3600.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"row_count": 0}
    return {
        "row_count": len(rows),
        "ra_median_deg": statistics.median(x["ra_deg"] for x in rows),
        "dec_median_deg": statistics.median(x["dec_deg"] for x in rows),
        "hjd_min": min(x["hjd"] for x in rows),
        "hjd_max": max(x["hjd"] for x in rows),
        "gmag_mean": statistics.fmean(x["gmag"] for x in rows),
        "gmag_median": statistics.median(x["gmag"] for x in rows),
        "e_gmag_min": min(x["e_gmag"] for x in rows),
        "e_gmag_max": max(x["e_gmag"] for x in rows),
        "g_flag_counts": dict(sorted(Counter(x["g_flag"] for x in rows).items())),
    }


def scan_archive(
    archive_path: Path,
    target_seq: int = TABLE2["source_id"],
    orphan_seq: int = 615172,
    *,
    expected_archive_md5: str | None = EXPECTED_ARCHIVE_MD5,
    expected_archive_sha256: str | None = EXPECTED_ARCHIVE_SHA256,
    expected_data_sha256: str | None = EXPECTED_DATA_SHA256,
    expected_data_size: int | None = EXPECTED_DATA_SIZE,
    expected_total_rows: int | None = EXPECTED_TOTAL_ROWS,
    expected_ra_deg: float = TABLE2["ra_deg"],
    expected_dec_deg: float = TABLE2["dec_deg"],
    expected_gmag: float = TABLE2["gmag"],
    expected_ng: int = TABLE2["ng"],
) -> dict[str, Any]:
    archive_md5 = digest_file(archive_path, "md5")
    archive_sha256 = digest_file(archive_path, "sha256")
    errors: list[str] = []
    if expected_archive_md5 and archive_md5 != expected_archive_md5:
        errors.append(f"Archive MD5 mismatch: {archive_md5}")
    if expected_archive_sha256 and archive_sha256 != expected_archive_sha256:
        errors.append(f"Archive SHA-256 mismatch: {archive_sha256}")

    with zipfile.ZipFile(archive_path) as archive:
        members = [n for n in archive.namelist() if Path(n).name == "ztf2g" and "__MACOSX" not in n]
        if len(members) != 1:
            raise ValueError(f"Expected one ztf2g member, found {members!r}")
        member = members[0]
        info = archive.getinfo(member)
        expected_crc = info.CRC
        member_metadata = {
            "central_directory_file_size": info.file_size,
            "central_directory_compressed_size": info.compress_size,
            "compression_method": info.compress_type,
        }

    if shutil.which("unzip") is None:
        raise RuntimeError("Info-ZIP 'unzip' is required for this large archive")
    matches: dict[int, list[dict[str, Any]]] = {target_seq: [], orphan_seq: []}
    data_hash = hashlib.sha256()
    data_size = 0
    actual_crc = 0
    data_rows = 0
    malformed = 0
    field_counts: Counter[int] = Counter()
    parse_samples: list[str] = []

    # Info-ZIP was used to verify the complete 5 GB member in the prior audit.
    # Python ZipExtFile stopped at 739 MB for this archive.
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
            field_counts[len(fields)] += 1
            if fields and fields[0].strip().lower() == "sourceid":
                continue
            data_rows += 1
            if len(fields) != len(FIELDS):
                malformed += 1
                if len(parse_samples) < 5:
                    parse_samples.append(f"line {data_rows}: {line[:240]!r}")
                continue
            try:
                source_id = int(fields[0])
            except ValueError:
                malformed += 1
                if len(parse_samples) < 5:
                    parse_samples.append(f"line {data_rows}: invalid SourceID {fields[0]!r}")
                continue
            if source_id not in matches:
                continue
            try:
                values = {
                    "ra_deg": float(fields[1]),
                    "dec_deg": float(fields[2]),
                    "hjd": float(fields[3]),
                    "gmag": float(fields[4]),
                    "e_gmag": float(fields[5]),
                    "g_flag": fields[6].strip(),
                }
            except ValueError:
                malformed += 1
                continue
            if not all(math.isfinite(values[k]) for k in ("ra_deg", "dec_deg", "hjd", "gmag", "e_gmag")):
                malformed += 1
                continue
            matches[source_id].append(values)
        process.stdout.close()
        unzip_returncode = process.wait()
        stderr_file.seek(0)
        unzip_stderr = stderr_file.read().decode("utf-8", errors="replace").strip()

    data_sha256 = data_hash.hexdigest()
    actual_crc &= 0xFFFFFFFF
    crc_verified = actual_crc == expected_crc
    if unzip_returncode:
        errors.append(f"unzip exit code {unzip_returncode}: {unzip_stderr[-500:]}")
    if expected_total_rows is not None and data_rows != expected_total_rows:
        errors.append(f"Record count mismatch: {data_rows} != {expected_total_rows}")
    if malformed:
        errors.append(f"Malformed rows: {malformed}")
    if expected_data_size is not None and data_size != expected_data_size:
        errors.append(f"Extracted size mismatch: {data_size} != {expected_data_size}")
    if expected_data_sha256 and data_sha256 != expected_data_sha256:
        errors.append(f"Extracted SHA-256 mismatch: {data_sha256}")

    target = summarize(matches[target_seq])
    orphan = summarize(matches[orphan_seq])
    separation = None
    mag_delta = None
    if orphan.get("row_count"):
        separation = angular_separation_arcsec(
            expected_ra_deg, expected_dec_deg,
            orphan["ra_median_deg"], orphan["dec_median_deg"],
        )
        mag_delta = orphan["gmag_mean"] - expected_gmag
    strong = orphan.get("row_count") == expected_ng and separation is not None and separation <= 1.0

    return {
        "status": "FAILED_VALIDATION" if errors else (
            "COMPLETED" if crc_verified else "COMPLETED_WITH_ZIP_CRC_MISMATCH"
        ),
        "validation_errors": errors,
        "source": "Zenodo 10.5281/zenodo.3886372, ztf2g.zip",
        "archive": {
            "path_name": archive_path.name,
            "md5": archive_md5,
            "sha256": archive_sha256,
            "checksum_verified": not any("Archive " in e for e in errors),
            "zip_member_crc32_expected": f"{expected_crc:08x}",
            "zip_member_crc32_actual": f"{actual_crc:08x}",
            "zip_crc_verified": crc_verified,
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
            "integrity_verified": (
                (expected_data_size is None or data_size == expected_data_size)
                and (expected_data_sha256 is None or data_sha256 == expected_data_sha256)
            ),
        },
        "scan": {
            "data_rows": data_rows,
            "expected_data_rows": expected_total_rows,
            "malformed_rows": malformed,
            "field_count_distribution": {str(k): v for k, v in sorted(field_counts.items())},
            "parse_error_samples": parse_samples,
            "target_seq": target_seq,
            "orphan_seq": orphan_seq,
        },
        "table2_target": TABLE2,
        "target_seq_summary": target,
        "orphan_seq_summary": orphan,
        "comparison": {
            "orphan_row_count_equals_table2_ng": orphan.get("row_count") == expected_ng,
            "orphan_median_coordinate_separation_arcsec": separation,
            "orphan_mean_gmag_delta_from_table2": mag_delta,
            "strong_coordinate_match_to_table2_target": strong,
            "interpretation": "STRONG_IDENTITY_LEAD" if strong else "IDENTITY_NOT_CONFIRMED",
        },
        "warnings": [] if crc_verified else ["ZIP central-directory CRC differs; independent extracted-member hash/size remain mandatory."],
        "limitations": [
            "This diagnostic checks only the g-band archive.",
            "A coordinate match is an identity lead, not an automatic source-ID correction.",
            "This diagnostic does not explain the 11,602 candidate-only IDs or establish the publisher's selection rule.",
            "The r-band archive and other mismatched Seq values require separate checks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--target-seq", type=int, default=TABLE2["source_id"])
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
