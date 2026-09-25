from ztf_classifier.validation.sources import SOURCES, get_source, source_ids


def test_source_registry_contains_all_release_gate_sources():
    assert source_ids() == (
        "star_embed_ztf_40k",
        "ztf_periodic_781k",
        "ztf_periodic_730k",
        "ztf_dr24_source_subset",
        "alerce_reference",
    )


def test_reference_system_is_not_ground_truth():
    source = get_source("alerce_reference")
    assert source.provenance_role == "reference_system"
    assert source.immutable_evidence_required is True


def test_every_source_has_explicit_acquisition_contract():
    assert len(SOURCES) == 5
    for source in SOURCES:
        assert source.url.startswith("https://")
        assert source.version
        assert source.acquisition
