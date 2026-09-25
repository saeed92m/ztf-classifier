import json

from ztf_classifier.validation.gate import evaluate_release_gate


def test_release_gate_fails_closed_when_evidence_is_missing(tmp_path):
    result = evaluate_release_gate(
        registry_dir="configs/benchmarks",
        evidence_dir=tmp_path,
    )
    assert result["status"] == "NOT_VERIFIED"
    assert result["release_blocking"] is True
    assert result["blockers"]
    assert any("benchmark evidence report is missing" in item for item in result["blockers"])


def test_release_gate_accepts_complete_minimal_reference_evidence(tmp_path):
    evidence = tmp_path / "alerce_reference"
    evidence.mkdir()
    (evidence / "benchmark_result.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "provenance_complete": True,
                "leakage": {
                    "object_overlap": "PASS",
                    "duplicate_objects": "PASS",
                    "target_leakage": "PASS",
                    "future_data_leakage": "PASS",
                    "benchmark_trained_artifacts": "PASS",
                    "preprocessing_consistency": "PASS",
                },
            }
        ),
        encoding="utf-8",
    )
    result = evaluate_release_gate(
        registry_dir="configs/benchmarks",
        evidence_dir=tmp_path,
    )
    alerce = next(item for item in result["benchmarks"] if item["benchmark_id"] == "alerce_reference")
    assert alerce["status"] == "BLOCKED"
    assert any("source/object hashes are not recorded" in item for item in alerce["blockers"])
