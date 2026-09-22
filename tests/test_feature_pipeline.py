import numpy as np
import pandas as pd

from ztf_classifier.features.pipeline import (
    BASIC_MIN_OBSERVATIONS,
    LS_MIN_OBSERVATIONS,
    V0_2_FEATURES,
    extract_v0_2_features,
    validate_v0_2_feature_vector,
)


def make_band(
    fid: int,
    n: int,
    period: float = 5.0,
) -> pd.DataFrame:
    t = np.linspace(0.0, 100.0, n)
    mag = 20.0 + 0.5 * np.sin(2.0 * np.pi * t / period)

    return pd.DataFrame(
        {
            "mjd": t,
            "fid": fid,
            "mag": mag,
            "magerr": np.full(n, 0.02),
        }
    )


def test_v0_2_feature_contract_has_exactly_42_features():
    assert len(V0_2_FEATURES) == 42
    assert len(set(V0_2_FEATURES)) == 42


def test_v0_2_pipeline_returns_exact_contract():
    internal = pd.concat(
        [
            make_band(1, 40),
            make_band(2, 40),
        ],
        ignore_index=True,
    )

    result = extract_v0_2_features(internal)

    assert tuple(result.keys()) == V0_2_FEATURES
    assert len(result) == 42

    validate_v0_2_feature_vector(result)


def test_basic_features_require_ten_observations():
    internal = pd.concat(
        [
            make_band(1, BASIC_MIN_OBSERVATIONS - 1),
            make_band(2, BASIC_MIN_OBSERVATIONS),
        ],
        ignore_index=True,
    )

    result = extract_v0_2_features(internal)

    assert np.isnan(result["g_n_obs"])
    assert np.isnan(result["g_mean_mag"])

    assert result["r_n_obs"] == BASIC_MIN_OBSERVATIONS


def test_lomb_scargle_requires_thirty_observations():
    internal = pd.concat(
        [
            make_band(1, LS_MIN_OBSERVATIONS - 1),
            make_band(2, LS_MIN_OBSERVATIONS),
        ],
        ignore_index=True,
    )

    result = extract_v0_2_features(internal)

    assert np.isnan(result["g_ls_best_period_days"])
    assert np.isnan(result["g_ls_best_power"])

    assert np.isfinite(result["r_ls_best_period_days"])
    assert np.isfinite(result["r_ls_best_power"])


def test_cross_band_features_require_both_bands():
    internal = make_band(1, 40)

    result = extract_v0_2_features(internal)

    assert np.isnan(result["mean_color_gr"])
    assert np.isnan(result["median_color_gr"])


def test_invalid_rows_are_not_counted_for_eligibility():
    g = make_band(1, 30)
    g.loc[:20, "magerr"] = 0.0

    r = make_band(2, 30)

    internal = pd.concat([g, r], ignore_index=True)

    result = extract_v0_2_features(internal)

    assert np.isnan(result["g_n_obs"])
    assert np.isnan(result["g_ls_best_period_days"])
    assert result["r_n_obs"] == 30
