"""Offline Parquet detection-acquisition backend."""

from __future__ import annotations

from pathlib import Path

from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionRequest,
    DetectionAcquisitionResult,
)
from ztf_classifier.io.parquet_detection_store import ParquetDetectionStore


class ParquetDetectionBackend(DetectionAcquisitionBackend):
    """Acquire light curves exclusively from a Parquet detection store."""

    def __init__(self, cache_dir: str | Path) -> None:
        self._store = ParquetDetectionStore(cache_dir)

    def acquire(
        self,
        request: DetectionAcquisitionRequest,
    ) -> DetectionAcquisitionResult:
        detections, non_detections = self._store.load(request.oid)

        return DetectionAcquisitionResult(
            request=request,
            detections=detections,
            non_detections=non_detections,
            cache_hit=True,
        )
