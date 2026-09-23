"""ALeRCE implementation of detection acquisition."""

from __future__ import annotations

from typing import Any

import pandas as pd

from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionRequest,
    DetectionAcquisitionResult,
)
from ztf_classifier.io.detection_store import DetectionStore


class AlerceDetectionBackend(DetectionAcquisitionBackend):
    """Acquire ZTF detections through ALeRCE with persistent caching."""

    def __init__(
        self,
        client: Any,
        store: DetectionStore,
    ) -> None:
        self._client = client
        self._store = store

    def acquire(
        self,
        request: DetectionAcquisitionRequest,
    ) -> DetectionAcquisitionResult:
        if self._store.exists(request.oid):
            detections, non_detections = self._store.load(request.oid)

            return DetectionAcquisitionResult(
                request=request,
                detections=detections,
                non_detections=non_detections,
                cache_hit=True,
            )

        response = self._client.query_lightcurve(
            request.oid,
            format="pandas",
            survey=request.survey,
        )

        detections = pd.DataFrame(
            response.iloc[0]["detections"]
        )
        non_detections = pd.DataFrame(
            response.iloc[0]["non_detections"]
        )

        self._store.save(
            request.oid,
            detections,
            non_detections,
        )

        return DetectionAcquisitionResult(
            request=request,
            detections=detections,
            non_detections=non_detections,
            cache_hit=False,
        )
