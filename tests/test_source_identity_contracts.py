import pytest

from ztf_classifier.domain import (
    AssociationEvidence,
    AssociationStatus,
    AstrophysicalSourceRef,
    CatalogEntryRef,
    EntityKind,
    IdentityStatus,
    SourceAssociation,
    SurveyObjectRef,
)


def _survey_object(*, band: str = "g", object_id: str = "ZTF-OID-1") -> SurveyObjectRef:
    return SurveyObjectRef(
        survey="ZTF",
        release="DR24",
        object_id=object_id,
        band=band,
        field=199,
        rcid=32,
    )


def _evidence(*, score: float = 0.7) -> AssociationEvidence:
    return AssociationEvidence(
        evidence_id="evidence-1",
        method="astrometric-likelihood",
        method_version="1.0",
        policy_version="policy-1",
        source_ref="ztf:DR24:ZTF-OID-1",
        candidate_ref="internal:source-1",
        score=score,
        score_kind="raw_score",
        separation_arcsec=0.4,
        content_hash="sha256:abc123",
    )


def test_survey_object_ref_preserves_native_identity_and_partition_context() -> None:
    ref = _survey_object()

    assert ref.survey == "ZTF"
    assert ref.release == "DR24"
    assert ref.object_id == "ZTF-OID-1"
    assert ref.band == "g"
    assert ref.field == 199
    assert ref.rcid == 32


def test_distinct_band_oids_remain_distinct_survey_objects() -> None:
    g_ref = _survey_object(band="g", object_id="ZTF-G-1")
    r_ref = _survey_object(band="r", object_id="ZTF-R-1")

    assert g_ref != r_ref
    assert len({g_ref, r_ref}) == 2


def test_survey_object_requires_survey_release_and_object_id() -> None:
    with pytest.raises(ValueError, match="survey, release and object_id"):
        SurveyObjectRef(survey="ZTF", release="", object_id="OID-1")


def test_catalog_entry_is_scoped_by_catalog_and_release() -> None:
    dr3 = CatalogEntryRef(catalog="Gaia", release="DR3", entry_id="123")
    dr4 = CatalogEntryRef(catalog="Gaia", release="DR4", entry_id="123")

    assert dr3 != dr4


def test_superseded_source_requires_lineage_target() -> None:
    with pytest.raises(ValueError, match="superseded_by"):
        AstrophysicalSourceRef(
            source_id="source-old",
            entity_kind=EntityKind.POINT_SOURCE,
            identity_status=IdentityStatus.SUPERSEDED,
            created_at="2026-11-12T00:00:00Z",
            provenance_refs=("manifest:1",),
        )


def test_calibrated_probability_requires_calibration_version() -> None:
    with pytest.raises(ValueError, match="calibration_version"):
        AssociationEvidence(
            evidence_id="e1",
            method="likelihood",
            method_version="1",
            policy_version="p1",
            source_ref="survey:oid",
            candidate_ref="source:1",
            score=0.8,
            score_kind="calibrated_probability",
        )


def test_raw_match_score_is_not_restricted_to_probability_range() -> None:
    evidence = _evidence(score=4.2)

    assert evidence.score == 4.2
    assert evidence.score_kind == "raw_score"


def test_calibrated_probability_must_be_bounded() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        AssociationEvidence(
            evidence_id="e1",
            method="likelihood",
            method_version="1",
            policy_version="p1",
            source_ref="survey:oid",
            candidate_ref="source:1",
            score=1.2,
            score_kind="calibrated_probability",
            calibration_version="cal-v1",
        )


def test_confirmed_association_requires_candidate_and_evidence() -> None:
    association = SourceAssociation(
        association_id="association-1",
        schema_version="1.0",
        status=AssociationStatus.CONFIRMED_MATCH,
        survey_objects=(_survey_object(),),
        candidate_source_ids=("source-1",),
        evidence=(_evidence(),),
        decision_policy_version="policy-1",
        decided_at="2026-11-12T00:00:00Z",
        confirmed_source_id="source-1",
    )

    assert association.confirmed_source_id == "source-1"
    assert association.status is AssociationStatus.CONFIRMED_MATCH


def test_confirmed_association_requires_supporting_evidence() -> None:
    with pytest.raises(ValueError, match="supporting evidence"):
        SourceAssociation(
            association_id="association-1",
            schema_version="1.0",
            status=AssociationStatus.CONFIRMED_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1",),
            evidence=(),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
            confirmed_source_id="source-1",
        )


def test_ambiguous_association_cannot_set_confirmed_source() -> None:
    with pytest.raises(ValueError, match="only confirmed matches"):
        SourceAssociation(
            association_id="association-2",
            schema_version="1.0",
            status=AssociationStatus.AMBIGUOUS_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1", "source-2"),
            evidence=(_evidence(),),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
            confirmed_source_id="source-1",
        )


def test_ambiguous_association_preserves_candidates_without_forcing_a_match() -> None:
    association = SourceAssociation(
        association_id="association-2",
        schema_version="1.0",
        status=AssociationStatus.AMBIGUOUS_MATCH,
        survey_objects=(_survey_object(),),
        candidate_source_ids=("source-1", "source-2"),
        evidence=(_evidence(),),
        decision_policy_version="policy-1",
        decided_at="2026-11-12T00:00:00Z",
    )

    assert association.confirmed_source_id is None
    assert association.candidate_source_ids == ("source-1", "source-2")


def test_unmatched_association_cannot_contain_candidate_source_ids() -> None:
    with pytest.raises(ValueError, match="unmatched associations"):
        SourceAssociation(
            association_id="association-3",
            schema_version="1.0",
            status=AssociationStatus.UNMATCHED,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1",),
            evidence=(),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
        )


def test_rejected_association_requires_rejected_candidate() -> None:
    with pytest.raises(ValueError, match="rejected candidate"):
        SourceAssociation(
            association_id="association-4",
            schema_version="1.0",
            status=AssociationStatus.REJECTED_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=(),
            evidence=(_evidence(),),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
        )


def test_duplicate_survey_object_refs_are_rejected() -> None:
    ref = _survey_object()

    with pytest.raises(ValueError, match="must not contain duplicates"):
        SourceAssociation(
            association_id="association-5",
            schema_version="1.0",
            status=AssociationStatus.UNMATCHED,
            survey_objects=(ref, ref),
            candidate_source_ids=(),
            evidence=(),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
        )
