"""Validation of production reproducibility manifests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.reproducibility.manifest import (
    REPRODUCIBILITY_SCHEMA_VERSION,
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ReproducibilityValidationResult:
    """Successful reproducibility manifest validation result."""

    manifest_path: Path
    dataset_path: Path
    feature_schema_path: Path
    dataset_sha256: str
    feature_schema_sha256: str


class ReproducibilityValidator:
    """Validate structural and cryptographic manifest integrity."""

    def validate(
        self,
        manifest_path: Path,
        *,
        project_root: Path | None = None,
        verify_files: bool = True,
    ) -> ReproducibilityValidationResult:
        if not manifest_path.is_file():
            raise ValueError(
                f"Reproducibility manifest does not exist: {manifest_path}"
            )

        try:
            manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Reproducibility manifest is not valid JSON."
            ) from exc

        if not isinstance(manifest, dict):
            raise TypeError("Reproducibility manifest must be a JSON object.")

        required_top_level = {
            "schema_version",
            "project",
            "run",
            "source",
            "runtime",
            "dependencies",
            "dataset",
            "feature_schema",
            "configuration",
            "reproducibility",
        }

        missing = required_top_level - set(manifest)
        if missing:
            raise ValueError(
                f"Manifest is missing required fields: {sorted(missing)}"
            )

        if manifest["schema_version"] != REPRODUCIBILITY_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported reproducibility manifest schema version."
            )

        if not isinstance(manifest["project"], str) or not manifest["project"]:
            raise ValueError("Manifest project must be a non-empty string.")

        for section in (
            "run",
            "source",
            "runtime",
            "dataset",
            "feature_schema",
            "reproducibility",
        ):
            if not isinstance(manifest[section], dict):
                raise TypeError(
                    f"Manifest section must be an object: {section}"
                )

        run = manifest["run"]
        for field in ("run_id", "created_utc", "purpose"):
            if not run.get(field):
                raise ValueError(
                    f"Manifest run.{field} is missing."
                )

        source = manifest["source"]

        if not source.get("git_commit"):
            raise ValueError("Manifest source.git_commit is missing.")

        if not isinstance(source["git_commit"], str):
            raise TypeError("Manifest source.git_commit must be a string.")

        if not isinstance(source.get("git_dirty"), bool):
            raise TypeError("Manifest source.git_dirty must be a boolean.")

        runtime = manifest["runtime"]

        for field in (
            "python",
            "python_implementation",
            "platform",
            "architecture",
            "executable",
        ):
            if not runtime.get(field):
                raise ValueError(
                    f"Manifest runtime.{field} is missing."
                )

        dependencies = manifest["dependencies"]

        if not isinstance(dependencies, dict):
            raise TypeError(
                "Manifest dependencies must be an object."
            )

        if any(
            not isinstance(name, str) or not isinstance(version, str)
            for name, version in dependencies.items()
        ):
            raise TypeError(
                "Manifest dependency names and versions must be strings."
            )

        dataset = manifest["dataset"]
        feature_schema = manifest["feature_schema"]

        for section_name, section in (
            ("dataset", dataset),
            ("feature_schema", feature_schema),
        ):
            for field in ("path", "sha256"):
                if not section.get(field):
                    raise ValueError(
                        f"Manifest {section_name}.{field} is missing."
                    )

            if not isinstance(section["path"], str):
                raise TypeError(
                    f"Manifest {section_name}.path must be a string."
                )

            if not isinstance(section["sha256"], str):
                raise TypeError(
                    f"Manifest {section_name}.sha256 must be a string."
                )

            if not _SHA256_PATTERN.fullmatch(section["sha256"]):
                raise ValueError(
                    f"Manifest {section_name}.sha256 is not a valid SHA-256."
                )

        configuration = manifest["configuration"]

        if not isinstance(configuration, dict):
            raise TypeError("Manifest configuration must be an object.")

        reproducibility = manifest["reproducibility"]

        for field in ("deterministic_order", "dataset_mutation"):
            if not isinstance(reproducibility.get(field), bool):
                raise TypeError(
                    f"Manifest reproducibility.{field} must be a boolean."
                )

        if project_root is None:
            project_root = manifest_path.parent

        project_root = project_root.resolve()

        dataset_path = Path(dataset["path"])
        feature_schema_path = Path(feature_schema["path"])

        if not dataset_path.is_absolute():
            dataset_path = project_root / dataset_path

        if not feature_schema_path.is_absolute():
            feature_schema_path = project_root / feature_schema_path

        dataset_path = dataset_path.resolve()
        feature_schema_path = feature_schema_path.resolve()

        if verify_files:
            if not dataset_path.is_file():
                raise ValueError(
                    f"Manifest dataset does not exist: {dataset_path}"
                )

            if not feature_schema_path.is_file():
                raise ValueError(
                    "Manifest feature schema does not exist: "
                    f"{feature_schema_path}"
                )

            actual_dataset_hash = sha256_file(dataset_path)

            if actual_dataset_hash != dataset["sha256"]:
                raise ValueError(
                    "Dataset SHA-256 does not match reproducibility manifest."
                )

            actual_schema_hash = sha256_file(feature_schema_path)

            if actual_schema_hash != feature_schema["sha256"]:
                raise ValueError(
                    "Feature schema SHA-256 does not match "
                    "reproducibility manifest."
                )
        else:
            actual_dataset_hash = dataset["sha256"]
            actual_schema_hash = feature_schema["sha256"]

        return ReproducibilityValidationResult(
            manifest_path=manifest_path,
            dataset_path=dataset_path,
            feature_schema_path=feature_schema_path,
            dataset_sha256=actual_dataset_hash,
            feature_schema_sha256=actual_schema_hash,
        )
