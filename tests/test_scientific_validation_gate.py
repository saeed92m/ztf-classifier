import json

import pytest

from ztf_classifier.validation.gate import (
    REQUIRED_SCIENTIFIC_CHECKS,
    evaluate_release_gate,
)
from ztf_classifier.validation.manifest import BenchmarkManifest


def test_release_gate_fails_closed_when_evidence_is_missing(tmp_path):
    result = evaluate_release_gate(registry_dir="configs/benchmarks", evidence_dir=tmp_path)
    assert result["status"] == "NOT_VERIFIED"
    assert result["release_blocking"] is True
    assert result["blockers"]
    assert any("benchmark evidence report is missing" in item for item in result["blockers"])


def test_release_gate_requires_full_scientific_check_contract(tmp_path):
    evidence = tmp_path / "alerce_reference"
    evidence.mkdir()
    checks = {name: "PASS" for name in REQUIRED_SCIENTIFIC_CHECKS}
    checks.pop("failure_code_correctness")
    (evidence / "benchmark_result.json").write_text(
        json.dumps({"status": "PASS", "provenance_complete": True, "checks": checks}),
        encoding="utf-8",
    )
    result = evaluate_release_gate(registry_dir="configs/benchmarks", evidence_dir=tmp_path)
    alerce = next(item for item in result["benchmarks"] if item["benchmark_id"] == "alerce_reference")
    assert alerce["status"] == "BLOCKED"
    assert any("scientific check failure_code_correctness is NOT_EXECUTED" in item for item in alerce["blockers"])


def test_manifest_rejects_unknown_scientific_checks():
    payload = {
        "benchmark_id": "example",
        "dataset_name": "Example",
        "source": "example",
        "version": "1",
        "retrieval_date": "2026-09-25",
        "object_id_column": "oid",
        "label_column": "label",
        "label_taxonomy": "example",
        "class_mapping": {"a": "a"},
        "split_definition": {},
        "leakage_exclusions": [],
        "preprocessing_contract": {},
        "input_contract": {},
        "ground_truth_provenance": {},
        "reference_system_provenance": {},
        "benchmark_code_version": "test",
        "required_leakage_checks": ["not_a_real_check"],
    }
    with pytest.raises(ValueError, match="unknown scientific checks"):
        BenchmarkManifest.from_dict(payload)
