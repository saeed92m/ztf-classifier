"""Evidence-bearing source identity contracts.

These records distinguish survey-native object identifiers from physical
astrophysical source identities. They define data contracts only; they do not
perform cross-matching, merge OIDs, or infer source identity.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from math import isfinite


class EntityKind(str, Enum):
    """Kinds of astrophysical entities represented by the identity registry."""

    POINT_SOURCE = "point_source"
    EXTENDED_SOURCE = "extended_source"
    TRANSIENT_EVENT_SOURCE = "transient_event_source"
    SOLAR_SYSTEM_BODY = "solar_system_body"
    UNRESOLVED_OR_BLENDED_SOURCE = "unresolved_or_blended_source"
    UNKNOWN_SOURCE = "unknown_source"


class IdentityStatus(str, Enum):
    """Lifecycle status of an internal astrophysical-source record."""

    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


class AssociationStatus(str, Enum):
    """Outcome of an evidence-backed association decision."""

    CONFIRMED_MATCH = "confirmed_match"
    AMBIGUOUS_MATCH = "ambiguous_match"
    UNMATCHED = "unmatched"
    REJECTED_MATCH = "rejected_match"
    DEFERRED_REVIEW = "deferred_review"


NO_CANDIDATE_REFERENCE = "no-candidate"


@dataclass(frozen=True)
class SurveyObjectRef:
    """A source-native survey object, not a physical-source identity."""

    survey: str
    release: str
    object_id: str
    band: str | None = None
    field: int | None = None
    rcid: int | None = None

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.survey, self.release, self.object_id)
        ):
            raise ValueError("survey, release and object_id are required.")
        if self.field is not None and self.field < 0:
            raise ValueError("field must be non-negative.")
        if self.rcid is not None and self.rcid < 0:
            raise ValueError("rcid must be non-negative.")
        if self.band is not None and not self.band.strip():
            raise ValueError("band must be non-empty when provided.")

    @property
    def reference_key(self) -> str:
        """Return a stable, unambiguous key for this survey-native object."""
        payload = json.dumps(
            [
                self.survey,
                self.release,
                self.object_id,
                self.band,
                self.field,
                self.rcid,
            ],
            ensure_ascii=True,
            separators=(",", ":"),
        )
        return f"survey-object:{payload}"


@dataclass(frozen=True)
class CatalogEntryRef:
    """An external catalog entry scoped to a catalog release."""

    catalog: str
    release: str
    entry_id: str

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.catalog, self.release, self.entry_id)
        ):
            raise ValueError("catalog, release and entry_id are required.")


@dataclass(frozen=True)
class AstrophysicalSourceRef:
    """An internal source hypothesis with explicit entity and identity status."""

    source_id: str
    entity_kind: EntityKind
    identity_status: IdentityStatus
    created_at: str
    provenance_refs: tuple[str, ...]
    superseded_by: str | None = None
    confirmation_association_id: str | None = None

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (self.source_id, self.created_at)
        ):
            raise ValueError("source_id and created_at are required.")
        if not isinstance(self.entity_kind, EntityKind):
            raise TypeError("entity_kind must be an EntityKind.")
        if not isinstance(self.identity_status, IdentityStatus):
            raise TypeError("identity_status must be an IdentityStatus.")
        if not isinstance(self.provenance_refs, tuple) or not self.provenance_refs:
            raise ValueError("provenance_refs must be a non-empty tuple.")
        if any(
            not isinstance(ref, str) or not ref.strip()
            for ref in self.provenance_refs
        ):
            raise ValueError("provenance_refs must contain non-empty strings.")
        if self.identity_status is IdentityStatus.SUPERSEDED:
            if not self.superseded_by or not self.superseded_by.strip():
                raise ValueError("superseded source records require superseded_by.")
            if self.superseded_by == self.source_id:
                raise ValueError("a source record cannot supersede itself.")
        elif self.superseded_by is not None:
            raise ValueError("superseded_by is only valid for superseded records.")
        if self.confirmation_association_id is not None and not (
            self.confirmation_association_id.strip()
        ):
            raise ValueError("confirmation_association_id must be non-empty.")
        if (
            self.identity_status is IdentityStatus.CONFIRMED
            and self.confirmation_association_id is None
        ):
            raise ValueError(
                "confirmed source identity requires a confirmation association ID."
            )


@dataclass(frozen=True)
class AssociationEvidence:
    """Versioned evidence supporting or rejecting one candidate association."""

    evidence_id: str
    method: str
    method_version: str
    policy_version: str
    source_ref: str
    candidate_ref: str
    score: float | None = None
    score_kind: str = "raw_score"
    calibration_version: str | None = None
    separation_arcsec: float | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.evidence_id,
            self.method,
            self.method_version,
            self.policy_version,
            self.source_ref,
            self.candidate_ref,
        )
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise ValueError(
                "association evidence identity and version fields are required."
            )
        if self.score_kind not in {"raw_score", "calibrated_probability"}:
            raise ValueError("score_kind must be raw_score or calibrated_probability.")
        if self.score is not None and not isfinite(self.score):
            raise ValueError("score must be finite.")
        if self.score_kind == "calibrated_probability":
            if self.score is None or not 0.0 <= self.score <= 1.0:
                raise ValueError("calibrated probability must be between 0 and 1.")
            if not self.calibration_version or not self.calibration_version.strip():
                raise ValueError("calibrated probability requires calibration_version.")
        if self.separation_arcsec is not None and (
            not isfinite(self.separation_arcsec) or self.separation_arcsec < 0
        ):
            raise ValueError("separation_arcsec must be finite and non-negative.")
        if self.content_hash is not None and not self.content_hash.strip():
            raise ValueError("content_hash must be non-empty when provided.")


@dataclass(frozen=True)
class SourceAssociation:
    """Append-only association decision; it never performs a source merge."""

    association_id: str
    schema_version: str
    status: AssociationStatus
    survey_objects: tuple[SurveyObjectRef, ...]
    candidate_source_ids: tuple[str, ...]
    evidence: tuple[AssociationEvidence, ...]
    decision_policy_version: str
    decided_at: str
    confirmed_source_id: str | None = None
    reviewer_ref: str | None = None
    supersedes_association_id: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.association_id,
            self.schema_version,
            self.decision_policy_version,
            self.decided_at,
        )
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise ValueError(
                "association identity, schema, policy and timestamp are required."
            )
        if not isinstance(self.status, AssociationStatus):
            raise TypeError("status must be an AssociationStatus.")
        if not isinstance(self.survey_objects, tuple) or not self.survey_objects:
            raise ValueError("survey_objects must be a non-empty tuple.")
        if any(not isinstance(item, SurveyObjectRef) for item in self.survey_objects):
            raise TypeError("survey_objects must contain SurveyObjectRef values.")
        if len(set(self.survey_objects)) != len(self.survey_objects):
            raise ValueError("survey_objects must not contain duplicates.")
        if not isinstance(self.candidate_source_ids, tuple):
            raise TypeError("candidate_source_ids must be a tuple.")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in self.candidate_source_ids
        ):
            raise ValueError("candidate_source_ids must contain non-empty strings.")
        if len(set(self.candidate_source_ids)) != len(self.candidate_source_ids):
            raise ValueError("candidate_source_ids must be unique.")
        if not isinstance(self.evidence, tuple):
            raise TypeError("evidence must be a tuple.")
        if any(not isinstance(item, AssociationEvidence) for item in self.evidence):
            raise TypeError("evidence must contain AssociationEvidence values.")
        if self.reviewer_ref is not None and not self.reviewer_ref.strip():
            raise ValueError("reviewer_ref must be non-empty when provided.")
        if self.supersedes_association_id is not None:
            if not self.supersedes_association_id.strip():
                raise ValueError(
                    "supersedes_association_id must be non-empty when provided."
                )
            if self.supersedes_association_id == self.association_id:
                raise ValueError("an association cannot supersede itself.")

        if (
            self.status is not AssociationStatus.DEFERRED_REVIEW
            and not self.evidence
        ):
            raise ValueError(
                "association decisions require evidence except deferred review."
            )

        if self.status is AssociationStatus.CONFIRMED_MATCH:
            if not self.confirmed_source_id or not self.confirmed_source_id.strip():
                raise ValueError("confirmed matches require confirmed_source_id.")
            if not self.evidence:
                raise ValueError("confirmed matches require supporting evidence.")
            if self.candidate_source_ids != (self.confirmed_source_id,):
                raise ValueError(
                    "confirmed matches must contain exactly the confirmed source ID."
                )
        elif self.confirmed_source_id is not None:
            raise ValueError("only confirmed matches may set confirmed_source_id.")

        if self.status is AssociationStatus.UNMATCHED and self.candidate_source_ids:
            raise ValueError(
                "unmatched associations cannot contain candidate source IDs."
            )

        if (
            self.status is AssociationStatus.AMBIGUOUS_MATCH
            and not self.candidate_source_ids
        ):
            raise ValueError(
                "ambiguous associations require at least one candidate source ID."
            )
        if (
            self.status is AssociationStatus.REJECTED_MATCH
            and not self.candidate_source_ids
        ):
            raise ValueError(
                "rejected matches require the rejected candidate source ID."
            )

        survey_reference_keys = {
            item.reference_key for item in self.survey_objects
        }
        if any(
            item.source_ref not in survey_reference_keys for item in self.evidence
        ):
            raise ValueError(
                "association evidence source_ref must match a declared survey object."
            )

        expected_candidate_refs = {
            f"astrophysical-source:{source_id}"
            for source_id in self.candidate_source_ids
        }
        evidence_candidate_refs = {
            item.candidate_ref for item in self.evidence
        }
        if self.status in {
            AssociationStatus.CONFIRMED_MATCH,
            AssociationStatus.AMBIGUOUS_MATCH,
            AssociationStatus.REJECTED_MATCH,
        } and evidence_candidate_refs != expected_candidate_refs:
            raise ValueError(
                "association evidence must cover exactly the declared candidate source IDs."
            )
        if self.status is AssociationStatus.UNMATCHED and any(
            item.candidate_ref != NO_CANDIDATE_REFERENCE
            for item in self.evidence
        ):
            raise ValueError(
                "unmatched evidence must use the no-candidate reference."
            )


def validate_source_confirmation(
    source: AstrophysicalSourceRef,
    association: SourceAssociation,
) -> None:
    """Validate that a confirmed source points to its matching association."""
    if source.identity_status is not IdentityStatus.CONFIRMED:
        raise ValueError("source identity is not confirmed.")
    if source.confirmation_association_id != association.association_id:
        raise ValueError("confirmation association ID does not match.")
    if association.status is not AssociationStatus.CONFIRMED_MATCH:
        raise ValueError("confirmation association is not a confirmed match.")
    if association.confirmed_source_id != source.source_id:
        raise ValueError("confirmed association points to a different source.")
