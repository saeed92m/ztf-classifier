"""Application service for user-facing production inference."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ztf_classifier.application.errors import (
    ApplicationInferenceError,
)
from ztf_classifier.application.schemas import (
    PredictionRequest,
    PredictionResponse,
)
from ztf_classifier.models.production_inference import (
    ProductionInferenceService,
)
from ztf_classifier.models.registry import FilesystemModelRegistry


class ApplicationService:
    """Orchestrate production inference for application clients."""

    def predict(
        self,
        request: PredictionRequest,
    ) -> PredictionResponse:
        """Run production inference for an application request."""

        try:
            artifact_dir = request.artifact_dir

            if request.registry_dir is not None:
                registry = FilesystemModelRegistry(
                    request.registry_dir
                )
                entry = registry.get(
                    request.model_version
                )
                artifact_dir = entry.artifact_dir

            assert artifact_dir is not None

            service = ProductionInferenceService(
                Path(artifact_dir)
            )

            result = service.predict(request.dataset)
            model_artifact = service.loaded_artifact.model_artifact
            provenance = service.loaded_artifact.provenance

        except Exception as exc:
            raise ApplicationInferenceError(
                "Production prediction failed."
            ) from exc

        return PredictionResponse(
            result=result,
            model_version=model_artifact.model_version,
            model_family=model_artifact.model_family,
            provenance=provenance,
        )

    def predict_dataframe(
        self,
        dataset: pd.DataFrame,
        artifact_dir: Path,
    ) -> PredictionResponse:
        """Convenience wrapper for dataframe-based artifact prediction."""

        request = PredictionRequest(
            dataset=dataset,
            artifact_dir=artifact_dir,
        )

        return self.predict(request)

    def predict_registered_dataframe(
        self,
        dataset: pd.DataFrame,
        registry_dir: Path,
        model_version: str,
    ) -> PredictionResponse:
        """Predict using an explicitly selected registered model."""

        request = PredictionRequest(
            dataset=dataset,
            registry_dir=registry_dir,
            model_version=model_version,
        )

        return self.predict(request)


__all__ = ["ApplicationService"]
