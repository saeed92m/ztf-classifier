"""FastAPI boundary for the production inference application service."""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from alerce.core import Alerce
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from ztf_classifier.api.config import ApiSettings
from ztf_classifier.api.errors import ApiContractError
from ztf_classifier.api.schemas import (
    AnalysisJobListResponse,
    AnalysisJobRequest,
    AnalysisJobResponse,
    ErrorResponse,
    FeatureBackendListResponse,
    FeatureBackendResponse,
    ModelResponse,
    ObjectAnalysisRequest,
    ObjectAnalysisResponse,
    ObjectObservationResponse,
    ObservationResponse,
    PredictionItem,
    PredictionRequest,
    PredictionResponse,
    ScientificCatalogResponse,
    ScientificResultResponse,
    ServiceStatusResponse,
)
from ztf_classifier.application.errors import ApplicationInferenceError
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.application.service import ApplicationService
from ztf_classifier.catalog import ScientificCatalogService
from ztf_classifier.features import ScientificFeatureEngine
from ztf_classifier.jobs.executor import SourceBackedAnalysisExecutor
from ztf_classifier.jobs.store import JobStore
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.registry import (
    FilesystemModelRegistry,
    ModelNotFoundError,
)
from ztf_classifier.reporting import ScientificReportService
from ztf_classifier.results import ScientificResultStore

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
    analysis_executor: SourceBackedAnalysisExecutor | None = None,
    feature_engine: ScientificFeatureEngine | None = None,
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
    results = ScientificResultStore(api_settings.result_store_path)
    catalog = ScientificCatalogService(results)
    reports = ScientificReportService()
    selected_feature_engine = feature_engine or ScientificFeatureEngine()
    executor = analysis_executor or SourceBackedAnalysisExecutor(
        api_settings,
        observation_service=observations,
        application_service=service,
        feature_engine=selected_feature_engine,
    )

    static_dir = Path(__file__).resolve().parents[1] / "web" / "static"
    if static_dir.is_dir():
        app.mount(
            "/workbench",
            StaticFiles(directory=static_dir, html=True),
            name="workbench",
        )

    @app.middleware("http")
    async def security_and_request_id_middleware(
        request: Request,
        call_next,
    ) -> JSONResponse:
        """Apply optional API-key protection and a stable request ID boundary."""
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        if api_settings.api_key and request.url.path.startswith("/v1/"):
            authorization = request.headers.get("Authorization", "")
            expected = f"Bearer {api_settings.api_key}"
            if not secrets.compare_digest(authorization, expected):
                response = _error_response(
                    ApiContractError(
                        "authentication_required",
                        "Valid API credentials are required.",
                        status_code=401,
                    ),
                    request_id=request_id,
                )
                response.headers["WWW-Authenticate"] = "Bearer"
                response.headers["X-Request-ID"] = request_id
                return response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

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
        "/v1/features/backends",
        response_model=FeatureBackendListResponse,
        tags=["features"],
    )
    def list_feature_backends() -> FeatureBackendListResponse:
        """Return registered scientific feature backend metadata."""
        return FeatureBackendListResponse(
            backends=[
                FeatureBackendResponse(**metadata)
                for metadata in selected_feature_engine.all_backend_metadata()
            ]
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
        if request.feature_backend not in selected_feature_engine.list_backends():
            raise ApiContractError(
                "feature_backend_not_found",
                f"Feature backend is not registered: {request.feature_backend}",
                status_code=404,
            )
        record = jobs.create(
            oid=oid,
            survey=request.survey,
            model_version=request.model_version,
            feature_backend=request.feature_backend,
            feature_parameters=request.feature_parameters,
        )
        return AnalysisJobResponse(**record.to_dict())

    @app.get(
        "/v1/jobs",
        response_model=AnalysisJobListResponse,
        tags=["jobs"],
    )
    def list_analysis_jobs(
        status: str | None = Query(default=None, min_length=1, max_length=16),
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> AnalysisJobListResponse:
        """Return a bounded operational view of durable analysis jobs."""
        try:
            records = jobs.list(status=status, limit=limit, offset=offset)
        except ValueError as exc:
            raise ApiContractError(
                "job_query_invalid",
                str(exc),
                status_code=422,
            ) from exc
        return AnalysisJobListResponse(
            items=[AnalysisJobResponse(**record.to_dict()) for record in records],
            limit=limit,
            offset=offset,
        )

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

    def _scientific_result_response(record: Any) -> ScientificResultResponse:
        """Serialize one durable scientific result without rebuilding its payload."""
        return ScientificResultResponse(**record.to_dict())

    @app.get(
        "/v1/jobs/{job_id}/result",
        response_model=ScientificResultResponse,
        tags=["jobs"],
    )
    def get_job_result(job_id: str) -> ScientificResultResponse:
        """Return the canonical durable scientific result for a completed job."""
        try:
            job = jobs.get(job_id)
        except KeyError as exc:
            raise ApiContractError(
                "job_not_found",
                f"Analysis job was not found: {job_id}",
                status_code=404,
            ) from exc

        if job.status != "succeeded" or job.scientific_result_id is None:
            raise ApiContractError(
                "job_result_not_ready",
                "A durable scientific result is not available for this job.",
                status_code=409,
            )

        try:
            record = results.get(job.scientific_result_id)
        except KeyError as exc:
            raise ApiContractError(
                "job_result_not_found",
                "The durable scientific result could not be found.",
                status_code=404,
            ) from exc
        return _scientific_result_response(record)

    @app.get(
        "/v1/results/{result_id}",
        response_model=ScientificResultResponse,
        tags=["results"],
    )
    def get_scientific_result(result_id: str) -> ScientificResultResponse:
        """Return a durable scientific result by stable result ID."""
        try:
            record = results.get(result_id)
        except KeyError as exc:
            raise ApiContractError(
                "scientific_result_not_found",
                f"Scientific result was not found: {result_id}",
                status_code=404,
            ) from exc
        return _scientific_result_response(record)

    @app.get(
        "/v1/results/{result_id}/report",
        response_class=Response,
        tags=["reports"],
    )
    def get_scientific_result_report(result_id: str) -> Response:
        """Render a durable scientific result without re-running inference."""
        try:
            record = results.get(result_id)
        except KeyError as exc:
            raise ApiContractError(
                "scientific_result_not_found",
                f"Scientific result was not found: {result_id}",
                status_code=404,
            ) from exc
        return Response(
            content=reports.render_markdown(record),
            media_type="text/markdown",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="ztf-analysis-{record.result_id}.md"'
                )
            },
        )

    @app.get(
        "/v1/catalog/results",
        response_model=ScientificCatalogResponse,
        tags=["catalog"],
    )
    def query_scientific_catalog(
        oid: str | None = Query(default=None, min_length=1, max_length=256),
        survey: str | None = Query(default=None, min_length=1, max_length=32),
        model_version: str | None = Query(default=None, min_length=1, max_length=128),
        created_after: str | None = Query(default=None, min_length=1, max_length=64),
        created_before: str | None = Query(default=None, min_length=1, max_length=64),
        limit: int = Query(default=100, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> ScientificCatalogResponse:
        """Query persisted scientific results without executing inference."""
        try:
            page = catalog.query(
                oid=oid,
                survey=survey,
                model_version=model_version,
                created_after=created_after,
                created_before=created_before,
                limit=limit,
                offset=offset,
            )
        except ValueError as exc:
            raise ApiContractError(
                "catalog_query_invalid",
                str(exc),
                status_code=422,
            ) from exc
        return ScientificCatalogResponse(
            items=[_scientific_result_response(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
            has_next=page.has_next,
        )

    @app.get(
        "/v1/catalog/results.csv",
        response_class=Response,
        tags=["catalog"],
    )
    def export_scientific_catalog(
        oid: str | None = Query(default=None, min_length=1, max_length=256),
        survey: str | None = Query(default=None, min_length=1, max_length=32),
        model_version: str | None = Query(default=None, min_length=1, max_length=128),
        created_after: str | None = Query(default=None, min_length=1, max_length=64),
        created_before: str | None = Query(default=None, min_length=1, max_length=64),
        limit: int = Query(default=1000, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> Response:
        """Export one bounded deterministic catalog page as CSV."""
        try:
            page = catalog.query(
                oid=oid,
                survey=survey,
                model_version=model_version,
                created_after=created_after,
                created_before=created_before,
                limit=limit,
                offset=offset,
            )
        except ValueError as exc:
            raise ApiContractError(
                "catalog_query_invalid",
                str(exc),
                status_code=422,
            ) from exc
        return Response(
            content=catalog.export_csv(page),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="scientific-catalog.csv"'},
        )

    @app.get(
        "/v1/objects/{oid}/results/latest",
        response_model=ScientificResultResponse,
        tags=["results"],
    )
    def get_latest_object_result(
        oid: str,
        survey: str = "ztf",
    ) -> ScientificResultResponse:
        """Return the newest durable scientific result for one object."""
        record = results.latest_for_object(oid, survey=survey)
        if record is None:
            raise ApiContractError(
                "scientific_result_not_found",
                f"No durable scientific result was found for object: {oid}",
                status_code=404,
            )
        return _scientific_result_response(record)

    @app.post(
        "/v1/objects/{oid}/analysis",
        response_model=ObjectAnalysisResponse,
        tags=["analysis"],
    )
    def object_analysis(
        oid: str,
        request: ObjectAnalysisRequest,
    ) -> ObjectAnalysisResponse:
        """Run source-backed observations through the shared scientific executor."""
        if request.feature_backend not in selected_feature_engine.list_backends():
            raise ApiContractError(
                "feature_backend_not_found",
                f"Feature backend is not registered: {request.feature_backend}",
                status_code=404,
            )
        try:
            result = executor.execute(
                oid=oid,
                survey=request.survey,
                model_version=request.model_version,
                feature_backend=request.feature_backend,
                feature_parameters=request.feature_parameters,
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

        prediction_data = result["prediction"]
        prediction = PredictionItem(**prediction_data)
        return ObjectAnalysisResponse(
            oid=result["oid"],
            survey=result["survey"],
            observation_count=result["observation_count"],
            observations=result["observations"],
            features=result["features"],
            feature_schema_version=result["feature_schema_version"],
            feature_backend=result["feature_backend"],
            feature_parameters=result["feature_parameters"],
            feature_provenance=result["feature_provenance"],
            prediction=prediction,
            model_version=result["model_version"],
            model_family=result["model_family"],
            diagnostics=result["diagnostics"],
            model_provenance=result["model_provenance"],
            observation_provenance=result["observation_provenance"],
            warnings=result["warnings"],
        )

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
