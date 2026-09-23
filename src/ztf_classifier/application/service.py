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


class ApplicationService:
    """Orchestrate production inference for application clients."""

    def predict(
        self,
        request: PredictionRequest,
    ) -> PredictionResponse:
        """Run production inference for an application request."""

        try:
            service = ProductionInferenceService(
                Path(request.artifact_dir)
            )

            result = service.predict(request.dataset)
            model_artifact = service.loaded_artifact.model_artifact

        except Exception as exc:
            raise ApplicationInferenceError(
                "Production prediction failed."
            ) from exc

        return PredictionResponse(
            result=result,
            model_version=model_artifact.model_version,
            model_family=model_artifact.model_family,
        )

    def predict_dataframe(
        self,
        dataset: pd.DataFrame,
        artifact_dir: Path,
    ) -> PredictionResponse:
        """Convenience wrapper for dataframe-based prediction."""

        request = PredictionRequest(
            dataset=dataset,
            artifact_dir=artifact_dir,
        )

        return self.predict(request)


__all__ = ["ApplicationService"]
