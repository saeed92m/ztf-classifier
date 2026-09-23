import pytest

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.selector import ObjectSelector

BENCHMARK_CLASSES = (
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


@pytest.fixture
def benchmark_config():
    return DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=BENCHMARK_CLASSES,
        probability_min=0.50,
        samples_per_class=10,
    )


def test_selector_returns_one_request_per_class(benchmark_config):
    requests = ObjectSelector(benchmark_config).requests()

    assert len(requests) == 15


def test_selector_preserves_class_order(benchmark_config):
    requests = ObjectSelector(benchmark_config).requests()

    assert tuple(r.class_name for r in requests) == BENCHMARK_CLASSES


def test_selector_builds_alerce_query_contract(benchmark_config):
    requests = ObjectSelector(benchmark_config).requests()

    first = requests[0]

    assert first.survey == "ZTF"
    assert first.classifier == "lc_classifier"
    assert first.class_name == "SNIa"
    assert first.probability == 0.50
    assert first.page_size == 10


def test_all_requests_share_selection_policy(benchmark_config):
    requests = ObjectSelector(benchmark_config).requests()

    assert {
        (r.survey, r.classifier, r.probability, r.page_size)
        for r in requests
    } == {
        ("ZTF", "lc_classifier", 0.50, 10)
    }


def test_requests_are_immutable(benchmark_config):
    request = ObjectSelector(benchmark_config).requests()[0]

    with pytest.raises((AttributeError, TypeError)):
        request.class_name = "AGN"
