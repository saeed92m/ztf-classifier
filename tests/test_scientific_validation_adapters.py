"""Tests for canonical source-backed benchmark adapter plans."""

from pathlib import Path

import pytest

from ztf_classifier.validation.adapters import AdapterContractError, build_adapter_plan
from ztf_classifier.validation.manifest import BenchmarkManifest

ROOT = Path(__file__).parents[1]
BENCHMARK_DIR = ROOT / "configs" / "benchmarks"


def load(name: str) -> BenchmarkManifest:
    return BenchmarkManifest.from_json(BENCHMARK_DIR / f"{name}.json")


def test_781k_adapter_builds_canonical_plan() -> None:
    plan = build_adapter_plan(load("ztf_periodic_781k"))
    assert plan.source_id == "ztf_periodic_781k"
    assert plan.urls
    plan.validate()


def test_730k_adapter_requires_781k_parent_and_is_derived() -> None:
    manifest = load("ztf_periodic_730k")
    plan = build_adapter_plan(manifest)
    assert plan.parent_benchmark_id == "ztf_periodic_781k"
    assert plan.urls == ()
    payload = manifest.to_dict()
    payload["ground_truth_provenance"]["parent_benchmark"] = "wrong"
    with pytest.raises(AdapterContractError, match="parent_benchmark"):
        build_adapter_plan(BenchmarkManifest.from_dict(payload))


def test_star_embed_adapter_resolves_revision_at_acquisition() -> None:
    plan = build_adapter_plan(load("star_embed_ztf_40k"))
    assert len(plan.urls) == 5
    assert plan.query_manifest["revision"] == "resolve_at_acquisition"


def test_star_embed_adapter_rejects_unverified_revision() -> None:
    manifest = load("star_embed_ztf_40k")
    payload = manifest.to_dict()
    payload["input_contract"]["revision"] = "not-a-revision"
    with pytest.raises(AdapterContractError, match="verified 40-character"):
        build_adapter_plan(BenchmarkManifest.from_dict(payload))


def test_star_embed_adapter_accepts_verified_revision() -> None:
    manifest = load("star_embed_ztf_40k")
    payload = manifest.to_dict()
    payload["input_contract"]["revision"] = "0123456789abcdef0123456789abcdef01234567"
    plan = build_adapter_plan(BenchmarkManifest.from_dict(payload))
    assert len(plan.urls) == 5
    assert len(plan.artifact_names) == 5
    assert plan.query_manifest["revision"] == payload["input_contract"]["revision"]


def test_dr24_adapter_fails_closed_without_pinned_query() -> None:
    with pytest.raises(AdapterContractError, match="pinned source subset"):
        build_adapter_plan(load("ztf_dr24_source_subset"))


def test_alerce_adapter_fails_closed_without_tap_query() -> None:
    with pytest.raises(AdapterContractError, match="TAP query"):
        build_adapter_plan(load("alerce_reference"))
