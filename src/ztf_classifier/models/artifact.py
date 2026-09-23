"""Production model artifact contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ztf_classifier.models.classes import MODEL_CLASSES, NUM_CLASSES
from ztf_classifier.models.config import ModelConfig


@dataclass(frozen=True)
class ModelArtifact:
    """Immutable metadata contract for a fitted production model."""

    model: Any
    model_version: str
    model_family: str
    classes: tuple[str, ...]
    feature_schema_version: str
    feature_names: tuple[str, ...]
    configuration: ModelConfig
    dataset_sha256: str
    feature_schema_sha256: str

    def __post_init__(self) -> None:
        """Validate the production model artifact contract."""

        if self.model is None:
            raise ValueError("Model artifact requires a fitted model.")

        if not self.model_version:
            raise ValueError("model_version must be non-empty.")

        if not self.model_family:
            raise ValueError("model_family must be non-empty.")

        if self.classes != MODEL_CLASSES:
            raise ValueError(
                "Model artifact classes must match the frozen class order."
            )

        if len(self.classes) != NUM_CLASSES:
            raise ValueError(
                "Model artifact must contain exactly 15 classes."
            )

        if not self.feature_schema_version:
            raise ValueError(
                "feature_schema_version must be non-empty."
            )

        if len(self.feature_names) != 42:
            raise ValueError(
                "Model artifact must contain exactly 42 features."
            )

        if len(set(self.feature_names)) != 42:
            raise ValueError(
                "Model artifact feature names must be unique."
            )

        if self.configuration.version != self.model_version:
            raise ValueError(
                "Model configuration version does not match "
                "model_version."
            )

        if self.configuration.family != self.model_family:
            raise ValueError(
                "Model configuration family does not match "
                "model_family."
            )

        if len(self.dataset_sha256) != 64:
            raise ValueError(
                "dataset_sha256 must be a SHA-256 hexadecimal digest."
            )

        if len(self.feature_schema_sha256) != 64:
            raise ValueError(
                "feature_schema_sha256 must be a SHA-256 hexadecimal digest."
            )


__all__ = ["ModelArtifact"]
