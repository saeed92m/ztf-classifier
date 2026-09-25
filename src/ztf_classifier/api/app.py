"""FastAPI boundary for the production inference application service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from alerce.core import Alerce
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ztf_classifier.api.config import ApiSettings
from ztf_classifier.api.errors import ApiContractError
from ztf_classifier.api.schemas import (
    AnalysisJobRequest,
    AnalysisJobResponse,
    ErrorResponse,
    ModelResponse,
    ObjectAnalysisRequest,
    ObjectAnalysisResponse,
    ObjectObservationResponse,
    ObservationResponse,
    PredictionItem,
    PredictionRequest,
    PredictionResponse,
    ServiceStatusResponse,
)
from ztf_classifier.application.errors import ApplicationInferenceError
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.jobs.store import JobStore
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.registry import (
    FilesystemModelRegistry,
    ModelNotFoundError,
)

API_VERSION = "v1"


def _error_response(
    error: ApiContractError,
    *,
    request_id: str | None = None,
) -> JSONResponse:
    """Build the stable JSON error envelope."""
    payload = ErrorResponse(
        code=error.code,
        message=error.message,
        request_id=request_id,
        details=error.details,
    )
    return JSONResponse(
        status_code=error.status_code,
        content=payload.model_dump(),
    )


def _registry(settings: ApiSettings) -> FilesystemModelRegistry:
    """Resolve the configured server-side registry."""
    if settings.registry_dir is None:
        raise ApiContractError(
            "model_not_configured",
            "No model registry is configured for this API instance.",
            status_code=503,
        )
    try:
        return FilesystemModelRegistry(settings.registry_dir)
    except (FileNotFoundError, ValueError) as exc:
        raise ApiContractError(
            "model_registry_unavailable",
            "The configured model registry is unavailable.",
            status_code=503,
        ) from exc


def _resolve_model_version(
    requested: str | None,
    settings: ApiSettings,
) -> str:
    """Resolve an explicit request model or the server default."""
    if settings.registry_dir is None:
        raise ApiContractError(
            "model_not_configured",
            "No model registry is configured for this API instance.",
            status_code=503,
        )
    version = requested or settings.default_model_version
    if not version:
        raise ApiContractError(
            "model_version_required",
            "model_version is required unless a server default is configured.",
            status_code=400,
        )
    return version


def _ensure_registered_model(
    model_version: str,
    settings: ApiSettings,
) -> tuple[FilesystemModelRegistry, Any]:
    """Resolve a model without accepting client filesystem paths."""
    registry = _registry(settings)
    try:
        return registry, registry.get(model_version)
    except ModelNotFoundError as exc:
        raise ApiContractError(
            "model_not_found",
            f"Model version is not registered: {model_version}",
            status_code=404,
        ) from exc


def _serialize_prediction(
    dataset: pd.DataFrame,
    response: Any,
) -> PredictionResponse:
    """Translate the domain/application result into JSON-safe API data."""
    result = response.result
    probabilities = (
        result.calibrated_probabilities
        if result.has_calibration
        else result.raw_probabilities
    )
    if probabilities is None:
        raise ApiContractError(
            "inference_result_invalid",
            "Prediction result does not contain probabilities.",
            status_code=500,
        )

    items: list[PredictionItem] = []
    for row_index in range(result.sample_count):
        oid = None
        if "oid" in dataset.columns:
            oid = str(dataset.iloc[row_index]["oid"])

        conformal: list[dict[str, Any]] = []
        if result.conformal is not None:
            for diagnostic in result.conformal.results:
                conformal.append(
                    {
                        "alpha": float(diagnostic.alpha),
                        "threshold": float(diagnostic.threshold),
                        "prediction_set": diagnostic.prediction_set_labels[
                            row_index
                        ].split("|")
                        if diagnostic.prediction_set_labels[row_index]
                        else [],
                        "prediction_set_size": int(
                            diagnostic.prediction_sets[row_index].sum()
                        ),
                    }
                )

        ood: dict[str, Any] | None = None
        if result.ood is not None:
            ood = {
                "anomaly_score": float(result.ood.anomaly_score[row_index]),
                "normality_score": float(result.ood.normality_score[row_index]),
                "anomaly_percentile": float(result.ood.anomaly_percentile[row_index]),
                "isolation_forest_label": int(
                    result.ood.isolation_forest_label[row_index]
                ),
                "anomaly_rank": int(result.ood.anomaly_rank[row_index]),
                "is_top_1pct_anomaly": bool(result.ood.is_top_1pct_anomaly[row_index]),
                "is_top_5pct_anomaly": bool(result.ood.is_top_5pct_anomaly[row_index]),
                "is_top_10pct_anomaly": bool(
                    result.ood.is_top_10pct_anomaly[row_index]
                ),
            }

        items.append(
            PredictionItem(
                oid=oid,
                predicted_class=result.top1_labels[row_index],
                predicted_class_index=int(result.top1_class_indices[row_index]),
                probabilities={
                    class_name: float(probabilities[row_index, class_index])
                    for class_index, class_name in enumerate(MODEL_CLASSES)
                },
                conformal=conformal,
                ood=ood,
            )
        )

    return PredictionResponse(
        model_version=response.model_version,
        model_family=response.model_family,
        sample_count=result.sample_count,
        predictions=items,
        diagnostics={
            "calibration": result.calibration_status,
            "conformal": result.conformal_status,
            "ood": result.ood_status,
        },
        provenance=result_provenance(response),
        warnings=list(result.warnings),
    )


def result_provenance(response: Any) -> dict[str, Any]:
    """Serialize model provenance without exposing filesystem internals."""
    provenance = response.provenance.to_dict()
    for section in ("dataset", "feature_schema", "model_configuration", "calibration"):
        value = provenance.get(section)
        if isinstance(value, dict):
            value.pop("path", None)
            value.pop("source_path", None)
    return provenance


def create_app(
    settings: ApiSettings | None = None,
    application_service: ApplicationService | None = None,
    observation_service: ObservationService | None = None,
) -> FastAPI:
    """Create the production API application."""
    api_settings = settings or ApiSettings.from_environment()
    service = application_service or ApplicationService()
    observations = observation_service or ObservationService(
        client=Alerce(),
        cache_dir=api_settings.observation_cache_dir,
    )

    app = FastAPI(
        title="ZTF Classifier API",
        version="1.0",
        description="Versioned scientific inference boundary for the ZTF Classifier platform.",
    )
    app.state.settings = api_settings
    app.state.application_service = service
    jobs = JobStore(api_settings.job_store_path)

    static_dir = Path(__file__).resolve().parents[1] / "web" / "static"
    if static_dir.is_dir():
        app.mount(
            "/workbench",
            StaticFiles(directory=static_dir, html=True),
            name="workbench",
        )

    @app.exception_handler(ApiContractError)
    async def api_contract_error_handler(
        request: Request,
        exc: ApiContractError,
    ) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID")
        return _error_response(exc, request_id=request_id)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Return a safe error envelope for unexpected server failures."""
        return _error_response(
            ApiContractError(
                "internal_server_error",
                "The API could not complete the request.",
                status_code=500,
            ),
            request_id=request.headers.get("X-Request-ID"),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            {
                "location": list(error.get("loc", ())),
                "message": error.get("msg", "Invalid request."),
                "type": error.get("type", "validation_error"),
            }
            for error in exc.errors()
        ]
        return _error_response(
            ApiContractError(
                "request_validation_failed",
                "Request validation failed.",
                status_code=422,
                details=details,
            ),
            request_id=request.headers.get("X-Request-ID"),
        )

    @app.get(
        "/health",
        response_model=ServiceStatusResponse,
        tags=["system"],
    )
    def health() -> ServiceStatusResponse:
        """Return process-level liveness."""
        return ServiceStatusResponse(status="ok")

    @app.get(
        "/ready",
        response_model=ServiceStatusResponse,
        tags=["system"],
    )
    def ready() -> ServiceStatusResponse:
        """Return readiness for the configured model registry."""
        version = _resolve_model_version(None, api_settings)
        _ensure_registered_model(version, api_settings)
        return ServiceStatusResponse(
            status="ready",
            model_version=version,
        )

    @app.get(
        "/v1/model",
        response_model=ModelResponse,
        tags=["models"],
    )
    def model() -> ModelResponse:
        """Return metadata for the configured/default production model."""
        version = _resolve_model_version(None, api_settings)
        _, entry = _ensure_registered_model(version, api_settings)
        return ModelResponse(
            model_version=entry.model_version,
            model_family=entry.model_family,
            artifact_schema_version=entry.artifact_schema_version,
            feature_schema_version=entry.feature_schema_version,
            feature_count=entry.feature_count,
            classes=list(entry.classes),
            dataset_sha256=entry.dataset_sha256,
            feature_schema_sha256=entry.feature_schema_sha256,
        )

    def run_prediction(payload: PredictionRequest) -> PredictionResponse:
        """Run inference through the application service only."""
        model_version = _resolve_model_version(
            payload.model_version,
            api_settings,
        )
        _ensure_registered_model(model_version, api_settings)
        dataset = pd.DataFrame.from_records(payload.records)
        if dataset.empty:
            raise ApiContractError(
                "empty_dataset",
                "records must contain at least one row.",
                status_code=422,
            )
        try:
            result = service.predict_registered_dataframe(
                dataset=dataset,
                registry_dir=_registry(api_settings).root_dir,
                model_version=model_version,
            )
        except ApplicationInferenceError as exc:
            raise ApiContractError(
                "inference_failed",
                "Production prediction failed.",
                status_code=500,
            ) from exc
        return _serialize_prediction(dataset, result)

    @app.post(
        "/v1/objects/{oid}/jobs",
        response_model=AnalysisJobResponse,
        status_code=202,
        tags=["jobs"],
    )
    def submit_analysis_job(
        oid: str,
        request: AnalysisJobRequest,
    ) -> AnalysisJobResponse:
        """Persist an analysis request for asynchronous execution."""
        record = jobs.create(
            oid=oid,
            survey=request.survey,
            model_version=request.model_version,
        )
        return AnalysisJobResponse(**record.to_dict())

    @app.get(
        "/v1/jobs/{job_id}",
        response_model=AnalysisJobResponse,
        tags=["jobs"],
    )
    def get_analysis_job(job_id: str) -> AnalysisJobResponse:
        """Return the durable state of an analysis job."""
        try:
            record = jobs.get(job_id)
        except KeyError as exc:
            raise ApiContractError(
                "job_not_found",
                f"Analysis job was not found: {job_id}",
                status_code=404,
            ) from exc
        return AnalysisJobResponse(**record.to_dict())

    @app.post(
        "/v1/objects/{oid}/analysis",
        response_model=ObjectAnalysisResponse,
        tags=["analysis"],
    )
    def object_analysis(
        oid: str,
        request: ObjectAnalysisRequest,
    ) -> ObjectAnalysisResponse:
        """Run source-backed observations through features and inference."""
        try:
            records, observation_provenance = observations.get_observations(
                oid,
                survey=request.survey,
            )
            if not records:
                raise ValueError("No valid observations available.")
            observation_frame = pd.DataFrame([record.to_dict() for record in records])
            from ztf_classifier.features.engine import ScientificFeatureEngine

            feature_result = ScientificFeatureEngine().compute(
                observation_frame,
                backend="native",
            )
            feature_frame = pd.DataFrame([feature_result.values])
            model_version = _resolve_model_version(
                request.model_version,
                api_settings,
            )
            _, entry = _ensure_registered_model(model_version, api_settings)
            response = service.predict_dataframe(
                feature_frame,
                Path(entry.artifact_dir),
            )
            prediction = _serialize_prediction(
                feature_frame,
                response,
            ).predictions[0]
            return ObjectAnalysisResponse(
                oid=oid,
                survey=request.survey,
                observation_count=len(records),
                observations=[record.to_dict() for record in records],
                features=feature_result.values,
                feature_schema_version=feature_result.feature_schema_version,
                feature_provenance=feature_result.provenance.to_dict(),
                prediction=prediction,
                model_version=response.model_version,
                model_family=response.model_family,
                diagnostics={
                    "calibration": response.result.calibration_status,
                    "conformal": response.result.conformal_status,
                    "ood": response.result.ood_status,
                },
                model_provenance=result_provenance(response),
                observation_provenance=observation_provenance.to_dict(),
                warnings=list(response.result.warnings),
            )
        except ApiContractError:
            raise
        except ValueError as exc:
            raise ApiContractError(
                "analysis_validation_failed",
                str(exc),
                status_code=422,
            ) from exc
        except Exception as exc:
            raise ApiContractError(
                "analysis_failed",
                "Object analysis could not be completed.",
                status_code=502,
            ) from exc

    @app.get(
        "/v1/objects/{oid}",
        response_model=ObjectObservationResponse,
        tags=["observations"],
    )
    def object_summary(oid: str, survey: str = "ztf") -> ObjectObservationResponse:
        """Return an object summary derived from normalized observations."""
        try:
            summary = observations.get_object_summary(oid, survey=survey)
        except ValueError as exc:
            raise ApiContractError(
                "object_not_found",
                f"No valid observations available for object: {oid}",
                status_code=404,
            ) from exc
        except Exception as exc:
            raise ApiContractError(
                "observation_acquisition_failed",
                "Object observations could not be acquired.",
                status_code=502,
            ) from exc
        payload = summary.to_dict()
        provenance = payload.pop("provenance")
        return ObjectObservationResponse(object=payload, provenance=provenance)

    @app.get(
        "/v1/objects/{oid}/observations",
        response_model=ObservationResponse,
        tags=["observations"],
    )
    def object_observations(
        oid: str,
        survey: str = "ztf",
    ) -> ObservationResponse:
        """Return normalized photometric observations for one object."""
        try:
            records, provenance = observations.get_observations(
                oid,
                survey=survey,
            )
        except ValueError as exc:
            raise ApiContractError(
                "observation_validation_failed",
                "Object observations failed validation.",
                status_code=422,
            ) from exc
        except Exception as exc:
            raise ApiContractError(
                "observation_acquisition_failed",
                "Object observations could not be acquired.",
                status_code=502,
            ) from exc
        return ObservationResponse(
            oid=oid,
            observations=[record.to_dict() for record in records],
            observation_count=len(records),
            provenance=provenance.to_dict(),
        )

    @app.post(
        "/v1/predict",
        response_model=PredictionResponse,
        tags=["inference"],
    )
    def predict(payload: PredictionRequest) -> PredictionResponse:
        """Classify one or more feature rows."""
        return run_prediction(payload)

    @app.post(
        "/v1/batch",
        response_model=PredictionResponse,
        tags=["inference"],
    )
    def batch(payload: PredictionRequest) -> PredictionResponse:
        """Batch endpoint using the same stable inference contract."""
        return run_prediction(payload)

    return app


app = create_app()


__all__ = ["API_VERSION", "app", "create_app"]
