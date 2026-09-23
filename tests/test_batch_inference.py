"""Tests for application batch inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.application.batch import (
    BATCH_SCHEMA_VERSION,
    BatchInferenceService,
)
from ztf_classifier.application.schemas import PredictionResponse
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.results import PredictionResult


def _response(sample_count: int = 2) -> PredictionResponse:
    """Build a deterministic prediction response."""

    probabilities = np.zeros(
        (sample_count, len(MODEL_CLASSES)),
        dtype=np.float64,
    )
    probabilities[:, 0] = 1.0

    result = PredictionResult(
        raw_probabilities=probabilities,
        raw_predicted_class_indices=np.zeros(
            sample_count,
            dtype=np.int64,
        ),
        raw_predicted_labels=tuple(
            MODEL_CLASSES[0]
            for _ in range(sample_count)
        ),
        calibrated_probabilities=probabilities.copy(),
        calibrated_predicted_class_indices=np.zeros(
            sample_count,
            dtype=np.int64,
        ),
        calibrated_predicted_labels=tuple(
            MODEL_CLASSES[0]
            for _ in range(sample_count)
        ),
    )

    return PredictionResponse(
        result=result,
        model_version="baseline_v0.2",
        model_family="XGBoost",
    )


class StubApplicationService:
    """Stub application service for batch tests."""

    def __init__(self, response: PredictionResponse) -> None:
        self.response = response
        self.dataset: pd.DataFrame | None = None
        self.artifact_dir: Path | None = None

    def predict_dataframe(
        self,
        dataset: pd.DataFrame,
        artifact_dir: Path,
    ) -> PredictionResponse:
        """Return the configured response."""

        self.dataset = dataset
        self.artifact_dir = artifact_dir
        return self.response


def test_batch_preserves_oid_and_row_count(
    tmp_path: Path,
) -> None:
    """Batch output must preserve input OIDs and row count."""

    stub = StubApplicationService(_response(2))

    service = BatchInferenceService(stub)

    dataset = pd.DataFrame(
        {
            "oid": ["ZTF001", "ZTF002"],
            "feature": [1.0, 2.0],
        }
    )

    result = service.predict(
        dataset,
        tmp_path,
    )

    assert result.schema_version == BATCH_SCHEMA_VERSION
    assert result.model_version == "baseline_v0.2"
    assert result.model_family == "XGBoost"
    assert len(result.predictions) == 2
    assert list(result.predictions["oid"]) == [
        "ZTF001",
        "ZTF002",
    ]


def test_batch_contains_all_probability_columns(
    tmp_path: Path,
) -> None:
    """Batch output must contain one probability column per class."""

    stub = StubApplicationService(_response(2))

    result = BatchInferenceService(stub).predict(
        pd.DataFrame(
            {
                "oid": ["ZTF001", "ZTF002"],
            }
        ),
        tmp_path,
    )

    for class_name in MODEL_CLASSES:
        column = f"probability_{class_name}"
        assert column in result.predictions.columns

    probability_columns = [
        f"probability_{name}"
        for name in MODEL_CLASSES
    ]

    assert np.allclose(
        result.predictions[probability_columns].sum(axis=1),
        1.0,
    )


def test_batch_works_without_oid(
    tmp_path: Path,
) -> None:
    """OID is optional for batch output."""

    stub = StubApplicationService(_response(2))

    result = BatchInferenceService(stub).predict(
        pd.DataFrame(
            {
                "feature": [1.0, 2.0],
            }
        ),
        tmp_path,
    )

    assert "oid" not in result.predictions.columns
    assert len(result.predictions) == 2


def test_batch_uses_application_service(
    tmp_path: Path,
) -> None:
    """Batch must delegate inference to ApplicationService."""

    stub = StubApplicationService(_response(2))

    dataset = pd.DataFrame(
        {
            "oid": ["ZTF001", "ZTF002"],
        }
    )

    BatchInferenceService(stub).predict(
        dataset,
        tmp_path,
    )

    assert stub.dataset is dataset
    assert stub.artifact_dir == tmp_path


def test_batch_rejects_non_dataframe(
    tmp_path: Path,
) -> None:
    """Batch must reject non-DataFrame input."""

    service = BatchInferenceService(
        StubApplicationService(_response(1))
    )

    with pytest.raises(TypeError, match="pandas DataFrame"):
        service.predict(
            "not a dataframe",  # type: ignore[arg-type]
            tmp_path,
        )


def test_batch_prediction_class_matches_index(
    tmp_path: Path,
) -> None:
    """Top-1 class and class index must remain aligned."""

    stub = StubApplicationService(_response(2))

    result = BatchInferenceService(stub).predict(
        pd.DataFrame(
            {
                "oid": ["ZTF001", "ZTF002"],
            }
        ),
        tmp_path,
    )

    assert list(
        result.predictions["predicted_class"]
    ) == ["AGN", "AGN"]

    assert list(
        result.predictions["predicted_class_index"]
    ) == [0, 0]


def test_batch_result_rejects_invalid_schema_and_flags() -> None:
    """Batch result must reject invalid contract metadata."""
    from ztf_classifier.application.batch import BatchPredictionResult

    with pytest.raises(ValueError, match="Unsupported batch schema"):
        BatchPredictionResult(
            predictions=pd.DataFrame({"x": [1]}),
            model_version="v1",
            model_family="XGBoost",
            has_calibration=True,
            has_conformal=True,
            has_ood=True,
            schema_version="9.9",
        )

    with pytest.raises(TypeError, match="has_ood must be a bool"):
        BatchPredictionResult(
            predictions=pd.DataFrame({"x": [1]}),
            model_version="v1",
            model_family="XGBoost",
            has_calibration=True,
            has_conformal=True,
            has_ood="true",
        )
