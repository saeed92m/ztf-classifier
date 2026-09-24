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

BATCH_SCHEMA_VERSION = "1.1"


@dataclass(frozen=True)
class BatchPredictionResult:
    """Structured batch prediction output."""

    predictions: pd.DataFrame
    model_version: str
    model_family: str
    has_calibration: bool
    has_conformal: bool
    has_ood: bool
    schema_version: str = BATCH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate the batch result."""

        if not isinstance(self.predictions, pd.DataFrame):
            raise TypeError(
                "predictions must be a pandas DataFrame."
            )
        if self.predictions.empty:
            raise ValueError(
                "predictions must not be empty."
            )

        if not self.model_version:
            raise ValueError(
                "model_version must not be empty."
            )

        if not self.model_family:
            raise ValueError(
                "model_family must not be empty."
            )
        if self.schema_version != BATCH_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported batch schema version: {self.schema_version}"
            )

        for name in (
            "has_calibration",
            "has_conformal",
            "has_ood",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool.")


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
        """Run batch inference from a direct artifact directory."""

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

    def predict_registered(
        self,
        dataset: pd.DataFrame,
        registry_dir: Path,
        model_version: str,
    ) -> BatchPredictionResult:
        """Run batch inference from an explicitly selected registry model."""

        if not isinstance(dataset, pd.DataFrame):
            raise TypeError(
                "dataset must be a pandas DataFrame."
            )

        response = self._application_service.predict_registered_dataframe(
            dataset=dataset,
            registry_dir=registry_dir,
            model_version=model_version,
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

        if result.conformal is not None:
            for diagnostic in result.conformal.results:
                alpha = f"{diagnostic.alpha:.6f}".rstrip("0").rstrip(".")
                alpha = alpha.replace(".", "p")
                output[f"conformal_{alpha}_threshold"] = (
                    diagnostic.threshold
                )
                output[f"conformal_{alpha}_prediction_set"] = (
                    diagnostic.prediction_set_labels
                )
                output[f"conformal_{alpha}_prediction_set_size"] = (
                    diagnostic.prediction_sets.sum(axis=1).astype("int64")
                )

        if result.ood is not None:
            output["ood_anomaly_score"] = result.ood.anomaly_score
            output["ood_normality_score"] = result.ood.normality_score
            output["ood_anomaly_percentile"] = (
                result.ood.anomaly_percentile
            )
            output["ood_isolation_forest_label"] = (
                result.ood.isolation_forest_label
            )
            output["ood_anomaly_rank"] = result.ood.anomaly_rank
            output["ood_is_top_1pct_anomaly"] = (
                result.ood.is_top_1pct_anomaly
            )
            output["ood_is_top_5pct_anomaly"] = (
                result.ood.is_top_5pct_anomaly
            )
            output["ood_is_top_10pct_anomaly"] = (
                result.ood.is_top_10pct_anomaly
            )

        output["model_version"] = response.model_version
        output["model_family"] = response.model_family

        return BatchPredictionResult(
            predictions=output.reset_index(drop=True),
            model_version=response.model_version,
            model_family=response.model_family,
            has_calibration=result.has_calibration,
            has_conformal=result.has_conformal,
            has_ood=result.has_ood,
        )


__all__ = [
    "BATCH_SCHEMA_VERSION",
    "BatchInferenceService",
    "BatchPredictionResult",
]
