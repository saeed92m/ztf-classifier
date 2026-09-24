from __future__ import annotations

import pandas as pd
import pytest

from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.alerce_object import AlerceObjectBackend


class FakeAlerceClient:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.calls: list[dict[str, object]] = []

    def query_objects(self, **kwargs):
        self.calls.append(kwargs)
        return self.frame.copy()


def test_alerce_object_backend_normalizes_label_provenance() -> None:
    client = FakeAlerceClient(
        pd.DataFrame(
            {
                "oid": ["ZTF_B", "ZTF_A"],
                "class": ["QSO", "QSO"],
                "classifier": ["lc_classifier", "lc_classifier"],
                "probability": [0.91, 0.99],
            }
        )
    )

    request = ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="QSO",
        probability=0.90,
        page_size=10,
        classifier_version="hierarchical_random_forest_1.0.0",
    )

    result = AlerceObjectBackend(client).acquire(request)
    frame = result.objects[0]

    assert client.calls == [
        {
            "classifier": "lc_classifier",
            "class_name": "QSO",
            "probability": 0.90,
            "page_size": 10,
            "format": "pandas",
        }
    ]

    assert frame["oid"].tolist() == ["ZTF_A", "ZTF_B"]
    assert frame["label_source"].tolist() == ["ALeRCE", "ALeRCE"]
    assert frame["label_type"].tolist() == ["classifier", "classifier"]
    assert frame["label_probability"].tolist() == [0.99, 0.91]
    assert frame["classifier_version"].tolist() == [
        "hierarchical_random_forest_1.0.0",
        "hierarchical_random_forest_1.0.0",
    ]
    assert frame["survey"].tolist() == ["ZTF", "ZTF"]


def test_alerce_object_backend_rejects_missing_api_columns() -> None:
    client = FakeAlerceClient(
        pd.DataFrame(
            {
                "oid": ["ZTF_A"],
                "class": ["QSO"],
                "classifier": ["lc_classifier"],
            }
        )
    )

    request = ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="QSO",
        probability=0.90,
        page_size=10,
    )

    with pytest.raises(ValueError, match="required columns"):
        AlerceObjectBackend(client).acquire(request)


def test_alerce_object_backend_rejects_invalid_probability() -> None:
    client = FakeAlerceClient(
        pd.DataFrame(
            {
                "oid": ["ZTF_A"],
                "class": ["QSO"],
                "classifier": ["lc_classifier"],
                "probability": ["not-a-number"],
            }
        )
    )

    request = ObjectSelectionRequest(
        survey="ZTF",
        classifier="lc_classifier",
        class_name="QSO",
        probability=0.90,
        page_size=10,
    )

    with pytest.raises(ValueError, match="invalid probabilities"):
        AlerceObjectBackend(client).acquire(request)
