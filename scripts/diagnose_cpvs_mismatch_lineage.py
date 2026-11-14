#!/usr/bin/env python3
"""Trace the 100 CPVS raw/Table2 count mismatches to epochs and coordinates."""
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

EXPECTED_TABLE2 = {
    "sha256": "2c77c5b6c14811f6abab6e1442ce82c6fb54dbdcfc141954165704fecfcb3881",
    "bytes": 178986858,
}
EXPECTED_MISMATCH = {
    "sha256": "d33c4dc3c575e520b867d84a1b9424368b2c44176f15651abba20b585ef0c8d5",
    "bytes": 15089,
    "rows": 100,
}
ARCHIVES = {
    "g": {
        "member": "ztf2g",
        "sha256": "47cd1823b3ccdb69fa3085381cf63ff0605f6d841fc3bc37489dce023ddc19b9",
        "member_sha256": "366aaf3539f83955bb1e29799df9e63005a9eb682f4f56d0807545a3534b0f16",
        "member_bytes": 5034066142,
        "member_rows": 89697393,
        "member_crc32": "d2f33aa0",
    },
    "r": {
        "member": "ztf2r",
        "sha256": "48331ba1157afc993a1399e094b97752a82d8d0f736d2fdf63fd7b2a82281b74",
        "member_sha256": "78df6d0b22099a7e5c6e74b897682c6ab94f90d5f9e887d4b0b3b152514e50fe",
        "member_bytes": 6175667360,
        "member_rows": 109971576,
        "member_crc32": "225495a0",
    },
}
SEARCH_RADIUS_ARCSEC = 3.0
CELL_DEG = 0.05
ARCSEC_PER_RADIAN = 206264.80624709636


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, expected: dict[str, Any]) -> str:
    if path.stat().st_size != expected["bytes"]:
        raise ValueError(f"{path.name} byte-count mismatch")
    digest = sha256_file(path)
    if digest != expected["sha256"]:
        raise ValueError(f"{path.name} SHA-256 mismatch: {digest}")
    return digest


def angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    dra = (r2 - r1 + math.pi) % (2.0 * math.pi) - math.pi
    ddec = d2 - d1
    value = math.sin(ddec / 2.0) ** 2 + math.cos(d1) * math.cos(d2) * math.sin(dra / 2.0) ** 2
    return 2.0 * math.asin(math.sqrt(min(1.0, max(0.0, value)))) * ARCSEC_PER_RADIAN


def classify_time_scale(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "UNKNOWN"
    if 40000.0 <= value <= 100000.0:
        return "MJD_LIKE"
    if 2400000.0 <= value <= 2600000.0:
        return "HJD_OR_JD_LIKE"
    return "UNKNOWN"


def cell_key(ra: float, dec: float) -> tuple[int, int]:
    return int(math.floor((ra % 360.0) / CELL_DEG)), int(math.floor((dec + 90.0) / CELL_DEG))


def build_spatial_hash(targets: dict[int, dict[str, Any]]) -> dict[tuple[int, int], set[int]]:
    ra_cells = int(round(360.0 / CELL_DEG))
    index: dict[tuple[int, int], set[int]] = {}
    for source_id, item in targets.items():
        ra_cell, dec_cell = cell_key(item["ra"], item["dec"])
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                key = ((ra_cell + dx) % ra_cells, dec_cell + dy)
                index.setdefault(key, set()).add(source_id)
    return index


def load_table2(path: Path) -> dict[int, dict[str, Any]]:
    table: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="ascii") as stream:
        for line_number, line in enumerate(stream, start=1):
            fields = line.split()
            if not fields:
                continue
            if len(fields) != 27:
                raise ValueError(f"Table2 line {line_number}: expected 27 fields")
            source_id = int(fields[1])
            if source_id in table:
                raise ValueError(f"Duplicate Table2 SourceID {source_id}")
            table[source_id] = {
                "ZTF": fields[0], "ra": float(fields[2]), "dec": float(fields[3]),
                "Ng": int(fields[12]), "Nr": int(fields[13]),
            }
    if len(table) != 781602:
        raise ValueError(f"Expected 781602 Table2 objects, got {len(table)}")
    return table


def load_mismatches(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != EXPECTED_MISMATCH["rows"]:
        raise ValueError(f"Expected 100 mismatch objects, got {len(rows)}")
    ids = [int(row["SourceID"]) for row in rows]
    if len(set(ids)) != len(rows):
        raise ValueError("Mismatch TSV contains duplicate SourceIDs")
    return rows


def make_object_stats(source_id: int, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "SourceID": source_id, "ZTF": meta["ZTF"],
        "table2_ra": meta["ra"], "table2_dec": meta["dec"],
        "raw_rows": 0, "valid_numeric_rows": 0,
        "times": Counter(), "measurements": Counter(), "flags": Counter(),
        "ras": [], "decs": [], "magnitudes": [], "errors": [],
        "zero_magnitude_rows": 0, "zero_error_rows": 0, "negative_error_rows": 0,
    }


def parse_fields(line: bytes) -> list[str]:
    return line.strip().replace(b",", b" ").decode("ascii", errors="strict").split()


def scan_archive(
    archive_path: Path,
    band: str,
    table2: dict[int, dict[str, Any]],
    mismatch_rows: list[dict[str, str]],
) -> dict[str, Any]:
    config = ARCHIVES[band]
    archive_sha = sha256_file(archive_path)
    if archive_sha != config["sha256"]:
        raise ValueError(f"{band} archive SHA-256 mismatch")
    targets = {int(row["SourceID"]): table2[int(row["SourceID"])] for row in mismatch_rows}
    missing_targets = {
        sid: meta for sid, meta in targets.items()
        if int(next(row[f"raw_{band}"] for row in mismatch_rows if int(row["SourceID"]) == sid)) == 0
    }
    spatial_hash = build_spatial_hash(missing_targets)
    object_stats = {sid: make_object_stats(sid, meta) for sid, meta in targets.items()}
    seen_source_ids: set[int] = set()
    alias_owner: dict[int, tuple[int, float]] = {}
    aliases: dict[tuple[int, int], dict[str, Any]] = {}
    digest = hashlib.sha256()
    crc = 0
    member_bytes = 0
    member_rows = 0
    malformed = 0
    member_name = ""

    with zipfile.ZipFile(archive_path) as archive:
        members = [
            name for name in archive.namelist()
            if Path(name).name == config["member"] and "__MACOSX" not in name
        ]
        if len(members) != 1:
            raise ValueError(f"Expected one {config['member']} member; got {members}")
        member_name = members[0]
        info = archive.getinfo(member_name)
        if f"{info.CRC:08x}" != config["member_crc32"]:
            raise ValueError(f"{band} central-directory CRC mismatch")

    with tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            ["unzip", "-p", str(archive_path), member_name],
            stdout=subprocess.PIPE, stderr=stderr_file,
        )
        if process.stdout is None:
            raise RuntimeError("Info-ZIP stdout is unavailable")
        for raw in process.stdout:
            digest.update(raw)
            crc = zlib.crc32(raw, crc)
            member_bytes += len(raw)
            member_rows += 1
            try:
                fields = parse_fields(raw)
                if len(fields) != 7:
                    malformed += 1
                    continue
                source_id = int(fields[0])
                ra, dec, epoch, mag, err = map(float, fields[1:6])
            except (UnicodeDecodeError, ValueError):
                malformed += 1
                continue
            if not all(math.isfinite(value) for value in (ra, dec, epoch, mag, err)):
                malformed += 1
                continue
            flag = fields[6]

            if source_id in object_stats:
                item = object_stats[source_id]
                item["raw_rows"] += 1
                item["times"][round(epoch, 7)] += 1
                item["measurements"][(round(epoch, 7), round(mag, 7), round(err, 7), flag)] += 1
                item["flags"][flag] += 1
                item["ras"].append(ra)
                item["decs"].append(dec)
                if mag == 0:
                    item["zero_magnitude_rows"] += 1
                if err == 0:
                    item["zero_error_rows"] += 1
                if err < 0:
                    item["negative_error_rows"] += 1
                if mag != 0 and err > 0:
                    item["valid_numeric_rows"] += 1
                    item["magnitudes"].append(mag)
                    item["errors"].append(err)
                continue

            if source_id not in seen_source_ids:
                seen_source_ids.add(source_id)
                ra_cell, dec_cell = cell_key(ra, dec)
                candidate_ids = spatial_hash.get((ra_cell, dec_cell), set())
                best: tuple[float, int] | None = None
                for target_id in candidate_ids:
                    target = missing_targets[target_id]
                    separation = angular_separation_arcsec(ra, dec, target["ra"], target["dec"])
                    if separation <= SEARCH_RADIUS_ARCSEC and (best is None or separation < best[0]):
                        best = (separation, target_id)
                if best is not None:
                    separation, target_id = best
                    alias_owner[source_id] = (target_id, separation)
                    aliases[(target_id, source_id)] = {
                        "target_SourceID": target_id,
                        "target_ZTF": missing_targets[target_id]["ZTF"],
                        "alternate_SourceID": source_id,
                        "separation_arcsec": separation,
                        "alternate_raw_rows": 0,
                        "flags": Counter(),
                        "time_min": epoch,
                        "time_max": epoch,
                    }
            alias = alias_owner.get(source_id)
            if alias is not None:
                target_id, separation = alias
                record = aliases[(target_id, source_id)]
                record["alternate_raw_rows"] += 1
                record["flags"][flag] += 1
                record["time_min"] = min(record["time_min"], epoch)
                record["time_max"] = max(record["time_max"], epoch)

        process.stdout.close()
        return_code = process.wait()
        stderr_file.seek(0)
        stderr = stderr_file.read().decode("utf-8", errors="replace")
    if return_code:
        raise RuntimeError(f"Info-ZIP failed for {band}: {stderr[-1200:]}")
    member_sha = digest.hexdigest()
    crc_hex = f"{crc & 0xFFFFFFFF:08x}"
    if member_sha != config["member_sha256"]:
        raise ValueError(f"{band} member SHA-256 mismatch")
    if member_bytes != config["member_bytes"] or member_rows != config["member_rows"]:
        raise ValueError(f"{band} member size/row-count mismatch")
    if crc_hex != config["member_crc32"] or malformed:
        raise ValueError(f"{band} member CRC or malformed-row validation failed")

    objects = []
    for source_id, item in sorted(object_stats.items()):
        times = item.pop("times")
        measurements = item.pop("measurements")
        flags = item.pop("flags")
        ras, decs = item.pop("ras"), item.pop("decs")
        mags, errors = item.pop("magnitudes"), item.pop("errors")
        if ras:
            offsets = [
                angular_separation_arcsec(item["table2_ra"], item["table2_dec"], ra, dec)
                for ra, dec in zip(ras, decs)
            ]
            item["median_coordinate_offset_arcsec"] = sorted(offsets)[len(offsets)//2]
            item["max_coordinate_offset_arcsec"] = max(offsets)
            item["ra_min"], item["ra_max"] = min(ras), max(ras)
            item["dec_min"], item["dec_max"] = min(decs), max(decs)
        else:
            item["median_coordinate_offset_arcsec"] = None
            item["max_coordinate_offset_arcsec"] = None
            item["ra_min"] = item["ra_max"] = None
            item["dec_min"] = item["dec_max"] = None
        item["unique_epoch_count"] = len(times)
        item["duplicate_epoch_rows"] = sum(v-1 for v in times.values() if v > 1)
        item["unique_measurement_count"] = len(measurements)
        item["duplicate_measurement_rows"] = sum(v-1 for v in measurements.values() if v > 1)
        item["time_min"] = min(times) if times else None
        item["time_max"] = max(times) if times else None
        item["time_scale_hint"] = classify_time_scale(item["time_min"])
        item["flag_counts_json"] = json.dumps(dict(sorted(flags.items())), sort_keys=True)
        item["magnitude_min"] = min(mags) if mags else None
        item["magnitude_max"] = max(mags) if mags else None
        item["error_min"] = min(errors) if errors else None
        item["error_max"] = max(errors) if errors else None
        objects.append(item)
    alias_rows = []
    for record in aliases.values():
        flags = record.pop("flags")
        record["flag_counts_json"] = json.dumps(dict(sorted(flags.items())), sort_keys=True)
        record["time_scale_hint"] = classify_time_scale(record["time_min"])
        alias_rows.append(record)
    alias_rows.sort(key=lambda x: (x["target_SourceID"], x["separation_arcsec"]))
    return {
        "archive_sha256": archive_sha, "member_sha256": member_sha,
        "member_crc32": crc_hex, "member_bytes": member_bytes, "member_rows": member_rows,
        "malformed_rows": malformed, "objects": objects, "coordinate_aliases": alias_rows,
        "targets_without_raw_rows": [sid for sid, item in object_stats.items() if item["raw_rows"] == 0],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table2", type=Path, required=True)
    parser.add_argument("--mismatches", type=Path, required=True)
    parser.add_argument("--g-archive", type=Path, required=True)
    parser.add_argument("--r-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    table2_hash = verify_file(args.table2, EXPECTED_TABLE2)
    mismatch_hash = verify_file(args.mismatches, EXPECTED_MISMATCH)
    table2 = load_table2(args.table2)
    mismatches = load_mismatches(args.mismatches)
    scans = {
        band: scan_archive(path, band, table2, mismatches)
        for band, path in (("g", args.g_archive), ("r", args.r_archive))
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)

    object_path = args.output_dir / "cpvs_mismatch_object_lineage.tsv"
    object_columns = [
        "band", "SourceID", "ZTF", "table2_ra", "table2_dec", "raw_rows",
        "valid_numeric_rows", "unique_epoch_count", "duplicate_epoch_rows",
        "unique_measurement_count", "duplicate_measurement_rows", "time_min",
        "time_max", "time_scale_hint", "flag_counts_json",
        "median_coordinate_offset_arcsec", "max_coordinate_offset_arcsec",
        "ra_min", "ra_max", "dec_min", "dec_max", "magnitude_min",
        "magnitude_max", "error_min", "error_max", "zero_magnitude_rows",
        "zero_error_rows", "negative_error_rows",
    ]
    with object_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=object_columns, delimiter="\t")
        writer.writeheader()
        for band, result in scans.items():
            for obj in result["objects"]:
                writer.writerow({"band": band, **obj})

    alias_path = args.output_dir / "cpvs_mismatch_coordinate_aliases.tsv"
    alias_columns = [
        "band", "target_SourceID", "target_ZTF", "alternate_SourceID",
        "separation_arcsec", "alternate_raw_rows", "flag_counts_json",
        "time_min", "time_max", "time_scale_hint",
    ]
    with alias_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=alias_columns, delimiter="\t")
        writer.writeheader()
        for band, result in scans.items():
            for alias in result["coordinate_aliases"]:
                writer.writerow({"band": band, **alias})

    report = {
        "schema_version": "1.0",
        "diagnostic": "CPVS raw/Table2 mismatch epoch and coordinate lineage",
        "scope": "100 previously identified object-level count mismatches; read-only diagnostics",
        "inputs": {
            "table2_sha256": table2_hash,
            "mismatch_tsv_sha256": mismatch_hash,
            "table2_rows": len(table2),
            "mismatch_objects": len(mismatches),
        },
        "coordinate_search": {
            "radius_arcsec": SEARCH_RADIUS_ARCSEC,
            "cell_size_degrees": CELL_DEG,
            "purpose": "Find nearby alternate SourceIDs for targets with zero raw rows in a band.",
        },
        "bands": {
            band: {
                "archive_sha256": result["archive_sha256"],
                "member_sha256": result["member_sha256"],
                "member_crc32": result["member_crc32"],
                "member_bytes": result["member_bytes"],
                "member_rows": result["member_rows"],
                "malformed_rows": result["malformed_rows"],
                "targets_without_raw_rows": len(result["targets_without_raw_rows"]),
                "coordinate_alias_matches": len(result["coordinate_aliases"]),
            }
            for band, result in scans.items()
        },
        "time_scale_hints": {
            band: dict(Counter(obj["time_scale_hint"] for obj in result["objects"]))
            for band, result in scans.items()
        },
        "interpretation_limit": (
            "A nearby alternate SourceID is a lead for manual/source-backed review, not permission to remap IDs. "
            "Coordinate proximity does not prove identity, and missing rows do not prove low SNR."
        ),
        "outputs": {
            "object_lineage": object_path.name,
            "coordinate_aliases": alias_path.name,
        },
    }
    report_path = args.output_dir / "cpvs_mismatch_lineage_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for path in (report_path, object_path, alias_path):
        print(f"{path.name} bytes={path.stat().st_size} sha256={sha256_file(path)}")
    print(json.dumps(report, indent=2))


def classify_time_scale(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "UNKNOWN"
    if 40000.0 <= value <= 100000.0:
        return "MJD_LIKE"
    if 2400000.0 <= value <= 2600000.0:
        return "HJD_OR_JD_LIKE"
    return "UNKNOWN"


def load_mismatches(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != EXPECTED_MISMATCH["rows"]:
        raise ValueError(f"Expected 100 mismatch objects, got {len(rows)}")
    ids = [int(row["SourceID"]) for row in rows]
    if len(set(ids)) != len(rows):
        raise ValueError("Mismatch TSV contains duplicate SourceIDs")
    return rows


if __name__ == "__main__":
    main()
