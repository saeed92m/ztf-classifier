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
        """Build a canonical manifest from validated object records."""
        if not isinstance(objects, pd.DataFrame):
            raise TypeError("Object records must be a pandas DataFrame.")

        missing = set(REQUIRED_OBJECT_COLUMNS) - set(objects.columns)
        if missing:
            raise ValueError(
                f"Object records are missing columns: {sorted(missing)}"
            )

        if objects.empty:
            raise ValueError("Object records must not be empty.")

        manifest_objects = objects.loc[
            :, list(REQUIRED_OBJECT_COLUMNS)
        ].copy()

        manifest_objects["oid"] = manifest_objects["oid"].astype(str)
        if manifest_objects["oid"].eq("").any():
            raise ValueError("Object manifest contains empty OIDs.")

        if manifest_objects["oid"].duplicated().any():
            duplicates = sorted(
                manifest_objects.loc[
                    manifest_objects["oid"].duplicated(keep=False),
                    "oid",
                ].unique()
            )
            raise ValueError(
                "Object manifest contains duplicate OIDs: "
                + ", ".join(duplicates)
            )

        unexpected_classes = sorted(
            set(manifest_objects["class"].astype(str))
            - set(self._config.classes)
        )
        if unexpected_classes:
            raise ValueError(
                "Object manifest contains classes not present in the "
                "dataset configuration: "
                + ", ".join(unexpected_classes)
            )

        missing_classes = sorted(
            set(self._config.classes)
            - set(manifest_objects["class"].astype(str))
        )
        if missing_classes:
            raise ValueError(
                "Object manifest is missing configured classes: "
                + ", ".join(missing_classes)
            )

        probabilities = pd.to_numeric(
            manifest_objects["probability"],
            errors="coerce",
        )
        label_probabilities = pd.to_numeric(
            manifest_objects["label_probability"],
            errors="coerce",
        )

        if probabilities.isna().any() or label_probabilities.isna().any():
            raise ValueError(
                "Object manifest contains invalid probability values."
            )

        if not probabilities.between(0.0, 1.0).all():
            raise ValueError(
                "Object manifest contains probabilities outside [0, 1]."
            )

        if not label_probabilities.between(0.0, 1.0).all():
            raise ValueError(
                "Object manifest contains label probabilities outside [0, 1]."
            )

        if not (
            probabilities.reset_index(drop=True)
            .equals(label_probabilities.reset_index(drop=True))
        ):
            raise ValueError(
                "Object manifest probability and label_probability differ."
            )

        if manifest_objects["classifier"].astype(str).ne(
            self._config.classifier
        ).any():
            raise ValueError(
                "Object manifest contains an unexpected classifier."
            )

        if manifest_objects["survey"].astype(str).ne(
            self._config.survey
        ).any():
            raise ValueError(
                "Object manifest contains an unexpected survey."
            )

        if manifest_objects["classifier_version"].astype(str).ne(
            self._config.classifier_version
        ).any():
            raise ValueError(
                "Object manifest contains an unexpected classifier version."
            )

        manifest_objects = manifest_objects.sort_values(
            "oid"
        ).reset_index(drop=True)

        return ObjectManifest(
            objects=manifest_objects,
            dataset_version=self._config.dataset_version,
            probability_min=self._config.probability_min,
            samples_per_class=self._config.samples_per_class,
        )
