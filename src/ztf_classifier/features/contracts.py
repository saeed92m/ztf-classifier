"""Contracts for the unified scientific feature engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd


@dataclass(frozen=True)
class FeatureProvenance:
    """Traceability metadata for one feature computation."""

    backend: str
    software_version: str
    feature_schema_version: str
    parameters: dict[str, Any]
    input_observation_sha256: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe provenance."""
        return {
            "backend": self.backend,
            "software_version": self.software_version,
            "feature_schema_version": self.feature_schema_version,
            "parameters": dict(self.parameters),
            "input_observation_sha256": self.input_observation_sha256,
        }


@dataclass(frozen=True)
class FeatureResult:
    """Feature vector plus its schema and provenance."""

    values: dict[str, float]
    feature_schema_version: str
    provenance: FeatureProvenance

    @property
    def feature_names(self) -> tuple[str, ...]:
        """Return deterministic feature order."""
        return tuple(self.values)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe feature result."""
        return {
            "feature_schema_version": self.feature_schema_version,
            "features": dict(self.values),
            "provenance": self.provenance.to_dict(),
        }


class FeatureBackend(Protocol):
    """Backend contract consumed by the unified feature engine."""

    name: str
    software_version: str
    feature_schema_version: str

    def extract(
        self,
        observations: pd.DataFrame,
        *,
        parameters: dict[str, Any],
    ) -> dict[str, float]:
        """Extract one deterministic feature vector."""
        ...
