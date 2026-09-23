"""Batch inference application service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ztf_classifier.application.errors import (
    ApplicationInferenceError,
)
from ztf_classifier.application.schemas import (
    PredictionResponse,
)
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.models.classes import MODEL_CLASSES

BATCH_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class BatchPredictionResult:
    """Structured batch prediction output."""

    predictions: pd.DataFrame
    model_version: str
    model_family: str
    schema_version: str = BATCH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate the batch result."""

        if not isinstance(self.predictions, pd.DataFrame):
            raise TypeError(
                "predictions must be a pandas DataFrame."
            )

        if not self.model_version:
            raise ValueError(
                "model_version must not be empty."
            )

        if not self.model_family:
            raise ValueError(
                "model_family must not be empty."
            )


class BatchInferenceService:
    """Run batch inference through the production application path."""

    def __init__(
        self,
        application_service: ApplicationService | None = None,
    ) -> None:
        """Initialize the batch service."""

        self._application_service = (
            application_service
            if application_service is not None
            else ApplicationService()
        )

    def predict(
        self,
        dataset: pd.DataFrame,
        artifact_dir: Path,
    ) -> BatchPredictionResult:
        """Run batch inference and return a tabular result."""

        if not isinstance(dataset, pd.DataFrame):
            raise TypeError(
                "dataset must be a pandas DataFrame."
            )

        response = self._application_service.predict_dataframe(
            dataset=dataset,
            artifact_dir=artifact_dir,
        )

        return self._build_result(
            dataset,
            response,
        )

    @staticmethod
    def _build_result(
        dataset: pd.DataFrame,
        response: PredictionResponse,
    ) -> BatchPredictionResult:
        """Build the stable batch output table."""

        result = response.result

        if result.has_calibration:
            probabilities = result.calibrated_probabilities
        else:
            probabilities = result.raw_probabilities

        if probabilities is None:
            raise ApplicationInferenceError(
                "Prediction result does not contain probabilities."
            )

        if len(dataset) != result.sample_count:
            raise ApplicationInferenceError(
                "Input and prediction row counts do not match."
            )

        output = pd.DataFrame(index=dataset.index)

        if "oid" in dataset.columns:
            output["oid"] = dataset["oid"].astype(str).to_numpy()

        output["predicted_class"] = list(
            result.top1_labels
        )
        output["predicted_class_index"] = (
            result.top1_class_indices
        )

        for index, class_name in enumerate(MODEL_CLASSES):
            output[f"probability_{class_name}"] = (
                probabilities[:, index]
            )

        output["model_version"] = response.model_version
        output["model_family"] = response.model_family

        return BatchPredictionResult(
            predictions=output.reset_index(drop=True),
            model_version=response.model_version,
            model_family=response.model_family,
        )


__all__ = [
    "BATCH_SCHEMA_VERSION",
    "BatchInferenceService",
    "BatchPredictionResult",
]
