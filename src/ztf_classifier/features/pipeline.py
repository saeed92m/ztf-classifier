"""Canonical v0.2 feature extraction pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ztf_classifier.features.basic import basic_band_features
from ztf_classifier.features.cross_band import basic_cross_band_features
from ztf_classifier.features.periodicity import lomb_scargle_features
from ztf_classifier.preprocessing.lightcurve import prepare_band_lightcurve

V0_2_FEATURES: tuple[str, ...] = (
    "g_baseline_days",
    "g_ls_best_frequency",
    "g_ls_best_period_days",
    "g_ls_best_power",
    "g_ls_fap",
    "g_ls_max_period_days",
    "g_ls_min_period_days",
    "g_max_mag",
    "g_mean_mag",
    "g_mean_magerr",
    "g_median_mag",
    "g_median_magerr",
    "g_min_mag",
    "g_n_obs",
    "g_p05_mag",
    "g_p25_mag",
    "g_p75_mag",
    "g_p95_mag",
    "g_variability_ratio",
    "g_weighted_mean_mag",
    "mean_color_gr",
    "median_color_gr",
    "r_baseline_days",
    "r_ls_best_frequency",
    "r_ls_best_period_days",
    "r_ls_best_power",
    "r_ls_fap",
    "r_ls_max_period_days",
    "r_ls_min_period_days",
    "r_max_mag",
    "r_mean_mag",
    "r_mean_magerr",
    "r_median_mag",
    "r_median_magerr",
    "r_min_mag",
    "r_n_obs",
    "r_p05_mag",
    "r_p25_mag",
    "r_p75_mag",
    "r_p95_mag",
    "r_variability_ratio",
    "r_weighted_mean_mag",
)

V0_2_FEATURE_SET = frozenset(V0_2_FEATURES)

BASIC_MIN_OBSERVATIONS = 10
LS_MIN_OBSERVATIONS = 30


def _prefixed_basic_features(
    lc: pd.DataFrame,
    band: str,
) -> dict[str, float | int]:
    """Extract basic features and prefix them with the band name."""
    features = basic_band_features(lc)

    return {
        f"{band}_{name}": value
        for name, value in features.items()
    }


def extract_v0_2_features(
    internal_lc: pd.DataFrame,
) -> dict[str, float]:
    """Extract the canonical 42-feature v0.2 feature vector.

    The orchestration rules reproduce the historical v0.2 eligibility:

    - Basic g/r features require >= 10 valid observations.
    - Lomb-Scargle g/r features require >= 30 valid observations.
    - Cross-band features require valid observations in both bands.

    Features that are not eligible are returned as NaN.

    The returned dictionary contains exactly the canonical v0.2
    feature contract in its frozen order.
    """
    required = {"mjd", "fid", "mag", "magerr"}
    missing = required - set(internal_lc.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    # Reuse the canonical preprocessing path.
    g = prepare_band_lightcurve(internal_lc, fid=1)
    r = prepare_band_lightcurve(internal_lc, fid=2)

    features: dict[str, float] = {
        name: np.nan for name in V0_2_FEATURES
    }

    if len(g) >= BASIC_MIN_OBSERVATIONS:
        basic_g = _prefixed_basic_features(g, "g")

        for name in V0_2_FEATURES:
            if name.startswith("g_") and name in basic_g:
                features[name] = basic_g[name]

    if len(r) >= BASIC_MIN_OBSERVATIONS:
        basic_r = _prefixed_basic_features(r, "r")

        for name in V0_2_FEATURES:
            if name.startswith("r_") and name in basic_r:
                features[name] = basic_r[name]

    if len(g) >= LS_MIN_OBSERVATIONS:
        ls_g = lomb_scargle_features(g, "g")

        for name, value in ls_g.items():
            if name in V0_2_FEATURE_SET:
                features[name] = value

    if len(r) >= LS_MIN_OBSERVATIONS:
        ls_r = lomb_scargle_features(r, "r")

        for name, value in ls_r.items():
            if name in V0_2_FEATURE_SET:
                features[name] = value

    if len(g) > 0 and len(r) > 0:
        cross_band = basic_cross_band_features(g, r)

        for name, value in cross_band.items():
            if name in V0_2_FEATURE_SET:
                features[name] = value

    return {
        name: features[name]
        for name in V0_2_FEATURES
    }


def validate_v0_2_feature_vector(
    features: dict[str, float],
) -> None:
    """Validate the canonical v0.2 feature contract."""
    if tuple(features.keys()) != V0_2_FEATURES:
        raise ValueError(
            "Feature vector does not match the canonical v0.2 "
            "feature order."
        )

    if set(features) != V0_2_FEATURE_SET:
        raise ValueError(
            "Feature vector does not contain exactly the canonical "
            "v0.2 feature set."
        )
