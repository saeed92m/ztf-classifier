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


def _evidence(
    *,
    score: float = 0.7,
    survey_object: SurveyObjectRef | None = None,
    candidate_source_id: str | None = "source-1",
) -> AssociationEvidence:
    source_object = survey_object or _survey_object()
    return AssociationEvidence(
        evidence_id=f"evidence-{candidate_source_id or 'none'}",
        method="astrometric-likelihood",
        method_version="1.0",
        policy_version="policy-1",
        source_ref=source_object.reference_key,
        candidate_ref=(
            f"astrophysical-source:{candidate_source_id}"
            if candidate_source_id is not None
            else "no-candidate"
        ),
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
        evidence=(
            _evidence(candidate_source_id="source-1"),
            _evidence(candidate_source_id="source-2"),
        ),
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
            evidence=(_evidence(),),
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


def test_confirmed_association_cannot_leave_competing_candidates() -> None:
    with pytest.raises(ValueError, match="exactly the confirmed source ID"):
        SourceAssociation(
            association_id="association-6",
            schema_version="1.0",
            status=AssociationStatus.CONFIRMED_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1", "source-2"),
            evidence=(_evidence(),),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
            confirmed_source_id="source-1",
        )


def test_association_cannot_supersede_itself() -> None:
    with pytest.raises(ValueError, match="cannot supersede itself"):
        SourceAssociation(
            association_id="association-7",
            schema_version="1.0",
            status=AssociationStatus.UNMATCHED,
            survey_objects=(_survey_object(),),
            candidate_source_ids=(),
            evidence=(),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
            supersedes_association_id="association-7",
        )


def test_final_association_decisions_require_evidence() -> None:
    with pytest.raises(ValueError, match="require evidence"):
        SourceAssociation(
            association_id="association-8",
            schema_version="1.0",
            status=AssociationStatus.UNMATCHED,
            survey_objects=(_survey_object(),),
            candidate_source_ids=(),
            evidence=(),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
        )


def test_deferred_review_may_wait_for_evidence() -> None:
    association = SourceAssociation(
        association_id="association-9",
        schema_version="1.0",
        status=AssociationStatus.DEFERRED_REVIEW,
        survey_objects=(_survey_object(),),
        candidate_source_ids=(),
        evidence=(),
        decision_policy_version="policy-1",
        decided_at="2026-11-12T00:00:00Z",
    )

    assert association.status is AssociationStatus.DEFERRED_REVIEW


def test_source_record_cannot_supersede_itself() -> None:
    with pytest.raises(ValueError, match="cannot supersede itself"):
        AstrophysicalSourceRef(
            source_id="source-1",
            entity_kind=EntityKind.POINT_SOURCE,
            identity_status=IdentityStatus.SUPERSEDED,
            created_at="2026-11-12T00:00:00Z",
            provenance_refs=("manifest:1",),
            superseded_by="source-1",
        )



def test_survey_object_reference_key_includes_full_partition_identity() -> None:
    g_ref = _survey_object(band="g", object_id="ZTF-OID-1")
    r_ref = _survey_object(band="r", object_id="ZTF-OID-1")

    assert g_ref.reference_key != r_ref.reference_key


def test_confirmed_source_requires_association_reference() -> None:
    with pytest.raises(ValueError, match="confirmation association ID"):
        AstrophysicalSourceRef(
            source_id="source-1",
            entity_kind=EntityKind.POINT_SOURCE,
            identity_status=IdentityStatus.CONFIRMED,
            created_at="2026-11-12T00:00:00Z",
            provenance_refs=("manifest:1",),
        )


def _confirmed_association() -> SourceAssociation:
    return SourceAssociation(
        association_id="association-confirmed",
        schema_version="1.0",
        status=AssociationStatus.CONFIRMED_MATCH,
        survey_objects=(_survey_object(),),
        candidate_source_ids=("source-1",),
        evidence=(_evidence(candidate_source_id="source-1"),),
        decision_policy_version="policy-1",
        decided_at="2026-11-12T00:00:00Z",
        confirmed_source_id="source-1",
    )


def test_confirmed_source_reference_must_match_confirmed_association() -> None:
    source = AstrophysicalSourceRef(
        source_id="source-1",
        entity_kind=EntityKind.POINT_SOURCE,
        identity_status=IdentityStatus.CONFIRMED,
        created_at="2026-11-12T00:00:00Z",
        provenance_refs=("manifest:1",),
        confirmation_association_id="association-confirmed",
    )

    validate_source_confirmation(source, _confirmed_association())


def test_confirmed_source_rejects_association_for_another_source() -> None:
    source = AstrophysicalSourceRef(
        source_id="source-2",
        entity_kind=EntityKind.POINT_SOURCE,
        identity_status=IdentityStatus.CONFIRMED,
        created_at="2026-11-12T00:00:00Z",
        provenance_refs=("manifest:1",),
        confirmation_association_id="association-confirmed",
    )

    with pytest.raises(ValueError, match="different source"):
        validate_source_confirmation(source, _confirmed_association())


def test_association_rejects_evidence_for_unrelated_survey_object() -> None:
    with pytest.raises(ValueError, match="must match a declared survey object"):
        SourceAssociation(
            association_id="association-wrong-source",
            schema_version="1.0",
            status=AssociationStatus.CONFIRMED_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1",),
            evidence=(
                _evidence(
                    survey_object=_survey_object(object_id="ZTF-OID-OTHER"),
                    candidate_source_id="source-1",
                ),
            ),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
            confirmed_source_id="source-1",
        )


def test_confirmed_association_rejects_evidence_for_different_candidate() -> None:
    with pytest.raises(ValueError, match="cover exactly the declared candidate"):
        SourceAssociation(
            association_id="association-wrong-candidate",
            schema_version="1.0",
            status=AssociationStatus.CONFIRMED_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1",),
            evidence=(_evidence(candidate_source_id="source-2"),),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
            confirmed_source_id="source-1",
        )


def test_ambiguous_association_requires_evidence_for_every_candidate() -> None:
    with pytest.raises(ValueError, match="cover exactly the declared candidate"):
        SourceAssociation(
            association_id="association-partial-ambiguity",
            schema_version="1.0",
            status=AssociationStatus.AMBIGUOUS_MATCH,
            survey_objects=(_survey_object(),),
            candidate_source_ids=("source-1", "source-2"),
            evidence=(_evidence(candidate_source_id="source-1"),),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
        )


def test_unmatched_association_evidence_must_record_no_candidate() -> None:
    with pytest.raises(ValueError, match="no-candidate reference"):
        SourceAssociation(
            association_id="association-unmatched-wrong-evidence",
            schema_version="1.0",
            status=AssociationStatus.UNMATCHED,
            survey_objects=(_survey_object(),),
            candidate_source_ids=(),
            evidence=(_evidence(candidate_source_id="source-1"),),
            decision_policy_version="policy-1",
            decided_at="2026-11-12T00:00:00Z",
        )
