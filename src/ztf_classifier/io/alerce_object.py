"""ALeRCE implementation of object acquisition."""

from __future__ import annotations

from typing import Any

import pandas as pd

from ztf_classifier.dataset.manifest import REQUIRED_OBJECT_COLUMNS
from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
    ObjectAcquisitionResult,
)


class AlerceObjectBackend(ObjectAcquisitionBackend):
    """Acquire classified ZTF objects through ALeRCE."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        result = self._client.query_objects(
            classifier=request.classifier,
            class_name=request.class_name,
            probability=request.probability,
            page_size=request.page_size,
            format="pandas",
        )

        if not isinstance(result, pd.DataFrame):
            raise TypeError(
                "ALeRCE object query must return a pandas DataFrame."
            )

        objects = result.copy()

        required_api_columns = {
            "oid",
            "probability",
        }
        missing = sorted(
            required_api_columns - set(objects.columns)
        )
        if missing:
            raise ValueError(
                "ALeRCE object response is missing required columns: "
                + ", ".join(missing)
            )

        objects["oid"] = objects["oid"].astype(str)
        if "class" not in objects.columns:
            objects["class"] = request.class_name
        else:
            objects["class"] = objects["class"].astype(str)

        if "classifier" not in objects.columns:
            objects["classifier"] = request.classifier
        else:
            objects["classifier"] = objects["classifier"].astype(str)
        objects["probability"] = pd.to_numeric(
            objects["probability"],
            errors="coerce",
        )

        if objects["probability"].isna().any():
            raise ValueError(
                "ALeRCE object response contains invalid probabilities."
            )

        if objects["oid"].eq("").any():
            raise ValueError(
                "ALeRCE object response contains empty object identifiers."
            )

        objects["label_source"] = "ALeRCE"
        objects["label_type"] = "classifier"
        objects["label_probability"] = objects["probability"]
        objects["classifier_version"] = request.classifier_version
        objects["survey"] = request.survey

        missing_canonical = sorted(
            set(REQUIRED_OBJECT_COLUMNS) - set(objects.columns)
        )
        if missing_canonical:
            raise ValueError(
                "ALeRCE object normalization failed; missing canonical "
                "columns: "
                + ", ".join(missing_canonical)
            )

        objects = (
            objects.sort_values(
                ["probability", "oid"],
                ascending=[False, True],
            )
            .drop_duplicates("oid", keep="first")
            .reset_index(drop=True)
        )

        return ObjectAcquisitionResult(
            request=request,
            objects=(objects,),
        )
