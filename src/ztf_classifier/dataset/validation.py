"""Validation contracts for canonical dataset manifests."""

from __future__ import annotations

import pandas as pd

from ztf_classifier.dataset.manifest import ObjectManifest


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
