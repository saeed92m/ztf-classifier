from pathlib import Path

import pytest

from ztf_classifier.dataset.config import DatasetConfig

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


def test_benchmark_json_loads() -> None:
    config = DatasetConfig.from_json(CONFIG_PATH)

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

    assert config.requested_object_count == 150


def test_benchmark_json_selection_policy_is_historical() -> None:
    config = DatasetConfig.from_json(CONFIG_PATH)

    policy = config.selection_policy()

    assert policy["probability"] == 0.90
    assert policy["fallback_probability"] == 0.50
    assert policy["samples_per_class"] == 10
    assert policy["page_size"] == 10
    assert policy["classes"] == EXPECTED_CLASSES


def test_from_dict_converts_classes_to_tuple() -> None:
    config = DatasetConfig.from_dict(
        {
            "dataset_version": "test",
            "survey": "ztf",
            "source": "ALeRCE",
            "classifier": "lc_classifier",
            "classes": ["A", "B"],
            "samples_per_class": 2,
            "probability_min": 0.9,
        }
    )

    assert config.classes == ("A", "B")


def test_missing_required_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing required"):
        DatasetConfig.from_dict(
            {
                "dataset_version": "test",
                "survey": "ztf",
            }
        )


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        DatasetConfig.from_json(path)


def test_missing_json_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        DatasetConfig.from_json(path)
