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



def test_release_publication_is_manual_and_explicitly_authorized() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "default: false" in workflow
    assert "inputs.publish == true" in workflow
    assert "inputs.validation_run_id" in workflow
    assert "inputs.release_sha" in workflow
    assert '"head_branch": "main"' in workflow
    assert '"conclusion": "success"' in workflow



def test_release_workflow_never_moves_existing_tags_or_overwrites_releases() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "gh api --method DELETE" not in workflow
    assert "--clobber" not in workflow
    assert "gh release edit" not in workflow
    assert "Repair existing mutable release in place" not in workflow
    assert "Refusing to delete or move an existing tag" in workflow
    assert "refusing to overwrite assets or edit release metadata" in workflow
