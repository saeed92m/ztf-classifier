import shutil
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.models.artifact_io import ModelArtifactLoader
from ztf_classifier.models.calibration import TemperatureScaler
from ztf_classifier.models.inference import XGBoostInferenceEngine
from ztf_classifier.models.production_conformal import (
    ProductionConformalDiagnostics,
)
from ztf_classifier.models.production_inference import (
    ProductionInferenceService,
)
from ztf_classifier.models.results import PredictionResult
from ztf_classifier.pipeline.model import ModelPipeline

LEGACY_ARTIFACT = Path(
    "runs/model_baseline_v0.2_production/artifact"
)
DATASET = Path(
    "data/processed/features_v0.2.parquet"
)


def _load_dataset() -> pd.DataFrame:
    return pd.read_parquet(DATASET)


@pytest.fixture(scope="session")
def diagnostic_artifact(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[Path]:
    token = tmp_path_factory.mktemp("4b").name
    output_dir = Path(f"tmp-test-model-pipeline-{token}")

    try:
        result = ModelPipeline(
            project_root=Path("."),
            dataset_path=DATASET,
            fold_assignments_path=Path(
                "reports/tables/stratified_cv_fold_assignments_v0.1.parquet"
            ),
            feature_schema_path=Path(
                "reports/tables/final_feature_set_v0.2.parquet"
            ),
            model_config_path=Path(
                "reports/tables/final_model_config_v0.2.json"
            ),
            output_dir=output_dir,
        ).run()

        yield result.artifact_dir
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def _build_service(
    artifact: Path = LEGACY_ARTIFACT,
) -> ProductionInferenceService:
    return ProductionInferenceService(artifact)


def test_service_loads_production_artifact() -> None:
    service = _build_service()

    assert service.artifact_dir == LEGACY_ARTIFACT.resolve()
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
    dataset = _load_dataset()
    service = _build_service()

    loaded = ModelArtifactLoader().load(LEGACY_ARTIFACT)

    engine = XGBoostInferenceEngine(
        model=loaded.model_artifact.model,
        feature_schema_path=(
            LEGACY_ARTIFACT / "feature_schema.parquet"
        ),
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


def test_diagnostic_artifact_loads_all_persisted_components(
    diagnostic_artifact: Path,
) -> None:
    service = _build_service(diagnostic_artifact)

    assert service.loaded_artifact.conformal is not None
    assert service.loaded_artifact.ood is not None
    assert service.loaded_artifact.ood_model is not None


def test_diagnostic_artifact_returns_conformal_outputs(
    diagnostic_artifact: Path,
) -> None:
    service = _build_service(diagnostic_artifact)
    result = service.predict(_load_dataset())

    assert result.conformal is not None
    assert isinstance(
        result.conformal,
        ProductionConformalDiagnostics,
    )

    assert len(result.conformal.results) == 3
    assert result.conformal.sample_count == 150

    assert tuple(
        diagnostic.alpha
        for diagnostic in result.conformal.results
    ) == (0.05, 0.10, 0.20)

    for diagnostic in result.conformal.results:
        assert diagnostic.prediction_sets.shape == (150, 15)
        assert len(diagnostic.prediction_set_labels) == 150


def test_diagnostic_conformal_uses_raw_probabilities(
    diagnostic_artifact: Path,
) -> None:
    service = _build_service(diagnostic_artifact)
    result = service.predict(_load_dataset())

    artifact = service.loaded_artifact.conformal

    assert artifact is not None
    assert result.conformal is not None

    expected = ProductionConformalDiagnostics.predict(
        result.raw_probabilities,
        artifact,
    )

    for actual, expected_result in zip(
        result.conformal.results,
        expected.results,
        strict=True,
    ):
        assert actual.alpha == expected_result.alpha
        assert actual.threshold == expected_result.threshold

        np.testing.assert_array_equal(
            actual.prediction_sets,
            expected_result.prediction_sets,
        )

        assert (
            actual.prediction_set_labels
            == expected_result.prediction_set_labels
        )


def test_diagnostic_artifact_returns_ood_outputs(
    diagnostic_artifact: Path,
) -> None:
    service = _build_service(diagnostic_artifact)
    result = service.predict(_load_dataset())

    assert result.ood is not None
    assert result.ood.sample_count == 150

    assert result.ood.anomaly_score.shape == (150,)
    assert result.ood.normality_score.shape == (150,)
    assert result.ood.anomaly_percentile.shape == (150,)
    assert result.ood.isolation_forest_label.shape == (150,)
    assert result.ood.anomaly_rank.shape == (150,)

    assert result.ood.is_top_1pct_anomaly.shape == (150,)
    assert result.ood.is_top_5pct_anomaly.shape == (150,)
    assert result.ood.is_top_10pct_anomaly.shape == (150,)


def test_diagnostic_ood_matches_persisted_production_model(
    diagnostic_artifact: Path,
) -> None:
    dataset = _load_dataset()
    service = _build_service(diagnostic_artifact)
    result = service.predict(dataset)

    loaded = service.loaded_artifact
    assert loaded.ood is not None
    assert loaded.ood_model is not None
    assert result.ood is not None

    engine = XGBoostInferenceEngine(
        model=loaded.model_artifact.model,
        feature_schema_path=(
            diagnostic_artifact / "feature_schema.parquet"
        ),
    )

    features = engine.prepare_features(dataset)
    X = features.to_numpy(dtype=np.float64)

    model = loaded.ood_model

    anomaly_score = model.anomaly_scores(X)
    normality_score = model.normality_scores(X)
    labels = model.labels(X)
    percentiles = loaded.ood.anomaly_percentile(anomaly_score)
    ranks = loaded.ood.anomaly_rank(anomaly_score)
    flags = loaded.ood.anomaly_flags(percentiles)

    np.testing.assert_array_equal(
        result.ood.anomaly_score,
        anomaly_score,
    )
    np.testing.assert_array_equal(
        result.ood.normality_score,
        normality_score,
    )
    np.testing.assert_array_equal(
        result.ood.anomaly_percentile,
        percentiles,
    )
    np.testing.assert_array_equal(
        result.ood.anomaly_rank,
        ranks,
    )
    np.testing.assert_array_equal(
        result.ood.isolation_forest_label,
        labels,
    )

    np.testing.assert_array_equal(
        result.ood.is_top_1pct_anomaly,
        flags[99.0],
    )
    np.testing.assert_array_equal(
        result.ood.is_top_5pct_anomaly,
        flags[95.0],
    )
    np.testing.assert_array_equal(
        result.ood.is_top_10pct_anomaly,
        flags[90.0],
    )


def test_diagnostic_service_is_deterministic(
    diagnostic_artifact: Path,
) -> None:
    service = _build_service(diagnostic_artifact)
    dataset = _load_dataset()

    first = service.predict(dataset)
    second = service.predict(dataset)

    assert first.conformal is not None
    assert second.conformal is not None
    assert first.ood is not None
    assert second.ood is not None

    for first_result, second_result in zip(
        first.conformal.results,
        second.conformal.results,
        strict=True,
    ):
        np.testing.assert_array_equal(
            first_result.prediction_sets,
            second_result.prediction_sets,
        )
        assert (
            first_result.prediction_set_labels
            == second_result.prediction_set_labels
        )

    np.testing.assert_array_equal(
        first.ood.anomaly_score,
        second.ood.anomaly_score,
    )
    np.testing.assert_array_equal(
        first.ood.normality_score,
        second.ood.normality_score,
    )
    np.testing.assert_array_equal(
        first.ood.anomaly_percentile,
        second.ood.anomaly_percentile,
    )
    np.testing.assert_array_equal(
        first.ood.anomaly_rank,
        second.ood.anomaly_rank,
    )
    np.testing.assert_array_equal(
        first.ood.isolation_forest_label,
        second.ood.isolation_forest_label,
    )


def test_diagnostic_ood_rank_is_reference_relative(
    diagnostic_artifact: Path,
) -> None:
    service = _build_service(diagnostic_artifact)

    assert service.loaded_artifact.ood is not None
    assert service.loaded_artifact.ood_model is not None

    reference = (
        service.loaded_artifact.ood_model.reference_anomaly_scores
    )

    assert reference is not None

    result = service.predict(_load_dataset())

    assert result.ood is not None

    expected_rank = service.loaded_artifact.ood.anomaly_rank(
        result.ood.anomaly_score
    )

    np.testing.assert_array_equal(
        result.ood.anomaly_rank,
        expected_rank,
    )

    expected_percentile = (
        service.loaded_artifact.ood.anomaly_percentile(
            result.ood.anomaly_score
        )
    )

    np.testing.assert_array_equal(
        result.ood.anomaly_percentile,
        expected_percentile,
    )


def test_diagnostic_service_matches_direct_classification_inference(
    diagnostic_artifact: Path,
) -> None:
    dataset = _load_dataset()
    service = _build_service(diagnostic_artifact)

    loaded = ModelArtifactLoader().load(diagnostic_artifact)

    engine = XGBoostInferenceEngine(
        model=loaded.model_artifact.model,
        feature_schema_path=(
            diagnostic_artifact / "feature_schema.parquet"
        ),
    )

    direct = engine.predict(dataset)
    result = service.predict(dataset)

    np.testing.assert_array_equal(
        result.raw_probabilities,
        direct.probabilities,
    )
    np.testing.assert_array_equal(
        result.raw_predicted_class_indices,
        direct.predicted_class_indices,
    )
    np.testing.assert_array_equal(
        result.raw_predicted_labels,
        direct.predicted_labels,
    )
