import pandas as pd

from ztf_classifier.validation.checks import check_provenance
from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.runner import run_table_benchmark


def manifest(**overrides):
    payload = {
        "benchmark_id": "test_benchmark",
        "dataset_name": "Test benchmark",
        "source": "test-source",
        "version": "1",
        "retrieval_date": "2026-09-25",
        "object_id_column": "oid",
        "label_column": "truth",
        "label_taxonomy": "binary",
        "class_mapping": {"A": "A", "B": "B"},
        "split_definition": {"strategy": "object-level"},
        "leakage_exclusions": ["no duplicate objects"],
        "preprocessing_contract": {"version": "1"},
        "input_contract": {"prediction_column": "prediction"},
        "ground_truth_provenance": {"kind": "independent labels"},
        "reference_system_provenance": {"kind": "independent reference", "is_ground_truth": False},
        "benchmark_code_version": "test",
        "required_leakage_checks": ["duplicate_objects"],
    }
    payload.update(overrides)
    return BenchmarkManifest.from_dict(payload)


def test_runner_is_fail_closed_when_declared_check_cannot_execute(tmp_path):
    frame = pd.DataFrame({"oid": ["A", "B"], "truth": ["A", "B"], "prediction": ["A", "B"]})
    path = tmp_path / "predictions.csv"
    frame.to_csv(path, index=False)
    result = run_table_benchmark(
        manifest=manifest(required_leakage_checks=["object_overlap"]),
        input_path=path,
        output_dir=tmp_path / "report",
    )
    assert result.status == "BLOCKED"
    assert result.checks["object_overlap"]["status"] == "BLOCKED"


def test_provenance_requires_canonical_adapter():
    frame = pd.DataFrame({"oid": ["A"], "truth": ["A"], "prediction": ["A"]})
    result = check_provenance(manifest(required_leakage_checks=["provenance"]), "missing.csv")
    assert result.status == "BLOCKED"
