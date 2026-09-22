import numpy as np
import pandas as pd

from ztf_classifier.preprocessing.lightcurve import prepare_band_lightcurve


def test_prepare_band_filters_invalid_rows_and_sorts():
    internal_lc = pd.DataFrame(
        {
            "mjd": [59003.0, 59001.0, np.nan, 59002.0, 59004.0],
            "fid": [1, 1, 1, 2, 1],
            "mag": [20.3, 20.1, 20.2, 19.8, np.nan],
            "magerr": [0.1, 0.2, 0.1, 0.15, 0.1],
        }
    )

    result = prepare_band_lightcurve(internal_lc, 1)

    assert result["mjd"].tolist() == [59001.0, 59003.0]
    assert result["mag"].tolist() == [20.1, 20.3]
    assert result.index.tolist() == [0, 1]


def test_prepare_band_rejects_non_positive_magerr():
    internal_lc = pd.DataFrame(
        {
            "mjd": [59001.0, 59002.0, 59003.0],
            "fid": [1, 1, 1],
            "mag": [20.0, 20.1, 20.2],
            "magerr": [0.1, 0.0, -0.1],
        }
    )

    result = prepare_band_lightcurve(internal_lc, 1)

    assert len(result) == 1
    assert result["mjd"].tolist() == [59001.0]


def test_prepare_band_returns_empty_for_missing_band():
    internal_lc = pd.DataFrame(
        {
            "mjd": [59001.0],
            "fid": [1],
            "mag": [20.0],
            "magerr": [0.1],
        }
    )

    result = prepare_band_lightcurve(internal_lc, 2)

    assert result.empty
    assert result.columns.tolist() == internal_lc.columns.tolist()
