"""Provenance-bearing external catalog and cross-match contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogMatch:
    """One contextual cross-match; never an implicit ground-truth label."""

    catalog: str
    catalog_version: str
    retrieved_at: str
    source_id: str
    matched_id: str | None
    matching_method: str
    matching_policy: str
    match_radius_arcsec: float | None = None
    match_probability: float | None = None
    match_quality: str | None = None
    evaluation_role: str = "context"
    provenance: dict[str, str] | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.catalog or not self.catalog_version:
            raise ValueError("catalog and catalog_version are required.")
        if not self.source_id or not self.matching_method or not self.matching_policy:
            raise ValueError("source_id, matching_method and matching_policy are required.")
        if self.evaluation_role not in {"context", "reference", "validation"}:
            raise ValueError("evaluation_role must be context, reference or validation.")
        if self.match_radius_arcsec is not None and self.match_radius_arcsec <= 0:
            raise ValueError("match_radius_arcsec must be positive.")
        if self.match_probability is not None and not 0.0 <= self.match_probability <= 1.0:
            raise ValueError("match_probability must be between 0 and 1.")


@dataclass(frozen=True)
class CatalogContext:
    """Versioned contextual catalog evidence attached to an observation."""

    matches: tuple[CatalogMatch, ...]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("schema_version must not be empty.")
        if not isinstance(self.matches, tuple):
            raise TypeError("matches must be a tuple.")
