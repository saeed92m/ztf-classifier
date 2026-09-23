"""Application request and response schemas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ztf_classifier.models.results import PredictionResult


@dataclass(frozen=True)
class PredictionRequest:
    """Request for production prediction."""

    dataset: pd.DataFrame
    artifact_dir: Path

    def __post_init__(self) -> None:
        """Validate the application request."""

        if not isinstance(self.dataset, pd.DataFrame):
            raise TypeError("dataset must be a pandas DataFrame.")

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


@dataclass(frozen=True)
class PredictionResponse:
    """Application response containing prediction and model metadata."""

    result: PredictionResult
    model_version: str
    model_family: str

    def __post_init__(self) -> None:
        """Validate response metadata."""

        if not self.model_version:
            raise ValueError("model_version must not be empty.")

        if not self.model_family:
            raise ValueError("model_family must not be empty.")

    @property
    def sample_count(self) -> int:
        """Return the number of classified samples."""

        return self.result.sample_count
