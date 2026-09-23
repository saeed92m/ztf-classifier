"""Persistent dataset artifact contracts and serialization."""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
    FeatureDataset,
)
from ztf_classifier.features.pipeline import V0_2_FEATURES


@dataclass(frozen=True)
class DatasetArtifact:
    """Persistent representation of a canonical feature dataset."""

    dataset: FeatureDataset
    artifact_path: Path
    manifest_path: Path
    input_manifest_sha256: str
    artifact_sha256: str

    def __post_init__(self) -> None:
        if not self.input_manifest_sha256:
            raise ValueError("input_manifest_sha256 must not be empty.")
        if not self.artifact_sha256:
            raise ValueError("artifact_sha256 must not be empty.")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def sha256_dataframe(data: pd.DataFrame) -> str:
    """Return a deterministic SHA-256 digest of a DataFrame."""
    canonical = data.copy()

    canonical = canonical.sort_values("oid").reset_index(drop=True)

    payload = canonical.to_json(
        orient="split",
        date_format="iso",
        double_precision=15,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


class DatasetArtifactWriter:
    """Write a FeatureDataset and its reproducibility manifest."""

    def write(
        self,
        dataset: FeatureDataset,
        output_dir: Path,
        input_manifest_sha256: str,
    ) -> DatasetArtifact:
        output_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = output_dir / "features.parquet"
        manifest_path = output_dir / "dataset_manifest.json"

        data = (
            dataset.data
            .sort_values("oid")
            .reset_index(drop=True)
        )

        expected_columns = (
            FEATURE_DATASET_METADATA_COLUMNS
            + V0_2_FEATURES
        )

        if tuple(data.columns) != expected_columns:
            raise ValueError(
                "Dataset columns do not match the canonical schema."
            )

        data.to_parquet(
            artifact_path,
            index=False,
        )

        artifact_sha256 = sha256_file(artifact_path)

        manifest = {
            "dataset_version": dataset.dataset_version,
            "feature_schema_version": dataset.feature_schema_version,
            "object_count": len(data),
            "feature_count": len(V0_2_FEATURES),
            "class_count": int(data["class"].nunique()),
            "class_counts": {
                str(key): int(value)
                for key, value in (
                    data["class"].value_counts().sort_index().items()
                )
            },
            "columns": list(data.columns),
            "metadata_columns": list(FEATURE_DATASET_METADATA_COLUMNS),
            "feature_columns": list(V0_2_FEATURES),
            "deterministic_order": "oid_ascending",
            "input_manifest_sha256": input_manifest_sha256,
            "artifact_sha256": artifact_sha256,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        }

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return DatasetArtifact(
            dataset=dataset,
            artifact_path=artifact_path,
            manifest_path=manifest_path,
            input_manifest_sha256=input_manifest_sha256,
            artifact_sha256=artifact_sha256,
        )
