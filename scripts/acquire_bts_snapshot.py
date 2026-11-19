#!/usr/bin/env python3
"""Acquire and normalize a dated snapshot of the public ZTF BTS explorer CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import requests
from astropy import units as u
from astropy.coordinates import Angle

BTS_CSV_URL = (
    "https://sites.astro.caltech.edu/ztf/bts/explorer.php"
    "?subsample=cantrans&endpeakmag=19.0&format=csv&quality=y&samprcf=y"
)
EXPECTED_INITIAL_ROWS = 10551
EXPECTED_INITIAL_SHA256 = (
    "af2362275074ff4b6c70523b9db6f2d5991af16fdd8d76ed47520948eb788e82"
)
REQUIRED_COLUMNS = ("ZTFID", "IAUID", "RA", "Dec", "type")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _angle_degrees(value: str, *, right_ascension: bool) -> float:
    text = str(value).strip()
    if not text:
        raise ValueError("coordinate is empty")
    sexagesimal = any(character in text for character in (":", "h", "d", "m", "s"))
    if sexagesimal:
        unit = u.hourangle if right_ascension else u.deg
        result = Angle(text, unit=unit).degree
    else:
        result = float(text)
    if not (-90.0 <= result <= 90.0) and not right_ascension:
        raise ValueError(f"declination is out of range: {value!r}")
    if right_ascension and not (0.0 <= result < 360.0):
        raise ValueError(f"right ascension is out of range: {value!r}")
    return float(result)


def parse_bts_csv(payload: bytes) -> list[dict[str, str | float]]:
    """Parse the publisher CSV, including its documented leading blank line."""
    text = payload.decode("utf-8-sig")
    text = text.lstrip("\ufeff\r\n ")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("BTS CSV has no header")
    reader.fieldnames = [name.strip() for name in reader.fieldnames]
    missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames))
    if missing:
        raise ValueError("BTS CSV is missing columns: " + ", ".join(missing))

    rows: list[dict[str, str | float]] = []
    seen_ids: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        ztf_id = str(row.get("ZTFID", "")).strip()
        if not ztf_id:
            raise ValueError(f"BTS row {row_number}: ZTFID is empty")
        if ztf_id in seen_ids:
            raise ValueError(f"BTS row {row_number}: duplicate ZTFID {ztf_id}")
        seen_ids.add(ztf_id)
        ra = _angle_degrees(row["RA"], right_ascension=True)
        dec = _angle_degrees(row["Dec"], right_ascension=False)
        normalized = {str(key): str(value or "").strip() for key, value in row.items()}
        normalized["external_id"] = ztf_id
        normalized["tns_id"] = normalized.get("IAUID", "")
        normalized["ra"] = ra
        normalized["dec"] = dec
        rows.append(normalized)
    if not rows:
        raise ValueError("BTS CSV contains no data rows")
    return rows


def deterministic_sample(
    rows: list[dict[str, str | float]], sample_size: int
) -> list[dict[str, str | float]]:
    """Choose a stable sample by SHA-256 of the external ZTF name."""
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    ordered = sorted(
        rows,
        key=lambda row: hashlib.sha256(
            str(row["external_id"]).encode("utf-8")
        ).hexdigest(),
    )
    return ordered[: min(sample_size, len(ordered))]


def write_csv(path: Path, rows: list[dict[str, str | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--code-version", default="unknown")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        BTS_CSV_URL,
        timeout=args.timeout,
        headers={"User-Agent": "ztf-classifier-independent-recovery/1.0"},
    )
    response.raise_for_status()
    payload = response.content
    if not payload:
        raise RuntimeError("BTS CSV response is empty")
    raw_path = args.output_dir / "bts_explorer_raw.csv"
    raw_path.write_bytes(payload)

    rows = parse_bts_csv(payload)
    sample = deterministic_sample(rows, args.sample_size)
    normalized_path = args.output_dir / "bts_catalog_normalized.csv"
    sample_path = args.output_dir / "bts_catalog_sample.csv"
    write_csv(normalized_path, rows)
    write_csv(sample_path, sample)

    digest = sha256_bytes(payload)
    metadata = {
        "schema_version": "bts-source-snapshot-v1",
        "source": "ZTF Bright Transient Survey Sample Explorer",
        "source_url": BTS_CSV_URL,
        "resolved_url": response.url,
        "code_version": args.code_version,
        "retrieval_timestamp_utc": datetime.now(UTC).isoformat(),
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "etag": response.headers.get("etag"),
        "last_modified": response.headers.get("last-modified"),
        "content_length_header": response.headers.get("content-length"),
        "raw_response_sha256": digest,
        "raw_response_bytes": len(payload),
        "row_count": len(rows),
        "expected_initial_snapshot": {
            "retrieved_on": "2026-11-02",
            "row_count": EXPECTED_INITIAL_ROWS,
            "sha256": EXPECTED_INITIAL_SHA256,
            "matches_initial_snapshot": (
                len(rows) == EXPECTED_INITIAL_ROWS
                and digest == EXPECTED_INITIAL_SHA256
            ),
        },
        "columns": list(rows[0]),
        "unique_ztf_ids": len({str(row["external_id"]) for row in rows}),
        "sample_size_requested": args.sample_size,
        "sample_size_written": len(sample),
        "sample_ids": [str(row["external_id"]) for row in sample],
        "artifacts": {
            "raw_csv": {
                "path": raw_path.name,
                "sha256": sha256_bytes(raw_path.read_bytes()),
                "size_bytes": raw_path.stat().st_size,
            },
            "normalized_catalog": {
                "path": normalized_path.name,
                "sha256": sha256_bytes(normalized_path.read_bytes()),
                "size_bytes": normalized_path.stat().st_size,
            },
            "sample": {
                "path": sample_path.name,
                "sha256": sha256_bytes(sample_path.read_bytes()),
                "size_bytes": sample_path.stat().st_size,
            },
        },
        "coordinate_contract": {
            "ra_unit": "degree",
            "dec_unit": "degree",
            "source_format": "sexagesimal or decimal, parsed explicitly",
        },
    }
    metadata_path = args.output_dir / "bts_snapshot_manifest.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"source_rows={len(rows)}")
    print(f"sample_rows={len(sample)}")
    print(f"raw_sha256={digest}")
    print(f"initial_snapshot_match={metadata['expected_initial_snapshot']['matches_initial_snapshot']}")
    print(f"manifest={metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
