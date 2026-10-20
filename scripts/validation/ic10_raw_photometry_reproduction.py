#!/usr/bin/env python3
"""Recompute published IC 10 per-OID magnitude statistics from raw IRSA light curves.

The sample is deterministic and deliberately includes multi-OID SourceIDs.
This checks source-backed photometry summaries; it is not classifier-accuracy
validation and does not claim to reproduce every paper filtering decision.
"""
from __future__ import annotations

import hashlib
import http.client
import io
import json
import time
import urllib.error
import urllib.parse
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
}
SAMPLE_PER_BAND = 10
SAMPLE_SEED = 20261020
TOLERANCE_MAG = 1e-3
CUTOFF_MJD = 59892.0
COLLECTION = "ztf_dr15"


def download_catalog(name: str, root: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{BASE}/{name}?download=1"
    request = urllib.request.Request(url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    path = root / name
    path.write_bytes(payload)
    frame = pd.read_csv(path, dtype={"SourceID": "string", "OID": "string"})
    required = {"SourceID", "OID", "numobs", "mean", "std", "min", "max"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"{name}: missing columns {sorted(required - set(frame.columns))}")
    return frame, {
        "url": url,
        "bytes": len(payload),
        "md5": md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": int(len(frame)),
    }


def fetch_raw_batch(oids: list[str]) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    params = [("ID", oid) for oid in sorted(set(oids))]
    params.extend(
        [
            ("COLLECTION", COLLECTION),
            ("TIME", f"58194.0 {CUTOFF_MJD}"),
            ("FORMAT", "VOTABLE"),
        ]
    )
    url = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"})
    payload = b""
    attempts = 0
    for attempt in range(4):
        attempts = attempt + 1
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read()
            break
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError):
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    table = Table.read(io.BytesIO(payload))
    frame = table.to_pandas()
    oid_column = next((column for column in frame.columns if column.lower() in {"oid", "objectid"}), None)
    if oid_column is None:
        raise RuntimeError(f"IRSA batch response lacks an OID column; columns={list(frame.columns)}")
    frame[oid_column] = frame[oid_column].astype("string")
    required = {"mjd", "mag", "catflags"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"IRSA batch response missing columns {sorted(required - set(frame.columns))}")
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    by_oid = {
        str(oid): group.drop(columns=[oid_column]).reset_index(drop=True)
        for oid, group in frame.groupby(oid_column, sort=False)
    }
    return by_oid, {
        "url": url,
        "collection": COLLECTION,
        "attempts": attempts,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "total_rows": int(len(frame)),
        "returned_oids": sorted(by_oid),
        "raw_rows_by_oid": {oid: int(len(group)) for oid, group in by_oid.items()},
    }


def stats(frame: pd.DataFrame) -> dict[str, float | int]:
    values = pd.to_numeric(frame["mag"], errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        raise RuntimeError("No finite magnitudes after filtering")
    return {
        "n": int(len(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=0)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def profiles(raw: pd.DataFrame, band: str) -> dict[str, dict[str, float | int]]:
    finite = raw[np.isfinite(raw["mjd"]) & np.isfinite(raw["mag"])].copy()
    all_rows = finite.copy()
    cutoff = finite[finite["mjd"] < CUTOFF_MJD].copy()
    good = cutoff[cutoff["catflags"] == 0].copy()
    paper = good.copy()
    if band == "r":
        for low, high in ((58481.0, 58482.0), (58472.0, 58474.0), (59032.0, 59033.0)):
            paper = paper[(paper["mjd"] < low) | (paper["mjd"] > high)]
    return {
        "raw_finite": stats(all_rows),
        "catflags_zero_before_cutoff": stats(good),
        "paper_plot_filters": stats(paper),
    }


def main() -> None:
    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "test": "published per-OID mean/std/min/max versus raw IRSA light curves from the paper's frozen DR15 collection",
        "requested_collection": COLLECTION,
        "sample_per_band": SAMPLE_PER_BAND,
        "sample_seed": SAMPLE_SEED,
        "cutoff_mjd": CUTOFF_MJD,
        "tolerance_magnitude": TOLERANCE_MAG,
        "filter_profiles": {
            "raw_finite": "finite MJD and magnitude only",
            "catflags_zero_before_cutoff": "catflags == 0 and MJD < 59892",
            "paper_plot_filters": "previous profile; for r also excludes the three MJD intervals used by authors' public plotting code",
        },
        "limitations": [
            "Only a deterministic 10-OID sample per band is recomputed.",
            "This does not evaluate classifier accuracy or reproduce all variability/period filters.",
            "If IRSA no longer serves the DR15 collection through the API, the report records a blocked historical-source probe rather than silently using current data.",
        ],
        "catalogs": {},
        "comparisons": [],
    }
    with TemporaryDirectory(prefix="ztf-ic10-raw-photometry-") as tmp:
        root = Path(tmp)
        samples: dict[str, pd.DataFrame] = {}
        for filename, band in (("df_zr.csv", "r"), ("df_zg.csv", "g")):
            frame, meta = download_catalog(filename, root)
            # A fixed pseudorandom sample avoids selecting only low SourceIDs or one catalog region.
            sample = frame.sample(n=min(SAMPLE_PER_BAND, len(frame)), random_state=SAMPLE_SEED).sort_values(["SourceID", "OID"])
            samples[band] = sample
            report["catalogs"][band] = {**meta, "unique_source_ids": int(frame["SourceID"].nunique())}
        comparisons = report["comparisons"]
        sample_rows = {
            band: samples[band].to_dict(orient="records")
            for band in ("r", "g")
        }
        requested_oids = sorted(
            {str(row["OID"]) for rows in sample_rows.values() for row in rows}
        )
        try:
            raw_by_oid, batch_meta = fetch_raw_batch(requested_oids)
        except Exception as exc:
            report["raw_batch_failure"] = {
                "collection": COLLECTION,
                "requested_oids": requested_oids,
                "error": f"{type(exc).__name__}: {exc}",
            }
            report["result"] = "BLOCKED"
            print(json.dumps(report, indent=2, sort_keys=True))
            raise SystemExit(2) from exc
        report["raw_batch"] = batch_meta
        missing_oids = [oid for oid in requested_oids if oid not in raw_by_oid]
        if missing_oids:
            report["missing_raw_oids"] = missing_oids
            report["result"] = "BLOCKED"
            print(json.dumps(report, indent=2, sort_keys=True))
            raise SystemExit(2)
        for band in ("r", "g"):
            for row in sample_rows[band]:
                oid = str(row["OID"])
                raw = raw_by_oid[oid]
                raw_meta = {
                    "collection": COLLECTION,
                    "batch_payload_sha256": batch_meta["sha256"],
                    "raw_rows": int(len(raw)),
                }
                by_profile = profiles(raw, band)
                entry: dict[str, object] = {
                    "band": band,
                    "SourceID": str(row["SourceID"]),
                    "OID": oid,
                    "catalog_numobs": int(row["numobs"]),
                    "raw": raw_meta,
                    "published": {key: float(row[key]) for key in ("mean", "std", "min", "max")},
                    "profiles": {},
                }
                for profile_name, observed in by_profile.items():
                    deltas = {
                        key: abs(float(observed[key]) - float(row[key]))
                        for key in ("mean", "std", "min", "max")
                    }
                    profile_ok = max(deltas.values()) <= TOLERANCE_MAG
                    entry["profiles"][profile_name] = {
                        "observed": observed,
                        "absolute_deltas": deltas,
                        "within_tolerance": profile_ok,
                    }
                best_profile = min(
                    by_profile,
                    key=lambda name: max(
                        abs(float(by_profile[name][key]) - float(row[key]))
                        for key in ("mean", "std", "min", "max")
                    ),
                )
                best_delta = max(
                    abs(float(by_profile[best_profile][key]) - float(row[key]))
                    for key in ("mean", "std", "min", "max")
                )
                entry["best_matching_profile"] = best_profile
                entry["best_profile_max_abs_delta_mag"] = best_delta
                entry["best_profile_within_tolerance"] = best_delta <= TOLERANCE_MAG
                comparisons.append(entry)
                time.sleep(0.5)
        global_profiles: dict[str, object] = {}
        for profile_name in ("raw_finite", "catflags_zero_before_cutoff", "paper_plot_filters"):
            passing_oids = sum(
                1 for entry in comparisons
                if entry["profiles"][profile_name]["within_tolerance"]
            )
            global_profiles[profile_name] = {
                "oids_within_tolerance": passing_oids,
                "sampled_oids": len(comparisons),
                "all_oids_within_tolerance": passing_oids == len(comparisons),
            }
        clean_profile = global_profiles["catflags_zero_before_cutoff"]
        report["summary"] = {
            "sampled_oids": len(comparisons),
            "global_profile_results": global_profiles,
            "pass": clean_profile["all_oids_within_tolerance"],
            "pass_rule": "Only the documented clean-observation profile (catflags == 0 within DR15 MJD coverage) determines pass/fail. Plot-only date exclusions are diagnostic and cannot rescue a mismatch.",
        }
    report["result"] = "PASS" if report["summary"]["pass"] else "FAIL"
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
