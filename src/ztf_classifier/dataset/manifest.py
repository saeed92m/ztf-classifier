"""Canonical object-manifest construction."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_OBJECT_COLUMNS = (
    "oid",
    "class",
    "classifier",
    "probability",
    "label_source",
    "label_type",
    "label_probability",
    "classifier_version",
    "survey",
)


@dataclass(frozen=True)
class ObjectManifest:
    """Canonical object manifest with dataset-level provenance."""

    objects: pd.DataFrame
    dataset_version: str
    probability_min: float
    samples_per_class: int

    def __post_init__(self) -> None:
        missing = set(REQUIRED_OBJECT_COLUMNS) - set(self.objects.columns)
        if missing:
            raise ValueError(
                f"Object manifest is missing columns: {sorted(missing)}"
            )

        if self.objects["oid"].duplicated().any():
            raise ValueError("Object manifest contains duplicate OIDs")

        if self.samples_per_class <= 0:
            raise ValueError("samples_per_class must be greater than zero")

        if not 0.0 <= self.probability_min <= 1.0:
            raise ValueError("probability_min must be between 0.0 and 1.0")

    @property
    def object_count(self) -> int:
        return len(self.objects)

    @property
    def class_counts(self) -> pd.Series:
        return self.objects["class"].value_counts().sort_index()

    @property
    def classes(self) -> tuple[str, ...]:
        return tuple(sorted(self.objects["class"].unique()))
