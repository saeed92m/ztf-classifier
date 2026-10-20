#!/usr/bin/env python3
"""Recompute published IC 10 per-OID magnitude statistics from raw IRSA light curves.

The sample is deterministic and deliberately includes multi-OID SourceIDs.
This checks source-backed photometry summaries; it is not classifier-accuracy
validation and does not claim to reproduce every paper filtering decision.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
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


def fetch_raw(oid: str) -> tuple[pd.DataFrame, dict[str, object]]:
    url = (
        "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
        f"?ID={oid}&COLLECTION={COLLECTION}&FORMAT=VOTABLE"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    table = Table.read(io.BytesIO(payload))
    frame = table.to_pandas()
    needed = {"mjd", "mag", "catflags"}
    if not needed.issubset(frame.columns):
        raise RuntimeError(f"OID {oid}: raw IRSA response missing columns {sorted(needed - set(frame.columns))}")
    for column in needed:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame.empty:
        raise RuntimeError(f"OID {oid}: empty raw light curve")
    return frame, {
        "url": url,
        "collection": COLLECTION,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "raw_rows": int(len(frame)),
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
        probe_oid = str(samples["r"].iloc[0]["OID"])
        try:
            probe_raw, probe_meta = fetch_raw(probe_oid)
        except Exception as exc:
            report["historical_collection_probe"] = {
                "collection": COLLECTION,
                "probe_oid": probe_oid,
                "status": "UNAVAILABLE",
                "error": f"{type(exc).__name__}: {exc}",
            }
            report["result"] = "BLOCKED"
            print(json.dumps(report, indent=2, sort_keys=True))
            raise SystemExit(2) from exc
        report["historical_collection_probe"] = {
            "collection": COLLECTION,
            "probe_oid": probe_oid,
            "status": "AVAILABLE",
            "raw_rows": int(len(probe_raw)),
            "payload_sha256": probe_meta["sha256"],
            "url": probe_meta["url"],
        }
        raw_cache: dict[tuple[str, str], tuple[pd.DataFrame, dict[str, object]]] = {
            ("r", probe_oid): (probe_raw, probe_meta)
        }
        for band in ("r", "g"):
            for row in samples[band].to_dict(orient="records"):
                oid = str(row["OID"])
                if (band, oid) in raw_cache:
                    raw, raw_meta = raw_cache[(band, oid)]
                else:
                    raw, raw_meta = fetch_raw(oid)
                    raw_cache[(band, oid)] = (raw, raw_meta)
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
                time.sleep(0.15)
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
