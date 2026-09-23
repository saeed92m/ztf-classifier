import pandas as pd
import pytest

from ztf_classifier.io.parquet_detection_store import ParquetDetectionStore


def test_paths_follow_historical_cache_contract(tmp_path) -> None:
    store = ParquetDetectionStore(tmp_path)

    paths = store.paths("ZTF_TEST")

    assert paths.detections == tmp_path / "ZTF_TEST_detections.parquet"
    assert paths.non_detections == tmp_path / "ZTF_TEST_non_detections.parquet"


def test_missing_cache_is_not_a_cache_hit(tmp_path) -> None:
    store = ParquetDetectionStore(tmp_path)

    assert store.exists("ZTF_TEST") is False


def test_partial_cache_is_not_a_cache_hit(tmp_path) -> None:
    store = ParquetDetectionStore(tmp_path)

    detections = pd.DataFrame({"mjd": [1.0]})
    detections.to_parquet(
        tmp_path / "ZTF_TEST_detections.parquet",
        index=False,
    )

    assert store.exists("ZTF_TEST") is False


def test_save_and_load_round_trip(tmp_path) -> None:
    store = ParquetDetectionStore(tmp_path)

    detections = pd.DataFrame(
        {
            "mjd": [1.0, 2.0],
            "magpsf": [19.1, 19.2],
        }
    )
    non_detections = pd.DataFrame(
        {
            "mjd": [3.0],
            "diffmaglim": [20.1],
        }
    )

    store.save(
        "ZTF_TEST",
        detections,
        non_detections,
    )

    assert store.exists("ZTF_TEST") is True

    loaded_detections, loaded_non_detections = store.load("ZTF_TEST")

    pd.testing.assert_frame_equal(
        loaded_detections,
        detections,
    )
    pd.testing.assert_frame_equal(
        loaded_non_detections,
        non_detections,
    )


def test_load_rejects_missing_cache(tmp_path) -> None:
    store = ParquetDetectionStore(tmp_path)

    with pytest.raises(FileNotFoundError):
        store.load("ZTF_TEST")
