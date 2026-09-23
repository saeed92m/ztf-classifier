import pandas as pd
import pytest

from ztf_classifier.dataset.manifest import ObjectManifest


def make_objects() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "oid": ["ZTF_1", "ZTF_2"],
            "class": ["SNIa", "QSO"],
            "classifier": ["lc_classifier", "lc_classifier"],
            "probability": [0.500001, 0.501002],
            "label_source": ["ALeRCE", "ALeRCE"],
            "label_type": ["benchmark", "benchmark"],
            "label_probability": [0.500001, 0.501002],
            "classifier_version": [
                "hierarchical_random_forest_1.0.0",
                "hierarchical_random_forest_1.0.0",
            ],
            "survey": ["ZTF", "ZTF"],
        }
    )


def test_manifest_preserves_object_level_probability() -> None:
    objects = make_objects()

    manifest = ObjectManifest(
        objects=objects,
        dataset_version="benchmark_v0.2",
        probability_min=0.50,
        samples_per_class=1,
    )

    assert manifest.object_count == 2
    assert manifest.objects.loc[0, "label_probability"] == 0.500001


def test_manifest_reports_classes_and_counts() -> None:
    manifest = ObjectManifest(
        objects=make_objects(),
        dataset_version="benchmark_v0.2",
        probability_min=0.50,
        samples_per_class=1,
    )

    assert manifest.classes == ("QSO", "SNIa")
    assert manifest.class_counts.to_dict() == {
        "QSO": 1,
        "SNIa": 1,
    }


def test_manifest_rejects_duplicate_oids() -> None:
    objects = make_objects()
    objects.loc[1, "oid"] = "ZTF_1"

    with pytest.raises(ValueError, match="duplicate OIDs"):
        ObjectManifest(
            objects=objects,
            dataset_version="benchmark_v0.2",
            probability_min=0.50,
            samples_per_class=1,
        )


def test_manifest_rejects_missing_columns() -> None:
    objects = make_objects().drop(columns=["classifier_version"])

    with pytest.raises(ValueError, match="missing columns"):
        ObjectManifest(
            objects=objects,
            dataset_version="benchmark_v0.2",
            probability_min=0.50,
            samples_per_class=1,
        )
