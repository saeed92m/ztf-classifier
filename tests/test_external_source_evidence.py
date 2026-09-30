import pandas as pd
import pytest

from scripts.acquire_external_source_evidence import SourceQueryError, _prepare_alerce_frame, _validate


def test_external_source_validation_accepts_exact_sorted_subset():
    frame = pd.DataFrame(
        {
            "objectid": ["ZTF1", "ZTF2", "ZTF3"],
            "objra": [1.0, 2.0, 3.0],
            "objdec": [0.0, 1.0, 2.0],
            "nepochs": [10, 11, 12],
        }
    )
    _validate(frame, ["objectid", "objra", "objdec", "nepochs"], "objectid", 3)


@pytest.mark.parametrize(
    "frame, message",
    [
        (pd.DataFrame({"objectid": ["ZTF1", "ZTF1"]}), "duplicate"),
        (pd.DataFrame({"objectid": ["ZTF2", "ZTF1"]}), "not deterministically sorted"),
        (pd.DataFrame({"objectid": ["ZTF1"]}), "expected exactly"),
    ],
)
def test_external_source_validation_fails_closed(frame, message):
    with pytest.raises(SourceQueryError, match=message):
        _validate(frame, ["objectid"], "objectid", 2)


def test_alerce_preparation_deduplicates_versions_before_truncation():
    rows = [
        {"oid": "ZTF0002", "classifier_version": "2.0", "class_name": "A", "probability": 0.9, "classifier_name": "lc_classifier"},
        {"oid": "ZTF0001", "classifier_version": "1.0", "class_name": "B", "probability": 0.7, "classifier_name": "lc_classifier"},
        {"oid": "ZTF0001", "classifier_version": "2.0", "class_name": "B", "probability": 0.8, "classifier_name": "lc_classifier"},
        {"oid": "ZTF0003", "classifier_version": "1.0", "class_name": "C", "probability": 0.6, "classifier_name": "lc_classifier"},
    ]
    frame = pd.DataFrame(rows)
    expected = ["oid", "class_name", "probability", "classifier_name", "classifier_version"]

    prepared = _prepare_alerce_frame(frame, expected, "oid", 3)

    assert prepared["oid"].tolist() == ["ZTF0001", "ZTF0002", "ZTF0003"]
    assert prepared.loc[0, "classifier_version"] == "2.0"
