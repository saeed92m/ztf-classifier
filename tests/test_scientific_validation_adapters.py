"""Tests for canonical source-backed benchmark adapter plans."""

from pathlib import Path

import pytest

from ztf_classifier.validation.adapters import AdapterContractError, build_adapter_plan
from ztf_classifier.validation.manifest import BenchmarkManifest

ROOT = Path(__file__).parents[1]
BENCHMARK_DIR = ROOT / "configs" / "benchmarks"


def load(name: str) -> BenchmarkManifest:
    return BenchmarkManifest.from_json(BENCHMARK_DIR / f"{name}.json")


@pytest.mark.parametrize(
    "benchmark_id",
    [
        "star_embed_ztf_40k",
        "ztf_periodic_781k",
        "ztf_periodic_730k",
        "ztf_dr24_source_subset",
        "alerce_reference",
    ],
)
def test_canonical_adapters_build_deterministic_plans(benchmark_id: str) -> None:
    manifest = load(benchmark_id)
    if benchmark_id == "ztf_dr24_source_subset":
        payload = manifest.to_dict()
        payload["input_contract"]["query"] = {
            "sql": "SELECT TOP 10 oid FROM ztf_objects",
            "release": "DR24",
        }
        manifest = BenchmarkManifest.from_dict(payload)
    elif benchmark_id == "alerce_reference":
        payload = manifest.to_dict()
        payload["input_contract"]["query"] = "SELECT oid FROM objects LIMIT 10"
        manifest = BenchmarkManifest.from_dict(payload)

    plan = build_adapter_plan(manifest)
    assert plan.benchmark_id == benchmark_id
    assert plan.source_id == manifest.input_contract["adapter"]
    assert plan.urls
    plan.validate()


def test_730k_adapter_requires_781k_parent() -> None:
    manifest = load("ztf_periodic_730k")
    payload = manifest.to_dict()
    payload["ground_truth_provenance"]["parent_benchmark"] = "wrong"
    with pytest.raises(AdapterContractError, match="parent_benchmark"):
        build_adapter_plan(BenchmarkManifest.from_dict(payload))


def test_dr24_adapter_fails_closed_without_pinned_query() -> None:
    with pytest.raises(AdapterContractError, match="pinned source subset"):
        build_adapter_plan(load("ztf_dr24_source_subset"))


def test_alerce_adapter_fails_closed_without_tap_query() -> None:
    with pytest.raises(AdapterContractError, match="TAP query"):
        build_adapter_plan(load("alerce_reference"))


def test_star_embed_plan_pins_all_source_artifacts() -> None:
    plan = build_adapter_plan(load("star_embed_ztf_40k"))
    assert len(plan.urls) == 5
    assert len(plan.artifact_names) == 5
    assert len(plan.expected_sha256) == 5
    assert plan.query_manifest["revision"] == "18db85e"
