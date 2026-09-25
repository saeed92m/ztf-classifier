import json

import pandas as pd

from ztf_classifier.validation.checks import (
    check_future_data_leakage,
    check_object_overlap,
    check_target_leakage,
    run_scientific_checks,
)
from ztf_classifier.validation.manifest import BenchmarkManifest


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
        "required_leakage_checks": ["object_overlap"],
    }
    payload.update(overrides)
    return BenchmarkManifest.from_dict(payload)


def test_object_overlap_is_blocked_without_split_evidence():
    frame = pd.DataFrame({"oid": ["A", "B"], "truth": ["A", "B"]})
    result = check_object_overlap(manifest(), frame)
    assert result.status == "BLOCKED"


def test_object_overlap_executes_from_explicit_split_column():
    frame = pd.DataFrame(
        {
            "oid": ["A", "B", "C", "D"],
            "truth": ["A", "B", "A", "B"],
            "split": ["train", "train", "test", "test"],
        }
    )
    result = check_object_overlap(
        manifest(split_definition={"strategy": "object-level", "split_column": "split"}),
        frame,
    )
    assert result.status == "PASS"


def test_target_leakage_detects_declared_target_derived_column():
    frame = pd.DataFrame({"oid": ["A"], "truth": ["A"], "prediction": ["A"], "truth_encoded": [0]})
    result = check_target_leakage(
        manifest(preprocessing_contract={"forbidden_columns": ["truth_encoded"]}),
        frame,
    )
    assert result.status == "FAIL"


def test_future_data_leakage_detects_post_cutoff_observations():
    frame = pd.DataFrame(
        {
            "oid": ["A", "B"],
            "truth": ["A", "B"],
            "prediction": ["A", "B"],
            "obs_time": ["2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z"],
        }
    )
    result = check_future_data_leakage(
        manifest(
            split_definition={
                "strategy": "object-level",
                "observation_time_column": "obs_time",
                "training_cutoff": "2020-06-01T00:00:00Z",
            }
        ),
        frame,
    )
    assert result.status == "FAIL"


def test_runner_emits_structured_check_results(tmp_path):
    frame = pd.DataFrame(
        {
            "oid": ["A", "B"],
            "truth": ["A", "B"],
            "prediction": ["A", "B"],
        }
    )
    input_path = tmp_path / "predictions.csv"
    frame.to_csv(input_path, index=False)
    m = manifest(
        required_leakage_checks=["duplicate_objects"],
    )
    from ztf_classifier.validation.runner import run_table_benchmark

    result = run_table_benchmark(m, input_path, tmp_path / "report")
    assert result.status == "PASS"
    assert result.checks["duplicate_objects"]["status"] == "PASS"
    payload = json.loads((tmp_path / "report" / "benchmark_result.json").read_text())
    assert payload["checks"]["duplicate_objects"]["check_id"] == "duplicate_objects"
