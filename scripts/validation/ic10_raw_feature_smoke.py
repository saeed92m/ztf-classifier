#!/usr/bin/env python3
"""Run frozen v0.2 features on a paired raw ZTF source from the IC 10 paper.

This complements the numerical catalog comparison: it tests real g/r light
curves from the paper's selected source, but it is not a classifier-accuracy
test and the paper's P/V/N labels are not mapped to the frozen model taxonomy.
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

import numpy as np
import pandas as pd
from astropy.table import Table

from ztf_classifier.features.pipeline import (
    V0_2_FEATURES,
    extract_v0_2_features,
    validate_v0_2_feature_vector,
)
from ztf_classifier.preprocessing.lightcurve import prepare_band_lightcurve

ZENODO_BASE = "https://zenodo.org/records/14979711/files"
FILES = {
    "df_zr.csv": "0589a1bda6abd960145ad6116275851d",
    "df_zg.csv": "3cb5b49b1064a2bac0bc7ab9201fa0e0",
    "df_color.csv": "6c7d0c8cb21515eea093fd861d83aa47",
}
HISTORICAL_CUTOFF_MJD = 59447.224132
PAPER_CUTOFF_MJD = 59892.0
BAD_R_INTERVALS = ((58481.0, 58482.0), (58472.0, 58474.0), (59032.0, 59033.0))


def fetch_bytes(url: str, timeout: int = 90) -> tuple[bytes, int]:
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


def fetch_catalog(name: str) -> tuple[pd.DataFrame, dict[str, object]]:
    url = f"{ZENODO_BASE}/{name}?download=1"
    payload, attempts = fetch_bytes(url, timeout=60)
    md5 = hashlib.md5(payload).hexdigest()
    if md5 != FILES[name]:
        raise RuntimeError(f"{name}: publisher MD5 mismatch: {md5}")
    frame = pd.read_csv(io.BytesIO(payload), dtype={"SourceID": "string", "OID": "string"})
    return frame, {
        "url": url,
        "bytes": len(payload),
        "attempts": attempts,
        "md5": md5,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": int(len(frame)),
    }


def best_oid_per_source(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"SourceID", "OID", "numobs"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"Published band table missing columns: {sorted(required - set(frame.columns))}")
    result = frame.copy()
    result["numobs"] = pd.to_numeric(result["numobs"], errors="coerce")
    result = result.dropna(subset=["SourceID", "OID", "numobs"])
    return result.sort_values(
        ["SourceID", "numobs", "OID"],
        ascending=[True, False, True],
    ).drop_duplicates("SourceID", keep="first")


def fetch_raw_lightcurve(oid: str) -> tuple[pd.DataFrame, dict[str, object]]:
    # Match the paper's public code: the live API is not pinned to a release.
    params = urllib.parse.urlencode({"ID": oid, "TIME": f"58194.0 {PAPER_CUTOFF_MJD}"})
    url = f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?{params}"
    payload, attempts = fetch_bytes(url, timeout=45)
    table = Table.read(io.BytesIO(payload), format="votable")
    frame = table.to_pandas()
    required = {"mjd", "mag", "magerr", "catflags"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"OID {oid}: raw API missing columns {sorted(required - set(frame.columns))}")
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame, {
        "url": url,
        "release_pinning": "none; same unpinned API pattern as the paper's public code",
        "bytes": len(payload),
        "attempts": attempts,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "raw_rows": int(len(frame)),
    }


def clean_band(raw: pd.DataFrame, band: str) -> tuple[pd.DataFrame, dict[str, int]]:
    counts = {"raw_rows": int(len(raw))}
    current = raw.copy()
    current = current[current["catflags"] == 0].copy()
    counts["after_catflags_zero"] = int(len(current))
    current = current[current["mjd"] < PAPER_CUTOFF_MJD].copy()
    counts["after_paper_mjd_cutoff"] = int(len(current))
    if band == "r":
        for low, high in BAD_R_INTERVALS:
            current = current[(current["mjd"] < low) | (current["mjd"] > high)].copy()
    counts["after_paper_plot_date_exclusions"] = int(len(current))
    finite = np.isfinite(current[["mjd", "mag", "magerr"]].to_numpy(dtype=float)).all(axis=1)
    current = current.loc[finite].copy()
    counts["after_finite_numeric_filter"] = int(len(current))
    current = current[current["magerr"] > 0].copy()
    counts["after_positive_magerr_filter"] = int(len(current))
    current["fid"] = 1 if band == "g" else 2
    return current[["mjd", "fid", "mag", "magerr"]], counts


def finite_or_none(value: object) -> float | None:
    number = float(value)
    return number if np.isfinite(number) else None


def main() -> None:
    report: dict[str, object] = {
        "dataset": "ZTF IC 10 variable catalog",
        "doi": "10.5281/zenodo.14979711",
        "test": "frozen v0.2 feature extraction on a paired raw g/r source from the independent paper",
        "historical_cutoff_mjd": HISTORICAL_CUTOFF_MJD,
        "paper_mjd_cutoff": PAPER_CUTOFF_MJD,
        "source_selection": "intersection of color-table SourceIDs and the highest-numobs OID per band; maximize the minimum published g/r numobs, deterministic tie-break",
        "raw_api_note": "The paper's public code does not pin COLLECTION; raw API results are therefore live and may not reproduce the paper's historical snapshot.",
        "files": {},
    }
    catalogs: dict[str, pd.DataFrame] = {}
    for name in FILES:
        catalogs[name], report["files"][name] = fetch_catalog(name)
    r_best = best_oid_per_source(catalogs["df_zr.csv"])
    g_best = best_oid_per_source(catalogs["df_zg.csv"])
    color_ids = set(catalogs["df_color.csv"]["SourceID"].dropna().astype("string"))
    paired = r_best.merge(g_best, on="SourceID", suffixes=("_r", "_g"))
    paired = paired[paired["SourceID"].astype("string").isin(color_ids)].copy()
    if paired.empty:
        raise RuntimeError("No common SourceID remains across g, r, and color tables")
    paired["min_numobs"] = np.minimum(paired["numobs_r"], paired["numobs_g"])
    eligible = paired[(paired["numobs_r"] >= 30) & (paired["numobs_g"] >= 30)].copy()
    if eligible.empty:
        raise RuntimeError("No paired IC 10 SourceID has at least 30 published observations in both bands")
    eligible["distance_from_100_per_band"] = (
        (eligible["numobs_r"] - 100).abs() + (eligible["numobs_g"] - 100).abs()
    )
    chosen = eligible.sort_values(
        ["distance_from_100_per_band", "SourceID"],
        ascending=[True, True],
    ).iloc[0]
    source_id = str(chosen["SourceID"])
    oid_r, oid_g = str(chosen["OID_r"]), str(chosen["OID_g"])

    raw_r, meta_r = fetch_raw_lightcurve(oid_r)
    raw_g, meta_g = fetch_raw_lightcurve(oid_g)
    clean_r, counts_r = clean_band(raw_r, "r")
    clean_g, counts_g = clean_band(raw_g, "g")
    internal = pd.concat([clean_g, clean_r], ignore_index=True)
    if internal.empty:
        raise RuntimeError(f"SourceID {source_id}: no valid observations remain after filtering")
    features = extract_v0_2_features(internal, cutoff_mjd=HISTORICAL_CUTOFF_MJD)
    validate_v0_2_feature_vector(features)
    if len(features) != 42:
        raise RuntimeError(f"Expected 42 frozen v0.2 features, got {len(features)}")
    for feature_name in ("g_mean_mag", "r_mean_mag", "mean_color_gr"):
        if not np.isfinite(features[feature_name]):
            raise RuntimeError(f"Expected finite basic feature {feature_name}")
    historical = internal[internal["mjd"] <= HISTORICAL_CUTOFF_MJD].copy()
    expected_g = len(prepare_band_lightcurve(historical, fid=1))
    expected_r = len(prepare_band_lightcurve(historical, fid=2))
    if features["g_n_obs"] != expected_g or features["r_n_obs"] != expected_r:
        raise RuntimeError("Feature engine observation counts do not match canonical preprocessing")
    if expected_g < 10 or expected_r < 10:
        raise RuntimeError(
            f"Selected source did not exercise basic features: g={expected_g}, r={expected_r}"
        )

    report.update(
        {
            "result": "PASS",
            "SourceID": source_id,
            "OID_g": oid_g,
            "OID_r": oid_r,
            "published_numobs_g": int(chosen["numobs_g"]),
            "published_numobs_r": int(chosen["numobs_r"]),
            "raw_g": meta_g,
            "raw_r": meta_r,
            "g_filter_counts": counts_g,
            "r_filter_counts": counts_r,
            "feature_count": len(features),
            "feature_order_matches_frozen_v0_2": tuple(features) == V0_2_FEATURES,
            "historical_g_observations": expected_g,
            "historical_r_observations": expected_r,
            "g_mean_mag": finite_or_none(features["g_mean_mag"]),
            "r_mean_mag": finite_or_none(features["r_mean_mag"]),
            "mean_color_gr": finite_or_none(features["mean_color_gr"]),
            "g_ls_period_days": finite_or_none(features["g_ls_best_period_days"]),
            "r_ls_period_days": finite_or_none(features["r_ls_best_period_days"]),
            "g_ls_eligible": expected_g >= 30,
            "r_ls_eligible": expected_r >= 30,
            "classifier_accuracy_evaluated": False,
            "note": "Feature extraction and schema passed on an independent paper source. No prediction score is interpreted as scientific validation because the paper labels are not mapped to the frozen v0.2 taxonomy.",
        }
    )
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
