"""Parquet implementation of the raw detection store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ztf_classifier.io.detection_store import (
    DetectionStore,
    DetectionStorePaths,
)


class ParquetDetectionStore(DetectionStore):
    """Store raw detections and non-detections as Parquet files."""

    def __init__(self, cache_dir: str | Path) -> None:
        self._cache_dir = Path(cache_dir)

    def paths(self, oid: str) -> DetectionStorePaths:
        return DetectionStorePaths(
            detections=self._cache_dir / f"{oid}_detections.parquet",
            non_detections=self._cache_dir / f"{oid}_non_detections.parquet",
        )

    def exists(self, oid: str) -> bool:
        paths = self.paths(oid)
        return paths.detections.exists() and paths.non_detections.exists()

    def load(self, oid: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        paths = self.paths(oid)

        if not self.exists(oid):
            raise FileNotFoundError(
                f"Cached light curve is incomplete or missing for {oid}"
            )

        return (
            pd.read_parquet(paths.detections),
            pd.read_parquet(paths.non_detections),
        )

    def save(
        self,
        oid: str,
        detections: Any,
        non_detections: Any,
    ) -> None:
        paths = self.paths(oid)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        detections.to_parquet(paths.detections, index=False)
        non_detections.to_parquet(paths.non_detections, index=False)
