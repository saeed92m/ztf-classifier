"""Source-backed scientific execution for persistent analysis jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.errors import ApplicationError
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.features.engine import ScientificFeatureEngine
from ztf_classifier.jobs.errors import AnalysisJobExecutionError
from ztf_classifier.jobs.store import JobRecord
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.registry import FilesystemModelRegistry, ModelNotFoundError


class SourceBackedAnalysisExecutor:
    """Execute a queued object-analysis job through the scientific pipeline."""

    def __init__(
        self,
        settings: ApiSettings,
        *,
        observation_service: ObservationService,
        application_service: ApplicationService | None = None,
        feature_engine: ScientificFeatureEngine | None = None,
    ) -> None:
        self.settings = settings
        self.observation_service = observation_service
        self.application_service = application_service or ApplicationService()
        self.feature_engine = feature_engine or ScientificFeatureEngine()

    def __call__(self, job: JobRecord) -> dict[str, Any]:
        return self.execute(
            oid=job.oid,
            survey=job.survey,
            model_version=job.model_version,
            feature_backend=job.feature_backend,
            feature_parameters=job.feature_parameters,
        )

    def execute(
        self,
        *,
        oid: str,
        survey: str,
        model_version: str | None,
        feature_backend: str = "native",
        feature_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            return self._execute(
                oid=oid,
                survey=survey,
                model_version=model_version,
                feature_backend=feature_backend,
                feature_parameters=feature_parameters,
            )
        except AnalysisJobExecutionError:
            raise
        except (
            ApplicationError,
            ValueError,
            KeyError,
            FileNotFoundError,
            ModelNotFoundError,
        ) as exc:
            raise AnalysisJobExecutionError(
                "Object analysis could not be completed."
            ) from exc

    def _execute(
        self,
        *,
        oid: str,
        survey: str,
        model_version: str | None,
        feature_backend: str = "native",
        feature_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        records, observation_provenance = self.observation_service.get_observations(
            oid,
            survey=survey,
        )
        if not records:
            raise AnalysisJobExecutionError("No valid observations were acquired.")

        observations = pd.DataFrame([record.to_dict() for record in records])
        feature_result = self.feature_engine.compute(
            observations,
            backend=feature_backend,
            parameters=feature_parameters or {},
        )

        model_version = model_version or self.settings.default_model_version
        if not model_version or self.settings.registry_dir is None:
            raise AnalysisJobExecutionError("No production model is configured.")

        registry = FilesystemModelRegistry(self.settings.registry_dir)
        entry = registry.get(model_version)
        prediction_response = self.application_service.predict_dataframe(
            pd.DataFrame([feature_result.values]),
            Path(entry.artifact_dir),
        )
        result = prediction_response.result
        probabilities = (
            result.calibrated_probabilities
            if result.has_calibration
            else result.raw_probabilities
        )
        if probabilities is None:
            raise AnalysisJobExecutionError("Prediction result contains no probabilities.")

        prediction: dict[str, Any] = {
            "predicted_class": result.top1_labels[0],
            "predicted_class_index": int(result.top1_class_indices[0]),
            "probabilities": {
                class_name: float(probabilities[0, index])
                for index, class_name in enumerate(MODEL_CLASSES)
            },
        }

        model_provenance = prediction_response.provenance.to_dict()
        for section in ("dataset", "feature_schema", "model_configuration", "calibration"):
            value = model_provenance.get(section)
            if isinstance(value, dict):
                value.pop("path", None)
                value.pop("source_path", None)

        return {
            "schema_version": "1.0",
            "oid": oid,
            "survey": survey,
            "observation_count": len(records),
            "observations": [record.to_dict() for record in records],
            "features": feature_result.values,
            "feature_backend": feature_backend,
            "feature_parameters": feature_parameters or {},
            "feature_schema_version": feature_result.feature_schema_version,
            "feature_provenance": feature_result.provenance.to_dict(),
            "prediction": prediction,
            "model_version": prediction_response.model_version,
            "model_family": prediction_response.model_family,
            "diagnostics": {
                "calibration": result.calibration_status,
                "conformal": result.conformal_status,
                "ood": result.ood_status,
            },
            "model_provenance": model_provenance,
            "observation_provenance": observation_provenance.to_dict(),
            "warnings": list(result.warnings),
        }


__all__ = ["AnalysisJobExecutionError", "SourceBackedAnalysisExecutor"]
