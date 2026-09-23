from pathlib import Path

from ztf_classifier.io.detection_store import (
    DetectionStore,
    DetectionStorePaths,
)


def test_detection_store_paths_are_immutable() -> None:
    paths = DetectionStorePaths(
        detections=Path("/tmp/object_detections.parquet"),
        non_detections=Path("/tmp/object_non_detections.parquet"),
    )

    assert paths.detections.name == "object_detections.parquet"
    assert paths.non_detections.name == "object_non_detections.parquet"


def test_detection_store_is_abstract() -> None:
    assert DetectionStore.__abstractmethods__ == {
        "paths",
        "exists",
        "load",
        "save",
    }
