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

def test_extract_v0_2_features_cutoff_excludes_future_observations():
    import pandas as pd

    from ztf_classifier.features.pipeline import extract_v0_2_features

    lc = pd.DataFrame(
        {
            "mjd": [
                59000.0, 59001.0, 59002.0, 59003.0,
                59004.0, 59005.0, 59006.0, 59007.0,
                59008.0, 59009.0, 59010.0, 59011.0,
            ],
            "fid": [1] * 12,
            "mag": [
                20.0, 20.1, 19.9, 20.2,
                19.8, 20.3, 19.7, 20.4,
                19.6, 20.5, 19.5, 20.6,
            ],
            "magerr": [0.1] * 12,
        }
    )

    cutoff = 59009.0

    full_features = extract_v0_2_features(lc)
    historical_features = extract_v0_2_features(
        lc,
        cutoff_mjd=cutoff,
    )

    assert historical_features["g_n_obs"] == 10
    assert full_features["g_n_obs"] == 12

    assert historical_features["g_baseline_days"] == 9.0
    assert full_features["g_baseline_days"] == 11.0


def test_cutoff_features_match_explicit_historical_slice():
    import numpy as np
    import pandas as pd

    from ztf_classifier.features.pipeline import (
        V0_2_FEATURES,
        extract_v0_2_features,
    )

    lc = pd.DataFrame(
        {
            "mjd": [
                59000.0, 59001.0, 59002.0, 59003.0,
                59004.0, 59005.0, 59006.0, 59007.0,
                59008.0, 59009.0, 59010.0, 59011.0,
                59000.5, 59001.5, 59002.5, 59003.5,
                59004.5, 59005.5, 59006.5, 59007.5,
                59008.5, 59009.5, 59010.5, 59011.5,
            ],
            "fid": [1] * 12 + [2] * 12,
            "mag": [
                20.0, 20.1, 19.9, 20.2,
                19.8, 20.3, 19.7, 20.4,
                19.6, 20.5, 19.5, 20.6,
                20.2, 20.0, 20.3, 19.9,
                20.4, 19.8, 20.5, 19.7,
                20.6, 19.6, 20.7, 19.5,
            ],
            "magerr": [0.1] * 24,
        }
    )

    cutoff = 59009.0
    historical = lc.loc[lc["mjd"] <= cutoff].copy()

    cutoff_features = extract_v0_2_features(
        lc,
        cutoff_mjd=cutoff,
    )
    explicit_features = extract_v0_2_features(historical)

    assert list(cutoff_features) == list(V0_2_FEATURES)
    assert list(explicit_features) == list(V0_2_FEATURES)

    for name in V0_2_FEATURES:
        left = cutoff_features[name]
        right = explicit_features[name]

        if np.isnan(left) and np.isnan(right):
            continue

        assert np.isclose(
            left,
            right,
            rtol=1e-10,
            atol=1e-12,
        ), f"Feature mismatch: {name}: {left} != {right}"

def test_cutoff_extraction_does_not_mutate_original_light_curve():
    lc = pd.DataFrame(
        {
            "mjd": [
                59000.0, 59001.0, 59002.0, 59003.0,
                59004.0, 59005.0, 59006.0, 59007.0,
                59008.0, 59009.0, 59010.0, 59011.0,
            ],
            "fid": [1] * 12,
            "mag": [
                20.0, 20.1, 19.9, 20.2,
                19.8, 20.3, 19.7, 20.4,
                19.6, 20.5, 19.5, 20.6,
            ],
            "magerr": [0.1] * 12,
        }
    )

    original = lc.copy(deep=True)

    result = extract_v0_2_features(
        lc,
        cutoff_mjd=59009.0,
    )

    assert result["g_n_obs"] == 10
    pd.testing.assert_frame_equal(lc, original)
