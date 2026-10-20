#!/usr/bin/env python3
"""Run the frozen v0.2 feature engine on one small external ZTF light curve."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from ztf_classifier.features.pipeline import (
    V0_2_FEATURES,
    extract_v0_2_features,
    validate_v0_2_feature_vector,
)

URL = (
    "https://raw.githubusercontent.com/light-curve/test-data/"
    "master/SNIa/light-curves/ZTF18aahatvc.csv"
)
EXPECTED_GIT_BLOB_SHA1 = "92d75069f519073b36f0d27057034a82481d7ba5"
HISTORICAL_CUTOFF_MJD = 59447.224132


def main() -> None:
    request = urllib.request.Request(
        URL, headers={"User-Agent": "ztf-classifier-independent-validation/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()

    git_blob_sha1 = hashlib.sha1(
        b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    ).hexdigest()
    if git_blob_sha1 != EXPECTED_GIT_BLOB_SHA1:
        raise RuntimeError(
            f"Raw light-curve Git blob SHA-1 mismatch: {git_blob_sha1}"
        )

    with TemporaryDirectory(prefix="ztf-bts-lightcurve-") as tmp:
        path = Path(tmp) / "ZTF18aahatvc.csv"
        path.write_bytes(payload)
        raw = pd.read_csv(path)

    required = {"time", "mag", "magerr", "band"}
    if not required.issubset(raw.columns):
        raise RuntimeError(f"Raw light curve missing columns: {sorted(required - set(raw.columns))}")

    bands = raw["band"].astype("string").str.strip().str.lower()
    fid = bands.map({"g": 1, "r": 2})
    if fid.isna().any():
        raise RuntimeError(f"Unexpected band values: {sorted(bands[fid.isna()].unique().tolist())}")

    internal = pd.DataFrame(
        {
            "mjd": pd.to_numeric(raw["time"], errors="coerce"),
            "fid": fid.astype("int64"),
            "mag": pd.to_numeric(raw["mag"], errors="coerce"),
            "magerr": pd.to_numeric(raw["magerr"], errors="coerce"),
        }
    )
    if internal.isna().any().any() or not np.isfinite(internal.to_numpy(dtype=float)).all():
        raise RuntimeError("Input light curve contains invalid numeric observations")
    if (internal["magerr"] <= 0).any():
        raise RuntimeError("Input light curve contains non-positive magnitude errors")

    features = extract_v0_2_features(
        internal, cutoff_mjd=HISTORICAL_CUTOFF_MJD
    )
    validate_v0_2_feature_vector(features)

    g_count = int((internal["fid"] == 1).sum())
    r_count = int((internal["fid"] == 2).sum())
    if g_count < 10 or r_count < 10:
        raise RuntimeError(
            f"Fixture must exercise basic g/r features; got g={g_count}, r={r_count}"
        )
    if features["g_n_obs"] != g_count or features["r_n_obs"] != r_count:
        raise RuntimeError("Feature engine observation counts do not match input")
    if not np.isfinite([features["g_mean_mag"], features["r_mean_mag"]]).all():
        raise RuntimeError("Expected basic g/r features are non-finite")
    if not np.isnan(features["g_ls_best_period_days"]) or not np.isnan(
        features["r_ls_best_period_days"]
    ):
        raise RuntimeError("Lomb-Scargle features should be ineligible below 30 points per band")

    report = {
        "result": "PASS",
        "source": "light-curve/test-data SNIa ZTF BTS sample",
        "object_id": "ZTF18aahatvc",
        "source_url": URL,
        "git_blob_sha1": git_blob_sha1,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "input_rows": len(internal),
        "g_observations": g_count,
        "r_observations": r_count,
        "cutoff_mjd": HISTORICAL_CUTOFF_MJD,
        "feature_count": len(features),
        "feature_order_matches_frozen_v0_2": tuple(features) == V0_2_FEATURES,
        "g_mean_mag": features["g_mean_mag"],
        "r_mean_mag": features["r_mean_mag"],
        "g_ls_period_days": None,
        "r_ls_period_days": None,
        "note": (
            "Feature extraction passed. Lomb-Scargle periods are correctly "
            "ineligible because this sample has fewer than 30 observations "
            "in each band. This is not a classifier-accuracy test."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
