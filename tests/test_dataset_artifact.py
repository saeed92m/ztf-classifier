from pathlib import Path

import pandas as pd

from ztf_classifier.dataset.artifact import (
    DatasetArtifactWriter,
    sha256_dataframe,
    sha256_file,
)
from ztf_classifier.dataset.features import (
    FEATURE_DATASET_METADATA_COLUMNS,
    FeatureDataset,
)
from ztf_classifier.features.pipeline import V0_2_FEATURES


def make_dataset() -> FeatureDataset:
    row = {
        column: 0.0
        for column in V0_2_FEATURES
    }

    metadata = {
        "oid": "ZTF_TEST",
        "class": "SNIa",
        "classifier": "lc_classifier",
        "probability": 0.5,
        "label_source": "ALeRCE",
        "label_type": "benchmark",
        "label_probability": 0.5,
        "classifier_version": "hierarchical_random_forest_1.0.0",
        "survey": "ZTF",
    }

    row = {**metadata, **row}

    data = pd.DataFrame(
        [row],
        columns=FEATURE_DATASET_METADATA_COLUMNS + V0_2_FEATURES,
    )

    return FeatureDataset(
        data=data,
        dataset_version="benchmark_v0.2",
        feature_schema_version="v0.2",
    )


def test_writer_creates_artifact_and_manifest(tmp_path: Path) -> None:
    dataset = make_dataset()

    result = DatasetArtifactWriter().write(
        dataset=dataset,
        output_dir=tmp_path,
        input_manifest_sha256="input-hash",
    )

    assert result.artifact_path.exists()
    assert result.manifest_path.exists()
    assert result.artifact_sha256
    assert result.input_manifest_sha256 == "input-hash"

    loaded = pd.read_parquet(result.artifact_path)

    assert tuple(loaded.columns) == (
        FEATURE_DATASET_METADATA_COLUMNS + V0_2_FEATURES
    )
    assert len(loaded) == 1


def test_writer_is_deterministic_for_same_dataset(tmp_path: Path) -> None:
    dataset = make_dataset()

    first = DatasetArtifactWriter().write(
        dataset=dataset,
        output_dir=tmp_path / "first",
        input_manifest_sha256="input-hash",
    )

    second = DatasetArtifactWriter().write(
        dataset=dataset,
        output_dir=tmp_path / "second",
        input_manifest_sha256="input-hash",
    )

    assert sha256_dataframe(dataset.data) == sha256_dataframe(
        pd.read_parquet(first.artifact_path)
    )

    assert first.artifact_sha256 == second.artifact_sha256


def test_manifest_records_reproducibility_metadata(tmp_path: Path) -> None:
    import json

    dataset = make_dataset()

    result = DatasetArtifactWriter().write(
        dataset=dataset,
        output_dir=tmp_path,
        input_manifest_sha256="input-hash",
    )

    manifest = json.loads(
        result.manifest_path.read_text(encoding="utf-8")
    )

    assert manifest["dataset_version"] == "benchmark_v0.2"
    assert manifest["feature_schema_version"] == "v0.2"
    assert manifest["object_count"] == 1
    assert manifest["feature_count"] == 42
    assert manifest["class_count"] == 1
    assert manifest["class_counts"] == {"SNIa": 1}
    assert manifest["deterministic_order"] == "oid_ascending"
    assert manifest["input_manifest_sha256"] == "input-hash"
    assert manifest["artifact_sha256"] == result.artifact_sha256
    assert manifest["artifact_sha256"] == sha256_file(
        result.artifact_path
    )
    assert manifest["columns"] == list(
        FEATURE_DATASET_METADATA_COLUMNS + V0_2_FEATURES
    )
