#!/usr/bin/env python3
"""Audit external-source to ZTF DR24 OID recovery multiplicity.

This utility does not decide whether a spatial match is a true astrophysical
association. It reports identifier multiplicity by radius and filter.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CATALOG_FIELDS = ("external_id", "ra", "dec")
MATCH_FIELDS = ("external_id", "oid", "ra", "dec", "filtercode")
DEFAULT_RADII_ARCSEC = (1.0, 2.0, 5.0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_float(value: str, field: str, row_number: int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {row_number}: {field} must be numeric") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"row {row_number}: {field} must be finite")
    return parsed


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: CSV has no header")
        missing = sorted(set(required) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path}: missing required columns: {', '.join(missing)}")
        return list(reader)


def angular_separation_arcsec(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    """Return great-circle separation using a numerically stable haversine."""
    ra1, dec1, ra2, dec2 = map(
        math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg)
    )
    delta_ra = ra2 - ra1
    delta_dec = dec2 - dec1
    hav = (
        math.sin(delta_dec / 2.0) ** 2
        + math.cos(dec1) * math.cos(dec2) * math.sin(delta_ra / 2.0) ** 2
    )
    hav = min(1.0, max(0.0, hav))
    return math.degrees(2.0 * math.asin(math.sqrt(hav))) * 3600.0


def audit_recovery(
    catalog_rows: list[dict[str, str]],
    match_rows: list[dict[str, str]],
    *,
    radii_arcsec: tuple[float, ...] = DEFAULT_RADII_ARCSEC,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build per-source multiplicity rows and aggregate summaries."""
    if not catalog_rows:
        raise ValueError("catalog contains no source rows")
    if not radii_arcsec or any(
        not math.isfinite(radius) or radius <= 0 for radius in radii_arcsec
    ):
        raise ValueError("radii_arcsec must contain positive finite values")

    catalog: dict[str, tuple[float, float]] = {}
    for row_number, row in enumerate(catalog_rows, start=2):
        external_id = str(row["external_id"]).strip()
        if not external_id:
            raise ValueError(f"catalog row {row_number}: external_id is empty")
        if external_id in catalog:
            raise ValueError(f"catalog row {row_number}: duplicate external_id {external_id}")
        ra = _finite_float(row["ra"], "ra", row_number)
        dec = _finite_float(row["dec"], "dec", row_number)
        if not 0.0 <= ra < 360.0 or not -90.0 <= dec <= 90.0:
            raise ValueError(f"catalog row {row_number}: coordinates are out of range")
        catalog[external_id] = (ra, dec)

    unique_matches: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_match_rows = 0
    for row_number, row in enumerate(match_rows, start=2):
        external_id = str(row["external_id"]).strip()
        oid = str(row["oid"]).strip()
        if external_id not in catalog:
            raise ValueError(
                f"match row {row_number}: unknown external_id {external_id!r}"
            )
        if not oid:
            raise ValueError(f"match row {row_number}: oid is empty")
        ra = _finite_float(row["ra"], "ra", row_number)
        dec = _finite_float(row["dec"], "dec", row_number)
        if not 0.0 <= ra < 360.0 or not -90.0 <= dec <= 90.0:
            raise ValueError(f"match row {row_number}: coordinates are out of range")
        filtercode = str(row["filtercode"]).strip().lower()
        if not filtercode:
            raise ValueError(f"match row {row_number}: filtercode is empty")
        source_ra, source_dec = catalog[external_id]
        separation = angular_separation_arcsec(source_ra, source_dec, ra, dec)
        key = (external_id, oid)
        value = {
            "external_id": external_id,
            "oid": oid,
            "filtercode": filtercode,
            "ztf_ra": ra,
            "ztf_dec": dec,
            "separation_arcsec": separation,
        }
        if key in unique_matches:
            duplicate_match_rows += 1
            previous = unique_matches[key]
            if previous != value:
                raise ValueError(
                    f"conflicting duplicate match for external_id={external_id!r}, oid={oid!r}"
                )
        else:
            unique_matches[key] = value

    rows: list[dict[str, Any]] = []
    summaries: dict[str, Any] = {}
    for radius in sorted(set(radii_arcsec)):
        by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for match in unique_matches.values():
            if match["separation_arcsec"] <= radius:
                by_source[match["external_id"]].append(match)

        counts = Counter()
        oid_counts: list[int] = []
        for external_id in sorted(catalog):
            matches = sorted(
                by_source.get(external_id, []),
                key=lambda item: (item["filtercode"], item["oid"]),
            )
            oids = sorted({item["oid"] for item in matches})
            filters = sorted({item["filtercode"] for item in matches})
            per_filter = Counter(item["filtercode"] for item in matches)
            same_filter_multi = any(value > 1 for value in per_filter.values())
            oid_count = len(oids)
            oid_counts.append(oid_count)
            counts["matched_objects"] += int(oid_count > 0)
            counts["unmatched_objects"] += int(oid_count == 0)
            counts["multi_oid_objects"] += int(oid_count > 1)
            counts["multi_filter_objects"] += int(len(filters) > 1)
            counts["same_filter_multi_oid_objects"] += int(same_filter_multi)
            counts["matched_oid_rows"] += oid_count
            rows.append(
                {
                    "radius_arcsec": radius,
                    "external_id": external_id,
                    "ztf_oid_count": oid_count,
                    "ztf_oids": ";".join(oids),
                    "filter_count": len(filters),
                    "filtercodes": ";".join(filters),
                    "same_filter_multiple_oids": same_filter_multi,
                    "nearest_separation_arcsec": (
                        min(item["separation_arcsec"] for item in matches)
                        if matches
                        else None
                    ),
                }
            )

        summaries[str(radius)] = {
            "radius_arcsec": radius,
            "catalog_objects": len(catalog),
            "matched_objects": counts["matched_objects"],
            "unmatched_objects": counts["unmatched_objects"],
            "matched_oid_rows": counts["matched_oid_rows"],
            "multi_oid_objects": counts["multi_oid_objects"],
            "multi_filter_objects": counts["multi_filter_objects"],
            "same_filter_multi_oid_objects": counts[
                "same_filter_multi_oid_objects"
            ],
            "max_oids_per_source": max(oid_counts, default=0),
        }

    metadata = {
        "schema_version": "ztf-recovery-multiplicity-v1",
        "interpretation": (
            "OID multiplicity is descriptive. Multiple OIDs are not classified "
            "as false positives because ZTF objects are defined per filter, "
            "field, and quadrant."
        ),
        "duplicate_match_rows_removed": duplicate_match_rows,
        "unique_external_objects": len(catalog),
        "unique_external_ids": sorted(catalog),
        "unique_external_ztf_oid_pairs": len(unique_matches),
        "radii": summaries,
    }
    return rows, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--radii-arcsec",
        type=float,
        nargs="+",
        default=list(DEFAULT_RADII_ARCSEC),
    )
    args = parser.parse_args()

    catalog_rows = _read_csv(args.catalog, CATALOG_FIELDS)
    match_rows = _read_csv(args.matches, MATCH_FIELDS)
    per_object, summary = audit_recovery(
        catalog_rows, match_rows, radii_arcsec=tuple(args.radii_arcsec)
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_object_path = args.output_dir / "per_object_multiplicity.csv"
    with per_object_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "radius_arcsec",
                "external_id",
                "ztf_oid_count",
                "ztf_oids",
                "filter_count",
                "filtercodes",
                "same_filter_multiple_oids",
                "nearest_separation_arcsec",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(per_object)

    summary["inputs"] = {
        "catalog": {
            "path": str(args.catalog),
            "sha256": sha256_file(args.catalog),
            "rows": len(catalog_rows),
        },
        "matches": {
            "path": str(args.matches),
            "sha256": sha256_file(args.matches),
            "rows": len(match_rows),
        },
    }
    summary["parameters"] = {"radii_arcsec": sorted(set(args.radii_arcsec))}
    summary["outputs"] = {
        "per_object_multiplicity": {
            "path": per_object_path.name,
            "sha256": sha256_file(per_object_path),
        }
    }
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"catalog_objects={len(catalog_rows)}")
    for radius, metrics in summary["radii"].items():
        print(
            f"radius={radius} arcsec matched={metrics['matched_objects']} "
            f"unmatched={metrics['unmatched_objects']} "
            f"multi_oid={metrics['multi_oid_objects']} "
            f"same_filter_multi_oid={metrics['same_filter_multi_oid_objects']}"
        )
    print(f"summary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
