"""Application request and response schemas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ztf_classifier.models.provenance import ModelProvenance
from ztf_classifier.models.results import PredictionResult


@dataclass(frozen=True)
class PredictionRequest:
    """Request for production prediction."""

    dataset: pd.DataFrame
    artifact_dir: Path | None = None
    registry_dir: Path | None = None
    model_version: str | None = None

    def __post_init__(self) -> None:
        """Validate the application request."""

        if not isinstance(self.dataset, pd.DataFrame):
            raise TypeError("dataset must be a pandas DataFrame.")

        if self.artifact_dir is None and self.registry_dir is None:
            raise ValueError(
                "Either artifact_dir or registry_dir must be provided."
            )

        if self.artifact_dir is not None and (
            self.registry_dir is not None or self.model_version is not None
        ):
            raise ValueError(
                "artifact_dir cannot be combined with registry selection."
            )

        if self.registry_dir is not None and not self.model_version:
            raise ValueError(
                "model_version is required when registry_dir is provided."
            )

        if self.artifact_dir is not None:
            artifact_dir = Path(self.artifact_dir)
            if not artifact_dir.exists():
                raise ValueError(
                    f"Artifact directory does not exist: {artifact_dir}"
                )
            if not artifact_dir.is_dir():
                raise ValueError(
                    f"Artifact path is not a directory: {artifact_dir}"
                )
            object.__setattr__(
                self,
                "artifact_dir",
                artifact_dir.resolve(),
            )

        if self.registry_dir is not None:
            registry_dir = Path(self.registry_dir)
            if not registry_dir.exists():
                raise ValueError(
                    f"Model registry directory does not exist: {registry_dir}"
                )
            if not registry_dir.is_dir():
                raise ValueError(
                    f"Model registry path is not a directory: {registry_dir}"
                )
            object.__setattr__(
                self,
                "registry_dir",
                registry_dir.resolve(),
            )


@dataclass(frozen=True)
class PredictionResponse:
    """Application response containing prediction and model provenance."""

    result: PredictionResult
    model_version: str
    model_family: str
    provenance: ModelProvenance

    def __post_init__(self) -> None:
        """Validate response metadata."""

        if not self.model_version:
            raise ValueError("model_version must not be empty.")

        if not self.model_family:
            raise ValueError("model_family must not be empty.")

        if self.provenance.model_version != self.model_version:
            raise ValueError(
                "Provenance model_version does not match response."
            )

        if self.provenance.model_family != self.model_family:
            raise ValueError(
                "Provenance model_family does not match response."
            )

    @property
    def sample_count(self) -> int:
        """Return the number of classified samples."""

        return self.result.sample_count
