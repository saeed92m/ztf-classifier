import numpy as np

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.inference import InferenceResult
from ztf_classifier.models.result_builder import PredictionResultBuilder


def test_prediction_result_exposes_additive_status_metadata() -> None:
    probabilities = np.zeros((1, len(MODEL_CLASSES)), dtype=float)
    probabilities[0, 0] = 1.0
    inference = InferenceResult(
        probabilities=probabilities,
        predicted_class_indices=np.array([0], dtype=np.int64),
        predicted_labels=(MODEL_CLASSES[0],),
    )
    result = PredictionResultBuilder.build(
        inference,
        calibration_status="available",
        conformal_status="unavailable",
        ood_status="available",
        warnings=("legacy checksum",),
        artifact_schema_version="1.1",
        artifact_hash="a" * 64,
        feature_schema_hash="b" * 64,
        software_version="0.4.0",
        model_version="baseline_v0.2",
    )
    assert result.calibration_status == "available"
    assert result.conformal_status == "unavailable"
    assert result.ood_status == "available"
    assert result.warnings == ("legacy checksum",)
    assert result.artifact_schema_version == "1.1"
    assert result.software_version == "0.4.0"
