"""Tests for the production model artifact contract."""

from __future__ import annotations

import numpy as np
import pytest
from xgboost import XGBClassifier

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.config import ModelConfig


def _model() -> XGBClassifier:
    """Build a minimal fitted XGBoost model."""
    model = XGBClassifier(
        n_estimators=1,
        max_depth=1,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=15,
        eval_metric="mlogloss",
        tree_method="hist",
        random_state=42,
        n_jobs=1,
    )

    X = np.zeros((15, 42), dtype=np.float64)
    y = np.arange(15, dtype=np.int64)

    model.fit(X, y)

    return model


def _artifact() -> ModelArtifact:
    """Build a valid artifact contract."""
    return ModelArtifact(
        model=_model(),
        model_version="baseline_v0.2",
        model_family="XGBoost",
        classes=MODEL_CLASSES,
        feature_schema_version="v0.2",
        feature_names=tuple(
            f"feature_{index}"
            for index in range(42)
        ),
        configuration=ModelConfig(),
        dataset_sha256="a" * 64,
        feature_schema_sha256="b" * 64,
    )


def test_valid_model_artifact() -> None:
    artifact = _artifact()

    assert artifact.model_version == "baseline_v0.2"
    assert artifact.model_family == "XGBoost"
    assert artifact.classes == MODEL_CLASSES
    assert len(artifact.feature_names) == 42
    assert artifact.feature_schema_version == "v0.2"


def test_artifact_is_frozen() -> None:
    artifact = _artifact()

    with pytest.raises(AttributeError):
        artifact.model_version = "other"  # type: ignore[misc]


def test_artifact_requires_model() -> None:
    with pytest.raises(ValueError, match="requires a fitted model"):
        ModelArtifact(
            model=None,
            model_version="baseline_v0.2",
            model_family="XGBoost",
            classes=MODEL_CLASSES,
            feature_schema_version="v0.2",
            feature_names=tuple(
                f"feature_{index}"
                for index in range(42)
            ),
            configuration=ModelConfig(),
            dataset_sha256="a" * 64,
            feature_schema_sha256="b" * 64,
        )


def test_artifact_rejects_wrong_class_order() -> None:
    classes = tuple(reversed(MODEL_CLASSES))

    with pytest.raises(
        ValueError,
        match="frozen class order",
    ):
        ModelArtifact(
            model=_model(),
            model_version="baseline_v0.2",
            model_family="XGBoost",
            classes=classes,
            feature_schema_version="v0.2",
            feature_names=tuple(
                f"feature_{index}"
                for index in range(42)
            ),
            configuration=ModelConfig(),
            dataset_sha256="a" * 64,
            feature_schema_sha256="b" * 64,
        )


def test_artifact_rejects_wrong_feature_count() -> None:
    with pytest.raises(
        ValueError,
        match="exactly 42 features",
    ):
        ModelArtifact(
            model=_model(),
            model_version="baseline_v0.2",
            model_family="XGBoost",
            classes=MODEL_CLASSES,
            feature_schema_version="v0.2",
            feature_names=("only_one",),
            configuration=ModelConfig(),
            dataset_sha256="a" * 64,
            feature_schema_sha256="b" * 64,
        )


def test_artifact_rejects_configuration_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="configuration version",
    ):
        ModelArtifact(
            model=_model(),
            model_version="other",
            model_family="XGBoost",
            classes=MODEL_CLASSES,
            feature_schema_version="v0.2",
            feature_names=tuple(
                f"feature_{index}"
                for index in range(42)
            ),
            configuration=ModelConfig(),
            dataset_sha256="a" * 64,
            feature_schema_sha256="b" * 64,
        )


def test_artifact_rejects_invalid_hash_length() -> None:
    with pytest.raises(
        ValueError,
        match="dataset_sha256",
    ):
        ModelArtifact(
            model=_model(),
            model_version="baseline_v0.2",
            model_family="XGBoost",
            classes=MODEL_CLASSES,
            feature_schema_version="v0.2",
            feature_names=tuple(
                f"feature_{index}"
                for index in range(42)
            ),
            configuration=ModelConfig(),
            dataset_sha256="invalid",
            feature_schema_sha256="b" * 64,
        )
