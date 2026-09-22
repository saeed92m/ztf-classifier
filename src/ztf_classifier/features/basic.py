"""Basic photometric feature extraction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def basic_band_features(lc: pd.DataFrame) -> dict[str, float | int]:
    """Extract basic photometric features from one ZTF band.

    Required columns:
        mjd, mag, magerr

    Rows with non-finite values or non-positive magerr are ignored.

    The numerical definitions match the historical notebook implementation.
    """
    required = {"mjd", "mag", "magerr"}
    missing = required - set(lc.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = lc[["mjd", "mag", "magerr"]].copy()

    valid = (
        np.isfinite(data["mjd"])
        & np.isfinite(data["mag"])
        & np.isfinite(data["magerr"])
        & (data["magerr"] > 0)
    )
    data = data.loc[valid]

    if data.empty:
        raise ValueError("No valid observations")

    t = data["mjd"].to_numpy(dtype=float)
    x = data["mag"].to_numpy(dtype=float)
    e = data["magerr"].to_numpy(dtype=float)

    median = np.median(x)
    mean = np.mean(x)

    weights = 1.0 / np.square(e)
    weighted_mean = np.sum(weights * x) / np.sum(weights)

    q05, q25, q75, q95 = np.percentile(x, [5, 25, 75, 95])

    mad = np.median(np.abs(x - median))
    residuals = x - weighted_mean
    rms = np.sqrt(np.mean(residuals**2))

    reduced_chi2_like = np.sum(np.square(residuals / e)) / len(x)

    median_abs_norm_resid = np.median(np.abs(residuals / e))

    return {
        "n_obs": len(x),
        "baseline_days": np.max(t) - np.min(t),
        "mean_mag": mean,
        "median_mag": median,
        "weighted_mean_mag": weighted_mean,
        "std_mag": np.std(x, ddof=1),
        "mad_mag": mad,
        "min_mag": np.min(x),
        "max_mag": np.max(x),
        "amplitude_mag": np.max(x) - np.min(x),
        "p05_mag": q05,
        "p25_mag": q25,
        "p75_mag": q75,
        "p95_mag": q95,
        "iqr_mag": q75 - q25,
        "p95_p05_mag": q95 - q05,
        "mean_magerr": np.mean(e),
        "median_magerr": np.median(e),
        "rms_mag": rms,
        "reduced_chi2_like": reduced_chi2_like,
        "median_abs_norm_resid": median_abs_norm_resid,
    }
