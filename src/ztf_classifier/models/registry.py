"""Filesystem-backed model registry for immutable production artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ztf_classifier.models.artifact_io import (
    LoadedModelArtifact,
    ModelArtifactLoader,
)
from ztf_classifier.models.classes import MODEL_CLASSES

SUPPORTED_ARTIFACT_SCHEMAS = ("1.0", "1.1")
ARTIFACT_MANIFEST_NAME = "artifact_manifest.json"


class ModelRegistryError(Exception):
    """Base exception for model registry failures."""


class ModelNotFoundError(ModelRegistryError):
    """Raised when an explicitly requested model version is unavailable."""


class ModelRegistry(Protocol):
    """Application-facing interface for immutable model discovery."""

    def list_models(self) -> tuple["ModelRegistryEntry", ...]:
        """Return registered model metadata in deterministic order."""

    def get(self, model_version: str) -> "ModelRegistryEntry":
        """Resolve an explicitly requested model version."""

    def load(self, model_version: str) -> LoadedModelArtifact:
        """Load and validate an explicitly requested model artifact."""


@dataclass(frozen=True)
class ModelRegistryEntry:
    """Immutable metadata describing one registered model artifact."""

    model_version: str
    model_family: str
    artifact_schema_version: str
    feature_schema_version: str
    feature_count: int
    classes: tuple[str, ...]
    dataset_sha256: str
    feature_schema_sha256: str
    artifact_dir: Path

    def __post_init__(self) -> None:
        """Validate registry metadata."""
        if not self.model_version:
            raise ValueError("model_version must not be empty.")

        if not self.model_family:
            raise ValueError("model_family must not be empty.")

        if self.artifact_schema_version not in SUPPORTED_ARTIFACT_SCHEMAS:
            raise ValueError(
                "Unsupported artifact schema version: "
                f"{self.artifact_schema_version}"
            )

        if not self.feature_schema_version:
            raise ValueError("feature_schema_version must not be empty.")

        if self.feature_count != 42:
            raise ValueError("Registered models must contain 42 features.")

        if self.classes != MODEL_CLASSES:
            raise ValueError(
                "Registered model classes must match the frozen class order."
            )

        for name, value in (
            ("dataset_sha256", self.dataset_sha256),
            ("feature_schema_sha256", self.feature_schema_sha256),
        ):
            if len(value) != 64:
                raise ValueError(
                    f"{name} must be a SHA-256 hexadecimal digest."
                )
            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(
                    f"{name} must be hexadecimal."
                ) from exc

        artifact_dir = Path(self.artifact_dir).resolve()
        if not artifact_dir.is_dir():
            raise ValueError(
                f"Artifact directory does not exist: {artifact_dir}"
            )

        object.__setattr__(self, "artifact_dir", artifact_dir)


@dataclass(frozen=True)
class FilesystemModelRegistry:
    """Discover immutable model artifacts from a filesystem directory."""

    root_dir: Path

    def __post_init__(self) -> None:
        """Validate and normalize the registry root."""
        root = Path(self.root_dir).resolve()

        if not root.exists():
            raise FileNotFoundError(
                f"Model registry directory does not exist: {root}"
            )

        if not root.is_dir():
            raise ValueError(
                f"Model registry path is not a directory: {root}"
            )

        object.__setattr__(self, "root_dir", root)

    def list_models(self) -> tuple[ModelRegistryEntry, ...]:
        """Return all valid model entries in deterministic order."""
        entries: list[ModelRegistryEntry] = []

        for artifact_dir in sorted(self.root_dir.iterdir(), key=lambda p: p.name):
            if not artifact_dir.is_dir():
                continue

            manifest_path = artifact_dir / ARTIFACT_MANIFEST_NAME
            if not manifest_path.is_file():
                continue

            entries.append(self._read_entry(manifest_path, artifact_dir))

        entries.sort(key=lambda entry: entry.model_version)

        versions = [entry.model_version for entry in entries]
        if len(versions) != len(set(versions)):
            raise ModelRegistryError(
                "Model registry contains duplicate model versions."
            )

        return tuple(entries)

    def get(self, model_version: str) -> ModelRegistryEntry:
        """Resolve a model version without accepting filesystem paths."""
        if not isinstance(model_version, str) or not model_version.strip():
            raise ValueError("model_version must be a non-empty string.")

        for entry in self.list_models():
            if entry.model_version == model_version:
                return entry

        raise ModelNotFoundError(
            f"Model version is not registered: {model_version}"
        )

    def load(self, model_version: str) -> LoadedModelArtifact:
        """Load the explicitly selected model through the canonical loader."""
        entry = self.get(model_version)
        return ModelArtifactLoader().load(entry.artifact_dir)

    @classmethod
    def _read_entry(
        cls,
        manifest_path: Path,
        artifact_dir: Path,
    ) -> ModelRegistryEntry:
        """Read and validate registry metadata from an artifact manifest."""
        try:
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelRegistryError(
                f"Unable to read artifact manifest: {manifest_path}"
            ) from exc

        if not isinstance(manifest, dict):
            raise ModelRegistryError(
                f"Artifact manifest must be an object: {manifest_path}"
            )

        schema_version = manifest.get("artifact_schema_version")
        if schema_version not in SUPPORTED_ARTIFACT_SCHEMAS:
            raise ModelRegistryError(
                "Unsupported artifact schema version in "
                f"{manifest_path}: {schema_version}"
            )

        required = (
            "model_version",
            "model_family",
            "feature_schema_version",
            "classes",
            "feature_count",
            "dataset_sha256",
            "feature_schema_source_sha256",
            "files",
        )
        missing = [field for field in required if field not in manifest]
        if missing:
            raise ModelRegistryError(
                f"Artifact manifest is missing fields: {missing}"
            )

        if manifest["classes"] != list(MODEL_CLASSES):
            raise ModelRegistryError(
                f"Artifact classes do not match frozen classes: {manifest_path}"
            )

        if manifest["feature_count"] != 42:
            raise ModelRegistryError(
                f"Artifact feature count is not 42: {manifest_path}"
            )

        files = manifest["files"]
        if not isinstance(files, dict):
            raise ModelRegistryError(
                f"Artifact file metadata is invalid: {manifest_path}"
            )

        for key in (
            "model",
            "model_contract",
            "feature_schema",
            "calibration",
            "provenance",
        ):
            if key not in files:
                raise ModelRegistryError(
                    f"Artifact manifest is missing file metadata '{key}': "
                    f"{manifest_path}"
                )

        if schema_version == "1.1":
            for key in ("conformal", "ood", "ood_model"):
                if key not in files:
                    raise ModelRegistryError(
                        f"Artifact manifest is missing file metadata '{key}': "
                        f"{manifest_path}"
                    )

        return ModelRegistryEntry(
            model_version=str(manifest["model_version"]),
            model_family=str(manifest["model_family"]),
            artifact_schema_version=str(schema_version),
            feature_schema_version=str(
                manifest["feature_schema_version"]
            ),
            feature_count=int(manifest["feature_count"]),
            classes=tuple(manifest["classes"]),
            dataset_sha256=str(manifest["dataset_sha256"]),
            feature_schema_sha256=str(
                manifest["feature_schema_source_sha256"]
            ),
            artifact_dir=artifact_dir,
        )


__all__ = [
    "FilesystemModelRegistry",
    "ModelNotFoundError",
    "ModelRegistry",
    "ModelRegistryEntry",
    "ModelRegistryError",
]
