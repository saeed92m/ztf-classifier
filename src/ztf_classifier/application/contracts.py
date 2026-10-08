"""Stable, serializable contracts between the product layer and scientific core.

These contracts describe orchestration and evidence rather than implementing
scientific algorithms. Desktop GUI, CLI, API, and future adapters consume them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class DataSourceRef:
    """Reference to an input source without copying its payload."""

    source_id: str
    source_type: str
    locator: str
    schema_version: str
    retrieval_time: str | None = None
    provider_version: str | None = None
    content_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProvenanceRecord:
    """Evidence identifying where an analysis input came from."""

    source: DataSourceRef
    operation: str
    software_version: str
    model_version: str | None = None
    artifact_hash: str | None = None
    feature_schema_hash: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisRequest:
    """User/application request passed toward scientific analysis."""

    request_id: str
    sources: Sequence[DataSourceRef]
    operation: str
    model_version: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    """Scientific result envelope consumed by presentation layers."""

    request_id: str
    status: str
    result_type: str
    payload: Mapping[str, Any]
    provenance: Sequence[ProvenanceRecord]
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisExecution:
    """Scientific execution payload returned to the application boundary."""

    result_type: str
    payload: Mapping[str, Any]
    diagnostics: Mapping[str, Any]
    provenance: Sequence[ProvenanceRecord]


class ApplicationService:
    """Orchestrate application requests without implementing science."""

    def __init__(
        self,
        executor: Callable[[AnalysisRequest], AnalysisExecution],
        *,
        software_version: str,
    ) -> None:
        if not isinstance(software_version, str) or not software_version.strip():
            raise ValueError("software_version must be a non-empty string.")
        self._executor = executor
        self._software_version = software_version

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Validate and execute one application-level analysis request."""
        self._validate_request(request)
        execution = self._executor(request)
        return AnalysisResult(
            request_id=request.request_id,
            status="success",
            result_type=execution.result_type,
            payload=execution.payload,
            provenance=tuple(execution.provenance),
            diagnostics=execution.diagnostics,
        )

    @staticmethod
    def _validate_request(request: AnalysisRequest) -> None:
        if not request.request_id.strip():
            raise ApplicationInputError("request_id must be a non-empty string.")
        if not request.operation.strip():
            raise ApplicationInputError("operation must be a non-empty string.")
        if not request.sources:
            raise ApplicationInputError("at least one data source is required.")
        if any(not source.source_id.strip() for source in request.sources):
            raise ApplicationInputError("source_id must be non-empty.")
        if any(not source.source_type.strip() for source in request.sources):
            raise ApplicationInputError("source_type must be non-empty.")
        if any(not source.locator.strip() for source in request.sources):
            raise ApplicationInputError("locator must be non-empty.")
        if any(not source.schema_version.strip() for source in request.sources):
            raise ApplicationInputError("schema_version must be non-empty.")
