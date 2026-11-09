import numpy as np
import pytest

from ztf_classifier.models.data_adequacy import DataAdequacyResult


FEATURES = tuple(f"feature_{index}" for index in range(42))


def test_data_adequacy_reports_complete_and_partial_rows() -> None:
    matrix = np.ones((2, 42), dtype=np.float64)
    matrix[1, 1:] = np.nan

    result = DataAdequacyResult.from_matrix(matrix, FEATURES)

    assert result.sample_count == 2
    assert result.status == ("complete", "partial")
    np.testing.assert_array_equal(result.observed_feature_count, [42, 1])
    np.testing.assert_array_equal(result.missing_feature_count, [0, 41])
    np.testing.assert_allclose(result.coverage_fraction, [1.0, 1 / 42])
    assert result.missing_feature_names[0] == ()
    assert result.missing_feature_names[1] == FEATURES[1:]
    assert result.reason_codes == ((), ("MODEL_FEATURES_MISSING",))


def test_data_adequacy_treats_infinities_as_missing() -> None:
    matrix = np.ones((1, 42), dtype=np.float64)
    matrix[0, 0] = np.inf
    matrix[0, 1] = -np.inf
    matrix[0, 2] = np.nan

    result = DataAdequacyResult.from_matrix(matrix, FEATURES)

    assert result.status == ("partial",)
    assert result.observed_feature_count[0] == 39
    assert result.missing_feature_names[0] == FEATURES[:3]


def test_data_adequacy_rejects_invalid_schema() -> None:
    with pytest.raises(ValueError, match="exactly 42 named features"):
        DataAdequacyResult.from_matrix(np.ones((1, 41)), FEATURES[:41])

    with pytest.raises(ValueError, match="unique"):
        DataAdequacyResult.from_matrix(np.ones((1, 42)), ("duplicate",) * 42)


def test_data_adequacy_rejects_non_matrix_input() -> None:
    with pytest.raises(ValueError, match="two-dimensional"):
        DataAdequacyResult.from_matrix(np.ones(42), FEATURES)


def test_data_adequacy_arrays_are_immutable() -> None:
    result = DataAdequacyResult.from_matrix(np.ones((1, 42)), FEATURES)

    with pytest.raises(ValueError):
        result.observed_feature_count[0] = 0
