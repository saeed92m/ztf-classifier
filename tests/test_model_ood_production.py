"""Tests for persisted production OOD inference state."""

from __future__ import annotations

import numpy as np
import pytest

from ztf_classifier.models.config import OODConfig
from ztf_classifier.models.ood_production import OODProductionModel


def _features() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.normal(size=(150, 42))


def test_fit_predict_is_deterministic() -> None:
    X = _features()

    first = OODProductionModel(OODConfig()).fit(X)
    second = OODProductionModel(OODConfig()).fit(X)

    first_scores = first.anomaly_scores(X)
    second_scores = second.anomaly_scores(X)

    assert np.array_equal(first_scores, second_scores)


def test_fit_produces_reference_anomaly_scores() -> None:
    X = _features()

    fitted = OODProductionModel(OODConfig()).fit(X)

    scores = fitted.reference_anomaly_scores

    assert scores.shape == (150,)
    assert scores.dtype == np.float64
    assert np.isfinite(scores).all()


def test_anomaly_scores_are_negative_normality_scores() -> None:
    X = _features()

    fitted = OODProductionModel(OODConfig()).fit(X)

    scores = fitted.anomaly_scores(X)
    normality = fitted.normality_scores(X)

    assert np.allclose(
        scores,
        -normality,
        rtol=0.0,
        atol=1e-12,
    )


def test_predict_labels_are_binary_isolation_forest_labels() -> None:
    X = _features()

    fitted = OODProductionModel(OODConfig()).fit(X)

    labels = fitted.labels(X)

    assert labels.shape == (150,)
    assert set(labels.tolist()).issubset({-1, 1})


def test_wrong_feature_count_is_rejected() -> None:
    X = _features()

    fitted = OODProductionModel(OODConfig()).fit(X)

    with pytest.raises(ValueError, match="42 features"):
        fitted.anomaly_scores(X[:, :41])


def test_persistence_roundtrip(tmp_path) -> None:
    X = _features()

    fitted = OODProductionModel(OODConfig()).fit(X)

    path = tmp_path / "ood_model.joblib"
    fitted.save(path)

    loaded = OODProductionModel.load(path)

    assert np.array_equal(
        fitted.reference_anomaly_scores,
        loaded.reference_anomaly_scores,
    )

    assert np.array_equal(
        fitted.anomaly_scores(X),
        loaded.anomaly_scores(X),
    )

    assert np.array_equal(
        fitted.normality_scores(X),
        loaded.normality_scores(X),
    )

    assert np.array_equal(
        fitted.labels(X),
        loaded.labels(X),
    )


def test_save_refuses_existing_path(tmp_path) -> None:
    X = _features()

    fitted = OODProductionModel(OODConfig()).fit(X)

    path = tmp_path / "ood_model.joblib"
    fitted.save(path)

    with pytest.raises(FileExistsError):
        fitted.save(path)


def test_load_requires_existing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        OODProductionModel.load(
            tmp_path / "missing.joblib"
        )


def test_unfitted_model_rejects_inference() -> None:
    model = OODProductionModel(OODConfig())

    X = _features()

    with pytest.raises(
        RuntimeError,
        match="has not been fitted",
    ):
        model.anomaly_scores(X)


def test_unfitted_model_rejects_save(tmp_path) -> None:
    model = OODProductionModel(OODConfig())

    with pytest.raises(
        RuntimeError,
        match="has not been fitted",
    ):
        model.save(tmp_path / "ood_model.joblib")


def test_load_rejects_invalid_state_version(tmp_path) -> None:
    path = tmp_path / "ood_model.joblib"

    joblib = pytest.importorskip("joblib")

    joblib.dump(
        {
            "state_version": "999.0",
        },
        path,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported OOD production model state version",
    ):
        OODProductionModel.load(path)


def test_load_rejects_missing_state_fields(tmp_path) -> None:
    path = tmp_path / "ood_model.joblib"

    joblib = pytest.importorskip("joblib")

    joblib.dump(
        {
            "state_version": "1.0",
            "config": OODConfig(),
        },
        path,
    )

    with pytest.raises(
        ValueError,
        match="missing",
    ):
        OODProductionModel.load(path)


def test_load_rejects_invalid_state_type(tmp_path) -> None:
    path = tmp_path / "ood_model.joblib"

    joblib = pytest.importorskip("joblib")

    joblib.dump(
        [],
        path,
    )

    with pytest.raises(
        TypeError,
        match="must be a dictionary",
    ):
        OODProductionModel.load(path)
