import numpy as np
import pandas as pd

from ztf_classifier.io.alerce import alerce_to_internal_lc_robust


def test_corrected_photometry_has_priority():
    detections = pd.DataFrame(
        {
            "mjd": ["59002", "59001"],
            "fid": ["2", "1"],
            "magpsf_corr": ["19.1", "20.2"],
            "sigmapsf_corr_ext": ["0.11", "0.22"],
            "magpsf": ["19.5", "20.5"],
            "sigmapsf": ["0.15", "0.25"],
            "ra": ["10.0", "11.0"],
            "dec": ["20.0", "21.0"],
            "dubious": [False, False],
            "corrected": [True, True],
        }
    )

    result = alerce_to_internal_lc_robust(detections)

    assert result["mag"].tolist() == [20.2, 19.1]
    assert result["magerr"].tolist() == [0.22, 0.11]
    assert result["photometry_source"].tolist() == [
        "corrected",
        "corrected",
    ]


def test_invalid_corrected_photometry_falls_back_per_observation():
    detections = pd.DataFrame(
        {
            "mjd": [59001, 59002, 59003],
            "fid": [1, 1, 1],
            "magpsf_corr": [20.0, np.nan, 22.0],
            "sigmapsf_corr_ext": [0.1, 0.2, -1.0],
            "magpsf": [20.5, 21.5, 22.5],
            "sigmapsf": [0.15, 0.25, 0.35],
            "ra": [10.0, 10.0, 10.0],
            "dec": [20.0, 20.0, 20.0],
            "dubious": [False, False, False],
            "corrected": [True, False, False],
        }
    )

    result = alerce_to_internal_lc_robust(detections)

    assert result["mag"].tolist() == [20.0, 21.5, 22.5]
    assert result["magerr"].tolist() == [0.1, 0.25, 0.35]
    assert result["photometry_source"].tolist() == [
        "corrected",
        "raw_fallback",
        "raw_fallback",
    ]


def test_internal_schema_and_sorting():
    detections = pd.DataFrame(
        {
            "mjd": [59003, 59001, 59002],
            "fid": [2, 1, 1],
            "magpsf_corr": [20.3, 20.1, 20.2],
            "sigmapsf_corr_ext": [0.1, 0.1, 0.1],
            "magpsf": [20.4, 20.2, 20.3],
            "sigmapsf": [0.2, 0.2, 0.2],
            "ra": [10, 10, 10],
            "dec": [20, 20, 20],
            "dubious": [False, False, False],
            "corrected": [True, True, True],
        }
    )

    result = alerce_to_internal_lc_robust(detections)

    expected_columns = [
        "mjd",
        "fid",
        "mag",
        "magerr",
        "mag_raw",
        "magerr_raw",
        "mag_corr",
        "magerr_corr",
        "photometry_source",
        "ra",
        "dec",
        "dubious",
        "corrected",
        "source",
    ]

    assert result.columns.tolist() == expected_columns
    assert result["fid"].dtype == "Int64"
    assert result["source"].tolist() == [
        "ALeRCE",
        "ALeRCE",
        "ALeRCE",
    ]

    assert result[["fid", "mjd"]].values.tolist() == [
        [1, 59001.0],
        [1, 59002.0],
        [2, 59003.0],
    ]
