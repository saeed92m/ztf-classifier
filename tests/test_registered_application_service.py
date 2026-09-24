from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.application.errors import ApplicationInferenceError
from ztf_classifier.application.registry_service import (
    RegisteredApplicationService,
    RegisteredPredictionRequest,
)
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.registry import ModelRegistryEntry
from ztf_classifier.models.results import PredictionResult


def _entry(tmp_path: Path) -> ModelRegistryEntry:
    artifact_dir = tmp_path / "artifact"
    artifact_dir.mkdir()
    return ModelRegistryEntry(
        model_version="baseline_v0.2",
        model_family="XGBoost",
        artifact_schema_version="1.1",
        feature_schema_version="v0.2",
        feature_count=42,
        classes=MODEL_CLASSES,
        dataset_sha256="a" * 64,
        feature_schema_sha256="b" * 64,
        artifact_dir=artifact_dir,
    )


def test_registered_request_validates_model_version() -> None:
    with pytest.raises(ValueError, match="model_version"):
        RegisteredPredictionRequest(
            dataset=pd.DataFrame({"feature": [1.0]}),
            model_version=" ",
        )


def test_registered_request_rejects_non_dataframe() -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        RegisteredPredictionRequest(
            dataset=[1.0],  # type: ignore[arg-type]
            model_version="baseline_v0.2",
        )


def test_registered_service_resolves_explicit_model_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = PredictionResult(
        raw_probabilities=np.eye(15, dtype=np.float64)[:1],
        raw_predicted_class_indices=np.array([0]),
        raw_predicted_labels=(MODEL_CLASSES[0],),
    )
    entry = _entry(tmp_path)
    captured: dict[str, object] = {}

    class FakeRegistry:
        def get(self, model_version: str) -> ModelRegistryEntry:
            captured["model_version"] = model_version
            return entry

    class FakeProductionService:
        def __init__(self, artifact_dir: Path) -> None:
            captured["artifact_dir"] = artifact_dir

        def predict(self, dataset: pd.DataFrame) -> PredictionResult:
            captured["dataset"] = dataset
            return expected

    monkeypatch.setattr(
        "ztf_classifier.application.registry_service.ProductionInferenceService",
        FakeProductionService,
    )

    dataset = pd.DataFrame({"feature": [1.0]})
    response = RegisteredApplicationService(FakeRegistry()).predict_dataframe(
        dataset,
        "baseline_v0.2",
    )

    assert response.result is expected
    assert response.model_version == "baseline_v0.2"
    assert response.model_family == "XGBoost"
    assert captured["model_version"] == "baseline_v0.2"
    assert captured["artifact_dir"] == entry.artifact_dir
    assert captured["dataset"] is dataset


def test_registered_service_wraps_registry_or_inference_errors(
    tmp_path: Path,
) -> None:
    entry = _entry(tmp_path)

    class FailingRegistry:
        def get(self, model_version: str) -> ModelRegistryEntry:
            raise RuntimeError("registry failure")

    with pytest.raises(
        ApplicationInferenceError,
        match="Registered production prediction failed",
    ) as exc_info:
        RegisteredApplicationService(FailingRegistry()).predict(
            RegisteredPredictionRequest(
                dataset=pd.DataFrame({"feature": [1.0]}),
                model_version=entry.model_version,
            )
        )

    assert isinstance(exc_info.value.__cause__, RuntimeError)
