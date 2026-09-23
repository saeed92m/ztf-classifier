from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
    FeatureDatasetBuilder,
)
from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.io.parquet_detection import ParquetDetectionBackend

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ARTIFACT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "benchmark_v0.2"
    / "features.parquet"
)

RAW_CACHE = PROJECT_ROOT / "data" / "raw" / "alerce"


def test_offline_feature_dataset_reproduces_frozen_v0_2() -> None:
    source = pd.read_parquet(SOURCE_ARTIFACT)

    metadata_columns = list(FEATURE_DATASET_METADATA_COLUMNS)

    manifest = ObjectManifest(
        objects=source[metadata_columns].copy(),
        dataset_version="benchmark_v0.2",
        probability_min=0.9,
        samples_per_class=10,
    )

    backend = ParquetDetectionBackend(RAW_CACHE)

    dataset = FeatureDatasetBuilder(
        manifest=manifest,
        acquisition_backend=backend,
        feature_schema_version="v0.2",
    ).build()

    expected = source.sort_values("oid").reset_index(drop=True)
    actual = dataset.data.sort_values("oid").reset_index(drop=True)

    assert dataset.object_count == 150
    assert dataset.feature_count == 42
    assert actual.shape == (150, 51)

    assert_frame_equal(
        actual[metadata_columns],
        expected[metadata_columns],
        check_dtype=True,
        check_exact=True,
    )

    feature_columns = list(
        expected.columns[len(metadata_columns):]
    )

    assert feature_columns == list(
        actual.columns[len(metadata_columns):]
    )

    assert_frame_equal(
        actual[feature_columns],
        expected[feature_columns],
        check_dtype=False,
        check_exact=False,
        rtol=0.0,
        atol=1e-10,
    )
