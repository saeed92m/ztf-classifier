from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ztf_classifier.models.provenance import (
    PROVENANCE_SCHEMA_VERSION,
    ModelProvenanceBuilder,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "data/processed/benchmark_v0.2/features.parquet"
)

FEATURE_SCHEMA_PATH = (
    PROJECT_ROOT
    / "reports/tables/final_feature_set_v0.2.parquet"
)

MODEL_CONFIG_PATH = (
    PROJECT_ROOT
    / "reports/tables/final_model_config_v0.2.json"
)

CALIBRATION_SOURCE_PATH = (
    PROJECT_ROOT
    / "reports/tables/xgboost_baseline_v0.2_oof_predictions.parquet"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def build_provenance():
    builder = ModelProvenanceBuilder(
        project_root=PROJECT_ROOT,
    )

    return builder.build(
        artifact_version="1.0",
        model_version="baseline_v0.2",
        model_family="XGBoost",
        dataset_version="benchmark_v0.2",
        dataset_path=DATASET_PATH,
        feature_schema_version="v0.2",
        feature_schema_path=FEATURE_SCHEMA_PATH,
        model_config_path=MODEL_CONFIG_PATH,
        calibration_method="temperature_scaling",
        calibration_temperature=1.0268501887,
        calibration_source_path=CALIBRATION_SOURCE_PATH,
    )


def test_build_captures_expected_provenance():
    provenance = build_provenance()

    assert (
        provenance.schema_version
        == PROVENANCE_SCHEMA_VERSION
    )

    assert provenance.artifact_version == "1.0"
    assert provenance.model_version == "baseline_v0.2"
    assert provenance.model_family == "XGBoost"

    assert provenance.dataset_version == "benchmark_v0.2"
    assert provenance.dataset_sha256 == sha256(
        DATASET_PATH
    )

    assert provenance.feature_schema_version == "v0.2"
    assert provenance.feature_schema_sha256 == sha256(
        FEATURE_SCHEMA_PATH
    )

    assert provenance.model_config_sha256 == sha256(
        MODEL_CONFIG_PATH
    )

    assert provenance.calibration_method == (
        "temperature_scaling"
    )

    assert provenance.calibration_temperature == (
        1.0268501887
    )

    assert provenance.calibration_source_sha256 == sha256(
        CALIBRATION_SOURCE_PATH
    )

    assert len(provenance.git_commit) == 40
    assert isinstance(provenance.git_dirty, bool)

    assert provenance.python_version
    assert provenance.platform
    assert provenance.machine

    assert provenance.dependencies[
        "ztf-classifier"
    ] == "0.2.0"

    assert provenance.dependencies["numpy"] == "2.4.6"
    assert provenance.dependencies["pandas"] == "3.0.6"
    assert provenance.dependencies["scipy"] == "1.17.1"
    assert provenance.dependencies[
        "scikit-learn"
    ] == "1.9.1"
    assert provenance.dependencies["xgboost"] == "3.2.0"
    assert provenance.dependencies["pyarrow"] == "25.0.1"


def test_paths_are_project_relative():
    provenance = build_provenance()

    assert provenance.dataset_path == (
        "data/processed/benchmark_v0.2/features.parquet"
    )

    assert provenance.feature_schema_path == (
        "reports/tables/final_feature_set_v0.2.parquet"
    )

    assert provenance.model_config_path == (
        "reports/tables/final_model_config_v0.2.json"
    )

    assert provenance.calibration_source_path == (
        "reports/tables/"
        "xgboost_baseline_v0.2_oof_predictions.parquet"
    )


def test_to_dict_has_stable_top_level_contract():
    provenance = build_provenance()

    data = provenance.to_dict()

    assert set(data) == {
        "provenance_schema_version",
        "artifact_version",
        "model",
        "dataset",
        "feature_schema",
        "model_configuration",
        "calibration",
        "source_control",
        "runtime",
        "dependencies",
    }

    assert data["provenance_schema_version"] == "1.0"

    assert data["model"] == {
        "version": "baseline_v0.2",
        "family": "XGBoost",
    }

    assert data["dataset"]["version"] == "benchmark_v0.2"
    assert data["dataset"]["sha256"] == sha256(
        DATASET_PATH
    )

    assert data["feature_schema"]["version"] == "v0.2"
    assert data["feature_schema"]["sha256"] == sha256(
        FEATURE_SCHEMA_PATH
    )

    assert data["calibration"]["method"] == (
        "temperature_scaling"
    )

    assert data["calibration"]["temperature"] == (
        1.0268501887
    )


def test_write_creates_valid_json(tmp_path):
    provenance = build_provenance()

    output = tmp_path / "provenance.json"

    provenance.write(output)

    assert output.is_file()

    data = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert data == provenance.to_dict()
