#!/usr/bin/env python3
"""Compare published IC 10 color-table photometry with single-OID band rows.

This is a catalog-internal numerical consistency check, not an independent
raw-photometry re-extraction or a classifier-accuracy evaluation.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from astropy.table import Table

BASE = "https://zenodo.org/records/14979711/files"
FILES = {
    "df_zr.csv": "0589a1bda6abd960145ad6116275851d",
    "df_zg.csv": "3cb5b49b1064a2bac0bc7ab9201fa0e0",
    "df_color.csv": "6c7d0c8cb21515eea093fd861d83aa47",
}
TOLERANCE_MAG = 1e-6
FIELDS = ("mean", "std", "min", "max")


def download(name: str, root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{BASE}/{name}?download=1"
    request = urllib.request.Request(
        url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    path = root / name
    path.write_bytes(payload)
    frame = pd.read_csv(path)
    return frame, {
        "url": url,
        "bytes": len(payload),
        "md5": md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": len(frame),
    }


def download_ecsv(
    name: str, root: Path, record_files: dict[str, dict[str, object]]
) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{BASE}/{name}?download=1"
    file_record = record_files.get(name)
    if file_record is None:
        raise RuntimeError(f"{name}: file is absent from Zenodo record metadata")
    request = urllib.request.Request(
        url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    checksum = str(file_record.get("checksum", ""))
    expected_md5 = checksum.removeprefix("md5:")
    actual_md5 = hashlib.md5(payload).hexdigest()
    if checksum.startswith("md5:") and actual_md5 != expected_md5:
        raise RuntimeError(f"{name}: Zenodo API MD5 mismatch: {actual_md5}")
    path = root / name
    path.write_bytes(payload)
    frame = Table.read(io.BytesIO(payload), format="ascii.ecsv").to_pandas()
    return frame, {
        "url": url,
        "bytes": len(payload),
        "zenodo_checksum": checksum or None,
        "md5": actual_md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": int(len(frame)),
        "unique_oids": int(frame["OID"].nunique()) if "OID" in frame else None,
    }


def normalize_oid(value: object) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError, OverflowError):
        return str(value)


def compare_csv_to_ecsv(
    csv_frame: pd.DataFrame, ecsv_frame: pd.DataFrame, band: str
) -> dict[str, object]:
    fields = ("numobs", "mean", "std", "min", "max")
    required = {"OID", "SourceID", *fields}
    for label, frame in (("CSV", csv_frame), ("ECSV", ecsv_frame)):
        missing = required - set(frame.columns)
        if missing:
            raise RuntimeError(f"{band} {label}: missing columns {sorted(missing)}")
    left = csv_frame.copy()
    right = ecsv_frame.copy()
    left["_oid_key"] = left["OID"].map(normalize_oid)
    right["_oid_key"] = right["OID"].map(normalize_oid)
    left = left.drop_duplicates("_oid_key", keep=False).set_index("_oid_key")
    right = right.drop_duplicates("_oid_key", keep=False).set_index("_oid_key")
    common = sorted(set(left.index) & set(right.index))
    csv_only = sorted(set(left.index) - set(right.index))
    ecsv_only = sorted(set(right.index) - set(left.index))
    comparisons: dict[str, object] = {}
    mismatches: list[dict[str, object]] = []
    for field in fields:
        a = pd.to_numeric(left.loc[common, field], errors="coerce")
        b = pd.to_numeric(right.loc[common, field], errors="coerce")
        valid = np.isfinite(a.to_numpy(dtype=float)) & np.isfinite(b.to_numpy(dtype=float))
        delta = np.abs(a.to_numpy(dtype=float)[valid] - b.to_numpy(dtype=float)[valid])
        if field == "numobs":
            bad = np.flatnonzero(valid & (a.to_numpy(dtype=float) != b.to_numpy(dtype=float)))
            tolerance = 0.0
        else:
            bad = np.flatnonzero(valid & (np.abs(a.to_numpy(dtype=float) - b.to_numpy(dtype=float)) > TOLERANCE_MAG))
            tolerance = TOLERANCE_MAG
        comparisons[field] = {
            "finite_pairs": int(valid.sum()),
            "tolerance": tolerance,
            "mismatches": int(len(bad)),
            "max_absolute_delta": float(delta.max()) if len(delta) else None,
        }
        for idx in bad[:20]:
            mismatches.append({
                "band": band,
                "OID": common[int(idx)],
                "field": field,
                "csv_value": float(a.iloc[int(idx)]),
                "ecsv_value": float(b.iloc[int(idx)]),
                "absolute_delta": float(abs(a.iloc[int(idx)] - b.iloc[int(idx)])),
            })
    source_id_mismatches = []
    for oid in common:
        if str(left.loc[oid, "SourceID"]) != str(right.loc[oid, "SourceID"]):
            source_id_mismatches.append({
                "OID": oid,
                "csv_SourceID": str(left.loc[oid, "SourceID"]),
                "ecsv_SourceID": str(right.loc[oid, "SourceID"]),
            })
    return {
        "csv_rows": int(len(csv_frame)),
        "ecsv_rows": int(len(ecsv_frame)),
        "csv_unique_oids": int(csv_frame["OID"].map(normalize_oid).nunique()),
        "ecsv_unique_oids": int(ecsv_frame["OID"].map(normalize_oid).nunique()),
        "common_oids": len(common),
        "csv_only_oids_sample": csv_only[:20],
        "ecsv_only_oids_sample": ecsv_only[:20],
        "source_id_mismatches": len(source_id_mismatches),
        "source_id_mismatch_examples": source_id_mismatches[:20],
        "field_comparisons": comparisons,
        "mismatch_examples_capped_at_20": mismatches[:20],
        "pass": not csv_only and not ecsv_only and not source_id_mismatches and not mismatches,
    }


def main() -> None:
    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "test": "color-table vs band-table photometry for unambiguous single-OID SourceIDs",
        "tolerance_magnitude": TOLERANCE_MAG,
        "scope_limit": (
            "Catalog-internal consistency only. It does not re-extract raw photometry "
            "and does not validate the 15-class model."
        ),
    }
    with TemporaryDirectory(prefix="ztf-ic10-numeric-") as tmp:
        root = Path(tmp)
        metadata_url = "https://zenodo.org/api/records/14979711"
        metadata_request = urllib.request.Request(
            metadata_url,
            headers={"User-Agent": "ztf-classifier-independent-validation/1.0"},
        )
        with urllib.request.urlopen(metadata_request, timeout=60) as response:
            metadata_payload = response.read()
        record = json.loads(metadata_payload)
        record_files = {
            str(item["key"]): item for item in record.get("files", [])
            if isinstance(item, dict) and "key" in item
        }
        frames: dict[str, pd.DataFrame] = {}
        integrity: dict[str, object] = {}
        for name in FILES:
            frames[name], integrity[name] = download(name, root)
        ecsv_frames: dict[str, pd.DataFrame] = {}
        ecsv_integrity: dict[str, object] = {}
        for band, name in (("r", "t_zr_20250225.ecsv"), ("g", "t_zg_20250225.ecsv")):
            ecsv_frames[band], ecsv_integrity[name] = download_ecsv(name, root, record_files)
        zr, zg, color = frames["df_zr.csv"], frames["df_zg.csv"], frames["df_color.csv"]
        ecsv_export_comparisons = {
            "r": compare_csv_to_ecsv(zr, ecsv_frames["r"], "r"),
            "g": compare_csv_to_ecsv(zg, ecsv_frames["g"], "g"),
        }

        required = {
            "df_zr.csv": {"SourceID", "OID", *FIELDS},
            "df_zg.csv": {"SourceID", "OID", *FIELDS},
            "df_color.csv": {"SourceID", *[f"{field}_mag_{band}" for field in FIELDS for band in ("g", "r")]},
        }
        for name, frame in frames.items():
            missing = required[name] - set(frame.columns)
            if missing:
                raise RuntimeError(f"{name}: required numeric columns absent: {sorted(missing)}")

        # A SourceID can map to multiple OIDs. Restrict comparison to exactly
        # one distinct OID in each band to avoid mixing non-identical lightcurves.
        def single_oid_rows(frame: pd.DataFrame) -> pd.DataFrame:
            counts = frame.groupby("SourceID", dropna=False)["OID"].nunique()
            ids = set(counts[counts == 1].index.astype(str))
            one = frame[frame["SourceID"].astype(str).isin(ids)].copy()
            if one["SourceID"].astype(str).duplicated().any():
                # Multiple duplicate rows for the same OID are still ambiguous.
                one = one.sort_values("OID").drop_duplicates("SourceID", keep=False)
            return one

        zr_one = single_oid_rows(zr)
        zg_one = single_oid_rows(zg)
        color = color.copy()
        color["SourceID"] = color["SourceID"].astype(str)
        zr_one["SourceID"] = zr_one["SourceID"].astype(str)
        zg_one["SourceID"] = zg_one["SourceID"].astype(str)
        zr_map = zr_one.set_index("SourceID")
        zg_map = zg_one.set_index("SourceID")
        color_map = color.drop_duplicates("SourceID", keep=False).set_index("SourceID")

        common = sorted(set(color_map.index) & set(zr_map.index) & set(zg_map.index))
        if not common:
            raise RuntimeError("No SourceIDs eligible for unambiguous cross-table comparison")

        comparisons: dict[str, object] = {}
        failures: list[dict[str, object]] = []
        compared_values = 0
        for band, band_map in (("r", zr_map), ("g", zg_map)):
            per_field: dict[str, object] = {}
            for field in FIELDS:
                left = pd.to_numeric(color_map.loc[common, f"{field}_mag_{band}"], errors="coerce")
                right = pd.to_numeric(band_map.loc[common, field], errors="coerce")
                valid = np.isfinite(left.to_numpy(dtype=float)) & np.isfinite(right.to_numpy(dtype=float))
                delta = np.abs(left.to_numpy(dtype=float)[valid] - right.to_numpy(dtype=float)[valid])
                compared_values += int(valid.sum())
                bad = np.flatnonzero(valid & (np.abs(left.to_numpy(dtype=float) - right.to_numpy(dtype=float)) > TOLERANCE_MAG))
                for idx in bad[:20]:
                    failures.append({
                        "band": band, "field": field, "SourceID": common[int(idx)],
                        "color_table_value": float(left.iloc[int(idx)]),
                        "band_table_value": float(right.iloc[int(idx)]),
                        "absolute_delta": float(abs(left.iloc[int(idx)] - right.iloc[int(idx)])),
                    })
                per_field[field] = {
                    "finite_pairs": int(valid.sum()),
                    "max_absolute_delta_mag": float(delta.max()) if len(delta) else None,
                    "mismatches_over_tolerance": int(len(bad)),
                }
            comparisons[band] = per_field

        report["publisher_files"] = integrity
        report["zenodo_record_metadata"] = {
            "url": metadata_url,
            "sha256": hashlib.sha256(metadata_payload).hexdigest(),
            "record_version": record.get("metadata", {}).get("version"),
        }
        report["publisher_ecsv_source_tables"] = ecsv_integrity
        report["csv_vs_ecsv_source_table_comparison"] = ecsv_export_comparisons
        report["csv_vs_ecsv_source_tables_pass"] = all(
            result["pass"] for result in ecsv_export_comparisons.values()
        )
        report["eligible_source_ids"] = len(common)
        report["compared_numeric_values"] = compared_values
        report["comparisons"] = comparisons
        report["mismatch_examples_capped_at_20"] = failures[:20]
        report["result"] = "PASS" if not failures else "FAIL"
        if failures or not report["csv_vs_ecsv_source_tables_pass"]:
            raise RuntimeError(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
