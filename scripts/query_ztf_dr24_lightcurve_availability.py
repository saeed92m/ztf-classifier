#!/usr/bin/env python3
"""Check DR24 Lightcurves HATS availability for recovered Objects Table OIDs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

DR24_LIGHTCURVES_HATS = (
    "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats"
)
REQUIRED_MATCH_COLUMNS = ("external_id", "oid", "filtercode", "fid")
REQUIRED_TARGET_COLUMNS = ("external_id", "ra", "dec")
REQUIRED_LIGHTCURVE_COLUMNS = ("objectid", "filterid", "nepochs")
FILTER_ID_TO_CODE = {1: "zg", 2: "zr", 3: "zi"}


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not-installed"


def _read_csv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no CSV header")
        missing = sorted(set(required) - set(reader.fieldnames))
        if missing:
            raise ValueError(
                f"{path} is missing required columns: " + ", ".join(missing)
            )
        rows = list(reader)
    return rows


def _as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer value for {field}: {value!r}") from exc


def query_lightcurve_availability(
    targets: list[dict[str, str]],
    matches: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Use the DR24 objectid index to check for light-curve rows."""
    if not targets:
        raise ValueError("target catalogue is empty")
    target_ids = [str(row["external_id"]).strip() for row in targets]
    if any(not value for value in target_ids):
        raise ValueError("target catalogue contains an empty external_id")
    if len(set(target_ids)) != len(target_ids):
        raise ValueError("target catalogue contains duplicate external_id")

    oid_to_matches: dict[int, list[dict[str, str]]] = {}
    for match in matches:
        external_id = str(match["external_id"]).strip()
        if external_id not in set(target_ids):
            raise ValueError(f"match references unknown target: {external_id}")
        oid = _as_int(match["oid"], "oid")
        if oid <= 0:
            raise ValueError(f"invalid OID: {oid}")
        oid_to_matches.setdefault(oid, []).append(match)

    requested_oids = sorted(oid_to_matches)
    if not requested_oids:
        return (
            [],
            [
                {
                    "external_id": target_id,
                    "objects_table_oid_count": 0,
                    "lightcurve_row_count": 0,
                    "missing_lightcurve_oid_count": 0,
                    "total_nepochs": 0,
                    "zg_oids": 0,
                    "zr_oids": 0,
                    "zi_oids": 0,
                }
                for target_id in target_ids
            ],
            {
                "schema_version": "ztf-dr24-lightcurve-availability-v1",
                "source": "IRSA ZTF DR24 Lightcurves HATS",
                "catalog_uri": DR24_LIGHTCURVES_HATS,
                "query_timestamp_utc": datetime.now(UTC).isoformat(),
                "code_version": os.environ.get("GITHUB_SHA", "unknown"),
                "target_count": len(targets),
                "requested_oid_count": 0,
                "found_oid_count": 0,
                "missing_oid_count": 0,
                "index_column": "objectid",
                "index_search_performed": False,
                "interpretation": "No Objects Table OIDs were supplied.",
            },
        )

    try:
        import lsdb
    except ImportError as exc:
        raise RuntimeError(
            "Install the spatial-catalog dependencies: pip install lsdb==0.10.4 s3fs"
        ) from exc

    catalog = lsdb.open_catalog(
        DR24_LIGHTCURVES_HATS,
        columns=list(REQUIRED_LIGHTCURVE_COLUMNS),
    )
    available_columns = set(catalog.all_columns)
    missing = sorted(set(REQUIRED_LIGHTCURVE_COLUMNS) - available_columns)
    if missing:
        raise ValueError(
            "DR24 Lightcurves schema is missing required columns: "
            + ", ".join(missing)
        )

    index_columns = list(catalog.hc_collection.all_indexes.keys())
    if "objectid" not in index_columns:
        raise ValueError(
            "DR24 Lightcurves HATS catalogue has no objectid index; "
            "refusing an unindexed fallback scan"
        )

    result = catalog.id_search(values={"objectid": requested_oids})
    frame = result.compute()
    if "objectid" not in frame.columns:
        frame = frame.reset_index()
    if "objectid" not in frame.columns:
        raise ValueError("DR24 id_search result has no objectid column")
    if frame["objectid"].duplicated().any():
        duplicates = sorted(
            int(value)
            for value in frame.loc[
                frame["objectid"].duplicated(keep=False), "objectid"
            ].tolist()
        )
        raise ValueError(
            "DR24 Lightcurves returned duplicate objectid rows: "
            + ", ".join(map(str, duplicates[:20]))
        )

    found: dict[int, dict[str, Any]] = {}
    for row in frame.to_dict(orient="records"):
        oid = _as_int(row["objectid"], "objectid")
        if oid not in oid_to_matches:
            raise ValueError(f"DR24 returned an unrequested OID: {oid}")
        filter_id = _as_int(row["filterid"], "filterid")
        nepochs = _as_int(row["nepochs"], "nepochs")
        if nepochs < 0:
            raise ValueError(f"negative nepochs for OID {oid}")
        found[oid] = {"filterid": filter_id, "nepochs": nepochs}

    oid_rows: list[dict[str, Any]] = []
    for oid in requested_oids:
        source_matches = oid_to_matches[oid]
        external_ids = sorted({str(row["external_id"]) for row in source_matches})
        filtercodes = sorted({str(row["filtercode"]) for row in source_matches})
        fids = sorted({_as_int(row["fid"], "fid") for row in source_matches})
        if len(filtercodes) != 1 or len(fids) != 1:
            raise ValueError(
                f"Objects Table metadata is inconsistent for OID {oid}"
            )
        object_filtercode = filtercodes[0]
        object_fid = fids[0]
        lightcurve = found.get(oid)
        filter_id = lightcurve["filterid"] if lightcurve else None
        nepochs = lightcurve["nepochs"] if lightcurve else None
        expected_filtercode = FILTER_ID_TO_CODE.get(filter_id) if filter_id else None
        metadata_consistent = (
            filter_id is None
            or (filter_id == object_fid and expected_filtercode == object_filtercode)
        )
        if not metadata_consistent:
            raise ValueError(
                f"filter metadata mismatch for OID {oid}: "
                f"Objects Table fid/filtercode={object_fid}/{object_filtercode}, "
                f"Lightcurves filterid={filter_id}"
            )
        oid_rows.append(
            {
                "oid": str(oid),
                "external_ids": ";".join(external_ids),
                "objects_table_filtercode": object_filtercode,
                "objects_table_fid": object_fid,
                "lightcurve_row_found": lightcurve is not None,
                "lightcurve_filterid": "" if filter_id is None else filter_id,
                "nepochs": "" if nepochs is None else nepochs,
                "has_photometry": bool(nepochs is not None and nepochs > 0),
                "filter_metadata_consistent": metadata_consistent,
            }
        )

    target_rows: list[dict[str, Any]] = []
    for target_id in target_ids:
        target_oids = [
            oid
            for oid, source_matches in oid_to_matches.items()
            if any(str(row["external_id"]) == target_id for row in source_matches)
        ]
        found_oids = [oid for oid in target_oids if oid in found]
        total_nepochs = sum(found[oid]["nepochs"] for oid in found_oids)
        target_rows.append(
            {
                "external_id": target_id,
                "objects_table_oid_count": len(target_oids),
                "lightcurve_row_count": len(found_oids),
                "missing_lightcurve_oid_count": len(target_oids) - len(found_oids),
                "total_nepochs": total_nepochs,
                "zg_oids": sum(
                    oid_rows_by_oid["objects_table_filtercode"] == "zg"
                    for oid_rows_by_oid in oid_rows
                    if int(oid_rows_by_oid["oid"]) in target_oids
                    and oid_rows_by_oid["lightcurve_row_found"]
                ),
                "zr_oids": sum(
                    oid_rows_by_oid["objects_table_filtercode"] == "zr"
                    for oid_rows_by_oid in oid_rows
                    if int(oid_rows_by_oid["oid"]) in target_oids
                    and oid_rows_by_oid["lightcurve_row_found"]
                ),
                "zi_oids": sum(
                    oid_rows_by_oid["objects_table_filtercode"] == "zi"
                    for oid_rows_by_oid in oid_rows
                    if int(oid_rows_by_oid["oid"]) in target_oids
                    and oid_rows_by_oid["lightcurve_row_found"]
                ),
            }
        )

    schema_columns = sorted(available_columns)
    schema_payload = json.dumps(
        schema_columns, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    metadata = {
        "schema_version": "ztf-dr24-lightcurve-availability-v1",
        "source": "IRSA ZTF DR24 Lightcurves HATS",
        "catalog_uri": DR24_LIGHTCURVES_HATS,
        "query_timestamp_utc": datetime.now(UTC).isoformat(),
        "code_version": os.environ.get("GITHUB_SHA", "unknown"),
        "runtime": {
            "python": sys.version.split()[0],
            "lsdb": _package_version("lsdb"),
            "s3fs": _package_version("s3fs"),
        },
        "catalog_schema": {
            "available_columns": schema_columns,
            "available_column_count": len(schema_columns),
            "columns_sha256": hashlib.sha256(schema_payload).hexdigest(),
        },
        "index_column": "objectid",
        "index_columns": index_columns,
        "index_search_performed": True,
        "target_count": len(targets),
        "requested_oid_count": len(requested_oids),
        "found_oid_count": len(found),
        "missing_oid_count": len(requested_oids) - len(found),
        "oids_with_photometry": sum(
            row["has_photometry"] for row in oid_rows
        ),
        "filter_id_to_code": FILTER_ID_TO_CODE,
        "interpretation": (
            "An indexed Lightcurves row confirms a time-series record exists. "
            "It does not certify clean epochs, minimum cadence, or scientific usability."
        ),
    }
    return oid_rows, target_rows, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    targets = _read_csv(args.targets, REQUIRED_TARGET_COLUMNS)
    matches = _read_csv(args.matches, REQUIRED_MATCH_COLUMNS)
    oid_rows, target_rows, metadata = query_lightcurve_availability(
        targets, matches
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    oid_path = args.output_dir / "lightcurve_availability_by_oid.csv"
    with oid_path.open("w", newline="", encoding="utf-8") as handle:
        fields = (
            "oid",
            "external_ids",
            "objects_table_filtercode",
            "objects_table_fid",
            "lightcurve_row_found",
            "lightcurve_filterid",
            "nepochs",
            "has_photometry",
            "filter_metadata_consistent",
        )
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(oid_rows)

    target_path = args.output_dir / "lightcurve_availability_by_bts.csv"
    with target_path.open("w", newline="", encoding="utf-8") as handle:
        fields = (
            "external_id",
            "objects_table_oid_count",
            "lightcurve_row_count",
            "missing_lightcurve_oid_count",
            "total_nepochs",
            "zg_oids",
            "zr_oids",
            "zi_oids",
        )
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(target_rows)

    metadata["inputs"] = {
        "targets_sha256": hashlib.sha256(args.targets.read_bytes()).hexdigest(),
        "matches_sha256": hashlib.sha256(args.matches.read_bytes()).hexdigest(),
    }
    metadata["outputs"] = {
        "by_oid": {
            "path": oid_path.name,
            "rows": len(oid_rows),
            "sha256": hashlib.sha256(oid_path.read_bytes()).hexdigest(),
        },
        "by_bts": {
            "path": target_path.name,
            "rows": len(target_rows),
            "sha256": hashlib.sha256(target_path.read_bytes()).hexdigest(),
        },
    }
    manifest_path = args.output_dir / "lightcurve_availability_manifest.json"
    manifest_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"requested_oids={metadata['requested_oid_count']}")
    print(f"found_oids={metadata['found_oid_count']}")
    print(f"missing_oids={metadata['missing_oid_count']}")
    print(f"oids_with_photometry={metadata['oids_with_photometry']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
