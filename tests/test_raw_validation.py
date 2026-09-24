from __future__ import annotations

import pandas as pd

from ztf_classifier.dataset.raw_validation import RawDatasetValidator


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


def _write_pair(cache_dir, oid: str, *, reverse: bool = False) -> None:
    detections = pd.DataFrame(
        {
            column: [1, 2]
            for column in DETECTION_COLUMNS
        }
    )
    detections["mjd"] = [2.0, 1.0] if reverse else [1.0, 2.0]
    detections["fid"] = [1, 2]
    detections["corrected"] = [True, True]
    detections["dubious"] = [False, False]

    non_detections = pd.DataFrame(
        {
            "tid": [1],
            "mjd": [3.0],
            "fid": [1],
            "diffmaglim": [20.0],
        }
    )

    detections.to_parquet(
        cache_dir / f"{oid}_detections.parquet",
        index=False,
    )
    non_detections.to_parquet(
        cache_dir / f"{oid}_non_detections.parquet",
        index=False,
    )


def test_extra_cache_object_is_a_validation_failure(tmp_path) -> None:
    _write_pair(tmp_path, "ZTF_A")
    _write_pair(tmp_path, "ZTF_EXTRA")

    result = RawDatasetValidator(
        canonical_oids={"ZTF_A"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "FAIL"
    assert result.extra_oids == ("ZTF_EXTRA",)
    assert any("ZTF_EXTRA" in error for error in result.errors)


def test_detection_ordering_violation_is_a_validation_failure(tmp_path) -> None:
    _write_pair(tmp_path, "ZTF_A", reverse=True)

    result = RawDatasetValidator(
        canonical_oids={"ZTF_A"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "FAIL"
    assert result.ordering["detection_ordering_failures"] == ("ZTF_A",)
    assert any("not sorted by mjd" in error for error in result.errors)


def test_valid_raw_cache_passes(tmp_path) -> None:
    _write_pair(tmp_path, "ZTF_A")

    result = RawDatasetValidator(
        canonical_oids={"ZTF_A"},
        cache_dir=tmp_path,
    ).validate()

    assert result.status == "PASS"
    assert result.missing_oids == ()
    assert result.extra_oids == ()
    assert result.incomplete_pairs == ()
    assert result.errors == ()
