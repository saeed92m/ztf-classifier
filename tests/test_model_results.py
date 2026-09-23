"""Tests for the unified prediction result contract."""

from __future__ import annotations

import numpy as np
import pytest

from ztf_classifier.models.classes import MODEL_CLASSES, NUM_CLASSES
from ztf_classifier.models.results import PredictionResult


def _probabilities(rows: int = 3) -> np.ndarray:
    """Return deterministic valid multiclass probabilities."""
    probabilities = np.full(
        (rows, NUM_CLASSES),
        1.0 / NUM_CLASSES,
        dtype=float,
    )

    for row in range(rows):
        probabilities[row] = 0.0
        probabilities[row, row] = 0.7
        probabilities[row, (row + 1) % NUM_CLASSES] = 0.2
        probabilities[row, (row + 2) % NUM_CLASSES] = 0.1

    return probabilities


def _indices(probabilities: np.ndarray) -> np.ndarray:
    """Return deterministic top-1 class indices."""
    return np.argmax(
        probabilities,
        axis=1,
    ).astype(np.int64)


def _labels(indices: np.ndarray) -> tuple[str, ...]:
    """Convert class indices to frozen labels."""
    return tuple(
        MODEL_CLASSES[index]
        for index in indices
    )


def _result(rows: int = 3) -> PredictionResult:
    """Build a valid minimal prediction result."""
    probabilities = _probabilities(rows)
    indices = _indices(probabilities)

    return PredictionResult(
        raw_probabilities=probabilities,
        raw_predicted_class_indices=indices,
        raw_predicted_labels=_labels(indices),
    )


def test_minimal_result_contract() -> None:
    """A raw inference result is valid without optional diagnostics."""
    result = _result()

    assert result.sample_count == 3
    assert result.has_calibration is False
    assert result.has_conformal is False
    assert result.has_ood is False
    assert result.top1_labels == result.raw_predicted_labels
    np.testing.assert_array_equal(
        result.top1_class_indices,
        result.raw_predicted_class_indices,
    )


def test_calibrated_result_is_preferred_for_top1() -> None:
    """Calibrated predictions become the preferred top-1 output."""
    raw = _probabilities()
    calibrated = np.roll(
        raw,
        shift=1,
        axis=1,
    )

    raw_indices = _indices(raw)
    calibrated_indices = _indices(calibrated)

    result = PredictionResult(
        raw_probabilities=raw,
        raw_predicted_class_indices=raw_indices,
        raw_predicted_labels=_labels(raw_indices),
        calibrated_probabilities=calibrated,
        calibrated_predicted_class_indices=calibrated_indices,
        calibrated_predicted_labels=_labels(calibrated_indices),
    )

    assert result.has_calibration is True
    assert result.top1_labels == result.calibrated_predicted_labels
    np.testing.assert_array_equal(
        result.top1_class_indices,
        calibrated_indices,
    )


def test_calibrated_predictions_require_complete_contract() -> None:
    """Calibrated probabilities require both index and label outputs."""
    raw = _probabilities()

    with pytest.raises(
        ValueError,
        match="Calibrated probabilities require calibrated predictions",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=_indices(raw),
            raw_predicted_labels=_labels(_indices(raw)),
            calibrated_probabilities=raw,
        )


def test_labels_must_match_indices() -> None:
    """Class labels must correspond exactly to class indices."""
    raw = _probabilities()
    indices = _indices(raw)

    invalid_labels = list(_labels(indices))
    invalid_labels[0] = MODEL_CLASSES[(indices[0] + 1) % NUM_CLASSES]

    with pytest.raises(
        ValueError,
        match="labels do not match class indices",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=tuple(invalid_labels),
        )


def test_probability_shape_is_enforced() -> None:
    """The frozen model requires exactly 15 class probabilities."""
    raw = np.ones((3, NUM_CLASSES - 1), dtype=float)
    indices = np.zeros(3, dtype=np.int64)

    with pytest.raises(
        ValueError,
        match="must contain 15 classes",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(indices),
        )


def test_probability_simplex_is_enforced() -> None:
    """Probability rows must sum to one."""
    raw = _probabilities()
    raw[0, 0] += 0.05
    indices = _indices(raw)

    with pytest.raises(
        ValueError,
        match="do not sum to one",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(indices),
        )


def test_non_finite_probabilities_are_rejected() -> None:
    """Non-finite probabilities are invalid."""
    raw = _probabilities()
    raw[0, 0] = np.nan
    indices = np.zeros(3, dtype=np.int64)

    with pytest.raises(
        ValueError,
        match="non-finite values",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(indices),
        )


def test_negative_probabilities_are_rejected() -> None:
    """Negative probabilities are invalid."""
    raw = _probabilities()
    raw[0, 0] = -0.1
    indices = np.zeros(3, dtype=np.int64)

    with pytest.raises(
        ValueError,
        match="negative values",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(indices),
        )


def test_prediction_indices_are_range_checked() -> None:
    """Class indices must remain inside the frozen 0..14 range."""
    raw = _probabilities()
    indices = np.zeros(3, dtype=np.int64)
    indices[0] = NUM_CLASSES

    with pytest.raises(
        ValueError,
        match="class indices are out of range",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(
                np.zeros(3, dtype=np.int64),
            ),
        )


def test_optional_conformal_result_must_align() -> None:
    """Conformal diagnostics must have the same sample count."""
    raw = _probabilities()
    indices = _indices(raw)

    class FakeConformal:
        sample_count = 2

    with pytest.raises(
        ValueError,
        match="Conformal result sample count",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(indices),
            conformal=FakeConformal(),  # type: ignore[arg-type]
        )


def test_optional_ood_result_must_align() -> None:
    """OOD diagnostics must have the same sample count."""
    raw = _probabilities()
    indices = _indices(raw)

    class FakeOOD:
        sample_count = 2

    with pytest.raises(
        ValueError,
        match="OOD result sample count",
    ):
        PredictionResult(
            raw_probabilities=raw,
            raw_predicted_class_indices=indices,
            raw_predicted_labels=_labels(indices),
            ood=FakeOOD(),  # type: ignore[arg-type]
        )


def test_result_is_frozen() -> None:
    """The dataclass contract must be immutable."""
    result = _result()

    with pytest.raises(
        AttributeError,
    ):
        result.raw_probabilities = np.zeros(
            (3, NUM_CLASSES),
        )


def test_arrays_are_normalized_to_expected_dtypes() -> None:
    """Inputs are normalized to stable production dtypes."""
    raw = _probabilities()
    indices = _indices(raw)

    result = PredictionResult(
        raw_probabilities=raw.astype(np.float32),
        raw_predicted_class_indices=indices.astype(np.int32),
        raw_predicted_labels=_labels(indices),
    )

    assert result.raw_probabilities.dtype == np.float64
    assert result.raw_predicted_class_indices.dtype == np.int64
