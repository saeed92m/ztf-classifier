import numpy as np
import pandas as pd
import pytest

from ztf_classifier.features.basic import basic_band_features


def test_basic_band_features():
    lc = pd.DataFrame(
        {
            "mjd": [1.0, 2.0, 3.0, np.nan],
            "mag": [20.0, 21.0, 19.0, 99.0],
            "magerr": [0.1, 0.2, 0.1, 0.1],
        }
    )

    result = basic_band_features(lc)

    assert result["n_obs"] == 3
    assert result["baseline_days"] == 2.0
    assert np.isfinite(result["weighted_mean_mag"])
    assert result["min_mag"] == 19.0
    assert result["max_mag"] == 21.0


def test_basic_band_features_empty():
    lc = pd.DataFrame(
        {
            "mjd": [1.0],
            "mag": [20.0],
            "magerr": [0.0],
        }
    )

    with pytest.raises(ValueError, match="No valid observations"):
        basic_band_features(lc)
