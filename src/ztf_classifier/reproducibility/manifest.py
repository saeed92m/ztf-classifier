"""Production reproducibility manifest contracts."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.reproducibility.environment import (
    collect_dependency_versions,
    collect_environment,
    collect_git_state,
)

REPRODUCIBILITY_SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    """Return the current UTC timestamp in ISO-8601 form."""
    return datetime.now(UTC).isoformat()


def _relative_path(path: Path, project_root: Path) -> str:
    """Return a portable path relative to the project root."""
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"Path must be inside project root: {path}"
        ) from exc


def _json_safe(value: Any) -> Any:
    """Normalize configuration values into JSON-compatible objects."""
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, Path):
        return str(value)

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise TypeError(
        f"Unsupported configuration value type: {type(value).__name__}"
    )


@dataclass(frozen=True)
class ReproducibilityManifest:
    """Persistent production reproducibility manifest."""

    data: dict[str, Any]
    manifest_path: Path

    def write(self) -> Path:
        """Write the manifest as stable, canonical JSON."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

        self.manifest_path.write_text(
            json.dumps(
                self.data,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return self.manifest_path


class ReproducibilityManifestBuilder:
    """Build a reproducibility manifest for a production run."""

    def build(
        self,
        *,
        project_root: Path,
        dataset_path: Path,
        feature_schema_path: Path,
        output_path: Path,
        project: str = "ZTF Classifier",
        purpose: str = "production_run",
        command: str | None = None,
        configuration: dict[str, Any] | None = None,
        object_count: int | None = None,
        feature_count: int | None = None,
        dataset_version: str | None = None,
        feature_schema_version: str | None = None,
    ) -> ReproducibilityManifest:
        project_root = project_root.resolve()
        dataset_path = dataset_path.resolve()
        feature_schema_path = feature_schema_path.resolve()

        dataset_relative_path = _relative_path(
            dataset_path,
            project_root,
        )
        feature_schema_relative_path = _relative_path(
            feature_schema_path,
            project_root,
        )

        if not dataset_path.is_file():
            raise ValueError(f"Dataset does not exist: {dataset_path}")

        if not feature_schema_path.is_file():
            raise ValueError(
                f"Feature schema does not exist: {feature_schema_path}"
            )

        if object_count is not None and object_count < 0:
            raise ValueError("object_count must be non-negative.")

        if feature_count is not None and feature_count < 0:
            raise ValueError("feature_count must be non-negative.")

        git = collect_git_state(project_root)

        data = {
            "schema_version": REPRODUCIBILITY_SCHEMA_VERSION,
            "project": project,
            "run": {
                "run_id": str(uuid.uuid4()),
                "created_utc": _utc_now(),
                "purpose": purpose,
                "command": command,
            },
            "source": git,
            "runtime": collect_environment(),
            "dependencies": collect_dependency_versions(),
            "dataset": {
                "path": dataset_relative_path,
                "sha256": sha256_file(dataset_path),
                "object_count": object_count,
                "feature_count": feature_count,
                "dataset_version": dataset_version,
            },
            "feature_schema": {
                "path": feature_schema_relative_path,
                "sha256": sha256_file(feature_schema_path),
                "version": feature_schema_version,
            },
            "configuration": _json_safe(configuration or {}),
            "reproducibility": {
                "deterministic_order": True,
                "dataset_mutation": False,
            },
        }

        return ReproducibilityManifest(
            data=data,
            manifest_path=output_path,
        )
