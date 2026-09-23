from dataclasses import dataclass

from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionRequest,
    DetectionAcquisitionResult,
)


@dataclass(frozen=True)
class FakeBackend(DetectionAcquisitionBackend):
    """Minimal backend used only to test the acquisition contract."""

    def acquire(
        self,
        request: DetectionAcquisitionRequest,
    ) -> DetectionAcquisitionResult:
        return DetectionAcquisitionResult(
            request=request,
            detections=(),
            non_detections=(),
            cache_hit=False,
        )


def test_detection_acquisition_contract() -> None:
    request = DetectionAcquisitionRequest(
        oid="ZTF_TEST",
        survey="ZTF",
    )

    result = FakeBackend().acquire(request)

    assert result.request == request
    assert result.detections == ()
    assert result.non_detections == ()
    assert result.cache_hit is False


def test_detection_acquisition_request_is_immutable() -> None:
    request = DetectionAcquisitionRequest(
        oid="ZTF_TEST",
        survey="ZTF",
    )

    try:
        request.oid = "OTHER"
    except AttributeError:
        pass
    else:
        raise AssertionError("Request must be immutable")
