"""Human-in-the-loop discovery and candidate evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveryCandidate:
    """A versioned candidate assembled from analysis and evidence."""

    candidate_id: str
    candidate_version: str
    oid: str
    analysis_mode: str
    model_version: str
    generation_rule_version: str
    review_status: str = "unreviewed"
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (
            self.candidate_id,
            self.candidate_version,
            self.oid,
            self.analysis_mode,
            self.model_version,
            self.generation_rule_version,
        )
        if not all(required):
            raise ValueError("candidate identity/version fields are required.")
        if self.review_status not in {"unreviewed", "in_review", "accepted", "rejected", "deferred"}:
            raise ValueError("invalid review_status.")


@dataclass(frozen=True)
class HumanReview:
    """Provenance-bearing scientific review evidence."""

    candidate_id: str
    candidate_version: str
    reviewer_ref: str
    reviewed_at: str
    decision: str
    evidence_presented: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.candidate_id, self.candidate_version, self.reviewer_ref, self.reviewed_at)):
            raise ValueError("review identity and timestamp are required.")
        if self.decision not in {"accept", "reject", "defer", "needs_more_evidence"}:
            raise ValueError("invalid review decision.")


@dataclass(frozen=True)
class LearningFeedback:
    """Controlled feedback eligible for later dataset construction."""

    feedback_id: str
    candidate_id: str
    candidate_version: str
    review_ref: str
    created_at: str
    intended_role: str = "review_evidence"
    dataset_version: str | None = None

    def __post_init__(self) -> None:
        if not all((self.feedback_id, self.candidate_id, self.candidate_version, self.review_ref, self.created_at)):
            raise ValueError("feedback identity/provenance fields are required.")
        if self.intended_role not in {"review_evidence", "training_candidate", "validation_candidate"}:
            raise ValueError("invalid intended_role.")
        if self.intended_role != "review_evidence" and not self.dataset_version:
            raise ValueError("training/validation feedback requires an explicit dataset_version.")
