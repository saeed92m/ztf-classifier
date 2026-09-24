"""Builders for canonical dataset manifests."""

from __future__ import annotations

import pandas as pd

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.manifest import (
    REQUIRED_OBJECT_COLUMNS,
    ObjectManifest,
)


class ObjectManifestBuilder:
    """Build a canonical object manifest from object records."""

    def __init__(self, config: DatasetConfig) -> None:
        self._config = config

    def build(self, objects: pd.DataFrame) -> ObjectManifest:
        """Build a canonical manifest from object records."""
        base_required_columns = {
            "oid",
            "class",
            "classifier",
            "probability",
        }

        missing_base = base_required_columns - set(objects.columns)
        if missing_base:
            raise ValueError(
                f"Object records are missing columns: {sorted(missing_base)}"
            )

        manifest_objects = objects.copy()

        manifest_objects["label_source"] = self._config.source
        manifest_objects["label_type"] = "classifier"
        manifest_objects["label_probability"] = pd.to_numeric(
            manifest_objects["probability"],
            errors="raise",
        )
        manifest_objects["classifier_version"] = (
            self._config.classifier_version
        )
        manifest_objects["survey"] = self._config.survey

        manifest_objects = manifest_objects.loc[
            :, list(REQUIRED_OBJECT_COLUMNS)
        ].copy()

        manifest_objects = manifest_objects.sort_values(
            "oid"
        ).reset_index(drop=True)

        return ObjectManifest(
            objects=manifest_objects,
            dataset_version=self._config.dataset_version,
            probability_min=self._config.probability_min,
            samples_per_class=self._config.samples_per_class,
        )
