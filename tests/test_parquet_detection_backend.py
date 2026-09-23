import pandas as pd
import pytest

from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionRequest,
)
from ztf_classifier.io.parquet_detection import ParquetDetectionBackend


def test_parquet_detection_backend_returns_cached_lightcurve(
    tmp_path,
) -> None:
    oid = "ZTF_TEST"

    detections = pd.DataFrame(
        {
            "mjd": [1.0, 2.0],
            "fid": [1, 2],
            "mag": [20.0, 20.5],
            "magerr": [0.1, 0.2],
        }
    )

    non_detections = pd.DataFrame(
        {
            "mjd": [3.0],
            "fid": [1],
            "diffmaglim": [21.0],
            "isdiffpos": ["t"],
        }
    )

    detections.to_parquet(
        tmp_path / f"{oid}_detections.parquet",
        index=False,
    )
    non_detections.to_parquet(
        tmp_path / f"{oid}_non_detections.parquet",
        index=False,
    )

    backend = ParquetDetectionBackend(tmp_path)

    result = backend.acquire(
        DetectionAcquisitionRequest(
            oid=oid,
            survey="ZTF",
        )
    )

    assert result.cache_hit is True
    pd.testing.assert_frame_equal(result.detections, detections)
    pd.testing.assert_frame_equal(result.non_detections, non_detections)


def test_parquet_detection_backend_requires_complete_cache(
    tmp_path,
) -> None:
    oid = "ZTF_MISSING"

    detections = pd.DataFrame(
        {
            "mjd": [1.0],
            "fid": [1],
            "mag": [20.0],
            "magerr": [0.1],
        }
    )

    detections.to_parquet(
        tmp_path / f"{oid}_detections.parquet",
        index=False,
    )

    backend = ParquetDetectionBackend(tmp_path)

    with pytest.raises(FileNotFoundError, match="incomplete or missing"):
        backend.acquire(
            DetectionAcquisitionRequest(
                oid=oid,
                survey="ZTF",
            )
        )
