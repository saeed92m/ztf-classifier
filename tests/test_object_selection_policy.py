from dataclasses import dataclass

import pandas as pd

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
    probability_min=0.90,
    fallback_probability=0.50,
    samples_per_class=10,
    page_size=10,
)


@dataclass
class FakeBackend(ObjectAcquisitionBackend):
    """Backend returning configured results and recording requests."""

    responses: dict[tuple[str, float], pd.DataFrame]
    calls: list[ObjectSelectionRequest]

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        self.calls.append(request)

        frame = self.responses.get(
            (request.class_name, request.probability),
            pd.DataFrame(),
        )

        return ObjectAcquisitionResult(
            request=request,
            objects=(frame,),
        )


def make_frame(*oids: str) -> pd.DataFrame:
    return pd.DataFrame({"oid": list(oids)})


def test_primary_result_is_used_without_fallback() -> None:
    from ztf_classifier.dataset.selection import ObjectSelectionPolicy

    backend = FakeBackend(
        responses={
            ("SNIa", 0.90): make_frame(
                *[f"PRIMARY_{i:02d}" for i in range(10)]
            ),
        },
        calls=[],
    )

    policy = ObjectSelectionPolicy(BENCHMARK_CONFIG)

    result = policy.acquire_class(
        class_name="SNIa",
        backend=backend,
    )

    assert len(result) == 10
    assert len(backend.calls) == 1
    assert backend.calls[0].probability == 0.90


def test_empty_primary_result_triggers_fallback() -> None:
    from ztf_classifier.dataset.selection import ObjectSelectionPolicy

    backend = FakeBackend(
        responses={
            ("SNIa", 0.90): pd.DataFrame(),
            ("SNIa", 0.50): make_frame(
                *[f"FALLBACK_{i:02d}" for i in range(10)]
            ),
        },
        calls=[],
    )

    policy = ObjectSelectionPolicy(BENCHMARK_CONFIG)

    result = policy.acquire_class(
        class_name="SNIa",
        backend=backend,
    )

    assert len(result) == 10
    assert tuple(result["oid"]) == tuple(
        f"FALLBACK_{i:02d}" for i in range(10)
    )

    assert len(backend.calls) == 2
    assert backend.calls[0].probability == 0.90
    assert backend.calls[1].probability == 0.50


def test_fallback_is_not_used_when_disabled() -> None:
    config = DatasetConfig(
        dataset_version="test",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=("SNIa",),
        probability_min=0.90,
        fallback_probability=None,
        samples_per_class=10,
    )

    from ztf_classifier.dataset.selection import ObjectSelectionPolicy

    backend = FakeBackend(
        responses={
            ("SNIa", 0.90): pd.DataFrame(),
            ("SNIa", 0.50): make_frame("SHOULD_NOT_BE_USED"),
        },
        calls=[],
    )

    policy = ObjectSelectionPolicy(config)

    result = policy.acquire_class(
        class_name="SNIa",
        backend=backend,
    )

    assert result.empty
    assert len(backend.calls) == 1
    assert backend.calls[0].probability == 0.90


def test_fallback_result_is_capped_to_requested_sample_count() -> None:
    from ztf_classifier.dataset.selection import ObjectSelectionPolicy

    backend = FakeBackend(
        responses={
            ("SNIa", 0.90): pd.DataFrame(),
            ("SNIa", 0.50): make_frame(
                *[f"OID_{i:02d}" for i in range(20)]
            ),
        },
        calls=[],
    )

    policy = ObjectSelectionPolicy(BENCHMARK_CONFIG)

    result = policy.acquire_class(
        class_name="SNIa",
        backend=backend,
    )

    assert len(result) == 10
    assert tuple(result["oid"]) == tuple(
        f"OID_{i:02d}" for i in range(10)
    )


def test_fallback_policy_preserves_request_contract() -> None:
    from ztf_classifier.dataset.selection import ObjectSelectionPolicy

    backend = FakeBackend(
        responses={
            ("SNIa", 0.90): pd.DataFrame(),
            ("SNIa", 0.50): make_frame(
                *[f"OID_{i:02d}" for i in range(10)]
            ),
        },
        calls=[],
    )

    policy = ObjectSelectionPolicy(BENCHMARK_CONFIG)

    policy.acquire_class(
        class_name="SNIa",
        backend=backend,
    )

    assert backend.calls[0] == ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="SNIa",
        probability=0.90,
        page_size=10,
    )

    assert backend.calls[1] == ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="SNIa",
        probability=0.50,
        page_size=10,
    )
