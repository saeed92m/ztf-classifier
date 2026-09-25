"""HTTP-facing schemas for the versioned scientific API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    """Feature rows for production inference."""

    model_config = ConfigDict(extra="forbid")

    records: list[dict[str, Any]] = Field(min_length=1, max_length=10_000)
    model_version: str | None = Field(default=None, min_length=1, max_length=128)


class PredictionItem(BaseModel):
    """One row of scientific classification output."""

    oid: str | None = None
    predicted_class: str
    predicted_class_index: int
    probabilities: dict[str, float]
    conformal: list[dict[str, Any]] = Field(default_factory=list)
    ood: dict[str, Any] | None = None


class PredictionResponse(BaseModel):
    """Stable API response carrying predictions and provenance metadata."""

    schema_version: str = "1.0"
    model_version: str
    model_family: str
    sample_count: int
    predictions: list[PredictionItem]
    diagnostics: dict[str, str]
    provenance: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class ModelResponse(BaseModel):
    """Public model metadata exposed by the API."""

    model_version: str
    model_family: str
    artifact_schema_version: str
    feature_schema_version: str
    feature_count: int
    classes: list[str]
    dataset_sha256: str
    feature_schema_sha256: str


class ServiceStatusResponse(BaseModel):
    """Health/readiness response."""

    status: str
    service: str = "ztf-classifier-api"
    model_version: str | None = None


class ErrorResponse(BaseModel):
    """Stable machine-readable API error."""

    code: str
    message: str
    request_id: str | None = None
    details: list[dict[str, Any]] = Field(default_factory=list)


class ObservationResponse(BaseModel):
    """Versioned normalized observation payload."""

    schema_version: str = "1.0"
    oid: str
    observations: list[dict[str, Any]]
    observation_count: int
    provenance: dict[str, Any]


class ObjectObservationResponse(BaseModel):
    """Object summary derived from the normalized observation stream."""

    schema_version: str = "1.0"
    object: dict[str, Any]
    provenance: dict[str, Any]


class ObjectAnalysisRequest(BaseModel):
    """Request to run the complete observation-to-inference workflow."""

    model_config = ConfigDict(extra="forbid")

    model_version: str | None = Field(default=None, min_length=1, max_length=128)
    survey: str = Field(default="ztf", min_length=1, max_length=32)
    feature_backend: str = Field(default="native", min_length=1, max_length=128)
    feature_parameters: dict[str, Any] = Field(default_factory=dict)


class ObjectAnalysisResponse(BaseModel):
    """Complete source-backed scientific analysis for one object."""

    schema_version: str = "1.0"
    oid: str
    survey: str
    observation_count: int
    observations: list[dict[str, Any]]
    features: dict[str, float]
    feature_schema_version: str
    feature_backend: str = "native"
    feature_parameters: dict[str, Any] = Field(default_factory=dict)
    feature_provenance: dict[str, Any]
    prediction: PredictionItem
    model_version: str
    model_family: str
    diagnostics: dict[str, str]
    model_provenance: dict[str, Any]
    observation_provenance: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class AnalysisJobRequest(BaseModel):
    """Request to enqueue one object analysis."""

    model_config = ConfigDict(extra="forbid")

    model_version: str | None = Field(default=None, min_length=1, max_length=128)
    survey: str = Field(default="ztf", min_length=1, max_length=32)
    feature_backend: str = Field(default="native", min_length=1, max_length=128)
    feature_parameters: dict[str, Any] = Field(default_factory=dict)


class AnalysisJobResponse(BaseModel):
    """Persistent analysis job state."""

    schema_version: str = "1.0"
    job_id: str
    oid: str
    survey: str
    model_version: str | None
    status: str
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    lease_expires_at: str | None = None
    scientific_result_id: str | None = None


class ScientificResultResponse(BaseModel):
    """Versioned durable scientific analysis result."""

    schema_version: str
    result_id: str
    job_id: str
    oid: str
    survey: str
    model_version: str
    created_at: str
    payload: dict[str, Any]


class ScientificCatalogResponse(BaseModel):
    """Paginated durable scientific-result catalog response."""

    schema_version: str = "1.0"
    items: list[ScientificResultResponse]
    total: int
    limit: int
    offset: int
    has_next: bool


class AnalysisJobListResponse(BaseModel):
    """Bounded durable analysis-job listing."""

    schema_version: str = "1.0"
    items: list[AnalysisJobResponse]
    limit: int
    offset: int


class FeatureBackendResponse(BaseModel):
    """Discoverable scientific feature backend metadata."""

    name: str
    software_version: str
    feature_schema_version: str


class FeatureBackendListResponse(BaseModel):
    """Versioned list of registered scientific feature backends."""

    schema_version: str = "1.0"
    backends: list[FeatureBackendResponse]


class ScientificValidationResponse(BaseModel):
    """Current fail-closed scientific release-gate state."""

    schema_version: str = "1.0"
    status: str
    release_blocking: bool
    required_checks: list[str] = Field(default_factory=list)
    benchmarks: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    source_probe: dict[str, Any] | None = None
    interpretation: str
