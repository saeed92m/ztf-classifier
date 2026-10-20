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
DR23_BULK_BASE = "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr23"
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


def fetch_raw_batch(
    oids: list[str], collection: str | None = None, timeout: int = 45
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    # The public API accepts repeated ID parameters, allowing a reproducible
    # batch request without issuing one HTTP request per light curve.
    query = [("ID", oid) for oid in oids]
    if collection is not None:
        query.append(("COLLECTION", collection))
    params = urllib.parse.urlencode(query)
    url = f"{IRSA_BASE}?{params}"
    payload, attempts = request_bytes(url, timeout=timeout)
    table = Table.read(io.BytesIO(payload), format="votable")
    frame = table.to_pandas()
    required = {"oid", "mjd", "mag", "magerr", "catflags"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"Raw IRSA response missing columns {sorted(required - set(frame.columns))}")
    for column in ("mjd", "mag", "magerr", "catflags"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    def normalize_oid(value: object) -> str:
        try:
            return str(int(float(value)))
        except (TypeError, ValueError, OverflowError):
            return str(value)

    frame["_requested_oid"] = frame["oid"].map(normalize_oid)
    by_oid = {
        oid: group.drop(columns=["_requested_oid"]).reset_index(drop=True)
        for oid, group in frame.groupby("_requested_oid", sort=False)
    }
    found = sorted(by_oid)
    metadata: dict[str, object] = {
        "url": url,
        "collection_parameter": collection,
        "release_pinning": collection or "none; live default API",
        "bytes": len(payload),
        "attempts": attempts,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "batch_rows": int(len(frame)),
        "requested_oids": list(oids),
        "found_oids": found,
        "missing_oids": sorted(set(oids) - set(found)),
        "columns": [column for column in frame.columns if column != "_requested_oid"],
    }
    return by_oid, metadata



def fetch_raw_oids_resilient(
    oids: list[str], timeout: int = 90, batch_size: int = 2
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, object]], list[dict[str, object]]]:
    """Fetch small batches first, then fall back to single OIDs on batch errors.

    Every request and fallback is represented in metadata. A failed request is
    never treated as an empty light curve or a scientific pass.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    combined: dict[str, pd.DataFrame] = {}
    metadata_by_oid: dict[str, dict[str, object]] = {}
    request_log: list[dict[str, object]] = []
    for start in range(0, len(oids), batch_size):
        chunk = oids[start : start + batch_size]
        try:
            found, meta = fetch_raw_batch(chunk, timeout=timeout)
            meta = {**meta, "request_mode": "batch", "batch_size": len(chunk)}
            request_log.append(meta)
            for oid in chunk:
                if oid in found:
                    combined[oid] = found[oid]
                    metadata_by_oid[oid] = meta
                else:
                    request_log.append({
                        "request_mode": "batch_missing_oid",
                        "requested_oids": [oid],
                        "parent_batch_sha256": meta.get("sha256"),
                        "error": "OID absent from successful batch response",
                    })
        except Exception as batch_exc:
            request_log.append({
                "request_mode": "batch_failed",
                "requested_oids": chunk,
                "error": f"{type(batch_exc).__name__}: {batch_exc}",
                "fallback": "single_oid_requests",
            })
            for oid in chunk:
                try:
                    found, meta = fetch_raw_batch([oid], timeout=timeout)
                    meta = {
                        **meta,
                        "request_mode": "single_oid_fallback",
                        "fallback_from_batch": chunk,
                        "batch_error": f"{type(batch_exc).__name__}: {batch_exc}",
                    }
                    request_log.append(meta)
                    if oid not in found:
                        request_log.append({
                            "request_mode": "single_oid_missing",
                            "requested_oids": [oid],
                            "error": "OID absent from single-OID response",
                        })
                        continue
                    combined[oid] = found[oid]
                    metadata_by_oid[oid] = meta
                except Exception as single_exc:
                    request_log.append({
                        "request_mode": "single_oid_failed",
                        "requested_oids": [oid],
                        "fallback_from_batch": chunk,
                        "batch_error": f"{type(batch_exc).__name__}: {batch_exc}",
                        "error": f"{type(single_exc).__name__}: {single_exc}",
                    })
                finally:
                    time.sleep(0.5)
        finally:
            time.sleep(0.5)
    return combined, metadata_by_oid, request_log


def raw_oid_metadata(
    raw: pd.DataFrame, batch_metadata: dict[str, object], oid: str
) -> dict[str, object]:
    metadata: dict[str, object] = {
        **batch_metadata,
        "oid": oid,
        "raw_rows": int(len(raw)),
        "max_mjd": float(raw["mjd"].max()) if raw["mjd"].notna().any() else None,
    }
    for source_column, target_key in (
        ("fieldid", "field_ids"),
        ("field", "field_ids"),
        ("rcid", "rcids"),
        ("filterid", "filter_ids"),
        ("fid", "filter_ids"),
        ("ccdid", "ccd_ids"),
        ("qid", "quadrant_ids"),
        ("filtercode", "filter_codes"),
    ):
        if source_column in raw.columns:
            if target_key == "filter_codes":
                metadata[target_key] = sorted(
                    str(value) for value in raw[source_column].dropna().unique()
                )
            else:
                metadata[target_key] = sorted(
                    int(value)
                    for value in pd.to_numeric(raw[source_column], errors="coerce").dropna().unique()
                )
    return metadata


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
        "batch_fetches": [],
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
            sample_rows = sample.to_dict(orient="records")
            oids = [str(row["OID"]) for row in sample_rows]
            current_data, current_meta_by_oid, current_request_log = fetch_raw_oids_resilient(
                oids, timeout=90, batch_size=2
            )
            report["batch_fetches"].extend(
                {"band": band, **meta} for meta in current_request_log
            )
            missing_current = sorted(set(oids) - set(current_data))
            if missing_current:
                report["raw_fetch_failure"] = {
                    "band": band,
                    "oids": missing_current,
                    "collection": None,
                    "error": "One or more OIDs could not be retrieved after small-batch and single-OID fallback attempts",
                    "completed_comparisons_before_failure": len(comparisons),
                    "request_log_entries": len(current_request_log),
                }
                report["result"] = "BLOCKED"
                print(json.dumps(report, indent=2, sort_keys=True))
                raise SystemExit(2)
            for row in sample_rows:
                oid = str(row["OID"])
                raw = current_data.get(oid)
                if raw is None:
                    report["raw_fetch_failure"] = {
                        "band": band,
                        "SourceID": str(row["SourceID"]),
                        "OID": oid,
                        "error": "OID absent from batched default-collection response",
                        "completed_comparisons_before_failure": len(comparisons),
                    }
                    report["result"] = "BLOCKED"
                    print(json.dumps(report, indent=2, sort_keys=True))
                    raise SystemExit(2)
                raw_meta = raw_oid_metadata(raw, current_meta_by_oid[oid], oid)
                by_profile = profiles(raw, band)
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
                    # IRSA accepts the pinned collection for single-OID queries;
                    # the multi-ID + COLLECTION form returned HTTP 404 in CI.
                    raw23_data, raw23_batch_meta = fetch_raw_batch([oid], collection="ztf_dr23", timeout=30)
                    report["batch_fetches"].append({
                        "band": band,
                        "release": "ztf_dr23",
                        **raw23_batch_meta,
                    })
                    raw23 = raw23_data.get(oid)
                    if raw23 is None:
                        raise RuntimeError("OID absent from pinned DR23 response")
                    raw23_meta = raw_oid_metadata(raw23, raw23_batch_meta, oid)
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
                finally:
                    # Respect the public IRSA service when checking many OIDs.
                    time.sleep(0.5)
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
    for release, base_url in (("dr15", DR15_BULK_BASE), ("dr23", DR23_BULK_BASE)):
        directory_urls = [
            f"{base_url}/",
            f"{base_url}/0/",
            f"{base_url}/1/",
        ]
        directory_urls.extend(
            f"{base_url}/{field_id // 1000}/field{field_id:06d}/"
            for field_id in fields[:12]
        )
        for url in directory_urls:
            try:
                payload, attempts = request_bytes(url, timeout=20)
                html = payload.decode("utf-8", errors="replace")
                links = sorted(set(re.findall(r"""href=["']([^"']+\.parquet)["']""", html, flags=re.IGNORECASE)))
                field_links = sorted(set(re.findall(r"""href=["'](field\d+/?)["']""", html, flags=re.IGNORECASE)))
                bulk_probes.append({
                    "release": release,
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
                    "release": release,
                    "url": url,
                    "status": "UNAVAILABLE",
                    "error": f"{type(exc).__name__}: {exc}",
                })
    report["bulk_archive_probes"] = {
        "base_urls": {"dr15": DR15_BULK_BASE, "dr23": DR23_BULK_BASE},
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
