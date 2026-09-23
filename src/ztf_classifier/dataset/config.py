"""Dataset configuration contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration for reproducible dataset acquisition."""

    dataset_version: str
    survey: str
    source: str
    classifier: str
    classes: tuple[str, ...]
    samples_per_class: int
    probability_min: float
    classifier_version: str = "unknown"
    fallback_probability: float | None = None
    page_size: int | None = None
    selection_strategy: str = "fallback_on_empty"

    def __post_init__(self) -> None:
        if not self.dataset_version:
            raise ValueError("dataset_version must not be empty")

        if not self.survey:
            raise ValueError("survey must not be empty")

        if not self.source:
            raise ValueError("source must not be empty")

        if not self.classifier:
            raise ValueError("classifier must not be empty")

        if not self.classifier_version:
            raise ValueError("classifier_version must not be empty")

        if not self.classes:
            raise ValueError("classes must not be empty")

        if len(set(self.classes)) != len(self.classes):
            raise ValueError("duplicate classes are not allowed")

        if self.samples_per_class <= 0:
            raise ValueError(
                "samples_per_class must be greater than zero"
            )

        if not 0.0 <= self.probability_min <= 1.0:
            raise ValueError(
                "probability_min must be between 0.0 and 1.0"
            )

        if self.fallback_probability is not None and not (
            0.0 <= self.fallback_probability <= 1.0
        ):
            raise ValueError(
                "fallback_probability must be between 0.0 and 1.0"
            )

        if self.page_size is not None and self.page_size <= 0:
            raise ValueError(
                "page_size must be greater than zero"
            )

        allowed_strategies = {
            "strict_primary",
            "fallback_on_empty",
            "historical_full_requery",
        }

        if self.selection_strategy not in allowed_strategies:
            raise ValueError(
                "unsupported selection_strategy: "
                + self.selection_strategy
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetConfig:
        """Construct a dataset configuration from a mapping."""

        if not isinstance(data, dict):
            raise TypeError("dataset configuration must be a dictionary")

        required = {
            "dataset_version",
            "survey",
            "source",
            "classifier",
            "classes",
            "samples_per_class",
            "probability_min",
        }

        missing = sorted(required - data.keys())

        if missing:
            raise ValueError(
                "missing required configuration fields: "
                + ", ".join(missing)
            )

        classes = data["classes"]

        if not isinstance(classes, (list, tuple)):
            raise TypeError("classes must be a list or tuple")

        return cls(
            dataset_version=data["dataset_version"],
            survey=data["survey"],
            source=data["source"],
            classifier=data["classifier"],
            classes=tuple(classes),
            samples_per_class=data["samples_per_class"],
            probability_min=data["probability_min"],
            classifier_version=data.get(
                "classifier_version",
                "unknown",
            ),
            fallback_probability=data.get(
                "fallback_probability",
            ),
            page_size=data.get("page_size"),
            selection_strategy=data.get(
                "selection_strategy",
                "fallback_on_empty",
            ),
        )

    @classmethod
    def from_json(cls, path: Path) -> DatasetConfig:
        """Load a dataset configuration from a JSON file."""

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"configuration file does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"configuration path is not a file: {path}"
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid JSON configuration: {path}"
            ) from exc

        return cls.from_dict(data)

    @property
    def requested_object_count(self) -> int:
        """Return the nominal requested object count."""

        return len(self.classes) * self.samples_per_class

    @property
    def effective_page_size(self) -> int:
        """Return the configured API page size."""

        return (
            self.samples_per_class
            if self.page_size is None
            else self.page_size
        )

    def selection_policy(self) -> dict[str, Any]:
        """Return the object-selection policy."""

        return {
            "probability": self.probability_min,
            "fallback_probability": self.fallback_probability,
            "samples_per_class": self.samples_per_class,
            "page_size": self.effective_page_size,
            "classes": self.classes,
            "selection_strategy": self.selection_strategy,
        }
