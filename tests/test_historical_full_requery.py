from __future__ import annotations

import pandas as pd

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.selection import ObjectSelectionPolicy
from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
    ObjectAcquisitionResult,
)

CLASSES = (
    "SNIa",
    "SNIbc",
    "SNII",
    "SLSN",
    "QSO",
    "AGN",
    "Blazar",
    "CV/Nova",
    "YSO",
    "LPV",
    "E",
    "DSCT",
    "RRL",
    "CEP",
    "Periodic-Other",
)


def make_config(
    *,
    strategy: str,
    fallback_probability: float | None = 0.50,
) -> DatasetConfig:
    return DatasetConfig(
        dataset_version="test",
        survey="ztf",
        source="ALeRCE",
        classifier="lc_classifier",
        classifier_version="hierarchical_random_forest_1.0.0",
        classes=CLASSES,
        samples_per_class=10,
        probability_min=0.90,
        fallback_probability=fallback_probability,
        page_size=10,
        selection_strategy=strategy,
    )


def make_frame(
    class_name: str,
    probability: float,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "oid": [
                f"{class_name.replace('/', '_')}_{probability:.2f}_{i}"
                for i in range(10)
            ],
            "class": [class_name] * 10,
            "probability": [probability] * 10,
        }
    )


class RecordingBackend(ObjectAcquisitionBackend):
    def __init__(self) -> None:
        self.calls: list[ObjectSelectionRequest] = []

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        self.calls.append(request)

        return ObjectAcquisitionResult(
            request=request,
            objects=(
                make_frame(
                    request.class_name,
                    request.probability,
                ),
            ),
        )


class EmptyPrimaryBackend(ObjectAcquisitionBackend):
    def __init__(self) -> None:
        self.calls: list[ObjectSelectionRequest] = []

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        self.calls.append(request)

        if request.probability == 0.90:
            frame = pd.DataFrame(
                columns=["oid", "class", "probability"]
            )
        else:
            frame = make_frame(
                request.class_name,
                request.probability,
            )

        return ObjectAcquisitionResult(
            request=request,
            objects=(frame,),
        )


def test_historical_full_requery_matches_two_pass_contract() -> None:
    config = make_config(strategy="historical_full_requery")
    backend = RecordingBackend()

    result = ObjectSelectionPolicy(config).acquire_all(
        backend=backend,
    )

    assert len(backend.calls) == 30

    first_pass = backend.calls[:15]
    second_pass = backend.calls[15:]

    assert [call.class_name for call in first_pass] == list(CLASSES)
    assert [call.class_name for call in second_pass] == list(CLASSES)

    assert all(call.probability == 0.90 for call in first_pass)
    assert all(call.probability == 0.50 for call in second_pass)

    assert all(call.page_size == 10 for call in backend.calls)
    assert all(call.survey == "ztf" for call in backend.calls)
    assert all(call.classifier == "lc_classifier" for call in backend.calls)

    assert len(result) == 150
    assert result["class"].value_counts().to_dict() == {
        class_name: 10 for class_name in CLASSES
    }

    assert result["class"].tolist() == [
        class_name
        for class_name in CLASSES
        for _ in range(10)
    ]


def test_strict_primary_does_not_requery_at_fallback() -> None:
    config = make_config(
        strategy="strict_primary",
        fallback_probability=0.50,
    )
    backend = RecordingBackend()

    result = ObjectSelectionPolicy(config).acquire_all(
        backend=backend,
    )

    assert len(backend.calls) == 15
    assert all(call.probability == 0.90 for call in backend.calls)
    assert len(result) == 150


def test_fallback_on_empty_only_requeries_empty_classes() -> None:
    config = make_config(strategy="fallback_on_empty")
    backend = EmptyPrimaryBackend()

    result = ObjectSelectionPolicy(config).acquire_all(
        backend=backend,
    )

    assert len(backend.calls) == 30

    for index, class_name in enumerate(CLASSES):
        primary = backend.calls[index * 2]
        fallback = backend.calls[index * 2 + 1]

        assert primary.class_name == class_name
        assert fallback.class_name == class_name

        assert primary.probability == 0.90
        assert fallback.probability == 0.50

        assert primary.page_size == 10
        assert fallback.page_size == 10

    assert len(result) == 150
    assert result["class"].value_counts().to_dict() == {
        class_name: 10 for class_name in CLASSES
    }
