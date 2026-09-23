"""Integration tests for inference, calibration, and result assembly."""

from __future__ import annotations

import numpy as np

from ztf_classifier.models.calibration import TemperatureScaler
from ztf_classifier.models.classes import MODEL_CLASSES, NUM_CLASSES
from ztf_classifier.models.inference import InferenceResult
from ztf_classifier.models.result_builder import PredictionResultBuilder


def _probabilities(rows: int = 4) -> np.ndarray:
    """Return deterministic valid multiclass probabilities."""
    probabilities = np.full(
        (rows, NUM_CLASSES),
        0.01 / (NUM_CLASSES - 2),
        dtype=np.float64,
    )

    for row in range(rows):
        probabilities[row, row] = 0.80
        probabilities[row, (row + 1) % NUM_CLASSES] = 0.19

    return probabilities


def _inference(probabilities: np.ndarray) -> InferenceResult:
    """Build an inference result from probabilities."""
    indices = np.argmax(
        probabilities,
        axis=1,
    ).astype(np.int64)

    labels = tuple(
        MODEL_CLASSES[index]
        for index in indices
    )

    return InferenceResult(
        probabilities=probabilities,
        predicted_class_indices=indices,
        predicted_labels=labels,
    )


def test_calibrated_probabilities_are_assembled_without_refitting() -> None:
    """Builder consumes an already-calibrated probability matrix."""
    raw = _probabilities()
    inference = _inference(raw)

    scaler = TemperatureScaler()

    temperature = 1.5

    calibrated = scaler.transform(
        raw,
        temperature,
    )

    result = PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    assert result.sample_count == 4
    assert result.has_calibration is True

    np.testing.assert_array_equal(
        result.raw_probabilities,
        raw,
    )

    np.testing.assert_array_equal(
        result.calibrated_probabilities,
        calibrated,
    )

    expected_indices = np.argmax(
        calibrated,
        axis=1,
    ).astype(np.int64)

    np.testing.assert_array_equal(
        result.calibrated_predicted_class_indices,
        expected_indices,
    )


def test_calibration_preserves_probability_simplex() -> None:
    """The integrated calibrated output remains a valid simplex."""
    raw = _probabilities()
    inference = _inference(raw)

    calibrated = TemperatureScaler().transform(
        raw,
        1.02685019,
    )

    result = PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    assert np.isfinite(
        result.calibrated_probabilities
    ).all()

    assert (
        result.calibrated_probabilities >= 0.0
    ).all()

    np.testing.assert_allclose(
        result.calibrated_probabilities.sum(axis=1),
        1.0,
        rtol=0.0,
        atol=1e-12,
    )


def test_calibration_does_not_change_raw_prediction() -> None:
    """Calibration is attached independently from raw inference."""
    raw = _probabilities()
    inference = _inference(raw)

    calibrated = TemperatureScaler().transform(
        raw,
        1.02685019,
    )

    result = PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    np.testing.assert_array_equal(
        result.raw_predicted_class_indices,
        inference.predicted_class_indices,
    )

    assert (
        result.raw_predicted_labels
        == inference.predicted_labels
    )
