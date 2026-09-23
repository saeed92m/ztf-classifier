"""Deterministic object-selection requests."""

from __future__ import annotations

from dataclasses import dataclass

from ztf_classifier.dataset.config import DatasetConfig


@dataclass(frozen=True)
class ObjectSelectionRequest:
    """Immutable request describing one class-level object selection."""

    survey: str
    classifier: str
    class_name: str
    probability: float
    page_size: int


class ObjectSelector:
    """Build deterministic selection requests from a dataset configuration."""

    def __init__(self, config: DatasetConfig) -> None:
        self._config = config

    def requests(self) -> tuple[ObjectSelectionRequest, ...]:
        """Return one selection request for each configured class."""
        return tuple(
            ObjectSelectionRequest(
                survey=self._config.survey,
                classifier=self._config.classifier,
                class_name=class_name,
                probability=self._config.probability_min,
                page_size=self._config.samples_per_class,
            )
            for class_name in self._config.classes
        )
