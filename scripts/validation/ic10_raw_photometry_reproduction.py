#!/usr/bin/env python3
"""Compare published IC 10 per-OID statistics with current raw IRSA light curves.

The paper's public code queries the default live API without a COLLECTION
parameter. This diagnostic reproduces that query pattern, records the exact
response hash, and separately probes the documented DR15 bulk archive URL.
It cannot claim a frozen historical-data match if the API snapshot has changed.
"""
from __future__ import annotations

import hashlib
import http.client
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd
from astropy.table import Table

ZENODO_BASE = "https://zenodo.org/records/14979711/files"
IRSA_BASE = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
DR15_BULK_BASE = "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr15"
FILES = {
    "df_zr.csv": "0589a1bda6abd960145ad6116275851d",
    "df_zg.csv": "3cb5b49b1064a2bac0bc7ab9201fa0e0",
}
SAMPLE_PER_BAND = 10
SAMPLE_SEED = 20261020
TOLERANCE_MAG = 1e-3
CUTOFF_MJD = 59892.0
BAD_R_INTERVALS = ((58481.0, 58482.0), (58472.0, 58474.0), (59032.0, 59033.0))


def request_bytes(url: str, timeout: int = 90) -> tuple[bytes, int]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ztf-classifier-independent-validation/1.0"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(), attempt + 1
        except urllib.error.HTTPError as exc:
            if exc.code not in (408, 429) and exc.code < 500:
                raise
            if attempt == 2:
                raise
            time.sleep(2**attempt)
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"Could not retrieve {url}")


def download_catalog(name: str) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{ZENODO_BASE}/{name}?download=1"
    payload, attempts = request_bytes(url, timeout=60)
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    frame = pd.read_csv(io.BytesIO(payload), dtype={"SourceID": "string", "OID": "string"})
    required = {"SourceID", "OID", "numobs", "mean", "std", "min", "max"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"{name}: missing columns {sorted(required - set(frame.columns))}")
    return frame, {
        "url": url,
        "bytes": len(payload),
        "attempts": attempts,
        "md5": md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": int(len(frame)),
        "unique_source_ids": int(frame["SourceID"].nunique()),
    }


def fetch_raw(oid: str, collection: str | None = None) -> tuple[pd.DataFrame, dict[str, object]]:
    # The default call matches the paper's public code. Pinned collections are
    # diagnostic comparisons against release snapshots available through IRSA.
    query = {"ID": oid}
    if collection is not None:
        query["COLLECTION"] = collection
    params = urllib.parse.urlencode(query)
    url = f"{IRSA_BASE}?{params}"
    payload, attempts = request_bytes(url, timeout=45)
    table = Table.read(io.BytesIO(payload), format="votable")
    frame = table.to_pandas()
    required = {"mjd", "mag", "magerr", "catflags"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"OID {oid}: raw IRSA response missing columns {sorted(required - set(frame.columns))}")
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    metadata: dict[str, object] = {
        "url": url,
        "collection_parameter": collection,
        "release_pinning": collection or "none; live default API",
        "bytes": len(payload),
        "attempts": attempts,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "raw_rows": int(len(frame)),
        "columns": list(frame.columns),
        "max_mjd": float(frame["mjd"].max()) if frame["mjd"].notna().any() else None,
    }
    for source_column, target_key in (
        ("fieldid", "field_ids"),
        ("field", "field_ids"),
        ("rcid", "rcids"),
        ("filterid", "filter_ids"),
        ("fid", "filter_ids"),
    ):
        if source_column in frame.columns:
            metadata[target_key] = sorted(
                int(value)
                for value in pd.to_numeric(frame[source_column], errors="coerce").dropna().unique()
            )
    return frame, metadata


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
    good = finite[finite["catflags"] == 0].copy()
    cutoff = good[good["mjd"] < CUTOFF_MJD].copy()
    paper_plot = cutoff.copy()
    if band == "r":
        for low, high in BAD_R_INTERVALS:
            paper_plot = paper_plot[(paper_plot["mjd"] < low) | (paper_plot["mjd"] > high)]
    return {
        "raw_finite": stats(finite),
        "catflags_zero_before_cutoff": stats(cutoff),
        "paper_plot_filters": stats(paper_plot),
    }


def main() -> None:
    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "test": "published per-OID mean/std/min/max versus current default and pinned historical IRSA light curves",
        "sample_per_band": SAMPLE_PER_BAND,
        "sample_seed": SAMPLE_SEED,
        "tolerance_magnitude": TOLERANCE_MAG,
        "paper_release_claim": "The paper describes using ZTF DR15 and the public code applies an MJD cutoff at 59892.",
        "public_code_collection_parameter": "The public code calls the light-curve API without COLLECTION, so its actual source release is not pinned by the code.",
        "zenodo_snapshot_filename_evidence": ["t_zr_20250225.ecsv", "t_zg_20250225.ecsv"],
        "latest_public_release_on_2025_02_25": "DR23 (released 2025-01-15)",
        "candidate_source_release_hypothesis": "DR23 is the likely default API collection when the 2025-02-25 catalog snapshot was produced, but this is not proven from the filenames alone.",
        "api_default_release_at_validation": "ZTF DR24 (IRSA lists DR24 as the latest public release from 2026-01-22).",
        "api_collection_limitation": "IRSA documents COLLECTION support for the latest five releases; this permits a direct DR23-vs-DR24 comparison without downloading the full bulk archive.",
        "release_note": "The paper text says DR15, but the public code does not pin COLLECTION and the catalog filenames are dated 2025-02-25, after DR23 was released. The script therefore compares current default data with explicitly pinned DR23; neither result alone establishes the exact collection used to produce the published tables.",
        "filter_profiles": {
            "raw_finite": "finite MJD and magnitude",
            "catflags_zero_before_cutoff": "catflags == 0 and MJD < 59892; primary scientific comparison",
            "paper_plot_filters": "previous profile; for r also excludes three date intervals in the authors' public plotting code",
        },
        "catalogs": {},
        "comparisons": [],
    }
    catalogs: dict[str, pd.DataFrame] = {}
    try:
        for name, band in (("df_zr.csv", "r"), ("df_zg.csv", "g")):
            catalogs[band], report["catalogs"][band] = download_catalog(name)
        comparisons = report["comparisons"]
        for band in ("r", "g"):
            frame = catalogs[band]
            sample = frame.sample(
                n=min(SAMPLE_PER_BAND, len(frame)),
                random_state=SAMPLE_SEED,
            ).sort_values(["SourceID", "OID"])
            for row in sample.to_dict(orient="records"):
                oid = str(row["OID"])
                try:
                    raw, raw_meta = fetch_raw(oid)
                    by_profile = profiles(raw, band)
                except Exception as exc:
                    report["raw_fetch_failure"] = {
                        "band": band,
                        "SourceID": str(row["SourceID"]),
                        "OID": oid,
                        "error": f"{type(exc).__name__}: {exc}",
                        "completed_comparisons_before_failure": len(comparisons),
                    }
                    report["result"] = "BLOCKED"
                    print(json.dumps(report, indent=2, sort_keys=True))
                    raise SystemExit(2) from exc
                published = {key: float(row[key]) for key in ("mean", "std", "min", "max")}
                entry: dict[str, object] = {
                    "band": band,
                    "SourceID": str(row["SourceID"]),
                    "OID": oid,
                    "catalog_numobs": int(row["numobs"]),
                    "raw": raw_meta,
                    "published": published,
                    "profiles": {},
                    "pinned_release_comparisons": {},
                }
                for profile_name, observed in by_profile.items():
                    deltas = {
                        key: abs(float(observed[key]) - published[key])
                        for key in ("mean", "std", "min", "max")
                    }
                    entry["profiles"][profile_name] = {
                        "observed": observed,
                        "absolute_deltas": deltas,
                        "within_tolerance": max(deltas.values()) <= TOLERANCE_MAG,
                    }
                try:
                    raw23, raw23_meta = fetch_raw(oid, collection="ztf_dr23")
                    entry["pinned_release_comparisons"]["ztf_dr23"] = {
                        "raw": raw23_meta,
                        "profiles": {},
                    }
                    for profile_name, observed in profiles(raw23, band).items():
                        deltas = {
                            key: abs(float(observed[key]) - published[key])
                            for key in ("mean", "std", "min", "max")
                        }
                        entry["pinned_release_comparisons"]["ztf_dr23"]["profiles"][profile_name] = {
                            "observed": observed,
                            "absolute_deltas": deltas,
                            "within_tolerance": max(deltas.values()) <= TOLERANCE_MAG,
                        }
                except Exception as exc:
                    entry["pinned_release_comparisons"]["ztf_dr23"] = {
                        "error": f"{type(exc).__name__}: {exc}"
                    }
                comparisons.append(entry)
                time.sleep(0.5)
    except SystemExit:
        raise
    except Exception as exc:
        report["setup_failure"] = f"{type(exc).__name__}: {exc}"
        report["result"] = "BLOCKED"
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(2) from exc

    comparisons = report["comparisons"]
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
    primary = global_profiles["catflags_zero_before_cutoff"]
    pinned_release_profiles: dict[str, object] = {}
    for profile_name in ("raw_finite", "catflags_zero_before_cutoff", "paper_plot_filters"):
        passing = sum(
            1
            for entry in comparisons
            if entry.get("pinned_release_comparisons", {}).get("ztf_dr23", {})
                .get("profiles", {}).get(profile_name, {}).get("within_tolerance", False)
        )
        available = sum(
            1 for entry in comparisons
            if "profiles" in entry.get("pinned_release_comparisons", {}).get("ztf_dr23", {})
        )
        pinned_release_profiles[profile_name] = {
            "oids_within_tolerance": passing,
            "oids_with_pinned_release_data": available,
            "sampled_oids": len(comparisons),
            "all_available_oids_within_tolerance": available > 0 and passing == available,
        }
    fields = sorted({
        int(field_id)
        for entry in comparisons
        for field_id in entry.get("raw", {}).get("field_ids", [])
    })
    bulk_probes = []
    directory_urls = [
        f"{DR15_BULK_BASE}/",
        f"{DR15_BULK_BASE}/0/",
        f"{DR15_BULK_BASE}/1/",
    ]
    directory_urls.extend(
        f"{DR15_BULK_BASE}/{field_id // 1000}/field{field_id:04d}/"
        for field_id in fields[:12]
    )
    for url in directory_urls:
        try:
            payload, attempts = request_bytes(url, timeout=20)
            html = payload.decode("utf-8", errors="replace")
            links = sorted(set(re.findall(r"""href=["']([^"']+\.parquet)["']""", html, flags=re.IGNORECASE)))
            field_links = sorted(set(re.findall(r"""href=["'](field\d+/?)["']""", html, flags=re.IGNORECASE)))
            bulk_probes.append({
                "url": url,
                "status": "AVAILABLE",
                "attempts": attempts,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "parquet_link_count": len(links),
                "parquet_links_sample": links[:5],
                "field_directory_links_sample": field_links[:10],
                "listing_prefix": html[:160],
            })
        except Exception as exc:
            bulk_probes.append({
                "url": url,
                "status": "UNAVAILABLE",
                "error": f"{type(exc).__name__}: {exc}",
            })
    report["dr15_bulk_archive_probes"] = {
        "base_url": DR15_BULK_BASE,
        "field_ids_discovered_from_live_api_metadata": fields,
        "probes": bulk_probes,
        "note": "Only directory listings were requested; no bulk Parquet photometry files were downloaded in this probe.",
    }

    report["summary"] = {
        "sampled_oids": len(comparisons),
        "global_profile_results": global_profiles,
        "pinned_ztf_dr23_profile_results": pinned_release_profiles,
        "pass": primary["all_oids_within_tolerance"],
        "pass_rule": "Every sampled OID must reproduce published mean/std/min/max within 0.001 mag using catflags == 0 and MJD < 59892. Alternative profiles and the pinned DR23 comparison are diagnostic until the original source collection is established.",
    }
    report["result"] = "PASS" if report["summary"]["pass"] else "FAIL"
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
