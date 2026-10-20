#!/usr/bin/env python3
"""Diagnose SourceID/OID multiplicity behind IC 10 catalog comparisons.

This is a read-only catalog-structure diagnostic. It does not re-extract raw
photometry, infer scientific membership, or evaluate classifier accuracy.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

BASE = "https://zenodo.org/records/14979711/files"
FILES = {
    "df_zr.csv": "0589a1bda6abd960145ad6116275851d",
    "df_zg.csv": "3cb5b49b1064a2bac0bc7ab9201fa0e0",
    "df_color.csv": "6c7d0c8cb21515eea093fd861d83aa47",
}


def load(name: str, root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{BASE}/{name}?download=1"
    req = urllib.request.Request(url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = response.read()
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    path = root / name
    path.write_bytes(payload)
    frame = pd.read_csv(path, dtype={"SourceID": "string", "OID": "string"})
    if "SourceID" not in frame or frame["SourceID"].isna().any():
        raise RuntimeError(f"{name}: missing or null SourceID")
    metadata = {
        "url": url,
        "bytes": len(payload),
        "md5": md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": int(len(frame)),
        "unique_source_ids": int(frame["SourceID"].nunique()),
    }
    return frame, metadata


def band_summary(frame: pd.DataFrame) -> dict[str, object]:
    if "OID" not in frame:
        return {"oid_column_present": False}
    counts = frame.groupby("SourceID", dropna=False)["OID"].nunique(dropna=False)
    hist = counts.value_counts().sort_index()
    multi = counts[counts > 1]
    return {
        "oid_column_present": True,
        "unique_oids": int(frame["OID"].nunique(dropna=True)),
        "source_ids_with_one_oid": int((counts == 1).sum()),
        "source_ids_with_multiple_oids": int((counts > 1).sum()),
        "source_ids_with_null_oid": int(frame.groupby("SourceID")["OID"].apply(lambda s: s.isna().any()).sum()),
        "oids_per_source_id_histogram": {str(int(k)): int(v) for k, v in hist.items()},
        "multi_oid_source_id_examples": [
            {"SourceID": str(source_id), "oid_count": int(count)}
            for source_id, count in multi.head(20).items()
        ],
    }


def main() -> None:
    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "purpose": "Explain the eligible sample size for band-vs-color summary-statistic comparison",
        "scope_limit": "Catalog structure only; no raw photometry re-extraction or classifier evaluation",
        "files": {},
    }
    frames: dict[str, pd.DataFrame] = {}
    with TemporaryDirectory(prefix="ztf-ic10-join-diagnostics-") as tmp:
        root = Path(tmp)
        for name in FILES:
            frame, meta = load(name, root)
            frames[name] = frame
            report["files"][name] = {**meta, "structure": band_summary(frame)}
        r = frames["df_zr.csv"]
        g = frames["df_zg.csv"]
        color = frames["df_color.csv"]
        r_ids, g_ids, c_ids = (set(f["SourceID"].astype("string")) for f in (r, g, color))
        r_single = set(r.groupby("SourceID")["OID"].nunique().loc[lambda s: s == 1].index.astype("string"))
        g_single = set(g.groupby("SourceID")["OID"].nunique().loc[lambda s: s == 1].index.astype("string"))
        report["joins"] = {
            "r_g_intersection_source_ids": len(r_ids & g_ids),
            "color_ids": len(c_ids),
            "color_ids_present_in_both_bands": len(c_ids & r_ids & g_ids),
            "color_ids_missing_from_r": len(c_ids - r_ids),
            "color_ids_missing_from_g": len(c_ids - g_ids),
            "ids_single_oid_in_both_bands": len(r_single & g_single),
            "color_ids_single_oid_in_both_bands": len(c_ids & r_single & g_single),
            "color_ids_rejected_due_to_multi_oid_or_missing_band": len(c_ids - (r_single & g_single)),
        }
    report["result"] = "PASS"
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
