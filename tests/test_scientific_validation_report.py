from ztf_classifier.validation.report import render_scientific_validation_report


def test_scientific_report_contains_gate_scope_and_blockers():
    report = render_scientific_validation_report(
        {
            "status": "NOT_VERIFIED",
            "release_blocking": True,
            "benchmarks": [
                {
                    "benchmark_id": "alerce_reference",
                    "evaluation_role": "reference_system",
                    "status": "BLOCKED",
                    "blockers": ["benchmark evidence report is missing"],
                }
            ],
            "blockers": ["alerce_reference: benchmark evidence report is missing"],
            "interpretation": "Benchmark success is not proof of universal correctness.",
        }
    )
    assert "Scientific Validation Report" in report
    assert "NOT_VERIFIED" in report
    assert "reference_system" in report
    assert "benchmark evidence report is missing" in report
    assert "not proof of universal correctness" in report
