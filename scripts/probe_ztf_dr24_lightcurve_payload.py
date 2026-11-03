#!/usr/bin/env python3
"""Probe a strictly bounded set of ZTF DR24 nested light-curve payloads.

This is an evidence-gathering tool. It does not normalize photometry for the
production feature pipeline, combine OIDs, or infer physical-source identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DR24_LIGHTCURVES_HATS = "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats"
PAYLOAD_COLUMNS = ("hmjd", "mag", "magerr", "clrcoeff", "catflags")
CATALOG_COLUMNS = (
    "objectid", "filterid", "fieldid", "rcid", "objra", "objdec",
    "nepochs", "lightcurve",
)
MAX_OIDS = 10


def _version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def parse_oids(value: str, *, maximum: int = 5) -> list[int]:
    """Parse unique positive OIDs and enforce a hard upper bound."""
    try:
        values = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise ValueError("OID list must contain comma-separated integers.") from exc
    if not values:
        raise ValueError("At least one OID is required.")
    if len(values) > min(maximum, MAX_OIDS):
        raise ValueError(f"Probe is limited to {min(maximum, MAX_OIDS)} OIDs.")
    if any(value <= 0 for value in values):
        raise ValueError("OIDs must be positive integers.")
    if len(values) != len(set(values)):
        raise ValueError("Duplicate OIDs are not allowed.")
    return values


def _nested_frame(value: Any, oid: int) -> pd.DataFrame:
    """Convert the HATS nested payload to a DataFrame without guessing fields."""
    if value is None:
        raise ValueError(f"DR24 OID {oid} has a null lightcurve payload.")
    try:
        frame = value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    except Exception as exc:
        raise ValueError(f"Cannot decode nested lightcurve payload for OID {oid}.") from exc
    missing = sorted(set(PAYLOAD_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(
            f"DR24 OID {oid} payload is missing columns: {', '.join(missing)}"
        )
    return frame.loc[:, list(PAYLOAD_COLUMNS)].reset_index(drop=True)


def _json_scalar(value: Any) -> Any:
    """Convert scalar values to deterministic JSON-safe Python values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def canonical_payload(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], str]:
    """Return ordered payload rows and their canonical SHA-256."""
    records = [
        {column: _json_scalar(value) for column, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]
    encoded = json.dumps(
        records, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return records, hashlib.sha256(encoded).hexdigest()


def summarize_payload(
    oid: int,
    metadata: dict[str, Any],
    payload: pd.DataFrame,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Summarize one OID and retain its bounded epoch rows for inspection."""
    records, payload_hash = canonical_payload(payload)
    hmjd = pd.to_numeric(payload["hmjd"], errors="coerce")
    mag = pd.to_numeric(payload["mag"], errors="coerce")
    magerr = pd.to_numeric(payload["magerr"], errors="coerce")
    catflags = pd.to_numeric(payload["catflags"], errors="coerce")
    hmjd_finite = hmjd[np.isfinite(hmjd)]
    mag_finite = mag[np.isfinite(mag)]
    magerr_finite = magerr[np.isfinite(magerr)]

    flag_counts: dict[str, int] = {}
    for value, count in catflags.value_counts(dropna=False).items():
        if pd.isna(value):
            key = "null"
        elif float(value).is_integer():
            key = str(int(value))
        else:
            key = str(value)
        flag_counts[key] = int(count)

    summary = {
        "objectid": oid,
        "filterid": int(metadata["filterid"]),
        "fieldid": int(metadata["fieldid"]),
        "rcid": int(metadata["rcid"]),
        "objra": float(metadata["objra"]),
        "objdec": float(metadata["objdec"]),
        "catalog_nepochs": int(metadata["nepochs"]),
        "payload_rows": len(payload),
        "payload_dtypes": {name: str(dtype) for name, dtype in payload.dtypes.items()},
        "epoch_count_matches": int(metadata["nepochs"]) == len(payload),
        "canonical_payload_sha256": payload_hash,
        "hmjd_finite_count": len(hmjd_finite),
        "hmjd_min": None if hmjd_finite.empty else float(hmjd_finite.min()),
        "hmjd_max": None if hmjd_finite.empty else float(hmjd_finite.max()),
        "mag_finite_count": len(mag_finite),
        "magerr_finite_count": len(magerr_finite),
        "magerr_positive_count": int((magerr_finite > 0).sum()),
        "catflags_counts": flag_counts,
        "clean_catflags_zero_count": int((catflags == 0).sum()),
        "photometry_interpretation": (
            "Raw DR24 payload values retained. No color correction, time-system "
            "conversion, quality selection, or production normalization applied."
        ),
    }
    epochs = [
        {
            "objectid": oid,
            "filterid": summary["filterid"],
            "fieldid": summary["fieldid"],
            "rcid": summary["rcid"],
            **record,
        }
        for record in records
    ]
    return summary, epochs


def probe(oids: list[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Retrieve only the requested OIDs through the published objectid index."""
    try:
        import lsdb
    except ImportError as exc:
        raise RuntimeError("Install lsdb==0.10.4 and s3fs to run this probe.") from exc

    catalog = lsdb.open_catalog(DR24_LIGHTCURVES_HATS, columns=list(CATALOG_COLUMNS))
    available = set(catalog.all_columns)
    missing = sorted(set(CATALOG_COLUMNS) - available)
    if missing:
        raise ValueError("DR24 HATS schema missing columns: " + ", ".join(missing))
    indexes = list(catalog.hc_collection.all_indexes.keys())
    if "objectid" not in indexes:
        raise ValueError("DR24 Lightcurves has no objectid index; refusing full scan.")

    result = catalog.id_search(values={"objectid": oids}).compute()
    if "objectid" not in result.columns:
        result = result.reset_index()
    if "objectid" not in result.columns:
        raise ValueError("DR24 id_search result has no objectid column.")
    if result["objectid"].duplicated().any():
        raise ValueError("DR24 returned duplicate objectid rows.")

    returned = {int(value) for value in result["objectid"].tolist()}
    unexpected = sorted(returned - set(oids))
    if unexpected:
        raise ValueError(f"DR24 returned unrequested OIDs: {unexpected}")

    summaries: list[dict[str, Any]] = []
    epoch_rows: list[dict[str, Any]] = []
    for row in result.to_dict(orient="records"):
        oid = int(row["objectid"])
        payload = _nested_frame(row["lightcurve"], oid)
        summary, epochs = summarize_payload(oid, row, payload)
        summaries.append(summary)
        epoch_rows.extend(epochs)

    schema_columns = sorted(str(column) for column in available)
    schema_bytes = json.dumps(schema_columns, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    metadata = {
        "schema_version": "ztf-dr24-lightcurve-payload-probe-v1",
        "source": "IRSA ZTF DR24 Lightcurves HATS",
        "catalog_uri": DR24_LIGHTCURVES_HATS,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "code_revision": os.environ.get("GITHUB_SHA", "unknown"),
        "runtime": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "lsdb": _version("lsdb"),
            "s3fs": _version("s3fs"),
        },
        "index_column": "objectid",
        "index_columns": indexes,
        "catalog_schema": {
            "available_columns": schema_columns,
            "column_count": len(schema_columns),
            "column_names_sha256": hashlib.sha256(schema_bytes).hexdigest(),
        },
        "requested_oids": oids,
        "returned_oids": sorted(returned),
        "missing_oids": sorted(set(oids) - returned),
        "summary_count": len(summaries),
        "epoch_row_count": len(epoch_rows),
        "limitations": [
            "This is a bounded payload inspection, not production acquisition.",
            "No astrophysical cross-OID grouping or identity inference is performed.",
            "No photometry normalization or scientific quality acceptance is performed.",
            "HMJD is retained as HMJD; it is not relabeled as MJD.",
            "The raw DR24 magnitude and color coefficient are retained separately.",
        ],
    }
    return summaries, epoch_rows, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oids", required=True, help="Comma-separated DR24 object IDs.")
    parser.add_argument("--max-oids", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.max_oids <= MAX_OIDS:
        parser.error(f"--max-oids must be between 1 and {MAX_OIDS}.")
    oids = parse_oids(args.oids, maximum=args.max_oids)
    summaries, epochs, manifest = probe(oids)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "dr24_lightcurve_payload_summary.json"
    summary_path.write_text(
        json.dumps(summaries, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    epoch_path = args.output_dir / "dr24_lightcurve_payload_epochs.csv"
    pd.DataFrame(epochs).to_csv(epoch_path, index=False, lineterminator="\n")
    manifest["outputs"] = {
        "summary": {
            "path": summary_path.name,
            "sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        },
        "epochs": {
            "path": epoch_path.name,
            "rows": len(epochs),
            "sha256": hashlib.sha256(epoch_path.read_bytes()).hexdigest(),
        },
    }
    manifest_path = args.output_dir / "dr24_lightcurve_payload_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"requested={len(oids)} returned={len(summaries)} epochs={len(epochs)}")
    print(f"missing_oids={manifest['missing_oids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
