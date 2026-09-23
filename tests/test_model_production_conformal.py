"""Tests for production conformal prediction diagnostics."""

from __future__ import annotations

import numpy as np
import pytest

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.conformal_artifact import ConformalArtifact
from ztf_classifier.models.production_conformal import (
    ProductionConformalDiagnostics,
    ProductionConformalResult,
)


def _artifact() -> ConformalArtifact:
    return ConformalArtifact(
        method="split_conformal_ood_diagnostic",
        alphas=(0.05, 0.10, 0.20),
        thresholds=(0.978004645, 0.963176780, 0.918114396),
        calibration_sample_count=150,
    )


def _probabilities() -> np.ndarray:
    probabilities = np.full(
        (3, 15),
        0.01,
        dtype=np.float64,
    )

    probabilities[0] = 0.01
    probabilities[0, 0] = 0.86
    probabilities[0, 1] = 0.13

    probabilities[1] = 0.01
    probabilities[1, 5] = 0.70
    probabilities[1, 6] = 0.16
    probabilities[1, 7] = 0.07

    probabilities[2] = 1.0 / 15.0

    probabilities /= probabilities.sum(axis=1, keepdims=True)

    return probabilities


def test_predict_uses_persisted_thresholds() -> None:
    artifact = _artifact()
    probabilities = _probabilities()

    diagnostics = ProductionConformalDiagnostics.predict(
        probabilities,
        artifact,
    )

    assert isinstance(
        diagnostics,
        ProductionConformalDiagnostics,
    )

    assert diagnostics.sample_count == 3
    assert tuple(
        result.alpha
        for result in diagnostics.results
    ) == (0.05, 0.10, 0.20)

    for result in diagnostics.results:
        assert result.threshold == artifact.threshold_for(
            result.alpha
        )


def test_prediction_sets_have_frozen_class_dimension() -> None:
    diagnostics = ProductionConformalDiagnostics.predict(
        _probabilities(),
        _artifact(),
    )

    for result in diagnostics.results:
        assert result.prediction_sets.shape == (3, 15)
        assert len(result.prediction_set_labels) == 3


def test_prediction_set_labels_match_boolean_sets() -> None:
    diagnostics = ProductionConformalDiagnostics.predict(
        _probabilities(),
        _artifact(),
    )

    result = diagnostics.for_alpha(0.05)

    for row, labels in zip(
        result.prediction_sets,
        result.prediction_set_labels,
    ):
        expected = "|".join(
            MODEL_CLASSES[index]
            for index in np.flatnonzero(row)
        )
        assert labels == expected


def test_for_alpha_returns_persisted_result() -> None:
    diagnostics = ProductionConformalDiagnostics.predict(
        _probabilities(),
        _artifact(),
    )

    result = diagnostics.for_alpha(0.10)

    assert result.alpha == 0.10
    assert result.threshold == _artifact().threshold_for(0.10)


def test_for_alpha_rejects_unknown_alpha() -> None:
    diagnostics = ProductionConformalDiagnostics.predict(
        _probabilities(),
        _artifact(),
    )

    with pytest.raises(
        KeyError,
        match="No persisted conformal result",
    ):
        diagnostics.for_alpha(0.15)


def test_prediction_sets_are_write_protected() -> None:
    diagnostics = ProductionConformalDiagnostics.predict(
        _probabilities(),
        _artifact(),
    )

    result = diagnostics.for_alpha(0.05)

    assert result.prediction_sets.flags.writeable is False

    with pytest.raises(ValueError):
        result.prediction_sets[0, 0] = True


@pytest.mark.parametrize(
    "probabilities",
    [
        np.ones(15),
        np.ones((3, 14)),
        np.full((3, 15), np.nan),
        np.full((3, 15), -0.1),
        np.zeros((3, 15)),
    ],
)
def test_predict_rejects_invalid_probabilities(
    probabilities: np.ndarray,
) -> None:
    with pytest.raises(ValueError):
        ProductionConformalDiagnostics.predict(
            probabilities,
            _artifact(),
        )


def test_result_rejects_mismatched_labels() -> None:
    prediction_sets = np.zeros(
        (2, 15),
        dtype=bool,
    )
    prediction_sets[0, 0] = True

    with pytest.raises(
        ValueError,
        match="labels do not match",
    ):
        ProductionConformalResult(
            alpha=0.05,
            threshold=0.978,
            prediction_sets=prediction_sets,
            prediction_set_labels=("WRONG", ""),
        )


def test_result_is_sample_count_stable() -> None:
    diagnostics = ProductionConformalDiagnostics.predict(
        _probabilities(),
        _artifact(),
    )

    assert all(
        result.sample_count == diagnostics.sample_count
        for result in diagnostics.results
    )
