#!/usr/bin/env python3
"""Reproducible smoke test against the published ZTF IC 10 catalog.

This validates external tabular ingestion, provenance hashes, identifier
preservation, and the paper's cross-band SourceID relation. It does not claim
to validate raw-light-curve feature extraction or classifier accuracy.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

from ztf_classifier.application.ingestion import DataIngestionService, ImportRequest

BASE = "https://zenodo.org/records/14979711/files"
FILES = {
    "df_zr.csv": {
        "md5": "0589a1bda6abd960145ad6116275851d",
        "required": ("SourceID", "OID", "filter", "var", "lc_var"),
    },
    "df_zg.csv": {
        "md5": "3cb5b49b1064a2bac0bc7ab9201fa0e0",
        "required": ("SourceID", "OID", "filter", "var", "lc_var"),
    },
    "df_color.csv": {
        "md5": "6c7d0c8cb21515eea093fd861d83aa47",
        "required": ("SourceID", "var"),
    },
}


def fetch_verified(name: str, target: Path) -> dict[str, object]:
    url = f"{BASE}/{name}?download=1"
    request = urllib.request.Request(
        url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]["md5"]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    target.write_bytes(payload)
    return {"url": url, "bytes": len(payload), "md5": md5,
            "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> None:
    report: dict[str, object] = {
        "dataset": "The data for ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "validation_scope": [
            "publisher MD5 verification",
            "application CSV ingestion",
            "required-column and row-count checks",
            "content SHA-256 provenance",
            "SourceID/OID preservation",
            "cross-band source membership consistency",
        ],
        "limitations": [
            "This is a published summary catalog, not raw photometry.",
            "This does not test the model's scientific accuracy or feature extraction.",
        ],
        "files": {},
    }
    imported: dict[str, pd.DataFrame] = {}
    with tempfile.TemporaryDirectory(prefix="ztf-ic10-validation-") as tmp:
        root = Path(tmp)
        service = DataIngestionService()
        for name, spec in FILES.items():
            path = root / name
            integrity = fetch_verified(name, path)
            result = service.import_file(
                ImportRequest(
                    path=path,
                    source_id=f"zenodo-14979711:{name}",
                    required_columns=spec["required"],
                )
            )
            frame = result.data
            if result.row_count != len(frame) or result.row_count == 0:
                raise RuntimeError(f"{name}: invalid imported row count")
            if result.content_sha256 != integrity["sha256"]:
                raise RuntimeError(f"{name}: application SHA-256 provenance mismatch")
            if frame["SourceID"].isna().any():
                raise RuntimeError(f"{name}: null SourceID values")
            if name != "df_color.csv" and frame["OID"].isna().any():
                raise RuntimeError(f"{name}: null OID values")
            imported[name] = frame
            report["files"][name] = {
                **integrity,
                "rows": result.row_count,
                "columns": list(result.columns),
                "unique_source_ids": int(frame["SourceID"].nunique()),
                "source_type": result.source.source_type,
                "source_id": result.source.source_id,
                "sha256_from_application": result.content_sha256,
            }

        r_ids = set(imported["df_zr.csv"]["SourceID"].astype("string"))
        g_ids = set(imported["df_zg.csv"]["SourceID"].astype("string"))
        color_ids = set(imported["df_color.csv"]["SourceID"].astype("string"))
        common_band_ids = r_ids & g_ids
        unexpected_color_ids = color_ids - common_band_ids
        if unexpected_color_ids:
            sample = sorted(unexpected_color_ids)[:10]
            raise RuntimeError(
                "Color catalog contains SourceIDs absent from one or both band "
                f"catalogs; count={len(unexpected_color_ids)}, sample={sample}"
            )
        report["cross_band"] = {
            "r_unique_source_ids": len(r_ids),
            "g_unique_source_ids": len(g_ids),
            "r_g_intersection_source_ids": len(common_band_ids),
            "color_unique_source_ids": len(color_ids),
            "color_ids_not_in_both_bands": len(unexpected_color_ids),
            "membership_check": "PASS",
        }

    report["result"] = "PASS"
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
