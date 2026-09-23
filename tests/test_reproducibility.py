"""Tests for the production reproducibility layer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.reproducibility.environment import (
    collect_dependency_versions,
    collect_environment,
    collect_git_state,
)
from ztf_classifier.reproducibility.manifest import (
    REPRODUCIBILITY_SCHEMA_VERSION,
    ReproducibilityManifestBuilder,
)
from ztf_classifier.reproducibility.validation import (
    ReproducibilityValidator,
)


def _init_git_repository(path: Path) -> None:
    subprocess.run(
        ["git", "init"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )

    (path / "README.md").write_text("test\n", encoding="utf-8")

    subprocess.run(
        ["git", "add", "."],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def _create_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root = tmp_path / "project"
    project_root.mkdir()

    dataset_path = project_root / "data" / "features.parquet"
    schema_path = project_root / "schema" / "features.parquet"

    dataset_path.parent.mkdir(parents=True)
    schema_path.parent.mkdir(parents=True)

    dataset_path.write_bytes(b"dataset-content")
    schema_path.write_bytes(b"schema-content")

    _init_git_repository(project_root)

    return project_root, dataset_path, schema_path


def _build_manifest(
    project_root: Path,
    dataset_path: Path,
    schema_path: Path,
) -> tuple[Path, dict]:
    manifest_path = project_root / "manifest.json"

    builder = ReproducibilityManifestBuilder()

    manifest = builder.build(
        project_root=project_root,
        dataset_path=dataset_path,
        feature_schema_path=schema_path,
        output_path=manifest_path,
        dataset_version="v0.2",
        feature_schema_version="v0.2",
        purpose="test",
        command="pytest",
    )

    manifest.write()

    return manifest_path, manifest.data


def test_collect_environment_contains_expected_fields() -> None:
    environment = collect_environment()

    assert environment["python"]
    assert environment["python_implementation"]
    assert environment["platform"]
    assert environment["architecture"]
    assert environment["executable"]


def test_collect_dependency_versions_returns_string_mapping() -> None:
    dependencies = collect_dependency_versions()

    assert isinstance(dependencies, dict)
    assert dependencies
    assert all(isinstance(name, str) for name in dependencies)
    assert all(isinstance(version, str) for version in dependencies.values())


def test_collect_git_state_reports_clean_repository(tmp_path: Path) -> None:
    project_root, _, _ = _create_project(tmp_path)

    state = collect_git_state(project_root)

    assert state["git_commit"]
    assert state["git_branch"]
    assert state["git_dirty"] is False


def test_collect_git_state_detects_dirty_repository(tmp_path: Path) -> None:
    project_root, _, _ = _create_project(tmp_path)

    (project_root / "README.md").write_text(
        "modified\n",
        encoding="utf-8",
    )

    state = collect_git_state(project_root)

    assert state["git_dirty"] is True


def test_builder_uses_portable_relative_paths(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, data = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    assert manifest_path.is_file()
    assert data["dataset"]["path"] == "data/features.parquet"
    assert data["feature_schema"]["path"] == "schema/features.parquet"
    assert not Path(data["dataset"]["path"]).is_absolute()
    assert not Path(data["feature_schema"]["path"]).is_absolute()


def test_builder_records_correct_hashes(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    _, data = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    assert data["dataset"]["sha256"] == sha256_file(dataset_path)
    assert data["feature_schema"]["sha256"] == sha256_file(schema_path)


def test_builder_rejects_dataset_outside_project_root(
    tmp_path: Path,
) -> None:
    project_root, _, schema_path = _create_project(tmp_path)
    outside_dataset = tmp_path / "outside.parquet"
    outside_dataset.write_bytes(b"outside")

    builder = ReproducibilityManifestBuilder()

    with pytest.raises(ValueError, match="inside project root"):
        builder.build(
            project_root=project_root,
            dataset_path=outside_dataset,
            feature_schema_path=schema_path,
            output_path=project_root / "manifest.json",
            dataset_version="v0.2",
            feature_schema_version="v0.2",
            purpose="test",
            command="pytest",
        )


def test_builder_rejects_missing_dataset(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)
    dataset_path.unlink()

    builder = ReproducibilityManifestBuilder()

    with pytest.raises(ValueError, match="Dataset does not exist"):
        builder.build(
            project_root=project_root,
            dataset_path=dataset_path,
            feature_schema_path=schema_path,
            output_path=project_root / "manifest.json",
            dataset_version="v0.2",
            feature_schema_version="v0.2",
            purpose="test",
            command="pytest",
        )


def test_builder_rejects_missing_feature_schema(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)
    schema_path.unlink()

    builder = ReproducibilityManifestBuilder()

    with pytest.raises(ValueError, match="Feature schema does not exist"):
        builder.build(
            project_root=project_root,
            dataset_path=dataset_path,
            feature_schema_path=schema_path,
            output_path=project_root / "manifest.json",
            dataset_version="v0.2",
            feature_schema_version="v0.2",
            purpose="test",
            command="pytest",
        )


def test_validator_accepts_valid_manifest(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, data = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    result = ReproducibilityValidator().validate(
        manifest_path,
        project_root=project_root,
    )

    assert result.manifest_path == manifest_path
    assert result.dataset_path == dataset_path.resolve()
    assert result.feature_schema_path == schema_path.resolve()
    assert result.dataset_sha256 == sha256_file(dataset_path)
    assert result.feature_schema_sha256 == sha256_file(schema_path)
    assert result.dataset_sha256 == data["dataset"]["sha256"]
    assert result.feature_schema_sha256 == data["feature_schema"]["sha256"]


def test_validator_detects_dataset_tampering(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, _ = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    dataset_path.write_bytes(b"tampered-dataset")

    with pytest.raises(
        ValueError,
        match="Dataset SHA-256 does not match",
    ):
        ReproducibilityValidator().validate(
            manifest_path,
            project_root=project_root,
        )


def test_validator_detects_feature_schema_tampering(
    tmp_path: Path,
) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, _ = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    schema_path.write_bytes(b"tampered-schema")

    with pytest.raises(
        ValueError,
        match="Feature schema SHA-256 does not match",
    ):
        ReproducibilityValidator().validate(
            manifest_path,
            project_root=project_root,
        )


def test_validator_rejects_missing_dataset(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, _ = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    dataset_path.unlink()

    with pytest.raises(
        ValueError,
        match="Manifest dataset does not exist",
    ):
        ReproducibilityValidator().validate(
            manifest_path,
            project_root=project_root,
        )


def test_validator_rejects_wrong_schema_version(
    tmp_path: Path,
) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, data = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    data["schema_version"] = "999.0"

    manifest_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported reproducibility manifest schema version",
    ):
        ReproducibilityValidator().validate(
            manifest_path,
            project_root=project_root,
        )


def test_validator_can_skip_file_verification(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    manifest_path, data = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    dataset_path.unlink()
    schema_path.unlink()

    result = ReproducibilityValidator().validate(
        manifest_path,
        project_root=project_root,
        verify_files=False,
    )

    assert result.dataset_sha256 == data["dataset"]["sha256"]
    assert result.feature_schema_sha256 == data["feature_schema"]["sha256"]


def test_manifest_has_expected_schema_version(tmp_path: Path) -> None:
    project_root, dataset_path, schema_path = _create_project(tmp_path)

    _, data = _build_manifest(
        project_root,
        dataset_path,
        schema_path,
    )

    assert data["schema_version"] == REPRODUCIBILITY_SCHEMA_VERSION
