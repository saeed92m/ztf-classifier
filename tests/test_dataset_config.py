import pytest

from ztf_classifier.dataset.config import DatasetConfig

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


def test_benchmark_config_contract():
    config = DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=BENCHMARK_CLASSES,
        probability_min=0.50,
        samples_per_class=10,
    )

    assert config.dataset_version == "benchmark_v0.2"
    assert config.survey == "ZTF"
    assert config.source == "ALeRCE"
    assert config.classifier == "lc_classifier"
    assert config.classes == BENCHMARK_CLASSES
    assert config.probability_min == 0.50
    assert config.samples_per_class == 10


def test_config_is_immutable():
    config = DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=BENCHMARK_CLASSES,
        probability_min=0.50,
        samples_per_class=10,
    )

    with pytest.raises((AttributeError, TypeError)):
        config.probability_min = 0.90


def test_duplicate_classes_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        DatasetConfig(
            dataset_version="benchmark_v0.2",
            survey="ZTF",
            source="ALeRCE",
            classifier="lc_classifier",
            classes=("SNIa", "SNIa"),
            probability_min=0.50,
            samples_per_class=10,
        )


@pytest.mark.parametrize(
    "probability",
    [-0.01, 1.01],
)
def test_probability_range_is_validated(probability):
    with pytest.raises(ValueError, match="probability"):
        DatasetConfig(
            dataset_version="benchmark_v0.2",
            survey="ZTF",
            source="ALeRCE",
            classifier="lc_classifier",
            classes=BENCHMARK_CLASSES,
            probability_min=probability,
            samples_per_class=10,
        )


def test_samples_per_class_must_be_positive():
    with pytest.raises(ValueError, match="samples_per_class"):
        DatasetConfig(
            dataset_version="benchmark_v0.2",
            survey="ZTF",
            source="ALeRCE",
            classifier="lc_classifier",
            classes=BENCHMARK_CLASSES,
            probability_min=0.50,
            samples_per_class=0,
        )


def test_expected_object_count():
    config = DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=BENCHMARK_CLASSES,
        probability_min=0.50,
        samples_per_class=10,
    )

    assert config.requested_object_count == 150


def test_selection_policy():
    config = DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=BENCHMARK_CLASSES,
        probability_min=0.50,
        samples_per_class=10,
    )

    policy = config.selection_policy()

    assert policy["probability"] == 0.50
    assert policy["samples_per_class"] == 10
    assert policy["classes"] == BENCHMARK_CLASSES
