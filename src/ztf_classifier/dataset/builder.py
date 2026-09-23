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
        missing = set(REQUIRED_OBJECT_COLUMNS) - set(objects.columns)
        if missing:
            raise ValueError(
                f"Object records are missing columns: {sorted(missing)}"
            )

        manifest_objects = objects.loc[
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
