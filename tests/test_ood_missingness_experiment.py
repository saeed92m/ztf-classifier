from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.run_ood_missingness_experiment import run_masking_sensitivity
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
