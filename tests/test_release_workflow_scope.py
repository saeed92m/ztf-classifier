"""Regression tests for the product/release evidence boundary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCIENTIFIC_WORKFLOW = ROOT / ".github" / "workflows" / "scientific-validation.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def test_routine_scientific_workflow_does_not_acquire_cpvs_data() -> None:
    workflow = SCIENTIFIC_WORKFLOW.read_text(encoding="utf-8")

    forbidden = (
        "ztf_periodic_781k",
        "ztf_periodic_730k",
        "published_table4.dat",
        "derive-730k",
        "zenodo.org/records/3886372",
        "zenodo.org/records/5764899",
    )
    for value in forbidden:
        assert value not in workflow

    assert "star_embed_ztf_40k" in workflow
    assert "name: scientific-validation-heavy" in workflow
    assert "ztf_dr24_source_subset" in workflow
    assert "alerce_reference" in workflow


def test_release_workflow_requires_product_evidence_without_cpvs() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    forbidden = (
        "ztf_periodic_781k",
        "ztf_periodic_730k",
        "frozen-reference-evidence-ztf_periodic",
        "scientific-frozen-cpvs",
        "cpvs_reconstruction_status.json",
    )
    for value in forbidden:
        assert value not in workflow

    assert "scientific-validation-heavy" in workflow
    assert "ztf_star_embed.acquisition.json" in workflow
    assert "ztf_dr24_source_subset" in workflow
    assert "alerce_reference" in workflow
    assert "frozen-reference-evidence-alerce_reference_frozen_20200609" in workflow
