"""Registry-backed application service for production inference."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ztf_classifier.application.errors import ApplicationInferenceError
from ztf_classifier.application.schemas import PredictionResponse
from ztf_classifier.models.production_inference import ProductionInferenceService
from ztf_classifier.models.registry import ModelRegistry


@dataclass(frozen=True)
class RegisteredPredictionRequest:
    """Request for inference against an explicitly registered model."""

    dataset: pd.DataFrame
    model_version: str

    def __post_init__(self) -> None:
        """Validate the registered-model request."""

        if not isinstance(self.dataset, pd.DataFrame):
            raise TypeError("dataset must be a pandas DataFrame.")

        if not isinstance(self.model_version, str) or not self.model_version.strip():
            raise ValueError("model_version must be a non-empty string.")


class RegisteredApplicationService:
    """Run production inference through the model registry boundary."""

    def __init__(self, registry: ModelRegistry) -> None:
        """Initialize the service with an explicit model registry."""

        self._registry = registry

    def predict(
        self,
        request: RegisteredPredictionRequest,
    ) -> PredictionResponse:
        """Resolve the requested model version and run inference."""

        try:
            entry = self._registry.get(request.model_version)
            service = ProductionInferenceService(entry.artifact_dir)
            result = service.predict(request.dataset)
            provenance = service.loaded_artifact.provenance
        except Exception as exc:
            raise ApplicationInferenceError(
                "Registered production prediction failed."
            ) from exc

        return PredictionResponse(
            result=result,
            model_version=entry.model_version,
            model_family=entry.model_family,
            provenance=provenance,
        )

    def predict_dataframe(
        self,
        dataset: pd.DataFrame,
        model_version: str,
    ) -> PredictionResponse:
        """Convenience wrapper for dataframe-based registered inference."""

        return self.predict(
            RegisteredPredictionRequest(
                dataset=dataset,
                model_version=model_version,
            )
        )


__all__ = [
    "RegisteredApplicationService",
    "RegisteredPredictionRequest",
]
