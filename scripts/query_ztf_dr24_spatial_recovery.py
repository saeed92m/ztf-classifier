#!/usr/bin/env python3
"""Spatially recover ZTF DR24 OIDs for an external coordinate catalog."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DR24_OBJECTS_HATS = (
    "s3://ipac-irsa-ztf/ztf/enhanced/dr24/objects/hats"
)
REQUIRED_COLUMNS = ("external_id", "ra", "dec")
BASE_CATALOG_COLUMNS = ("oid", "ra", "dec", "filtercode")
PROVENANCE_COLUMN_CANDIDATES = ("field", "ccdid", "qid", "rcid", "fid")


def _read_targets(path: Path, limit: int | None) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("target CSV has no header")
        missing = sorted(set(REQUIRED_COLUMNS) - set(reader.fieldnames))
        if missing:
            raise ValueError("target CSV missing columns: " + ", ".join(missing))
        rows = list(reader)
    if not rows:
        raise ValueError("target CSV has no rows")
    ids = [str(row["external_id"]).strip() for row in rows]
    if any(not value for value in ids):
        raise ValueError("target CSV contains an empty external_id")
    if len(set(ids)) != len(ids):
        raise ValueError("target CSV contains duplicate external_id values")
    return rows[:limit] if limit is not None else rows


def query_dr24(
    targets: list[dict[str, str]],
    *,
    radius_arcsec: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Query the official DR24 Objects Table HATS catalog for every target."""
    if radius_arcsec <= 0 or radius_arcsec >= 60:
        raise ValueError("radius_arcsec must be greater than 0 and less than 60")

    try:
        import lsdb
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional recovery dependency: pip install 'lsdb[full]==0.10.4'"
        ) from exc

    schema_catalog = lsdb.open_catalog(DR24_OBJECTS_HATS)
    available_columns = set(schema_catalog.all_columns)
    missing = sorted(set(BASE_CATALOG_COLUMNS) - available_columns)
    if missing:
        raise ValueError(
            "DR24 Objects Table schema is missing required columns: "
            + ", ".join(missing)
        )
    provenance_columns = [
        column
        for column in PROVENANCE_COLUMN_CANDIDATES
        if column in available_columns
    ]
    selected_columns = [*BASE_CATALOG_COLUMNS, *provenance_columns]
    catalog = lsdb.open_catalog(
        DR24_OBJECTS_HATS,
        columns=selected_columns,
    )
    matches: list[dict[str, Any]] = []
    query_records: list[dict[str, Any]] = []

    for index, target in enumerate(targets, start=1):
        external_id = str(target["external_id"]).strip()
        ra = float(target["ra"])
        dec = float(target["dec"])
        if not (0.0 <= ra < 360.0 and -90.0 <= dec <= 90.0):
            raise ValueError(f"invalid coordinates for {external_id}")
        cone = catalog.cone_search(
            ra=ra,
            dec=dec,
            radius_arcsec=radius_arcsec,
        )
        frame = cone.compute()
        returned = 0
        if not frame.empty:
            frame = frame.reset_index(drop=True)
            required = {"oid", "ra", "dec", "filtercode"}
            missing = sorted(required - set(frame.columns))
            if missing:
                raise ValueError(
                    "DR24 response missing columns: " + ", ".join(missing)
                )
            for row in frame.itertuples(index=False):
                record = row._asdict()
                match = {
                    "external_id": external_id,
                    "oid": str(record["oid"]),
                    "ra": float(record["ra"]),
                    "dec": float(record["dec"]),
                    "filtercode": str(record["filtercode"]),
                }
                for column in provenance_columns:
                    value = record.get(column)
                    match[column] = "" if value is None else value
                matches.append(match)
                returned += 1
        query_records.append(
            {
                "external_id": external_id,
                "ra": ra,
                "dec": dec,
                "query_radius_arcsec": radius_arcsec,
                "returned_oids": returned,
                "query_index": index,
            }
        )
        print(
            f"[{index}/{len(targets)}] {external_id}: "
            f"{returned} DR24 OIDs within {radius_arcsec:g} arcsec"
        )

    metadata = {
        "schema_version": "ztf-dr24-spatial-recovery-v2",
        "source": "IRSA ZTF DR24 Objects Table HATS",
        "catalog_uri": DR24_OBJECTS_HATS,
        "release": "DR24",
        "query_timestamp_utc": datetime.now(UTC).isoformat(),
        "query_radius_arcsec": radius_arcsec,
        "target_count": len(targets),
        "selected_columns": selected_columns,
        "provenance_columns": provenance_columns,
        "queries": query_records,
        "returned_match_rows": len(matches),
        "interpretation": (
            "A returned OID is a spatial association candidate. It is not "
            "automatically a unique astrophysical source identity."
        ),
    }
    return matches, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--radius-arcsec", type=float, default=5.0)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if args.limit <= 0:
        raise ValueError("--limit must be positive")
    targets = _read_targets(args.targets, args.limit)
    matches, metadata = query_dr24(
        targets, radius_arcsec=args.radius_arcsec
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    matches_path = args.output_dir / "dr24_spatial_matches.csv"
    with matches_path.open("w", newline="", encoding="utf-8") as handle:
        fields = (
            "external_id",
            "oid",
            "ra",
            "dec",
            "filtercode",
            *metadata["provenance_columns"],
        )
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(matches)

    metadata["matches_artifact"] = {
        "path": matches_path.name,
        "sha256": hashlib.sha256(matches_path.read_bytes()).hexdigest(),
        "size_bytes": matches_path.stat().st_size,
    }
    metadata_path = args.output_dir / "dr24_query_manifest.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"targets={len(targets)}")
    print(f"match_rows={len(matches)}")
    print(f"provenance_columns={','.join(metadata['provenance_columns'])}")
    print(f"manifest={metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
