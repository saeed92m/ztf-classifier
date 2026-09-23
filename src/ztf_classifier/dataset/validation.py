"""Validation contracts for canonical dataset manifests and artifacts."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.dataset.artifact import sha256_file
from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
)
from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.features.pipeline import V0_2_FEATURES

NON_EMPTY_METADATA_COLUMNS = (
    "oid",
    "class",
    "classifier",
    "label_source",
    "label_type",
    "classifier_version",
    "survey",
)

PROBABILITY_COLUMNS = (
    "probability",
    "label_probability",
)


def validate_against_historical_objects(
    manifest: ObjectManifest,
    historical: pd.DataFrame,
) -> None:
    """Validate a production object manifest against a frozen object artifact."""

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
    """Validation result for a persisted canonical dataset artifact."""

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
        *,
        expected_dataset_version: str | None = None,
        expected_feature_schema_version: str | None = None,
        input_manifest_path: Path | None = None,
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

        if data["oid"].isna().any():
            raise ValueError(
                "Dataset artifact contains null OIDs."
            )

        if (
            data["oid"]
            .astype("string")
            .str.strip()
            .eq("")
            .any()
        ):
            raise ValueError(
                "Dataset artifact contains empty OIDs."
            )

        for column in NON_EMPTY_METADATA_COLUMNS:
            if data[column].isna().any():
                raise ValueError(
                    f"Dataset artifact contains null metadata values: {column}"
                )

            if (
                data[column]
                .astype("string")
                .str.strip()
                .eq("")
                .any()
            ):
                raise ValueError(
                    f"Dataset artifact contains empty metadata values: {column}"
                )

        for column in PROBABILITY_COLUMNS:
            values = pd.to_numeric(
                data[column],
                errors="coerce",
            )

            if values.isna().any():
                raise ValueError(
                    f"Dataset artifact contains invalid probability values: {column}"
                )

            if not values.map(math.isfinite).all():
                raise ValueError(
                    f"Dataset artifact contains non-finite probability values: {column}"
                )

            if ((values < 0.0) | (values > 1.0)).any():
                raise ValueError(
                    f"Dataset artifact contains out-of-range probability values: {column}"
                )

        probability = pd.to_numeric(
            data["probability"],
            errors="coerce",
        )
        label_probability = pd.to_numeric(
            data["label_probability"],
            errors="coerce",
        )

        if not probability.equals(label_probability):
            raise ValueError(
                "Dataset artifact probability and label_probability are inconsistent."
            )

        feature_values = data[list(V0_2_FEATURES)].to_numpy(dtype=float)

        finite_mask = np.isfinite(feature_values)
        non_finite_mask = ~finite_mask & ~np.isnan(feature_values)

        if non_finite_mask.any():
            raise ValueError(
                "Dataset artifact contains non-finite feature values."
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

        if (
            expected_dataset_version is not None
            and manifest.get("dataset_version") != expected_dataset_version
        ):
            raise ValueError(
                "Dataset manifest dataset_version does not match expected version."
            )

        if (
            expected_feature_schema_version is not None
            and manifest.get("feature_schema_version")
            != expected_feature_schema_version
        ):
            raise ValueError(
                "Dataset manifest feature_schema_version does not match expected version."
            )

        if manifest.get("feature_schema_version") != "v0.2":
            raise ValueError(
                "Unsupported feature schema version."
            )

        actual_hash = sha256_file(artifact_path)

        if actual_hash != manifest["artifact_sha256"]:
            raise ValueError(
                "Artifact SHA-256 does not match manifest."
            )

        if input_manifest_path is not None:
            if not input_manifest_path.is_file():
                raise ValueError(
                    f"Input object manifest does not exist: {input_manifest_path}"
                )

            input_hash = sha256_file(input_manifest_path)

            if input_hash != manifest["input_manifest_sha256"]:
                raise ValueError(
                    "Input object manifest SHA-256 does not match dataset manifest."
                )

            object_manifest = pd.read_parquet(input_manifest_path)

            required_metadata = list(
                FEATURE_DATASET_METADATA_COLUMNS
            )

            if tuple(object_manifest.columns) != tuple(required_metadata):
                raise ValueError(
                    "Input object manifest columns do not match canonical metadata schema."
                )

            artifact_identity = (
                data[required_metadata]
                .sort_values("oid")
                .reset_index(drop=True)
            )

            manifest_identity = (
                object_manifest[required_metadata]
                .sort_values("oid")
                .reset_index(drop=True)
            )

            if not artifact_identity.equals(manifest_identity):
                raise ValueError(
                    "Input object manifest does not match dataset artifact metadata."
                )

        return DatasetArtifactValidationResult(
            artifact_path=artifact_path,
            manifest_path=manifest_path,
            object_count=len(data),
            feature_count=len(V0_2_FEATURES),
            class_count=data["class"].nunique(),
        )
