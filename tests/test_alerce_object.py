from dataclasses import dataclass

import pandas as pd

from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.alerce_object import AlerceObjectBackend


@dataclass
class FakeAlerceClient:
    calls: list[dict]

    def query_objects(self, **kwargs):
        self.calls.append(kwargs)

        return pd.DataFrame(
            {
                "oid": ["ZTF_TEST_001", "ZTF_TEST_002"],
                "probability": [0.91, 0.95],
            }
        )


def test_alerce_object_backend_preserves_selection_request() -> None:
    client = FakeAlerceClient(calls=[])
    backend = AlerceObjectBackend(client)

    request = ObjectSelectionRequest(
        survey="ztf",
        classifier="lc_classifier",
        class_name="SNIa",
        probability=0.50,
        page_size=10,
    )

    result = backend.acquire(request)

    assert result.request == request
    assert len(result.objects) == 1
    assert isinstance(result.objects[0], pd.DataFrame)


def test_alerce_object_backend_calls_api_with_exact_parameters() -> None:
    client = FakeAlerceClient(calls=[])
    backend = AlerceObjectBackend(client)

    request = ObjectSelectionRequest(
        survey="ztf",
        classifier="lc_classifier",
        class_name="QSO",
        probability=0.50,
        page_size=10,
    )

    backend.acquire(request)

    assert client.calls == [
        {
            "survey": "ztf",
            "classifier": "lc_classifier",
            "class_name": "QSO",
            "probability": 0.50,
            "page_size": 10,
            "format": "pandas",
        }
    ]
