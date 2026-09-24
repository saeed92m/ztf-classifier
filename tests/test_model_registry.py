"""Tests for the filesystem model registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.registry import (
    FilesystemModelRegistry,
    ModelNotFoundError,
    ModelRegistryError,
)


def _write_manifest(
    root: Path,
    directory: str,
    *,
    model_version: str,
    classes: list[str] | None = None,
    feature_count: int = 42,
    schema_version: str = "1.1",
) -> Path:
    artifact_dir = root / directory
    artifact_dir.mkdir(parents=True)

    files = {
        "model": {"path": "model.json", "sha256": "a" * 64},
        "model_contract": {
            "path": "model_contract.json",
            "sha256": "b" * 64,
        },
        "feature_schema": {
            "path": "feature_schema.parquet",
            "sha256": "c" * 64,
        },
        "calibration": {
            "path": "calibration.json",
            "sha256": "d" * 64,
        },
        "provenance": {
            "path": "provenance.json",
            "sha256": "e" * 64,
        },
    }

    if schema_version == "1.1":
        files.update(
            {
                "conformal": {
                    "path": "conformal.json",
                    "sha256": "f" * 64,
                },
                "ood": {
                    "path": "ood.json",
                    "sha256": "1" * 64,
                },
                "ood_model": {
                    "path": "ood_model.joblib",
                    "sha256": "2" * 64,
                },
            }
        )

    manifest = {
        "artifact_schema_version": schema_version,
        "model_version": model_version,
        "model_family": "XGBoost",
        "feature_schema_version": "v0.2",
        "classes": classes if classes is not None else list(MODEL_CLASSES),
        "feature_count": feature_count,
        "feature_names": [f"feature_{index}" for index in range(42)],
        "dataset_sha256": "3" * 64,
        "feature_schema_source_sha256": "4" * 64,
        "files": files,
    }

    (artifact_dir / "artifact_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    return artifact_dir


def test_registry_lists_models_deterministically(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        "second",
        model_version="model_b",
    )
    _write_manifest(
        tmp_path,
        "first",
        model_version="model_a",
    )

    registry = FilesystemModelRegistry(tmp_path)

    entries = registry.list_models()

    assert [entry.model_version for entry in entries] == [
        "model_a",
        "model_b",
    ]
    assert entries[0].feature_count == 42
    assert entries[0].classes == MODEL_CLASSES


def test_registry_requires_explicit_registered_version(
    tmp_path: Path,
) -> None:
    _write_manifest(
        tmp_path,
        "baseline",
        model_version="baseline_v0.2",
    )

    registry = FilesystemModelRegistry(tmp_path)

    entry = registry.get("baseline_v0.2")

    assert entry.model_family == "XGBoost"

    with pytest.raises(ModelNotFoundError):
        registry.get("unknown")


def test_registry_rejects_duplicate_model_versions(
    tmp_path: Path,
) -> None:
    _write_manifest(
        tmp_path,
        "one",
        model_version="duplicate",
    )
    _write_manifest(
        tmp_path,
        "two",
        model_version="duplicate",
    )

    with pytest.raises(ModelRegistryError, match="duplicate model versions"):
        FilesystemModelRegistry(tmp_path).list_models()


def test_registry_rejects_invalid_class_contract(
    tmp_path: Path,
) -> None:
    invalid_classes = list(MODEL_CLASSES)
    invalid_classes[-1] = "Invalid"

    _write_manifest(
        tmp_path,
        "invalid",
        model_version="invalid_model",
        classes=invalid_classes,
    )

    with pytest.raises(ModelRegistryError, match="frozen classes"):
        FilesystemModelRegistry(tmp_path).list_models()


def test_registry_rejects_invalid_feature_count(
    tmp_path: Path,
) -> None:
    _write_manifest(
        tmp_path,
        "invalid",
        model_version="invalid_model",
        feature_count=41,
    )

    with pytest.raises(ModelRegistryError, match="feature count"):
        FilesystemModelRegistry(tmp_path).list_models()
