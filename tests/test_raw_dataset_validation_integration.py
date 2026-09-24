from pathlib import Path

import pandas as pd

from ztf_classifier.dataset.raw_validation import RawDatasetValidator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "data/processed/benchmark_v0.2/features.parquet"
CACHE = PROJECT_ROOT / "data/raw/alerce"


def test_benchmark_v0_2_raw_dataset_validation() -> None:
    canonical_oids = set(
        pd.read_parquet(SOURCE)["oid"].astype(str)
    )

    result = RawDatasetValidator(
        canonical_oids=canonical_oids,
        cache_dir=CACHE,
    ).validate()

    assert result.passed

    assert result.canonical_objects == 150
    assert result.missing_oids == ()
    assert result.incomplete_pairs == ()
    assert result.schema_mismatches == ()
    assert result.invalid_required_values == ()

    assert result.fid_distribution == {
        "1": 142,
        "2": 142,
        "3": 44,
    }

    assert result.fid_set_distribution == {
        "1": 6,
        "1,2": 94,
        "1,2,3": 40,
        "1,3": 2,
        "2": 6,
        "2,3": 2,
    }

    assert result.ordering == {
        "detections_sorted_by_mjd": True,
        "non_detections_sorted_by_mjd": True,
        "detection_ordering_failures": (),
        "non_detection_ordering_failures": (),
    }

    assert result.detection_row_statistics == {
        "count": 150,
        "min": 4,
        "median": 74.0,
        "max": 1732,
        "mean": 189.63333333333333,
    }

    assert result.non_detection_row_statistics == {
        "count": 150,
        "min": 6,
        "median": 210.5,
        "max": 1918,
        "mean": 313.4266666666667,
    }

    assert len(result.low_observation_objects_lt10) == 1
    assert len(result.low_observation_objects_lt30) == 31

    assert result.corrected_statistics == {
        "corrected_true": 27379,
        "corrected_false": 1066,
    }
