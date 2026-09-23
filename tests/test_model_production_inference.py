from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.production_inference import (
    ProductionInferenceService,
)
from ztf_classifier.models.results import PredictionResult

ARTIFACT = Path(
    "runs/model_baseline_v0.2_production/artifact"
)
DATASET = Path(
    "data/processed/features_v0.2.parquet"
)


def _load_dataset() -> pd.DataFrame:
    return pd.read_parquet(DATASET)


def _build_service() -> ProductionInferenceService:
    return ProductionInferenceService(ARTIFACT)


def test_service_loads_production_artifact() -> None:
    service = _build_service()

    assert service.artifact_dir == ARTIFACT.resolve()
    assert service.loaded_artifact.model_artifact.model_version == (
        "baseline_v0.2"
    )
    assert service.loaded_artifact.model_artifact.model_family == (
        "XGBoost"
    )


def test_service_returns_prediction_result() -> None:
    service = _build_service()
    dataset = _load_dataset()

    result = service.predict(dataset)

    assert isinstance(result, PredictionResult)
    assert result.sample_count == 150

    assert result.raw_probabilities.shape == (150, 15)
    assert result.calibrated_probabilities is not None
    assert result.calibrated_probabilities.shape == (150, 15)

    assert len(result.raw_predicted_labels) == 150
    assert result.calibrated_predicted_labels is not None
    assert len(result.calibrated_predicted_labels) == 150


def test_service_returns_valid_calibrated_probabilities() -> None:
    service = _build_service()
    dataset = _load_dataset()

    result = service.predict(dataset)

    probabilities = result.calibrated_probabilities
    assert probabilities is not None

    assert np.isfinite(probabilities).all()
    assert (probabilities >= 0.0).all()

    np.testing.assert_allclose(
        probabilities.sum(axis=1),
        1.0,
        rtol=0.0,
        atol=1e-12,
    )


def test_service_uses_persisted_calibration_temperature() -> None:
    service = _build_service()
    dataset = _load_dataset()

    result = service.predict(dataset)

    raw = result.raw_probabilities
    temperature = service.loaded_artifact.calibration.temperature

    from ztf_classifier.models.calibration import TemperatureScaler

    expected = TemperatureScaler().transform(
        raw,
        temperature,
    )

    assert result.calibrated_probabilities is not None

    np.testing.assert_array_equal(
        result.calibrated_probabilities,
        expected,
    )


def test_service_is_deterministic() -> None:
    service = _build_service()
    dataset = _load_dataset()

    first = service.predict(dataset)
    second = service.predict(dataset)

    np.testing.assert_array_equal(
        first.raw_probabilities,
        second.raw_probabilities,
    )

    np.testing.assert_array_equal(
        first.calibrated_probabilities,
        second.calibrated_probabilities,
    )

    np.testing.assert_array_equal(
        first.raw_predicted_class_indices,
        second.raw_predicted_class_indices,
    )

    np.testing.assert_array_equal(
        first.calibrated_predicted_class_indices,
        second.calibrated_predicted_class_indices,
    )


def test_service_does_not_include_diagnostic_outputs() -> None:
    service = _build_service()
    dataset = _load_dataset()

    result = service.predict(dataset)

    assert result.conformal is None
    assert result.ood is None


def test_service_rejects_missing_artifact() -> None:
    missing = Path(
        "runs/model_baseline_v0.2_production/missing-artifact"
    )

    try:
        ProductionInferenceService(missing)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError(
            "ProductionInferenceService must reject a missing artifact."
        )


def test_service_matches_direct_artifact_inference() -> None:
    from ztf_classifier.models.artifact_io import ModelArtifactLoader
    from ztf_classifier.models.calibration import TemperatureScaler
    from ztf_classifier.models.inference import XGBoostInferenceEngine

    dataset = _load_dataset()
    service = _build_service()

    loaded = ModelArtifactLoader().load(ARTIFACT)

    engine = XGBoostInferenceEngine(
        model=loaded.model_artifact.model,
        feature_schema_path=ARTIFACT / "feature_schema.parquet",
    )

    direct_inference = engine.predict(dataset)

    direct_calibrated = TemperatureScaler().transform(
        direct_inference.probabilities,
        loaded.calibration.temperature,
    )

    service_result = service.predict(dataset)

    np.testing.assert_array_equal(
        service_result.raw_probabilities,
        direct_inference.probabilities,
    )

    np.testing.assert_array_equal(
        service_result.raw_predicted_class_indices,
        direct_inference.predicted_class_indices,
    )

    np.testing.assert_array_equal(
        service_result.raw_predicted_labels,
        direct_inference.predicted_labels,
    )

    assert service_result.calibrated_probabilities is not None

    np.testing.assert_array_equal(
        service_result.calibrated_probabilities,
        direct_calibrated,
    )

    np.testing.assert_array_equal(
        service_result.calibrated_predicted_class_indices,
        np.argmax(direct_calibrated, axis=1),
    )
