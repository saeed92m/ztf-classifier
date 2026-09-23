import json
from pathlib import Path

import pandas as pd
import pytest

from ztf_classifier.dataset.manifest import ObjectManifest
from ztf_classifier.dataset.validation import (
    DatasetArtifactValidator,
    validate_against_historical_objects,
)

ARTIFACT = Path("data/processed/benchmark_v0.2/features.parquet")
MANIFEST = Path("data/processed/benchmark_v0.2/dataset_manifest.json")


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


def test_dataset_artifact_validator_accepts_real_artifact() -> None:
    result = DatasetArtifactValidator().validate(
        artifact_path=ARTIFACT,
        manifest_path=MANIFEST,
    )

    assert result.object_count == 150
    assert result.feature_count == 42
    assert result.class_count == 15


def test_dataset_artifact_validator_rejects_missing_artifact(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Dataset artifact does not exist",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=tmp_path / "missing.parquet",
            manifest_path=MANIFEST,
        )


def test_dataset_artifact_validator_rejects_missing_manifest(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Dataset manifest does not exist",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=ARTIFACT,
            manifest_path=tmp_path / "missing.json",
        )


def test_dataset_artifact_validator_rejects_hash_mismatch(
    tmp_path: Path,
) -> None:
    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )
    manifest["artifact_sha256"] = "0" * 64

    manifest_copy = tmp_path / "dataset_manifest.json"
    manifest_copy.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Artifact SHA-256 does not match manifest",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=ARTIFACT,
            manifest_path=manifest_copy,
        )


def test_dataset_artifact_validator_rejects_duplicate_oid(
    tmp_path: Path,
) -> None:
    data = pd.read_parquet(ARTIFACT)
    data = pd.concat(
        [data, data.iloc[[0]]],
        ignore_index=True,
    )

    artifact_copy = tmp_path / "features.parquet"
    data.to_parquet(artifact_copy, index=False)

    manifest_copy = tmp_path / "dataset_manifest.json"
    manifest_copy.write_text(
        MANIFEST.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Dataset artifact contains duplicate OIDs",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=artifact_copy,
            manifest_path=manifest_copy,
        )


def test_dataset_artifact_validator_rejects_manifest_count_mismatch(
    tmp_path: Path,
) -> None:
    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )
    manifest["object_count"] = 149

    manifest_copy = tmp_path / "dataset_manifest.json"
    manifest_copy.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Manifest object_count does not match artifact",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=ARTIFACT,
            manifest_path=manifest_copy,
        )


def test_dataset_artifact_validator_rejects_schema_mismatch(
    tmp_path: Path,
) -> None:
    data = pd.read_parquet(ARTIFACT)
    data = data.drop(columns=["g_mean_mag"])

    artifact_copy = tmp_path / "features.parquet"
    data.to_parquet(artifact_copy, index=False)

    manifest_copy = tmp_path / "dataset_manifest.json"
    manifest_copy.write_text(
        MANIFEST.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Dataset artifact columns do not match",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=artifact_copy,
            manifest_path=manifest_copy,
        )


def test_dataset_artifact_validator_rejects_class_count_mismatch(
    tmp_path: Path,
) -> None:
    manifest = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )
    manifest["class_counts"]["AGN"] = 9

    manifest_copy = tmp_path / "dataset_manifest.json"
    manifest_copy.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Manifest class_counts do not match artifact",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=ARTIFACT,
            manifest_path=manifest_copy,
        )


def test_dataset_artifact_validator_rejects_non_deterministic_order(
    tmp_path: Path,
) -> None:
    data = pd.read_parquet(ARTIFACT)
    data = data.iloc[::-1].reset_index(drop=True)

    artifact_copy = tmp_path / "features.parquet"
    data.to_parquet(artifact_copy, index=False)

    manifest_copy = tmp_path / "dataset_manifest.json"
    manifest_copy.write_text(
        MANIFEST.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="deterministically ordered",
    ):
        DatasetArtifactValidator().validate(
            artifact_path=artifact_copy,
            manifest_path=manifest_copy,
        )
