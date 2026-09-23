from __future__ import annotations

import json
from pathlib import Path

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.selection import ObjectSelectionPolicy
from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.object_acquisition import (
    ObjectAcquisitionBackend,
    ObjectAcquisitionResult,
)

CONFIG_PATH = Path("configs/datasets/benchmark_v0.2.json")

EXPECTED_CLASSES = (
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


class ContractBackend(ObjectAcquisitionBackend):
    """Deterministic backend for configuration-contract testing."""

    def __init__(self) -> None:
        self.requests: list[ObjectSelectionRequest] = []

    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        import pandas as pd

        self.requests.append(request)

        probability = request.probability
        class_name = request.class_name

        frame = pd.DataFrame(
            {
                "oid": [
                    f"{class_name.replace('/', '_')}_{probability:.2f}_{i}"
                    for i in range(request.page_size)
                ],
                "class": [class_name] * request.page_size,
                "probability": [probability] * request.page_size,
            }
        )

        return ObjectAcquisitionResult(
            request=request,
            objects=(frame,),
        )


def load_config() -> DatasetConfig:
    payload = json.loads(
        CONFIG_PATH.read_text(encoding="utf-8")
    )
    return DatasetConfig.from_dict(payload)


def test_benchmark_v0_2_config_matches_frozen_contract() -> None:
    config = load_config()

    assert config.dataset_version == "benchmark_v0.2"
    assert config.survey == "ztf"
    assert config.source == "ALeRCE"
    assert config.classifier == "lc_classifier"
    assert config.classifier_version == (
        "hierarchical_random_forest_1.0.0"
    )

    assert config.classes == EXPECTED_CLASSES
    assert config.samples_per_class == 10
    assert config.probability_min == 0.90
    assert config.fallback_probability == 0.50
    assert config.page_size == 10
    assert config.effective_page_size == 10

    assert config.selection_strategy == (
        "historical_full_requery"
    )

    assert config.requested_object_count == 150


def test_benchmark_v0_2_selection_policy_executes_two_pass_contract() -> None:
    config = load_config()
    backend = ContractBackend()

    result = ObjectSelectionPolicy(config).acquire_all(
        backend=backend,
    )

    assert len(backend.requests) == 30

    first_pass = backend.requests[:15]
    second_pass = backend.requests[15:]

    assert [request.class_name for request in first_pass] == list(
        EXPECTED_CLASSES
    )
    assert [request.class_name for request in second_pass] == list(
        EXPECTED_CLASSES
    )

    assert all(
        request.probability == 0.90
        for request in first_pass
    )
    assert all(
        request.probability == 0.50
        for request in second_pass
    )

    assert all(
        request.survey == "ztf"
        for request in backend.requests
    )
    assert all(
        request.classifier == "lc_classifier"
        for request in backend.requests
    )
    assert all(
        request.page_size == 10
        for request in backend.requests
    )

    assert len(result) == 150

    counts = result["class"].value_counts().to_dict()

    assert counts == {
        class_name: 10
        for class_name in EXPECTED_CLASSES
    }

    assert result["class"].tolist() == [
        class_name
        for class_name in EXPECTED_CLASSES
        for _ in range(10)
    ]
