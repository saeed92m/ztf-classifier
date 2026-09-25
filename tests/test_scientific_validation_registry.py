import json

import pandas as pd

from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.regression import compare_metrics
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
        "evaluation_role": "ground_truth",
        "required_leakage_checks": ["object_overlap", "duplicate_objects"],
    }
    payload.update(overrides)
    return BenchmarkManifest.from_dict(payload)


def test_registry_loads_all_project_benchmarks():
    registry = BenchmarkRegistry("configs/benchmarks")
    ids = registry.validate_all()
    assert {
        "star_embed_ztf_40k",
        "ztf_periodic_730k",
        "ztf_periodic_781k",
        "ztf_dr24_source_subset",
        "alerce_reference",
    }.issubset(ids)


def test_reference_system_is_not_ground_truth():
    loaded = BenchmarkManifest.from_json("configs/benchmarks/alerce_reference.json")
    assert loaded.ground_truth_provenance["is_model_agreement"] is False
    assert loaded.reference_system_provenance["is_ground_truth"] is False


def test_runner_reports_metrics_and_hash(tmp_path):
    frame = pd.DataFrame(
        {
            "oid": ["A", "B", "C", "D"],
            "truth": ["A", "B", "A", "B"],
            "prediction": ["A", "B", "B", "B"],
            "p_a": [0.9, 0.1, 0.4, 0.1],
            "p_b": [0.1, 0.9, 0.6, 0.9],
        }
    )
    input_path = tmp_path / "predictions.parquet"
    frame.to_parquet(input_path, index=False)
    result = run_table_benchmark(
        manifest=manifest(probability_columns=["p_a", "p_b"]),
        input_path=input_path,
        output_dir=tmp_path / "report",
    )
    assert result.status == "PASS"
    assert result.row_count == 4
    assert len(result.input_sha256) == 64
    payload = json.loads((tmp_path / "report" / "benchmark_result.json").read_text())
    assert payload["metrics"]["accuracy"] == 0.75


def test_duplicate_objects_are_release_blocking(tmp_path):
    frame = pd.DataFrame(
        {
            "oid": ["A", "A"],
            "truth": ["A", "B"],
            "prediction": ["A", "B"],
        }
    )
    input_path = tmp_path / "predictions.csv"
    frame.to_csv(input_path, index=False)
    result = run_table_benchmark(
        manifest=manifest(),
        input_path=input_path,
        output_dir=tmp_path / "report",
    )
    assert result.status == "BLOCKED"
    assert result.leakage["duplicate_objects"] == "FAIL"


def test_regression_comparison_is_explicit():
    result = compare_metrics(
        {"macro_f1": 0.90, "accuracy": 0.95},
        {"macro_f1": 0.92, "accuracy": 0.95},
        tolerances={"macro_f1": 0.01, "accuracy": 0.0},
    )
    assert result["status"] == "REGRESSION"
    assert "macro_f1" in result["regressions"]


def test_reference_system_role_is_preserved_in_manifest_and_result(tmp_path):
    manifest_instance = manifest(
        evaluation_role="reference_system",
        label_column="reference_label",
        ground_truth_provenance={},
    )
    frame = pd.DataFrame(
        {
            "oid": ["A", "B"],
            "reference_label": ["A", "B"],
            "prediction": ["A", "B"],
        }
    )
    input_path = tmp_path / "reference.parquet"
    frame.to_parquet(input_path, index=False)
    result = run_table_benchmark(
        manifest=manifest_instance,
        input_path=input_path,
        output_dir=tmp_path / "report",
    )
    assert result.evaluation_role == "reference_system"
    assert result.status == "PASS"
    payload = json.loads(
        (tmp_path / "report" / "benchmark_result.json").read_text()
    )
    assert payload["evaluation_role"] == "reference_system"
