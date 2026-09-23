import numpy as np
import pytest

from ztf_classifier.models.conformal import (
    EmpiricalConformalPredictor,
)
from ztf_classifier.models.conformal_artifact import (
    ConformalArtifact,
)


def _artifact() -> ConformalArtifact:
    probabilities = np.eye(15, dtype=np.float64)
    y_true = np.arange(15, dtype=np.int64)

    results = EmpiricalConformalPredictor().fit_all(
        probabilities,
        y_true,
    )

    return ConformalArtifact.from_results(results)


def test_conformal_artifact_preserves_frozen_state():
    artifact = _artifact()

    assert artifact.method == "split_conformal_ood_diagnostic"
    assert artifact.alphas == (0.05, 0.10, 0.20)
    assert len(artifact.thresholds) == 3
    assert artifact.calibration_sample_count == 15
    assert len(artifact.classes) == 15


def test_conformal_artifact_round_trip_dict():
    artifact = _artifact()

    restored = ConformalArtifact.from_dict(
        artifact.to_dict()
    )

    assert restored == artifact


def test_conformal_artifact_applies_persisted_thresholds():
    artifact = _artifact()

    probabilities = np.full(
        (2, 15),
        1.0 / 15.0,
        dtype=np.float64,
    )

    prediction_sets = artifact.predict_sets(
        probabilities,
        0.10,
    )

    assert prediction_sets.shape == (2, 15)
    assert prediction_sets.dtype == bool


def test_conformal_artifact_rejects_unknown_alpha():
    artifact = _artifact()

    with pytest.raises(ValueError, match="Unsupported"):
        artifact.threshold_for(0.15)


def test_conformal_artifact_rejects_wrong_class_count():
    with pytest.raises(ValueError, match="15 classes"):
        ConformalArtifact(
            method="split_conformal_ood_diagnostic",
            alphas=(0.05,),
            thresholds=(0.95,),
            calibration_sample_count=10,
            classes=("AGN",),
        )


def test_conformal_artifact_rejects_invalid_threshold():
    with pytest.raises(ValueError, match="thresholds"):
        ConformalArtifact(
            method="split_conformal_ood_diagnostic",
            alphas=(0.05,),
            thresholds=(1.5,),
            calibration_sample_count=10,
        )


def test_conformal_artifact_rejects_non_simplex_probabilities():
    artifact = _artifact()

    probabilities = np.ones(
        (2, 15),
        dtype=np.float64,
    )

    with pytest.raises(ValueError, match="sum to one"):
        artifact.predict_sets(
            probabilities,
            0.05,
        )
