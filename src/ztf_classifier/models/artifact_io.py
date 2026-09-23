"""Serialization and integrity handling for production model artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.calibration_artifact import CalibrationArtifact
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.contracts import ModelContract
from ztf_classifier.models.provenance import ModelProvenance

ARTIFACT_SCHEMA_VERSION = "1.0"
REQUIRED_FILES = (
    "model",
    "model_contract",
    "feature_schema",
    "calibration",
    "provenance",
)


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _validate_sha256(value: Any, field_name: str) -> str:
    """Validate and return a SHA-256 hexadecimal digest."""

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string."
        )

    if len(value) != 64:
        raise ValueError(
            f"{field_name} must contain a 64-character SHA-256 digest."
        )

    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be hexadecimal."
        ) from exc

    return value


@dataclass(frozen=True)
class LoadedModelArtifact:
    """Complete production artifact loaded from disk."""

    model_artifact: ModelArtifact
    calibration: CalibrationArtifact
    provenance: ModelProvenance


@dataclass(frozen=True)
class ModelArtifactWriter:
    """Write a fitted model and its immutable metadata package."""

    def write(
        self,
        *,
        artifact: ModelArtifact,
        output_dir: Path,
        feature_schema_path: Path,
        calibration: CalibrationArtifact,
        provenance: ModelProvenance,
    ) -> Path:
        """Write and return the artifact directory."""

        output_dir = Path(output_dir)
        feature_schema_path = Path(feature_schema_path)

        if output_dir.exists():
            raise FileExistsError(
                f"Artifact directory already exists: {output_dir}"
            )

        if not feature_schema_path.is_file():
            raise FileNotFoundError(
                f"Feature schema does not exist: {feature_schema_path}"
            )

        source_schema_hash = _sha256(feature_schema_path)

        if source_schema_hash != artifact.feature_schema_sha256:
            raise ValueError(
                "Feature schema SHA-256 does not match the model artifact."
            )

        if artifact.model_version != provenance.model_version:
            raise ValueError(
                "Model artifact model_version does not match provenance."
            )

        if artifact.model_family != provenance.model_family:
            raise ValueError(
                "Model artifact model_family does not match provenance."
            )

        if (
            artifact.feature_schema_version
            != provenance.feature_schema_version
        ):
            raise ValueError(
                "Model artifact feature_schema_version "
                "does not match provenance."
            )

        if artifact.dataset_sha256 != provenance.dataset_sha256:
            raise ValueError(
                "Model artifact dataset SHA-256 does not match provenance."
            )

        if (
            artifact.feature_schema_sha256
            != provenance.feature_schema_sha256
        ):
            raise ValueError(
                "Model artifact feature schema SHA-256 "
                "does not match provenance."
            )

        if calibration.method != provenance.calibration_method:
            raise ValueError(
                "Calibration method does not match provenance."
            )

        if (
            calibration.temperature
            != provenance.calibration_temperature
        ):
            raise ValueError(
                "Calibration temperature does not match provenance."
            )

        output_dir.mkdir(parents=True)

        model_path = output_dir / "model.json"
        contract_path = output_dir / "model_contract.json"
        schema_path = output_dir / "feature_schema.parquet"
        calibration_path = output_dir / "calibration.json"
        provenance_path = output_dir / "provenance.json"

        artifact.model.save_model(model_path)

        contract_payload = ModelContract(
            artifact.configuration
        ).to_dict()

        contract_path.write_text(
            json.dumps(
                contract_payload,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        shutil.copy2(
            feature_schema_path,
            schema_path,
        )

        calibration.write(calibration_path)
        provenance.write(provenance_path)

        manifest = {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "model_version": artifact.model_version,
            "model_family": artifact.model_family,
            "feature_schema_version": artifact.feature_schema_version,
            "classes": list(artifact.classes),
            "feature_count": len(artifact.feature_names),
            "feature_names": list(artifact.feature_names),
            "dataset_sha256": _validate_sha256(
                artifact.dataset_sha256,
                "dataset_sha256",
            ),
            "feature_schema_source_sha256": source_schema_hash,
            "files": {
                "model": {
                    "path": "model.json",
                    "sha256": _sha256(model_path),
                },
                "model_contract": {
                    "path": "model_contract.json",
                    "sha256": _sha256(contract_path),
                },
                "feature_schema": {
                    "path": "feature_schema.parquet",
                    "sha256": _sha256(schema_path),
                },
                "calibration": {
                    "path": "calibration.json",
                    "sha256": _sha256(calibration_path),
                },
                "provenance": {
                    "path": "provenance.json",
                    "sha256": _sha256(provenance_path),
                },
            },
        }

        manifest_path = output_dir / "artifact_manifest.json"

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return output_dir


@dataclass(frozen=True)
class ModelArtifactLoader:
    """Load and validate a serialized production model artifact."""

    def load(
        self,
        artifact_dir: Path,
    ) -> LoadedModelArtifact:
        """Load and validate an artifact package."""

        artifact_dir = Path(artifact_dir).resolve()

        if not artifact_dir.is_dir():
            raise FileNotFoundError(
                f"Artifact directory does not exist: {artifact_dir}"
            )

        manifest_path = artifact_dir / "artifact_manifest.json"

        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"Artifact manifest does not exist: {manifest_path}"
            )

        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )

        self._validate_manifest(manifest)

        files = manifest["files"]
        paths: dict[str, Path] = {}

        for key in REQUIRED_FILES:
            metadata = files[key]
            relative_path = metadata["path"]
            expected_hash = metadata["sha256"]

            candidate = (
                artifact_dir / relative_path
            ).resolve()

            try:
                candidate.relative_to(artifact_dir)
            except ValueError as exc:
                raise ValueError(
                    f"Artifact path escapes artifact directory: "
                    f"{relative_path}"
                ) from exc

            if not candidate.is_file():
                raise FileNotFoundError(
                    f"Artifact file does not exist: {candidate}"
                )

            actual_hash = _sha256(candidate)

            if actual_hash != expected_hash:
                raise ValueError(
                    f"Artifact integrity check failed for '{key}'."
                )

            paths[key] = candidate

        contract_payload = json.loads(
            paths["model_contract"].read_text(
                encoding="utf-8"
            )
        )

        configuration = ModelContract.from_dict(
            contract_payload
        ).config

        self._validate_contract(
            contract_payload,
            manifest,
        )

        schema = pd.read_parquet(
            paths["feature_schema"]
        )

        feature_names = self._validate_feature_schema(
            schema,
            manifest,
        )

        calibration = CalibrationArtifact.read(
            paths["calibration"]
        )

        provenance_data = json.loads(
            paths["provenance"].read_text(
                encoding="utf-8"
            )
        )

        provenance = ModelProvenance(
            schema_version=str(
                provenance_data["provenance_schema_version"]
            ),
            artifact_version=str(
                provenance_data["artifact_version"]
            ),
            model_version=str(
                provenance_data["model"]["version"]
            ),
            model_family=str(
                provenance_data["model"]["family"]
            ),
            dataset_version=str(
                provenance_data["dataset"]["version"]
            ),
            dataset_path=str(
                provenance_data["dataset"]["path"]
            ),
            dataset_sha256=str(
                provenance_data["dataset"]["sha256"]
            ),
            feature_schema_version=str(
                provenance_data["feature_schema"]["version"]
            ),
            feature_schema_path=str(
                provenance_data["feature_schema"]["path"]
            ),
            feature_schema_sha256=str(
                provenance_data["feature_schema"]["sha256"]
            ),
            model_config_path=str(
                provenance_data["model_configuration"]["path"]
            ),
            model_config_sha256=str(
                provenance_data["model_configuration"]["sha256"]
            ),
            calibration_method=str(
                provenance_data["calibration"]["method"]
            ),
            calibration_temperature=float(
                provenance_data["calibration"]["temperature"]
            ),
            calibration_source_path=str(
                provenance_data["calibration"]["source_path"]
            ),
            calibration_source_sha256=str(
                provenance_data["calibration"]["source_sha256"]
            ),
            git_commit=str(
                provenance_data["source_control"]["git_commit"]
            ),
            git_dirty=bool(
                provenance_data["source_control"]["git_dirty"]
            ),
            python_version=str(
                provenance_data["runtime"]["python_version"]
            ),
            platform=str(
                provenance_data["runtime"]["platform"]
            ),
            machine=str(
                provenance_data["runtime"]["machine"]
            ),
            dependencies=dict(
                provenance_data["dependencies"]
            ),
        )

        self._validate_provenance(
            manifest=manifest,
            calibration=calibration,
            provenance=provenance,
        )

        from xgboost import XGBClassifier

        model: Any = XGBClassifier()
        model.load_model(paths["model"])

        artifact = ModelArtifact(
            model=model,
            model_version=str(
                manifest["model_version"]
            ),
            model_family=str(
                manifest["model_family"]
            ),
            classes=tuple(
                manifest["classes"]
            ),
            feature_schema_version=str(
                manifest["feature_schema_version"]
            ),
            feature_names=feature_names,
            configuration=configuration,
            dataset_sha256=str(
                manifest["dataset_sha256"]
            ),
            feature_schema_sha256=str(
                manifest["feature_schema_source_sha256"]
            ),
        )

        return LoadedModelArtifact(
            model_artifact=artifact,
            calibration=calibration,
            provenance=provenance,
        )

    @staticmethod
    def _validate_provenance(
        *,
        manifest: dict[str, Any],
        calibration: CalibrationArtifact,
        provenance: ModelProvenance,
    ) -> None:
        """Validate semantic consistency across artifact metadata."""

        if provenance.model_version != manifest["model_version"]:
            raise ValueError(
                "Provenance model_version does not match artifact."
            )

        if provenance.model_family != manifest["model_family"]:
            raise ValueError(
                "Provenance model_family does not match artifact."
            )

        if (
            provenance.feature_schema_version
            != manifest["feature_schema_version"]
        ):
            raise ValueError(
                "Provenance feature_schema_version "
                "does not match artifact."
            )

        if provenance.dataset_sha256 != manifest["dataset_sha256"]:
            raise ValueError(
                "Provenance dataset SHA-256 does not match artifact."
            )

        if (
            provenance.feature_schema_sha256
            != manifest["feature_schema_source_sha256"]
        ):
            raise ValueError(
                "Provenance feature schema SHA-256 "
                "does not match artifact."
            )

        if provenance.calibration_method != calibration.method:
            raise ValueError(
                "Provenance calibration method does not match "
                "calibration artifact."
            )

        if (
            provenance.calibration_temperature
            != calibration.temperature
        ):
            raise ValueError(
                "Provenance calibration temperature does not match "
                "calibration artifact."
            )

    @staticmethod
    def _validate_manifest(
        manifest: dict[str, Any],
    ) -> None:
        """Validate top-level artifact manifest metadata."""

        if not isinstance(manifest, dict):
            raise TypeError(
                "Artifact manifest must be a dictionary."
            )

        if manifest.get(
            "artifact_schema_version"
        ) != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported model artifact schema version."
            )

        for field in (
            "model_version",
            "model_family",
            "feature_schema_version",
        ):
            value = manifest.get(field)

            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"Artifact manifest field '{field}' is invalid."
                )

        classes = manifest.get("classes")

        if classes != list(MODEL_CLASSES):
            raise ValueError(
                "Artifact manifest classes do not match "
                "the frozen class order."
            )

        feature_count = manifest.get("feature_count")

        if feature_count != 42:
            raise ValueError(
                "Artifact manifest must contain exactly 42 features."
            )

        feature_names = manifest.get("feature_names")

        if (
            not isinstance(feature_names, list)
            or len(feature_names) != 42
            or len(set(feature_names)) != 42
        ):
            raise ValueError(
                "Artifact manifest contains an invalid feature schema."
            )

        _validate_sha256(
            manifest.get("dataset_sha256"),
            "dataset_sha256",
        )

        _validate_sha256(
            manifest.get(
                "feature_schema_source_sha256"
            ),
            "feature_schema_source_sha256",
        )

        files = manifest.get("files")

        if not isinstance(files, dict):
            raise TypeError(
                "Artifact manifest contains invalid file metadata."
            )

        for key in REQUIRED_FILES:
            metadata = files.get(key)

            if not isinstance(metadata, dict):
                raise TypeError(
                    f"Artifact manifest is missing '{key}' metadata."
                )

            relative_path = metadata.get("path")

            if not isinstance(relative_path, str):
                raise TypeError(
                    f"Invalid path metadata for '{key}'."
                )

            if not relative_path:
                raise ValueError(
                    f"Empty path metadata for '{key}'."
                )

            _validate_sha256(
                metadata.get("sha256"),
                f"files.{key}.sha256",
            )

    @staticmethod
    def _validate_contract(
        contract: dict[str, Any],
        manifest: dict[str, Any],
    ) -> None:
        """Validate the serialized model contract."""

        if not isinstance(contract, dict):
            raise TypeError(
                "Model contract must be a dictionary."
            )

        if contract.get(
            "model_version"
        ) != manifest.get("model_version"):
            raise ValueError(
                "Model contract version does not match artifact."
            )

        if contract.get(
            "model_family"
        ) != manifest.get("model_family"):
            raise ValueError(
                "Model contract family does not match artifact."
            )

        if contract.get(
            "classes"
        ) != list(MODEL_CLASSES):
            raise ValueError(
                "Model contract classes do not match frozen classes."
            )

        class_mapping = contract.get("class_to_index")

        if not isinstance(class_mapping, dict):
            raise TypeError(
                "Model contract class mapping must be a dictionary."
            )

    @staticmethod
    def _validate_feature_schema(
        schema: pd.DataFrame,
        manifest: dict[str, Any],
    ) -> tuple[str, ...]:
        """Validate and return the ordered feature schema."""

        required = {
            "feature_order",
            "feature",
        }

        if not required.issubset(schema.columns):
            raise ValueError(
                "Feature schema is missing required columns."
            )

        ordered = (
            schema
            .sort_values("feature_order")
            .reset_index(drop=True)
        )

        names = tuple(
            ordered["feature"].astype(str).tolist()
        )

        expected = tuple(
            manifest["feature_names"]
        )

        if names != expected:
            raise ValueError(
                "Artifact feature schema does not match manifest."
            )

        if len(names) != 42:
            raise ValueError(
                "Artifact feature schema must contain 42 features."
            )

        if len(set(names)) != 42:
            raise ValueError(
                "Artifact feature schema contains duplicates."
            )

        return names


__all__ = [
    "LoadedModelArtifact",
    "ModelArtifactLoader",
    "ModelArtifactWriter",
]
