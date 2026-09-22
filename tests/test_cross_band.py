import numpy as np
import pandas as pd
import pytest

from ztf_classifier.features.cross_band import basic_cross_band_features


def test_basic_cross_band_features():
    g_lc = pd.DataFrame(
        {
            "mag": [20.0, 21.0, 19.0, np.nan],
        }
    )

    r_lc = pd.DataFrame(
        {
            "mag": [19.0, 20.0, 18.0, np.nan],
        }
    )

    result = basic_cross_band_features(g_lc, r_lc)

    assert np.isclose(result["mean_color_gr"], 1.0)
    assert np.isclose(result["median_color_gr"], 1.0)
    assert np.isfinite(result["g_variability_ratio"])
    assert np.isfinite(result["r_variability_ratio"])


def test_basic_cross_band_features_empty_band():
    g_lc = pd.DataFrame({"mag": [np.nan, np.inf]})
    r_lc = pd.DataFrame({"mag": [19.0, 20.0]})

    with pytest.raises(
        ValueError,
        match="Both g and r must contain valid magnitudes",
    ):
        basic_cross_band_features(g_lc, r_lc)


def test_basic_cross_band_features_missing_mag():
    g_lc = pd.DataFrame({"mjd": [1.0]})
    r_lc = pd.DataFrame({"mag": [19.0]})

    with pytest.raises(
        ValueError,
        match="Missing required columns in g_lc",
    ):
        basic_cross_band_features(g_lc, r_lc)
