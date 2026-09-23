import pandas as pd
import pytest

from ztf_classifier.dataset.builder import ObjectManifestBuilder
from ztf_classifier.dataset.config import DatasetConfig


def make_config() -> DatasetConfig:
    return DatasetConfig(
        dataset_version="benchmark_v0.2",
        survey="ZTF",
        source="ALeRCE",
        classifier="lc_classifier",
        classes=("QSO", "SNIa"),
        probability_min=0.50,
        samples_per_class=1,
    )


def make_objects() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "oid": ["ZTF_2", "ZTF_1"],
            "class": ["QSO", "SNIa"],
            "classifier": ["lc_classifier", "lc_classifier"],
            "probability": [0.501002, 0.500001],
            "label_source": ["ALeRCE", "ALeRCE"],
            "label_type": ["benchmark", "benchmark"],
            "label_probability": [0.501002, 0.500001],
            "classifier_version": [
                "hierarchical_random_forest_1.0.0",
                "hierarchical_random_forest_1.0.0",
            ],
            "survey": ["ZTF", "ZTF"],
            "extra_column": ["ignored", "ignored"],
        }
    )


def test_builder_returns_canonical_manifest() -> None:
    manifest = ObjectManifestBuilder(make_config()).build(
        make_objects()
    )

    assert manifest.object_count == 2
    assert manifest.objects.columns.tolist() == [
        "oid",
        "class",
        "classifier",
        "probability",
        "label_source",
        "label_type",
        "label_probability",
        "classifier_version",
        "survey",
    ]


def test_builder_sorts_by_oid() -> None:
    manifest = ObjectManifestBuilder(make_config()).build(
        make_objects()
    )

    assert manifest.objects["oid"].tolist() == [
        "ZTF_1",
        "ZTF_2",
    ]


def test_builder_preserves_probability() -> None:
    manifest = ObjectManifestBuilder(make_config()).build(
        make_objects()
    )

    assert manifest.objects["probability"].tolist() == [
        0.500001,
        0.501002,
    ]


def test_builder_rejects_missing_columns() -> None:
    objects = make_objects().drop(columns=["label_source"])

    with pytest.raises(ValueError, match="missing columns"):
        ObjectManifestBuilder(make_config()).build(objects)
