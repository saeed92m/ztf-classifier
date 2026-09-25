"""Provenance contract for production model artifacts."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROVENANCE_SCHEMA_VERSION = "1.1"


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _git_output(
    project_root: Path,
    *args: str,
) -> str:
    """Return a Git command result."""

    result = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


@dataclass(frozen=True)
class ModelProvenance:
    """Immutable provenance metadata for one model artifact."""

    schema_version: str
    artifact_version: str
    model_version: str
    model_family: str
    dataset_version: str
    dataset_path: str
    dataset_sha256: str
    feature_schema_version: str
    feature_schema_path: str
    feature_schema_sha256: str
    model_config_path: str
    model_config_sha256: str
    calibration_method: str | None
    calibration_temperature: float | None
    calibration_source_path: str | None
    calibration_source_sha256: str | None
    git_commit: str
    git_dirty: bool
    python_version: str
    platform: str
    machine: str
    dependencies: dict[str, str]
    software_version: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Serialize provenance to a JSON-compatible dictionary."""

        return {
            "provenance_schema_version": self.schema_version,
            "artifact_version": self.artifact_version,
            "model": {
                "version": self.model_version,
                "family": self.model_family,
            },
            "dataset": {
                "version": self.dataset_version,
                "path": self.dataset_path,
                "sha256": self.dataset_sha256,
            },
            "feature_schema": {
                "version": self.feature_schema_version,
                "path": self.feature_schema_path,
                "sha256": self.feature_schema_sha256,
            },
            "model_configuration": {
                "path": self.model_config_path,
                "sha256": self.model_config_sha256,
            },
            **(
                {
                    "calibration": {
                        "method": self.calibration_method,
                        "temperature": self.calibration_temperature,
                        "source_path": self.calibration_source_path,
                        "source_sha256": self.calibration_source_sha256,
                    }
                }
                if self.calibration_method is not None
                else {}
            ),
            "source_control": {
                "git_commit": self.git_commit,
                "git_dirty": self.git_dirty,
            },
            "runtime": {
                "python_version": self.python_version,
                "platform": self.platform,
                "machine": self.machine,
            },
            "dependencies": dict(
                sorted(self.dependencies.items())
            ),
            "software": {
                "version": self.software_version,
            },
        }

    def write(self, path: Path) -> None:
        """Write the provenance manifest as JSON."""

        path = Path(path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                self.to_dict(),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True)
class ModelProvenanceBuilder:
    """Build provenance from the current project and runtime."""

    project_root: Path

    def build(
        self,
        *,
        artifact_version: str,
        model_version: str,
        model_family: str,
        dataset_version: str,
        dataset_path: Path,
        feature_schema_version: str,
        feature_schema_path: Path,
        model_config_path: Path,
        calibration_method: str,
        calibration_temperature: float,
        calibration_source_path: Path,
    ) -> ModelProvenance:
        """Build an immutable provenance snapshot."""

        project_root = Path(
            self.project_root
        ).resolve()

        dataset_path = Path(dataset_path).resolve()
        feature_schema_path = (
            Path(feature_schema_path).resolve()
        )
        model_config_path = (
            Path(model_config_path).resolve()
        )
        calibration_source_path = (
            Path(calibration_source_path).resolve()
        )

        for path in (
            dataset_path,
            feature_schema_path,
            model_config_path,
            calibration_source_path,
        ):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Provenance source does not exist: {path}"
                )

        package_names = (
            "ztf-classifier",
            "numpy",
            "pandas",
            "scipy",
            "scikit-learn",
            "xgboost",
            "pyarrow",
        )

        dependencies: dict[str, str] = {}

        for name in package_names:
            try:
                dependencies[name] = (
                    importlib.metadata.version(name)
                )
            except importlib.metadata.PackageNotFoundError:
                dependencies[name] = "NOT_INSTALLED"

        git_commit = _git_output(
            project_root,
            "rev-parse",
            "HEAD",
        )

        git_dirty = bool(
            _git_output(
                project_root,
                "status",
                "--porcelain=v1",
            )
        )

        try:
            software_version = importlib.metadata.version("ztf-classifier")
        except importlib.metadata.PackageNotFoundError:
            software_version = "unknown"

        return ModelProvenance(
            schema_version=PROVENANCE_SCHEMA_VERSION,
            artifact_version=artifact_version,
            model_version=model_version,
            model_family=model_family,
            dataset_version=dataset_version,
            dataset_path=str(
                dataset_path.relative_to(project_root)
            ),
            dataset_sha256=_sha256(dataset_path),
            feature_schema_version=feature_schema_version,
            feature_schema_path=str(
                feature_schema_path.relative_to(
                    project_root
                )
            ),
            feature_schema_sha256=_sha256(
                feature_schema_path
            ),
            model_config_path=str(
                model_config_path.relative_to(
                    project_root
                )
            ),
            model_config_sha256=_sha256(
                model_config_path
            ),
            calibration_method=calibration_method,
            calibration_temperature=float(
                calibration_temperature
            ),
            calibration_source_path=str(
                calibration_source_path.relative_to(
                    project_root
                )
            ),
            calibration_source_sha256=_sha256(
                calibration_source_path
            ),
            git_commit=git_commit,
            git_dirty=git_dirty,
            python_version=sys.version,
            platform=platform.platform(),
            machine=platform.machine(),
            dependencies=dependencies,
            software_version=software_version,
        )


__all__ = [
    "ModelProvenance",
    "ModelProvenanceBuilder",
]
