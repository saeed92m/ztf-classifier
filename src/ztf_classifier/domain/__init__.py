"""Domain contracts for the scientific analysis platform."""

from ztf_classifier.domain.source_identity import (
    AssociationEvidence,
    AssociationStatus,
    AstrophysicalSourceRef,
    CatalogEntryRef,
    EntityKind,
    IdentityStatus,
    SourceAssociation,
    SurveyObjectRef,
    validate_source_confirmation,
)

__all__ = [
    "AssociationEvidence",
    "AssociationStatus",
    "AstrophysicalSourceRef",
    "CatalogEntryRef",
    "EntityKind",
    "IdentityStatus",
    "SourceAssociation",
    "SurveyObjectRef",
    "validate_source_confirmation",
]
