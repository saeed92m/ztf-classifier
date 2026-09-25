"""Canonical feature-dataset construction."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.features.engine import ScientificFeatureEngine
from ztf_classifier.features.pipeline import V0_2_FEATURES
from ztf_classifier.io.alerce import alerce_to_internal_lc_robust
from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionRequest,
)

FEATURE_DATASET_METADATA_COLUMNS = (
    "oid",
    "class",
    "classifier",
    "probability",
    "label_source",
    "label_type",
    "label_probability",
    "classifier_version",
    "survey",
)


@dataclass(frozen=True)
class FeatureDataset:
    """Canonical feature dataset and its dataset-level metadata."""

    data: pd.DataFrame
    dataset_version: str
    feature_schema_version: str

    def __post_init__(self) -> None:
        expected = (
            FEATURE_DATASET_METADATA_COLUMNS
            + V0_2_FEATURES
        )

        if tuple(self.data.columns) != expected:
            raise ValueError(
                "Feature dataset columns do not match the canonical schema."
            )

        if self.data["oid"].duplicated().any():
            raise ValueError(
                "Feature dataset contains duplicate OIDs."
            )

    @property
    def object_count(self) -> int:
        return len(self.data)

    @property
    def feature_count(self) -> int:
        return len(V0_2_FEATURES)


class FeatureDatasetBuilder:
    """Build a canonical feature dataset from an object manifest."""

    def __init__(
        self,
        manifest: ObjectManifest,
        acquisition_backend: DetectionAcquisitionBackend,
        feature_schema_version: str = "v0.2",
        feature_engine: ScientificFeatureEngine | None = None,
    ) -> None:
        self._manifest = manifest
        self._acquisition_backend = acquisition_backend
        self._feature_schema_version = feature_schema_version
        self._feature_engine = feature_engine or ScientificFeatureEngine()

    def build(
        self,
        cutoff_mjd: float | None = None,
    ) -> FeatureDataset:
        """Build the canonical feature dataset deterministically.

        When ``cutoff_mjd`` is provided, only observations with
        ``mjd <= cutoff_mjd`` are used for feature extraction.
        """


        rows: list[dict[str, object]] = []

        manifest = (
            self._manifest.objects
            .sort_values("oid")
            .reset_index(drop=True)
        )

        for record in manifest.to_dict(orient="records"):
            request = DetectionAcquisitionRequest(
                oid=str(record["oid"]),
                survey=str(record["survey"]),
            )

            result = self._acquisition_backend.acquire(request)

            internal = alerce_to_internal_lc_robust(
                result.detections
            )

            features = self._feature_engine.compute(
                internal,
                backend="native",
                parameters=(
                    {"cutoff_mjd": cutoff_mjd}
                    if cutoff_mjd is not None
                    else {}
                ),
            ).values

            row = {
                column: record[column]
                for column in FEATURE_DATASET_METADATA_COLUMNS
            }
            row.update(features)

            rows.append(row)

        data = pd.DataFrame(
            rows,
            columns=(
                FEATURE_DATASET_METADATA_COLUMNS
                + V0_2_FEATURES
            ),
        )

        return FeatureDataset(
            data=data,
            dataset_version=self._manifest.dataset_version,
            feature_schema_version=self._feature_schema_version,
        )
