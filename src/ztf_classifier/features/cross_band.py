"""Cross-band photometric feature extraction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def basic_cross_band_features(
    g_lc: pd.DataFrame,
    r_lc: pd.DataFrame,
) -> dict[str, float]:
    """Extract basic g/r cross-band features.

    The numerical definitions match the historical notebook
    implementation.

    Required columns:
        mag

    Non-finite magnitudes are ignored independently in each band.
    """
    required = {"mag"}

    missing_g = required - set(g_lc.columns)
    missing_r = required - set(r_lc.columns)

    if missing_g:
        raise ValueError(
            f"Missing required columns in g_lc: {sorted(missing_g)}"
        )

    if missing_r:
        raise ValueError(
            f"Missing required columns in r_lc: {sorted(missing_r)}"
        )

    g = g_lc["mag"].to_numpy(dtype=float)
    r = r_lc["mag"].to_numpy(dtype=float)

    g = g[np.isfinite(g)]
    r = r[np.isfinite(r)]

    if len(g) == 0 or len(r) == 0:
        raise ValueError("Both g and r must contain valid magnitudes.")

    g_mean = np.mean(g)
    r_mean = np.mean(r)

    g_median = np.median(g)
    r_median = np.median(r)

    return {
        "mean_color_gr": g_mean - r_mean,
        "median_color_gr": g_median - r_median,
        "g_variability_ratio": np.std(g, ddof=1) / np.mean(g),
        "r_variability_ratio": np.std(r, ddof=1) / np.mean(r),
    }
