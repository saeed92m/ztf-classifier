import pytest

from ztf_classifier.models.catalog_context import CatalogContext, CatalogMatch
from ztf_classifier.models.discovery import DiscoveryCandidate, HumanReview, LearningFeedback
from ztf_classifier.models.explainability import (
    AnalysisModeContract,
    ExplainabilityEvidence,
    ModalityDeclaration,
)


def test_catalog_match_is_context_not_implicit_ground_truth() -> None:
    match = CatalogMatch(
        catalog="Gaia",
        catalog_version="DR3",
        retrieved_at="2026-10-03T00:00:00Z",
        source_id="ZTF1",
        matched_id="Gaia1",
        matching_method="cone",
        matching_policy="nearest-with-quality",
        evaluation_role="context",
    )
    context = CatalogContext(matches=(match,))
    assert context.matches[0].evaluation_role == "context"


def test_catalog_probability_is_bounded() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        CatalogMatch(
            catalog="Gaia",
            catalog_version="DR3",
            retrieved_at="now",
            source_id="ZTF1",
            matched_id="Gaia1",
            matching_method="cone",
            matching_policy="nearest",
            match_probability=1.1,
        )


def test_feedback_cannot_enter_training_without_dataset_version() -> None:
    with pytest.raises(ValueError, match="dataset_version"):
        LearningFeedback("f1", "c1", "v1", "r1", "now", intended_role="training_candidate")


def test_review_and_candidate_are_versioned() -> None:
    candidate = DiscoveryCandidate("c1", "v1", "ZTF1", "transient", "baseline_v0.2", "rule-v1")
    review = HumanReview("c1", "v1", "reviewer-1", "now", "defer")
    assert candidate.candidate_version == review.candidate_version


def test_explainability_and_modalities_are_explicit() -> None:
    evidence = ExplainabilityEvidence("feature-contribution-v1", "1.0", ("f1",), (0.2,))
    mode = AnalysisModeContract(
        "transient-v1",
        "classification",
        (ModalityDeclaration("light_curve"), ModalityDeclaration("catalog", required=False)),
        ("feature-contribution-v1",),
    )
    assert evidence.method in mode.explainability_methods
    assert mode.modalities[1].required is False
