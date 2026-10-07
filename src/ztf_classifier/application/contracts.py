"""Stable, serializable contracts between the product layer and scientific core.

These contracts describe orchestration and evidence rather than implementing
scientific algorithms. Desktop GUI, CLI, API, and future adapters consume them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


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