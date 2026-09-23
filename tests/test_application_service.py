from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.application.errors import ApplicationInferenceError
from ztf_classifier.application.schemas import (
    PredictionRequest,
    PredictionResponse,
)
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.models.results import PredictionResult


def test_prediction_request_accepts_valid_request(
    tmp_path: Path,
) -> None:
    dataset = pd.DataFrame({"feature": [1.0, 2.0]})

    request = PredictionRequest(
        dataset=dataset,
        artifact_dir=tmp_path,
    )

    assert request.dataset is dataset
    assert request.artifact_dir == tmp_path.resolve()


def test_prediction_request_rejects_non_dataframe(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="pandas DataFrame"):
        PredictionRequest(
            dataset=[1.0, 2.0],  # type: ignore[arg-type]
            artifact_dir=tmp_path,
        )


def test_prediction_request_rejects_missing_artifact_directory(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        PredictionRequest(
            dataset=pd.DataFrame(),
            artifact_dir=missing,
        )


def test_prediction_request_rejects_file_as_artifact_directory(
    tmp_path: Path,
) -> None:
    artifact_file = tmp_path / "artifact"
    artifact_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="not a directory",
    ):
        PredictionRequest(
            dataset=pd.DataFrame(),
            artifact_dir=artifact_file,
        )


def test_prediction_response_exposes_sample_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    probabilities = np.zeros((1, 15), dtype=np.float64)
    probabilities[0, 0] = 1.0

    expected = PredictionResult(
        raw_probabilities=probabilities,
        raw_predicted_class_indices=np.array([0]),
        raw_predicted_labels=("AGN",),
    )

    class FakeProductionService:
        def __init__(self, artifact_dir: Path) -> None:
            assert artifact_dir == tmp_path.resolve()

        def predict(self, dataset: pd.DataFrame) -> PredictionResult:
            assert list(dataset.columns) == ["feature"]
            return expected

    monkeypatch.setattr(
        "ztf_classifier.application.service.ProductionInferenceService",
        FakeProductionService,
    )

    response = ApplicationService().predict_dataframe(
        pd.DataFrame({"feature": [1.0]}),
        tmp_path,
    )

    assert isinstance(response, PredictionResponse)
    assert response.result is expected
    assert response.sample_count == 1


def test_application_service_wraps_inference_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FailingProductionService:
        def __init__(self, artifact_dir: Path) -> None:
            raise RuntimeError("artifact failure")

    monkeypatch.setattr(
        "ztf_classifier.application.service.ProductionInferenceService",
        FailingProductionService,
    )

    request = PredictionRequest(
        dataset=pd.DataFrame({"feature": [1.0]}),
        artifact_dir=tmp_path,
    )

    with pytest.raises(
        ApplicationInferenceError,
        match="Production prediction failed",
    ) as exc_info:
        ApplicationService().predict(request)

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_predict_dataframe_matches_request_based_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    probabilities = np.zeros((2, 15), dtype=np.float64)
    probabilities[:, 3] = 1.0

    expected = PredictionResult(
        raw_probabilities=probabilities,
        raw_predicted_class_indices=np.array([3, 3]),
        raw_predicted_labels=("CV/Nova", "CV/Nova"),
    )

    captured: dict[str, object] = {}

    class FakeProductionService:
        def __init__(self, artifact_dir: Path) -> None:
            captured["artifact_dir"] = artifact_dir

        def predict(self, dataset: pd.DataFrame) -> PredictionResult:
            captured["dataset"] = dataset
            return expected

    monkeypatch.setattr(
        "ztf_classifier.application.service.ProductionInferenceService",
        FakeProductionService,
    )

    dataset = pd.DataFrame({"feature": [1.0, 2.0]})

    response = ApplicationService().predict_dataframe(
        dataset,
        tmp_path,
    )

    assert response.result is expected
    assert captured["artifact_dir"] == tmp_path.resolve()
    assert captured["dataset"] is dataset
