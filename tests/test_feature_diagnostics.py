from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.features.diagnostics import diagnose_v0_2_feature_eligibility
from ztf_classifier.features.pipeline import extract_v0_2_features


def test_diagnostic_distinguishes_color_from_sample_std_eligibility() -> None:
    observations = pd.DataFrame(
        {
            "mjd": [60000.0, 60001.0, 60000.5],
            "fid": [1, 2, 2],
            "mag": [19.5, 20.0, 20.2],
            "magerr": [0.1, 0.1, 0.1],
        }
    )
    features = extract_v0_2_features(observations)
    report = diagnose_v0_2_feature_eligibility(observations, features)

    assert report["bands"]["g"]["valid_observations"] == 1
    assert report["bands"]["r"]["valid_observations"] == 2
    assert report["cross_band"]["color_features_eligible"] is True
    assert report["cross_band"]["variability_ratio_g_eligible"] is False
    assert report["cross_band"]["variability_ratio_r_eligible"] is True
    assert np.isfinite(features["mean_color_gr"])
    assert np.isnan(features["g_variability_ratio"])
    assert report["non_finite_feature_reasons"]["g_variability_ratio"] == (
        "insufficient_observations_for_sample_std"
    )


def test_diagnostic_reports_insufficient_basic_and_periodicity_observations() -> None:
    observations = pd.DataFrame(
        {
            "mjd": [60000.0 + index for index in range(9)],
            "fid": [1] * 9,
            "mag": [19.0 + index * 0.01 for index in range(9)],
            "magerr": [0.1] * 9,
        }
    )
    features = extract_v0_2_features(observations)
    report = diagnose_v0_2_feature_eligibility(observations, features)

    assert report["bands"]["g"]["basic_features_eligible"] is False
    assert report["bands"]["g"]["periodicity_features_eligible"] is False
    assert report["non_finite_feature_reasons"]["g_mean_mag"] == (
        "insufficient_observations_for_basic_features"
    )
    assert report["non_finite_feature_reasons"]["g_ls_best_period_days"] == (
        "insufficient_observations_for_periodicity_features"
    )
    assert np.isnan(features["g_mean_mag"])


def test_diagnostic_rejects_invalid_rows_using_canonical_preprocessing() -> None:
    observations = pd.DataFrame(
        {
            "mjd": [60000.0, np.nan, 60002.0, 60003.0],
            "fid": [1, 1, 1, 2],
            "mag": [19.0, 19.1, 19.2, 20.0],
            "magerr": [0.1, 0.1, 0.0, 0.1],
        }
    )
    report = diagnose_v0_2_feature_eligibility(observations)

    assert report["bands"]["g"]["input_rows"] == 3
    assert report["bands"]["g"]["valid_observations"] == 1
    assert report["bands"]["g"]["rejected_rows"] == 2
    assert report["bands"]["r"]["valid_observations"] == 1


def test_diagnostic_is_json_serializable_and_does_not_mutate_input() -> None:
    observations = pd.DataFrame(
        {
            "mjd": [60000.0, 60001.0],
            "fid": [1, 2],
            "mag": [19.0, 20.0],
            "magerr": [0.1, 0.1],
        }
    )
    original = observations.copy(deep=True)

    report = diagnose_v0_2_feature_eligibility(observations, {"missing": np.nan})

    json.dumps(report, allow_nan=False)
    pd.testing.assert_frame_equal(observations, original)
    assert report["non_finite_feature_reasons"]["missing"] == (
        "non_finite_despite_eligibility_or_backend_issue"
    )


def test_diagnostic_rejects_missing_schema_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        diagnose_v0_2_feature_eligibility(pd.DataFrame({"mjd": [1.0]}))
