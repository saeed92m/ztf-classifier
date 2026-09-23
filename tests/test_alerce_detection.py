from dataclasses import dataclass

import pandas as pd

from ztf_classifier.io.alerce_detection import AlerceDetectionBackend
from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionRequest,
)
from ztf_classifier.io.parquet_detection_store import (
    ParquetDetectionStore,
)


@dataclass
class FakeResponse:
    detections: list[dict]
    non_detections: list[dict]

    @property
    def iloc(self):
        return _FakeILoc(self)


@dataclass
class _FakeILoc:
    response: FakeResponse

    def __getitem__(self, index: int):
        assert index == 0
        return {
            "detections": self.response.detections,
            "non_detections": self.response.non_detections,
        }


class FakeAlerceClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def query_lightcurve(
        self,
        oid: str,
        *,
        format: str,
        survey: str,
    ) -> FakeResponse:
        self.calls.append((oid, format, survey))

        return FakeResponse(
            detections=[
                {"mjd": 1.0, "magpsf": 19.1},
                {"mjd": 2.0, "magpsf": 19.2},
            ],
            non_detections=[
                {"mjd": 3.0, "diffmaglim": 20.1},
            ],
        )


def test_cache_miss_queries_alerce_and_stores_result(tmp_path) -> None:
    client = FakeAlerceClient()
    store = ParquetDetectionStore(tmp_path)
    backend = AlerceDetectionBackend(client, store)

    request = DetectionAcquisitionRequest(
        oid="ZTF_TEST",
        survey="ztf",
    )

    result = backend.acquire(request)

    assert result.cache_hit is False
    assert client.calls == [
        ("ZTF_TEST", "pandas", "ztf"),
    ]

    assert isinstance(result.detections, pd.DataFrame)
    assert isinstance(result.non_detections, pd.DataFrame)
    assert len(result.detections) == 2
    assert len(result.non_detections) == 1

    assert store.exists("ZTF_TEST") is True


def test_cache_hit_does_not_query_alerce(tmp_path) -> None:
    client = FakeAlerceClient()
    store = ParquetDetectionStore(tmp_path)
    backend = AlerceDetectionBackend(client, store)

    request = DetectionAcquisitionRequest(
        oid="ZTF_TEST",
        survey="ztf",
    )

    first = backend.acquire(request)
    second = backend.acquire(request)

    assert first.cache_hit is False
    assert second.cache_hit is True

    assert client.calls == [
        ("ZTF_TEST", "pandas", "ztf"),
    ]

    pd.testing.assert_frame_equal(
        first.detections,
        second.detections,
    )
    pd.testing.assert_frame_equal(
        first.non_detections,
        second.non_detections,
    )
