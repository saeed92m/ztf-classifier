"""Tests for prediction result assembly."""

from __future__ import annotations

import numpy as np

from ztf_classifier.models.classes import MODEL_CLASSES, NUM_CLASSES
from ztf_classifier.models.inference import InferenceResult
from ztf_classifier.models.result_builder import PredictionResultBuilder


def _probabilities(rows: int = 3) -> np.ndarray:
    """Return deterministic valid multiclass probabilities."""
    probabilities = np.zeros(
        (rows, NUM_CLASSES),
        dtype=np.float64,
    )

    for row in range(rows):
        probabilities[row, row] = 0.7
        probabilities[row, (row + 1) % NUM_CLASSES] = 0.2
        probabilities[row, (row + 2) % NUM_CLASSES] = 0.1

    return probabilities


def _inference() -> InferenceResult:
    """Build a deterministic inference result."""
    probabilities = _probabilities()
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


def test_builder_preserves_raw_inference() -> None:
    """Raw inference outputs are preserved exactly."""
    inference = _inference()

    result = PredictionResultBuilder.build(
        inference,
    )

    np.testing.assert_array_equal(
        result.raw_probabilities,
        inference.probabilities,
    )

    np.testing.assert_array_equal(
        result.raw_predicted_class_indices,
        inference.predicted_class_indices,
    )

    assert result.raw_predicted_labels == inference.predicted_labels

    assert result.has_calibration is False
    assert result.has_conformal is False
    assert result.has_ood is False


def test_builder_derives_calibrated_top1() -> None:
    """Calibrated probabilities produce calibrated top-1 output."""
    inference = _inference()

    calibrated = np.roll(
        inference.probabilities,
        shift=1,
        axis=1,
    )

    result = PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    expected_indices = np.argmax(
        calibrated,
        axis=1,
    ).astype(np.int64)

    expected_labels = tuple(
        MODEL_CLASSES[index]
        for index in expected_indices
    )

    np.testing.assert_array_equal(
        result.calibrated_probabilities,
        calibrated,
    )

    np.testing.assert_array_equal(
        result.calibrated_predicted_class_indices,
        expected_indices,
    )

    assert result.calibrated_predicted_labels == expected_labels

    assert result.has_calibration is True
    assert result.top1_labels == expected_labels


def test_builder_does_not_modify_calibrated_input() -> None:
    """Assembly must not mutate the supplied probability matrix."""
    inference = _inference()

    calibrated = np.roll(
        inference.probabilities,
        shift=1,
        axis=1,
    )
    original = calibrated.copy()

    PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    np.testing.assert_array_equal(
        calibrated,
        original,
    )


def test_builder_accepts_optional_diagnostics() -> None:
    """Conformal and OOD diagnostics are passed through unchanged."""
    inference = _inference()

    class FakeConformal:
        sample_count = 3

    class FakeOOD:
        sample_count = 3

    conformal = FakeConformal()
    ood = FakeOOD()

    result = PredictionResultBuilder.build(
        inference,
        conformal=conformal,  # type: ignore[arg-type]
        ood=ood,  # type: ignore[arg-type]
    )

    assert result.conformal is conformal
    assert result.ood is ood
    assert result.has_conformal is True
    assert result.has_ood is True


def test_builder_keeps_raw_top1_without_calibration() -> None:
    """Raw top-1 remains the preferred output without calibration."""
    inference = _inference()

    result = PredictionResultBuilder.build(
        inference,
    )

    assert result.top1_labels == inference.predicted_labels

    np.testing.assert_array_equal(
        result.top1_class_indices,
        inference.predicted_class_indices,
    )


def test_builder_is_deterministic() -> None:
    """Identical inputs produce identical assembled results."""
    inference = _inference()

    calibrated = np.roll(
        inference.probabilities,
        shift=1,
        axis=1,
    )

    first = PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    second = PredictionResultBuilder.build(
        inference,
        calibrated_probabilities=calibrated,
    )

    np.testing.assert_array_equal(
        first.raw_probabilities,
        second.raw_probabilities,
    )

    np.testing.assert_array_equal(
        first.calibrated_probabilities,
        second.calibrated_probabilities,
    )

    np.testing.assert_array_equal(
        first.top1_class_indices,
        second.top1_class_indices,
    )

    assert first.top1_labels == second.top1_labels
