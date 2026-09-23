import json

import pandas as pd

from ztf_classifier.dataset.raw_validation import (
    RawDatasetValidator,
)

DETECTION_COLUMNS = (
    "tid",
    "mjd",
    "candid",
    "fid",
    "pid",
    "diffmaglim",
    "isdiffpos",
    "nid",
    "distnr",
    "magpsf",
    "magpsf_corr",
    "magpsf_corr_ext",
    "magap",
    "magap_corr",
    "sigmapsf",
    "sigmapsf_corr",
    "sigmapsf_corr_ext",
    "sigmagap",
    "sigmagap_corr",
    "ra",
    "dec",
    "rb",
    "rbversion",
    "drb",
    "magapbig",
    "sigmagapbig",
    "rfid",
    "has_stamp",
    "corrected",
    "dubious",
    "candid_alert",
    "step_id_corr",
    "phase",
    "parent_candid",
)

NON_DETECTION_COLUMNS = (
    "tid",
    "mjd",
    "fid",
    "diffmaglim",
)


def write_pair(tmp_path, oid, *, rows=2):
    detections = pd.DataFrame(
        {
            "tid": [1] * rows,
            "mjd": [1.0 + i for i in range(rows)],
            "candid": list(range(rows)),
            "fid": [1] * rows,
            "pid": [1] * rows,
            "diffmaglim": [20.0] * rows,
            "isdiffpos": ["t"] * rows,
            "nid": [1] * rows,
            "distnr": [1.0] * rows,
            "magpsf": [20.0] * rows,
            "magpsf_corr": [20.0] * rows,
            "magpsf_corr_ext": [20.0] * rows,
            "magap": [20.0] * rows,
            "magap_corr": [20.0] * rows,
            "sigmapsf": [0.1] * rows,
            "sigmapsf_corr": [0.1] * rows,
            "sigmapsf_corr_ext": [0.1] * rows,
            "sigmagap": [0.1] * rows,
            "sigmagap_corr": [0.1] * rows,
            "ra": [1.0] * rows,
            "dec": [1.0] * rows,
            "rb": [1.0] * rows,
            "rbversion": ["x"] * rows,
            "drb": [1.0] * rows,
            "magapbig": [20.0] * rows,
            "sigmagapbig": [0.1] * rows,
            "rfid": [1] * rows,
            "has_stamp": [True] * rows,
            "corrected": [True] * rows,
            "dubious": [False] * rows,
            "candid_alert": [1] * rows,
            "step_id_corr": [1] * rows,
            "phase": [0.0] * rows,
            "parent_candid": [1] * rows,
        }
    )

    non_detections = pd.DataFrame(
        {
            "tid": [1],
            "mjd": [10.0],
            "fid": [1],
            "diffmaglim": [21.0],
        }
    )

    detections.to_parquet(
        tmp_path / f"{oid}_detections.parquet",
        index=False,
    )
    non_detections.to_parquet(
        tmp_path / f"{oid}_non_detections.parquet",
        index=False,
    )


def test_valid_raw_dataset_passes(tmp_path):
    write_pair(tmp_path, "ZTF_A", rows=12)

    result = RawDatasetValidator(
        canonical_oids={"ZTF_A"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "PASS"
    assert result.missing_oids == ()
    assert result.extra_oids == ()
    assert result.incomplete_pairs == ()
    assert result.detection_row_statistics["count"] == 1
    assert result.detection_row_statistics["min"] == 12


def test_missing_canonical_oid_fails(tmp_path):
    result = RawDatasetValidator(
        canonical_oids={"ZTF_MISSING"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "FAIL"
    assert result.missing_oids == ("ZTF_MISSING",)


def test_extra_oid_is_reported_but_does_not_fail(tmp_path):
    write_pair(tmp_path, "ZTF_CANONICAL", rows=12)
    write_pair(tmp_path, "ZTF_EXTRA", rows=12)

    result = RawDatasetValidator(
        canonical_oids={"ZTF_CANONICAL"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "PASS"
    assert result.extra_oids == ("ZTF_EXTRA",)


def test_incomplete_pair_fails(tmp_path):
    oid = "ZTF_PARTIAL"

    pd.DataFrame({"mjd": [1.0], "fid": [1]}).to_parquet(
        tmp_path / f"{oid}_detections.parquet",
        index=False,
    )

    result = RawDatasetValidator(
        canonical_oids={oid},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "FAIL"
    assert result.incomplete_pairs == (oid,)


def test_schema_mismatch_fails(tmp_path):
    oid = "ZTF_BAD_SCHEMA"

    write_pair(tmp_path, oid, rows=12)

    path = tmp_path / f"{oid}_detections.parquet"
    frame = pd.read_parquet(path).drop(columns=["magpsf"])

    frame.to_parquet(path, index=False)

    result = RawDatasetValidator(
        canonical_oids={oid},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "FAIL"
    assert any(
        "detection schema mismatch" in item
        for item in result.schema_mismatches
    )


def test_invalid_mjd_fails(tmp_path):
    oid = "ZTF_BAD_MJD"

    write_pair(tmp_path, oid, rows=12)

    path = tmp_path / f"{oid}_detections.parquet"
    frame = pd.read_parquet(path)
    frame.loc[0, "mjd"] = None
    frame.to_parquet(path, index=False)

    result = RawDatasetValidator(
        canonical_oids={oid},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "FAIL"
    assert any(
        "invalid detection mjd" in item
        for item in result.invalid_required_values
    )


def test_low_observation_objects_are_reported(tmp_path):
    write_pair(tmp_path, "ZTF_LOW", rows=4)

    result = RawDatasetValidator(
        canonical_oids={"ZTF_LOW"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "PASS"
    assert result.low_observation_objects_lt10 == ("ZTF_LOW",)
    assert result.low_observation_objects_lt30 == ("ZTF_LOW",)


def test_result_is_json_serializable(tmp_path):
    write_pair(tmp_path, "ZTF_JSON", rows=12)

    result = RawDatasetValidator(
        canonical_oids={"ZTF_JSON"},
        cache_dir=tmp_path,
    ).validate()

    payload = result.to_dict()
    encoded = json.dumps(payload)

    assert '"status": "PASS"' in encoded
