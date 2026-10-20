#!/usr/bin/env python3
"""Compare published IC 10 color-table photometry with single-OID band rows.

This is a catalog-internal numerical consistency check, not an independent
raw-photometry re-extraction or a classifier-accuracy evaluation.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

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
        frames: dict[str, pd.DataFrame] = {}
        integrity: dict[str, object] = {}
        for name in FILES:
            frames[name], integrity[name] = download(name, root)
        zr, zg, color = frames["df_zr.csv"], frames["df_zg.csv"], frames["df_color.csv"]

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
        report["eligible_source_ids"] = len(common)
        report["compared_numeric_values"] = compared_values
        report["comparisons"] = comparisons
        report["mismatch_examples_capped_at_20"] = failures[:20]
        report["result"] = "PASS" if not failures else "FAIL"
        if failures:
            raise RuntimeError(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
