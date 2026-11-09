from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.run_ood_missingness_experiment import (
    build_feature_group_mapping,
    build_feature_masking_scenarios,
    build_natural_missingness_patterns,
    run_family_masking_sensitivity,
    run_masking_sensitivity,
)
from ztf_classifier.models.config import OODConfig
from ztf_classifier.models.ood_artifact import OODArtifact
from ztf_classifier.models.ood_production import OODProductionModel


def _fitted_reference() -> tuple[np.ndarray, OODProductionModel, OODArtifact]:
    X = np.random.default_rng(73).normal(size=(24, 42))
    config = OODConfig()
    model = OODProductionModel(config).fit(X)
    assert model.reference_anomaly_scores is not None
    reference = OODArtifact.from_config(config, model.reference_anomaly_scores)
    return X, model, reference


def test_masking_sensitivity_is_deterministic_and_does_not_mutate_input() -> None:
    X, model, reference = _fitted_reference()
    original = X.copy()
    oids = [f"ZTF_TEST_{index:03d}" for index in range(len(X))]
    labels = ["TEST"] * len(X)

    first_rows, first_summary = run_masking_sensitivity(
        X,
        oids,
        labels,
        model,
        reference,
        masked_feature_counts=(1, 41),
        replicates=2,
        random_seed=11,
    )
    second_rows, second_summary = run_masking_sensitivity(
        X,
        oids,
        labels,
        model,
        reference,
        masked_feature_counts=(1, 41),
        replicates=2,
        random_seed=11,
    )

    pd.testing.assert_frame_equal(first_rows, second_rows)
    pd.testing.assert_frame_equal(first_summary, second_summary)
    np.testing.assert_array_equal(X, original)
    assert set(first_rows["observed_feature_count"]) == {1, 41}
    assert np.isfinite(first_rows["masked_anomaly_score"]).all()
    assert np.isfinite(first_rows["masked_anomaly_percentile"]).all()
    assert set(first_summary["masked_feature_count"]) == {1, 41}
    for threshold in (90, 95, 99):
        assert (
            first_summary[f"suppressed_flag_count_{threshold}"]
            + first_summary[f"new_flag_count_{threshold}"]
            == first_summary[f"flag_flip_count_{threshold}"]
        ).all()


def test_masking_sensitivity_rejects_incomplete_baseline_rows() -> None:
    X, model, reference = _fitted_reference()
    X[0, 0] = np.nan

    with pytest.raises(ValueError, match="complete rows"):
        run_masking_sensitivity(
            X,
            [f"OID_{index}" for index in range(len(X))],
            ["TEST"] * len(X),
            model,
            reference,
            masked_feature_counts=(1,),
            replicates=1,
        )


def test_feature_groups_partition_the_frozen_v02_schema() -> None:
    from ztf_classifier.features.pipeline import V0_2_FEATURES

    groups = build_feature_group_mapping()
    group_features = [feature for definition in groups.values() for feature in definition["features"]]

    assert set(groups) == {
        "g_basic",
        "g_periodicity",
        "r_basic",
        "r_periodicity",
        "cross_band_color",
        "g_variability_ratio",
        "r_variability_ratio",
    }
    assert len(group_features) == len(set(group_features)) == 42
    assert set(group_features) == set(V0_2_FEATURES)
    assert {name: len(item["features"]) for name, item in groups.items()} == {
        "g_basic": 13,
        "g_periodicity": 6,
        "r_basic": 13,
        "r_periodicity": 6,
        "cross_band_color": 2,
        "g_variability_ratio": 1,
        "r_variability_ratio": 1,
    }
    assert groups["g_variability_ratio"]["minimum_valid_observations"] == 2
    assert groups["r_variability_ratio"]["minimum_valid_observations"] == 2


def test_extraction_mask_scenarios_match_v02_eligibility_thresholds() -> None:
    groups = build_feature_group_mapping()
    scenarios = build_feature_masking_scenarios(groups)

    expected = {
        "g_periodicity_unavailable": 6,
        "r_periodicity_unavailable": 6,
        "both_periodicity_unavailable": 12,
        "g_low_observation_2_to_9": 19,
        "r_low_observation_2_to_9": 19,
        "g_single_observation": 20,
        "r_single_observation": 20,
        "g_band_absent": 23,
        "r_band_absent": 23,
        "both_bands_low_observation_2_to_9": 38,
        "both_bands_single_observation": 40,
        "g_low_2_to_9_r_low_10_to_29": 25,
        "r_low_2_to_9_g_low_10_to_29": 25,
        "g_single_r_low_10_to_29": 26,
        "r_single_g_low_10_to_29": 26,
        "g_band_absent_r_low_10_to_29": 29,
        "r_band_absent_g_low_10_to_29": 29,
    }
    assert {
        name: scenario["missing_feature_count"] for name, scenario in scenarios.items()
    } == expected


def test_family_masking_is_deterministic_and_matches_natural_patterns() -> None:
    X, model, reference = _fitted_reference()
    groups = build_feature_group_mapping()
    scenarios = build_feature_masking_scenarios(groups)
    original = X.copy()
    oids = [f"ZTF_TEST_{index:03d}" for index in range(len(X))]
    labels = ["TEST"] * len(X)

    first_rows, first_summary = run_family_masking_sensitivity(
        X, oids, labels, model, reference, scenarios
    )
    second_rows, second_summary = run_family_masking_sensitivity(
        X, oids, labels, model, reference, scenarios
    )

    pd.testing.assert_frame_equal(first_rows, second_rows)
    pd.testing.assert_frame_equal(first_summary, second_summary)
    np.testing.assert_array_equal(X, original)
    assert len(first_summary) == len(scenarios)
    assert len(first_rows) == len(X) * len(scenarios)
    for threshold in (90, 95, 99):
        assert (
            first_summary[f"suppressed_flag_count_{threshold}"]
            + first_summary[f"new_flag_count_{threshold}"]
            == first_summary[f"flag_flip_count_{threshold}"]
        ).all()

    natural = X.copy()
    natural[0, :] = np.nan
    natural[0, :4] = X[0, :4]
    natural[1, :] = np.nan
    from ztf_classifier.features.pipeline import V0_2_FEATURES

    missing_names = set(
        scenarios["both_bands_low_observation_2_to_9"]["missing_features"]
    )
    observed_indices = [
        index
        for index, feature in enumerate(V0_2_FEATURES)
        if feature not in missing_names
    ]
    natural[1, observed_indices] = X[1, observed_indices]
    patterns, summary = build_natural_missingness_patterns(
        natural, oids, labels, scenarios
    )
    assert patterns.iloc[0]["matched_extraction_pattern"] == "unmatched"
    assert (
        patterns.iloc[1]["matched_extraction_pattern"]
        == "both_bands_low_observation_2_to_9"
    )
    assert summary["object_count"] == len(X)
