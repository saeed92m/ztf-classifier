"""Configuration contract for dataset construction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetConfig:
    """Immutable configuration describing a dataset selection policy."""

    dataset_version: str
    survey: str
    source: str
    classifier: str
    classes: tuple[str, ...]
    probability_min: float
    samples_per_class: int

    def __post_init__(self) -> None:
        if not self.dataset_version:
            raise ValueError("dataset_version must not be empty")

        if not self.survey:
            raise ValueError("survey must not be empty")

        if not self.source:
            raise ValueError("source must not be empty")

        if not self.classifier:
            raise ValueError("classifier must not be empty")

        if not self.classes:
            raise ValueError("classes must not be empty")

        if len(self.classes) != len(set(self.classes)):
            raise ValueError("classes contain duplicate values")

        if not 0.0 <= self.probability_min <= 1.0:
            raise ValueError(
                "probability_min must be between 0.0 and 1.0"
            )

        if self.samples_per_class <= 0:
            raise ValueError(
                "samples_per_class must be greater than zero"
            )

    @property
    def requested_object_count(self) -> int:
        """Return the number of objects requested by the selection policy."""
        return len(self.classes) * self.samples_per_class

    def selection_policy(self) -> dict[str, object]:
        """Return the normalized selection policy."""
        return {
            "probability": self.probability_min,
            "samples_per_class": self.samples_per_class,
            "classes": self.classes,
        }
