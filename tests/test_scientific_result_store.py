from pathlib import Path

import pytest

from ztf_classifier.results import ScientificResultStore


def test_save_and_get_round_trip(tmp_path: Path) -> None:
    store = ScientificResultStore(tmp_path / "results.sqlite3")
    payload = {
        "schema_version": "1.0",
        "oid": "ZTF17test",
        "features": {"amplitude": 1.2},
        "prediction": {"predicted_class": "AGN"},
    }

    record = store.save(
        job_id="job-1",
        oid="ZTF17test",
        survey="ztf",
        model_version="baseline_v0.2",
        payload=payload,
    )

    assert store.get(record.result_id) == record
    assert store.get_by_job_id("job-1") == record
    assert record.payload == payload


def test_save_is_idempotent_for_same_job(tmp_path: Path) -> None:
    store = ScientificResultStore(tmp_path / "results.sqlite3")
    kwargs = {
        "job_id": "job-1",
        "oid": "ZTF17test",
        "survey": "ztf",
        "model_version": "baseline_v0.2",
        "payload": {"prediction": {"predicted_class": "AGN"}},
    }

    first = store.save(**kwargs)
    second = store.save(**kwargs)

    assert second == first


def test_save_rejects_conflicting_retry(tmp_path: Path) -> None:
    store = ScientificResultStore(tmp_path / "results.sqlite3")
    store.save(
        job_id="job-1",
        oid="ZTF17test",
        survey="ztf",
        model_version="baseline_v0.2",
        payload={"value": 1},
    )

    with pytest.raises(ValueError, match="already exists"):
        store.save(
            job_id="job-1",
            oid="ZTF17test",
            survey="ztf",
            model_version="baseline_v0.2",
            payload={"value": 2},
        )


def test_missing_result_is_key_error(tmp_path: Path) -> None:
    store = ScientificResultStore(tmp_path / "results.sqlite3")

    with pytest.raises(KeyError):
        store.get("missing")


def test_latest_result_for_object(tmp_path: Path) -> None:
    store = ScientificResultStore(tmp_path / "results.sqlite3")
    first = store.save(
        job_id="job-1",
        oid="ZTF17test",
        survey="ztf",
        model_version="baseline_v0.2",
        payload={"value": 1},
    )
    latest = store.save(
        job_id="job-2",
        oid="ZTF17test",
        survey="ztf",
        model_version="baseline_v0.2",
        payload={"value": 2},
    )

    assert store.latest_for_object("ZTF17test").result_id == latest.result_id
    assert first.result_id != latest.result_id

def test_latest_result_for_missing_object_returns_none(tmp_path: Path) -> None:
    store = ScientificResultStore(tmp_path / "results.sqlite3")

    assert store.latest_for_object("missing") is None

