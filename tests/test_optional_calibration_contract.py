import numpy as np

from ztf_classifier.models.artifact_io import ModelArtifactLoader
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.inference import InferenceResult
from ztf_classifier.models.provenance import ModelProvenance
from ztf_classifier.models.result_builder import PredictionResultBuilder


def _manifest_without_calibration() -> dict[str, object]:
    digest = "a" * 64
    return {
        "artifact_schema_version": "1.0",
        "model_version": "v1",
        "model_family": "XGBoost",
        "feature_schema_version": "v0.2",
        "classes": list(MODEL_CLASSES),
        "feature_count": 42,
        "feature_names": [f"feature_{index}" for index in range(42)],
        "dataset_sha256": digest,
        "feature_schema_source_sha256": digest,
        "files": {
            "model": {"path": "model.json", "sha256": digest},
            "model_contract": {
                "path": "model_contract.json",
                "sha256": digest,
            },
            "feature_schema": {
                "path": "feature_schema.parquet",
                "sha256": digest,
            },
            "provenance": {
                "path": "provenance.json",
                "sha256": digest,
            },
        },
    }


def test_artifact_manifest_allows_calibration_to_be_absent() -> None:
    ModelArtifactLoader._validate_manifest(
        _manifest_without_calibration()
    )


def test_provenance_omits_calibration_section_when_unavailable() -> None:
    provenance = ModelProvenance(
        schema_version="1.1",
        artifact_version="1.0",
        model_version="v1",
        model_family="XGBoost",
        dataset_version="d1",
        dataset_path="dataset.parquet",
        dataset_sha256="a" * 64,
        feature_schema_version="v0.2",
        feature_schema_path="schema.parquet",
        feature_schema_sha256="b" * 64,
        model_config_path="config.json",
        model_config_sha256="c" * 64,
        calibration_method=None,
        calibration_temperature=None,
        calibration_source_path=None,
        calibration_source_sha256=None,
        git_commit="0" * 40,
        git_dirty=False,
        python_version="3.11.16",
        platform="Linux",
        machine="x86_64",
        dependencies={},
    )

    assert "calibration" not in provenance.to_dict()


def test_result_builder_falls_back_to_raw_when_calibration_is_unavailable() -> None:
    probabilities = np.array(
        [[0.8] + [0.2 / 14] * 14],
        dtype=np.float64,
    )
    inference = InferenceResult(
        probabilities=probabilities,
        predicted_class_indices=np.array([0], dtype=np.int64),
        predicted_labels=(MODEL_CLASSES[0],),
    )

    result = PredictionResultBuilder.build(
        inference,
        calibration_status="unavailable",
    )

    assert result.calibrated_probabilities is None
    assert result.has_calibration is False
    assert result.top1_labels == (MODEL_CLASSES[0],)
    assert result.calibration_status == "unavailable"
