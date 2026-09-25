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
