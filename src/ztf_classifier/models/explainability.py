"""Explainability and modality declarations for analysis results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplainabilityEvidence:
    """Supplementary model explanation, never a scientific-validity claim."""

    method: str
    schema_version: str
    top_features: tuple[str, ...] = ()
    values: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not self.method or not self.schema_version:
            raise ValueError("method and schema_version are required.")
        if len(self.top_features) != len(self.values):
            raise ValueError("top_features and values must have equal length.")


@dataclass(frozen=True)
class ModalityDeclaration:
    """Explicit input modality contract for an analysis mode."""

    name: str
    required: bool = True
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("modality name is required.")


@dataclass(frozen=True)
class AnalysisModeContract:
    """Registry-facing declaration of an analysis mode's consumed modalities."""

    mode_id: str
    task_type: str
    modalities: tuple[ModalityDeclaration, ...]
    explainability_methods: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.mode_id or not self.task_type:
            raise ValueError("mode_id and task_type are required.")
        names = [item.name for item in self.modalities]
        if len(names) != len(set(names)):
            raise ValueError("modality names must be unique.")
