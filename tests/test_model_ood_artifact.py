import numpy as np
import pytest

from ztf_classifier.models.config import OODConfig
from ztf_classifier.models.ood_artifact import OODArtifact


def _artifact() -> OODArtifact:
    return OODArtifact.from_config(
        OODConfig(),
        np.array(
            [0.10, 0.20, 0.30, 0.40, 0.50],
            dtype=np.float64,
        ),
    )


def test_ood_artifact_preserves_frozen_state():
    artifact = _artifact()

    assert artifact.method == "IsolationForest"
    assert artifact.n_estimators == 300
    assert artifact.contamination == "auto"
    assert artifact.random_state == 42
    assert artifact.n_jobs == 4
    assert artifact.anomaly_thresholds == (
        90.0,
        95.0,
        99.0,
    )
    assert artifact.feature_count == 42
    assert artifact.reference_anomaly_scores == (
        0.10,
        0.20,
        0.30,
        0.40,
        0.50,
    )


def test_ood_artifact_round_trip_dict():
    artifact = _artifact()

    restored = OODArtifact.from_dict(
        artifact.to_dict()
    )

    assert restored == artifact


def test_ood_artifact_computes_reference_percentiles():
    artifact = _artifact()

    scores = np.array(
        [0.10, 0.30, 0.60],
        dtype=np.float64,
    )

    percentiles = artifact.anomaly_percentile(
        scores
    )

    np.testing.assert_allclose(
        percentiles,
        [20.0, 60.0, 100.0],
    )


def test_ood_artifact_computes_reference_ranks():
    artifact = _artifact()

    scores = np.array(
        [0.10, 0.30, 0.60],
        dtype=np.float64,
    )

    ranks = artifact.anomaly_rank(scores)

    np.testing.assert_array_equal(
        ranks,
        [5, 3, 1],
    )


def test_ood_artifact_computes_threshold_flags():
    artifact = _artifact()

    percentiles = np.array(
        [89.0, 95.0, 99.0],
        dtype=np.float64,
    )

    flags = artifact.anomaly_flags(
        percentiles
    )

    np.testing.assert_array_equal(
        flags[90.0],
        [False, True, True],
    )

    np.testing.assert_array_equal(
        flags[95.0],
        [False, True, True],
    )

    np.testing.assert_array_equal(
        flags[99.0],
        [False, False, True],
    )


def test_ood_artifact_rejects_wrong_feature_count():
    with pytest.raises(ValueError, match="42 features"):
        OODArtifact(
            method="IsolationForest",
            n_estimators=300,
            contamination="auto",
            random_state=42,
            n_jobs=4,
            anomaly_thresholds=(90.0,),
            feature_count=41,
            reference_anomaly_scores=(0.1,),
        )


def test_ood_artifact_rejects_empty_reference():
    with pytest.raises(ValueError, match="must not be empty"):
        OODArtifact(
            method="IsolationForest",
            n_estimators=300,
            contamination="auto",
            random_state=42,
            n_jobs=4,
            anomaly_thresholds=(90.0,),
            feature_count=42,
            reference_anomaly_scores=(),
        )


def test_ood_artifact_rejects_invalid_threshold():
    with pytest.raises(ValueError, match="percentages"):
        OODArtifact(
            method="IsolationForest",
            n_estimators=300,
            contamination="auto",
            random_state=42,
            n_jobs=4,
            anomaly_thresholds=(101.0,),
            feature_count=42,
            reference_anomaly_scores=(0.1,),
        )
