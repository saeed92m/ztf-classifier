import pandas as pd
import pytest

from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.dataset.validation import (
    validate_against_historical_objects,
)


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


def make_manifest(objects: pd.DataFrame) -> ObjectManifest:
    return ObjectManifest(
        objects=objects,
        dataset_version="benchmark_v0.2",
        probability_min=0.50,
        samples_per_class=1,
    )


def test_matching_manifest_passes() -> None:
    objects = make_objects()

    validate_against_historical_objects(
        make_manifest(objects.copy()),
        objects.copy(),
    )


def test_oid_mismatch_is_rejected() -> None:
    objects = make_objects()
    manifest_objects = objects.copy()
    manifest_objects.loc[0, "oid"] = "ZTF_OTHER"

    with pytest.raises(ValueError, match="OIDs"):
        validate_against_historical_objects(
            make_manifest(manifest_objects),
            objects,
        )


def test_class_mismatch_is_rejected() -> None:
    objects = make_objects()
    manifest_objects = objects.copy()
    manifest_objects.loc[0, "class"] = "SNII"

    with pytest.raises(ValueError, match="class"):
        validate_against_historical_objects(
            make_manifest(manifest_objects),
            objects,
        )


def test_probability_mismatch_is_rejected() -> None:
    objects = make_objects()
    manifest_objects = objects.copy()
    manifest_objects.loc[0, "probability"] = 0.501

    with pytest.raises(ValueError, match="probability"):
        validate_against_historical_objects(
            make_manifest(manifest_objects),
            objects,
        )


def test_probability_mismatch_is_rejected_before_consistency_check() -> None:
    objects = make_objects()
    historical = objects.copy()
    historical.loc[0, "label_probability"] = 0.999

    with pytest.raises(
        ValueError,
        match="Manifest column does not match historical artifact: label_probability",
    ):
        validate_against_historical_objects(
            make_manifest(objects),
            historical,
        )
