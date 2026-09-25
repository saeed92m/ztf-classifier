"""Unified scientific feature-engine orchestration."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

from ztf_classifier.features.contracts import (
    FeatureBackend,
    FeatureProvenance,
    FeatureResult,
)
from ztf_classifier.features.pipeline import (
    extract_v0_2_features,
    validate_v0_2_feature_vector,
)


def _observation_sha256(observations: pd.DataFrame) -> str:
    """Hash normalized observations without filesystem paths."""
    canonical = observations.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class NativeV0_2Backend:
    """Native implementation preserving the frozen v0.2 feature contract."""

    name = "native"
    software_version = "ztf-classifier-native-v0.2"
    feature_schema_version = "v0.2"

    def extract(
        self,
        observations: pd.DataFrame,
        *,
        parameters: dict[str, Any],
    ) -> dict[str, float]:
        """Extract the historical 42-feature vector."""
        features = extract_v0_2_features(
            observations,
            cutoff_mjd=parameters.get("cutoff_mjd"),
        )
        validate_v0_2_feature_vector(features)
        return features


class ScientificFeatureEngine:
    """Dispatch scientific feature extraction through versioned backends."""

    def __init__(self, backends: list[FeatureBackend] | None = None) -> None:
        self._backends: dict[str, FeatureBackend] = {}
        for backend in backends or [NativeV0_2Backend()]:
            self.register_backend(backend)

    def register_backend(self, backend: FeatureBackend, *, replace: bool = False) -> None:
        """Register a backend with explicit collision semantics."""
        name = str(getattr(backend, "name", "")).strip()
        schema_version = str(getattr(backend, "feature_schema_version", "")).strip()
        software_version = str(getattr(backend, "software_version", "")).strip()
        if not name or not schema_version or not software_version:
            raise ValueError(
                "feature backends require name, software_version, and "
                "feature_schema_version"
            )
        if not callable(getattr(backend, "extract", None)):
            raise TypeError("feature backend must provide a callable extract method")
        if name in self._backends and not replace:
            raise ValueError(f"Feature backend already registered: {name}")
        self._backends[name] = backend

    def get_backend(self, name: str) -> FeatureBackend:
        """Return one registered backend or raise a stable lookup error."""
        try:
            return self._backends[name]
        except KeyError as exc:
            raise KeyError(f"Unknown feature backend: {name}") from exc

    def backend_metadata(self, name: str) -> dict[str, str]:
        """Return versioned backend metadata for UI/API discovery."""
        backend = self.get_backend(name)
        return {
            "name": backend.name,
            "software_version": backend.software_version,
            "feature_schema_version": backend.feature_schema_version,
        }

    def list_backends(self) -> tuple[str, ...]:
        """Return deterministic registered backend names."""
        return tuple(sorted(self._backends))

    def compute(
        self,
        observations: pd.DataFrame,
        *,
        backend: str = "native",
        parameters: dict[str, Any] | None = None,
    ) -> FeatureResult:
        """Compute a feature vector with explicit backend provenance."""
        if not isinstance(observations, pd.DataFrame):
            raise TypeError("observations must be a pandas DataFrame.")
        if observations.empty:
            raise ValueError("observations must contain at least one row.")

        selected = self._backends.get(backend)
        if selected is None:
            available = ", ".join(self.list_backends())
            raise ValueError(
                f"Unknown feature backend '{backend}'. Available: {available}"
            )

        effective_parameters = dict(parameters or {})
        values = selected.extract(
            observations,
            parameters=effective_parameters,
        )
        return FeatureResult(
            values=values,
            feature_schema_version=selected.feature_schema_version,
            provenance=FeatureProvenance(
                backend=selected.name,
                software_version=selected.software_version,
                feature_schema_version=selected.feature_schema_version,
                parameters=effective_parameters,
                input_observation_sha256=_observation_sha256(observations),
            ),
        )


__all__ = ["NativeV0_2Backend", "ScientificFeatureEngine"]
