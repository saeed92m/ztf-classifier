#!/usr/bin/env python3
"""Recompute the IC 10 catalog sample directly from pinned ZTF bulk Parquet releases."""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

BASE_URLS = {
    "dr15": "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr15",
    "dr23": "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr23",
}
TOLERANCE_MAG = 1e-3
CUTOFF_MJD = 59892.0
BAD_R_INTERVALS = ((58481.0, 58482.0), (58472.0, 58474.0), (59032.0, 59033.0))


def fetch_bytes(url: str, timeout: int = 60) -> tuple[bytes, int]:
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
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"Could not retrieve {url}")


def normalize_oid(value: object) -> str:
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    try:
        return str(int(float(text)))
    except (TypeError, ValueError, OverflowError):
        return text


def field_metadata_from_entry(entry: dict[str, object]) -> list[tuple[int, str, int, int]]:
    raw = entry.get("raw", {})
    fields = raw.get("field_ids", []) if isinstance(raw, dict) else []
    ccds = raw.get("ccd_ids", []) if isinstance(raw, dict) else []
    quadrants = raw.get("quadrant_ids", []) if isinstance(raw, dict) else []
    filters = raw.get("filter_codes", []) if isinstance(raw, dict) else []
    return sorted({
        (int(field_id), str(filter_code), int(ccd_id), int(quadrant_id))
        for field_id in fields
        for filter_code in filters
        for ccd_id in ccds
        for quadrant_id in quadrants
    })


def discover_directory(
    release: str, combo: tuple[int, str, int, int]
) -> tuple[str, dict[str, object]]:
    field_id, filter_code, ccd_id, quadrant_id = combo
    base_url = BASE_URLS[release]
    directory_url = f"{base_url}/{field_id // 1000}/field{field_id:06d}/"
    html_bytes, attempts = fetch_bytes(directory_url, timeout=30)
    html = html_bytes.decode("utf-8", errors="replace")
    links = re.findall(r"""href=["']([^"']+)["']""", html, flags=re.IGNORECASE)
    parquet_links = {Path(urllib.parse.unquote(link)).name for link in links if link.lower().endswith(".parquet")}
    filename = f"ztf_{field_id:06d}_{filter_code}_c{ccd_id:02d}_q{quadrant_id}_dr{release[2:]}.parquet"
    if filename not in parquet_links:
        raise RuntimeError(
            f"Expected Parquet file {filename} not listed at {directory_url}"
        )

    checksum_links = [
        link for link in links
        if "checksum" in link.lower() or link.lower().endswith((".md5", ".md5sum"))
    ]
    expected_md5 = None
    checksum_source = None
    for link in checksum_links:
        checksum_url = urllib.parse.urljoin(directory_url, link)
        try:
            checksum_payload, _ = fetch_bytes(checksum_url, timeout=20)
        except Exception:
            continue
        for line in checksum_payload.decode("utf-8", errors="replace").splitlines():
            match = re.match(r"^\s*([0-9a-fA-F]{32})\s+\*?(.+?)\s*$", line)
            if match and Path(match.group(2)).name == filename:
                expected_md5 = match.group(1).lower()
                checksum_source = checksum_url
                break
        if expected_md5:
            break

    return urllib.parse.urljoin(directory_url, filename), {
        "release": release,
        "field_id": field_id,
        "filter_code": filter_code,
        "ccd_id": ccd_id,
        "quadrant_id": quadrant_id,
        "directory_url": directory_url,
        "directory_sha256": hashlib.sha256(html_bytes).hexdigest(),
        "directory_bytes": len(html_bytes),
        "directory_attempts": attempts,
        "filename": filename,
        "listed_parquet_files": len(parquet_links),
        "publisher_md5": expected_md5,
        "publisher_checksum_url": checksum_source,
    }


def read_parquet_subset(
    url: str,
    file_metadata: dict[str, object],
    requested_oids: set[str],
) -> tuple[pd.DataFrame, dict[str, object]]:
    payload, attempts = fetch_bytes(url, timeout=120)
    actual_md5 = hashlib.md5(payload).hexdigest()
    expected_md5 = file_metadata.get("publisher_md5")
    if expected_md5 and actual_md5 != expected_md5:
        raise RuntimeError(
            f"Publisher MD5 mismatch for {file_metadata['filename']}: "
            f"expected {expected_md5}, got {actual_md5}"
        )
    frame = pd.read_parquet(io.BytesIO(payload), engine="pyarrow")
    lower_columns = {str(column).lower(): column for column in frame.columns}
    oid_column = lower_columns.get("oid") or lower_columns.get("objectid")
    mjd_column = lower_columns.get("mjd")
    mag_column = lower_columns.get("mag")
    catflags_column = lower_columns.get("catflags")
    required = {
        "oid": oid_column,
        "mjd": mjd_column,
        "mag": mag_column,
        "catflags": catflags_column,
    }
    missing = [name for name, column in required.items() if column is None]
    if missing:
        raise RuntimeError(
            f"{file_metadata['filename']} missing required columns {missing}; "
            f"available columns={list(frame.columns)}"
        )
    frame = frame.rename(columns={
        oid_column: "oid",
        mjd_column: "mjd",
        mag_column: "mag",
        catflags_column: "catflags",
    })
    frame["_oid_key"] = frame["oid"].map(normalize_oid)
    frame = frame[frame["_oid_key"].isin(requested_oids)].copy()
    for column in ("mjd", "mag", "catflags"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    metadata = {
        **file_metadata,
        "url": url,
        "bytes": len(payload),
        "attempts": attempts,
        "md5": actual_md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "parquet_rows_total": int(pd.read_parquet(io.BytesIO(payload), columns=["oid"], engine="pyarrow").shape[0]),
        "requested_oids": sorted(requested_oids),
        "found_oids": sorted(set(frame["_oid_key"])),
        "selected_rows": int(len(frame)),
        "columns": [str(column) for column in frame.columns if column != "_oid_key"],
    }
    return frame.drop(columns=["_oid_key"]), metadata


def profile_stats(raw: pd.DataFrame, band: str) -> dict[str, dict[str, float | int]]:
    finite = raw[np.isfinite(raw["mjd"]) & np.isfinite(raw["mag"])].copy()
    good = finite[finite["catflags"] == 0].copy()
    cutoff = good[good["mjd"] < CUTOFF_MJD].copy()
    plot = cutoff.copy()
    if band == "r":
        for low, high in BAD_R_INTERVALS:
            plot = plot[(plot["mjd"] < low) | (plot["mjd"] > high)]

    def summarize(frame: pd.DataFrame) -> dict[str, float | int]:
        values = pd.to_numeric(frame["mag"], errors="coerce").to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        if not len(values):
            return {"n": 0, "mean": float("nan"), "std_population": float("nan"),
                    "std_sample": float("nan"), "min": float("nan"), "max": float("nan")}
        return {
            "n": int(len(values)),
            "mean": float(np.mean(values)),
            "std_population": float(np.std(values, ddof=0)),
            "std_sample": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

    return {
        "raw_finite": summarize(finite),
        "catflags_zero_before_cutoff": summarize(cutoff),
        "paper_plot_filters": summarize(plot),
    }


def compare_stats(
    observed: dict[str, float | int], published: dict[str, float]
) -> dict[str, object]:
    results = {}
    for convention, std_key in (("population", "std_population"), ("sample", "std_sample")):
        deltas = {
            "mean": abs(float(observed["mean"]) - published["mean"]),
            "std": abs(float(observed[std_key]) - published["std"]),
            "min": abs(float(observed["min"]) - published["min"]),
            "max": abs(float(observed["max"]) - published["max"]),
        }
        results[convention] = {
            "absolute_deltas": deltas,
            "max_absolute_delta": max(deltas.values()),
            "within_tolerance": max(deltas.values()) <= TOLERANCE_MAG,
        }
    return results


def main() -> None:
    raw_report_path = Path("ic10-raw-photometry-report.json")
    numeric_report_path = Path("ic10-numeric-consistency-report.json")
    if not raw_report_path.is_file():
        raise RuntimeError("Missing ic10-raw-photometry-report.json from preceding workflow step")
    raw_report_bytes = raw_report_path.read_bytes()
    raw_report = json.loads(raw_report_bytes)
    entries = raw_report.get("comparisons", [])
    if len(entries) != 20:
        raise RuntimeError(
            f"Expected the fixed 20-OID raw report sample; found {len(entries)} comparisons"
        )
    combos: dict[tuple[int, str, int, int], set[str]] = {}
    entry_combos: dict[str, list[tuple[int, str, int, int]]] = {}
    for entry in entries:
        oid = normalize_oid(entry["OID"])
        oid_combos = field_metadata_from_entry(entry)
        if not oid_combos:
            raise RuntimeError(f"Missing field/CCD/quadrant/filter metadata for OID {oid}")
        entry_combos[oid] = oid_combos
        for combo in oid_combos:
            combos.setdefault(combo, set()).add(oid)

    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "test": "recompute published OID statistics from release-pinned bulk Parquet files",
        "input_reports": {
            "raw_photometry_report_sha256": hashlib.sha256(raw_report_bytes).hexdigest(),
            "numeric_consistency_report_sha256": (
                hashlib.sha256(numeric_report_path.read_bytes()).hexdigest()
                if numeric_report_path.is_file() else None
            ),
        },
        "sample_size": len(entries),
        "tolerance_magnitude": TOLERANCE_MAG,
        "fixed_cutoff_mjd": CUTOFF_MJD,
        "bad_r_intervals": BAD_R_INTERVALS,
        "unique_field_ccd_quadrant_filter_combinations": len(combos),
        "combinations": [
            {"field_id": f, "filter_code": filt, "ccd_id": c, "quadrant_id": q,
             "oids": sorted(oids)}
            for (f, filt, c, q), oids in sorted(combos.items())
        ],
        "releases": {},
    }

    overall_release_passes = {}
    for release, base_url in BASE_URLS.items():
        release_files = []
        raw_by_oid: dict[str, list[pd.DataFrame]] = {normalize_oid(e["OID"]): [] for e in entries}
        file_errors = []
        for combo, requested_oids in sorted(combos.items()):
            try:
                url, file_meta = discover_directory(release, combo)
                selected, read_meta = read_parquet_subset(url, file_meta, requested_oids)
                release_files.append(read_meta)
                for oid in requested_oids:
                    subset = selected[selected["oid"].map(normalize_oid) == oid].copy()
                    if not subset.empty:
                        raw_by_oid.setdefault(oid, []).append(subset)
            except Exception as exc:
                file_errors.append({
                    "release": release,
                    "combination": combo,
                    "requested_oids": sorted(requested_oids),
                    "error": f"{type(exc).__name__}: {exc}",
                })

        comparisons = []
        profile_summary = {
            profile: {
                "population_std_matches": 0,
                "sample_std_matches": 0,
                "oids_with_data": 0,
                "sampled_oids": len(entries),
            }
            for profile in ("raw_finite", "catflags_zero_before_cutoff", "paper_plot_filters")
        }
        for entry in entries:
            oid = normalize_oid(entry["OID"])
            pieces = raw_by_oid.get(oid, [])
            if not pieces:
                comparisons.append({
                    "band": entry["band"], "SourceID": str(entry["SourceID"]), "OID": oid,
                    "published": entry["published"], "catalog_numobs": entry["catalog_numobs"],
                    "result": "MISSING_FROM_BULK_FILES",
                })
                continue
            raw = pd.concat(pieces, ignore_index=True)
            observed_profiles = profile_stats(raw, str(entry["band"]))
            published = {key: float(entry["published"][key]) for key in ("mean", "std", "min", "max")}
            per_profile = {}
            for profile_name, observed in observed_profiles.items():
                match = compare_stats(observed, published)
                per_profile[profile_name] = {
                    "observed": observed,
                    "catalog_numobs": int(entry["catalog_numobs"]),
                    "numobs_delta": int(observed["n"]) - int(entry["catalog_numobs"]),
                    "comparisons": match,
                }
                profile_summary[profile_name]["oids_with_data"] += 1
                if match["population"]["within_tolerance"]:
                    profile_summary[profile_name]["population_std_matches"] += 1
                if match["sample"]["within_tolerance"]:
                    profile_summary[profile_name]["sample_std_matches"] += 1
            comparisons.append({
                "band": entry["band"],
                "SourceID": str(entry["SourceID"]),
                "OID": oid,
                "field_ccd_quadrant_filter_combinations": entry_combos[oid],
                "published": published,
                "catalog_numobs": int(entry["catalog_numobs"]),
                "bulk_rows_all_filters": int(len(raw)),
                "profiles": per_profile,
            })

        release_pass = {
            profile: {
                "population_std_all_oids_match": summary["oids_with_data"] == len(entries)
                    and summary["population_std_matches"] == len(entries),
                "sample_std_all_oids_match": summary["oids_with_data"] == len(entries)
                    and summary["sample_std_matches"] == len(entries),
                **summary,
            }
            for profile, summary in profile_summary.items()
        }
        overall_release_passes[release] = (
            release_pass["catflags_zero_before_cutoff"]["population_std_all_oids_match"]
        )
        report["releases"][release] = {
            "base_url": base_url,
            "files_downloaded": len(release_files),
            "file_errors": file_errors,
            "files": release_files,
            "profile_summary": release_pass,
            "comparisons": comparisons,
            "pass_primary_population_std": overall_release_passes[release],
        }

    report["result"] = "PASS" if any(overall_release_passes.values()) else "FAIL"
    report["interpretation_rule"] = (
        "PASS means at least one pinned release reproduces all 20 published mean/std/min/max "
        "values within 0.001 mag under catflags==0 and MJD<59892 using population standard "
        "deviation. Sample-standard-deviation matches are reported separately because the "
        "published table-generation convention is not fully documented."
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
