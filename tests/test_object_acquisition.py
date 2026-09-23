from dataclasses import dataclass

import pytest

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
    ObjectAcquisitionResult,
)

BENCHMARK_CONFIG = DatasetConfig(
    dataset_version="benchmark_v0.2",
    survey="ZTF",
    source="ALeRCE",
    classifier="lc_classifier",
    classes=("SNIa",),
    probability_min=0.50,
    samples_per_class=10,
)


@dataclass(frozen=True)
class FakeBackend(ObjectAcquisitionBackend):
    """Minimal backend used only to test the acquisition contract."""

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        return ObjectAcquisitionResult(
            request=request,
            objects=(),
        )


def test_acquisition_result_is_immutable():
    request = ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="SNIa",
        probability=0.50,
        page_size=10,
    )

    result = ObjectAcquisitionResult(
        request=request,
        objects=(),
    )

    with pytest.raises((AttributeError, TypeError)):
        result.objects = ("OID",)


def test_fake_backend_implements_acquisition_contract():
    backend = FakeBackend()

    request = ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="SNIa",
        probability=0.50,
        page_size=10,
    )

    result = backend.acquire(request)

    assert isinstance(result, ObjectAcquisitionResult)
    assert result.request == request
    assert result.objects == ()


def test_backend_receives_selection_request():
    backend = FakeBackend()

    request = ObjectSelectionRequest(
        survey=BENCHMARK_CONFIG.survey,
        classifier=BENCHMARK_CONFIG.classifier,
        class_name="SNIa",
        probability=BENCHMARK_CONFIG.probability_min,
        page_size=BENCHMARK_CONFIG.samples_per_class,
    )

    result = backend.acquire(request)

    assert result.request.class_name == "SNIa"
    assert result.request.probability == 0.50
    assert result.request.page_size == 10
