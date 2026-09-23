"""Validation contracts for canonical dataset manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
)
from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.features.pipeline import V0_2_FEATURES


def validate_against_historical_objects(
    manifest: ObjectManifest,
    historical: pd.DataFrame,
) -> None:
    """Validate a production object manifest against the frozen object artifact."""

    required = {
        "oid",
        "class",
        "classifier",
        "probability",
        "label_source",
        "label_type",
        "label_probability",
        "classifier_version",
        "survey",
    }

    missing = required - set(historical.columns)
    if missing:
        raise ValueError(
            f"Historical artifact is missing columns: {sorted(missing)}"
        )

    if len(manifest.objects) != len(historical):
        raise ValueError(
            "Manifest row count does not match historical artifact"
        )

    if manifest.objects["oid"].nunique() != historical["oid"].nunique():
        raise ValueError(
            "Manifest unique OID count does not match historical artifact"
        )

    manifest_index = manifest.objects.set_index("oid").sort_index()
    historical_index = historical.set_index("oid").sort_index()

    if not manifest_index.index.equals(historical_index.index):
        raise ValueError("Manifest OIDs do not match historical artifact")

    for column in (
        "class",
        "classifier",
        "label_source",
        "label_type",
        "classifier_version",
        "survey",
    ):
        if not manifest_index[column].equals(historical_index[column]):
            raise ValueError(
                f"Manifest column does not match historical artifact: {column}"
            )

    for column in ("probability", "label_probability"):
        if not manifest_index[column].equals(historical_index[column]):
            raise ValueError(
                f"Manifest column does not match historical artifact: {column}"
            )

    if not (historical["probability"] == historical["label_probability"]).all():
        raise ValueError(
            "Historical probability and label_probability are inconsistent"
        )

@dataclass(frozen=True)
class DatasetArtifactValidationResult:
    """Validation result for a persisted dataset artifact."""

    artifact_path: Path
    manifest_path: Path
    object_count: int
    feature_count: int
    class_count: int


class DatasetArtifactValidator:
    """Validate a persisted canonical dataset artifact independently."""

    def validate(
        self,
        artifact_path: Path,
        manifest_path: Path,
    ) -> DatasetArtifactValidationResult:
        if not artifact_path.is_file():
            raise ValueError(
                f"Dataset artifact does not exist: {artifact_path}"
            )

        if not manifest_path.is_file():
            raise ValueError(
                f"Dataset manifest does not exist: {manifest_path}"
            )

        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )

        data = pd.read_parquet(artifact_path)

        expected_columns = (
            FEATURE_DATASET_METADATA_COLUMNS
            + V0_2_FEATURES
        )

        if tuple(data.columns) != expected_columns:
            raise ValueError(
                "Dataset artifact columns do not match the canonical schema."
            )

        if data["oid"].duplicated().any():
            raise ValueError(
                "Dataset artifact contains duplicate OIDs."
            )

        if manifest["object_count"] != len(data):
            raise ValueError(
                "Manifest object_count does not match artifact."
            )

        if manifest["feature_count"] != len(V0_2_FEATURES):
            raise ValueError(
                "Manifest feature_count does not match canonical feature count."
            )

        if manifest["class_count"] != data["class"].nunique():
            raise ValueError(
                "Manifest class_count does not match artifact."
            )

        expected_class_counts = {
            str(key): int(value)
            for key, value in (
                data["class"].value_counts().sort_index().items()
            )
        }

        if manifest["class_counts"] != expected_class_counts:
            raise ValueError(
                "Manifest class_counts do not match artifact."
            )

        if manifest["columns"] != list(data.columns):
            raise ValueError(
                "Manifest columns do not match artifact."
            )

        if manifest["metadata_columns"] != list(
            FEATURE_DATASET_METADATA_COLUMNS
        ):
            raise ValueError(
                "Manifest metadata_columns do not match canonical schema."
            )

        if manifest["feature_columns"] != list(V0_2_FEATURES):
            raise ValueError(
                "Manifest feature_columns do not match canonical schema."
            )

        if manifest["deterministic_order"] != "oid_ascending":
            raise ValueError(
                "Unsupported deterministic ordering."
            )

        ordered_oids = data["oid"].astype(str).tolist()

        if ordered_oids != sorted(ordered_oids):
            raise ValueError(
                "Dataset artifact is not deterministically ordered by OID."
            )

        actual_hash = sha256_file(artifact_path)

        if actual_hash != manifest["artifact_sha256"]:
            raise ValueError(
                "Artifact SHA-256 does not match manifest."
            )

        return DatasetArtifactValidationResult(
            artifact_path=artifact_path,
            manifest_path=manifest_path,
            object_count=len(data),
            feature_count=len(V0_2_FEATURES),
            class_count=data["class"].nunique(),
        )
