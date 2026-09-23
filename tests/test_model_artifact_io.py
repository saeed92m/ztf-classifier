import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.artifact_io import (
    ModelArtifactLoader,
    ModelArtifactWriter,
)
from ztf_classifier.models.calibration_artifact import CalibrationArtifact
from ztf_classifier.models.xgboost import XGBoostTrainingEngine

DATASET_PATH = Path(
    "data/processed/benchmark_v0.2/features.parquet"
)

FEATURE_SCHEMA_PATH = Path(
    "reports/tables/final_feature_set_v0.2.parquet"
)


def _build_artifact() -> tuple[
    ModelArtifact,
    pd.DataFrame,
]:
    dataset = pd.read_parquet(DATASET_PATH)

    engine = XGBoostTrainingEngine(
        feature_schema_path=FEATURE_SCHEMA_PATH,
    )

    model = engine.fit_full(dataset)
    feature_names = tuple(
        engine.prepare_features(dataset).columns
    )

    import hashlib

    digest = hashlib.sha256()

    with FEATURE_SCHEMA_PATH.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    artifact = ModelArtifact(
        model=model,
        model_version="baseline_v0.2",
        model_family="XGBoost",
        classes=tuple(
            engine.prepare_target(dataset)[1]
        ),
        feature_schema_version="v0.2",
        feature_names=feature_names,
        configuration=engine._config,
        dataset_sha256=(
            "0" * 64
        ),
        feature_schema_sha256=digest.hexdigest(),
    )

    return artifact, dataset


def test_model_artifact_writer_loader_roundtrip(
    tmp_path: Path,
) -> None:
    artifact, dataset = _build_artifact()

    output_dir = (
        tmp_path / "baseline_v0.2"
    )

    writer = ModelArtifactWriter()

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    writer.write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
    )

    expected_files = {
        "model.json",
        "model_contract.json",
        "feature_schema.parquet",
        "calibration.json",
        "artifact_manifest.json",
    }

    assert {
        path.name
        for path in output_dir.iterdir()
    } == expected_files

    loaded_calibration = CalibrationArtifact.read(
        output_dir / "calibration.json"
    )

    assert loaded_calibration == calibration

    engine = XGBoostTrainingEngine(
        feature_schema_path=FEATURE_SCHEMA_PATH,
    )

    X = engine.prepare_features(dataset)

    original_probabilities = (
        artifact.model.predict_proba(X)
    )

    loader = ModelArtifactLoader()

    loaded_package = loader.load(
        output_dir,
    )

    loaded = loaded_package.model_artifact

    loaded_probabilities = (
        loaded.model.predict_proba(X)
    )

    assert loaded_package.calibration == calibration

    assert loaded.model_version == (
        artifact.model_version
    )
    assert loaded.model_family == (
        artifact.model_family
    )
    assert loaded.classes == artifact.classes
    assert loaded.feature_schema_version == (
        artifact.feature_schema_version
    )
    assert loaded.feature_names == (
        artifact.feature_names
    )
    assert loaded.configuration == (
        artifact.configuration
    )
    assert loaded.dataset_sha256 == (
        artifact.dataset_sha256
    )
    assert loaded.feature_schema_sha256 == (
        artifact.feature_schema_sha256
    )

    np.testing.assert_array_equal(
        loaded_probabilities,
        original_probabilities,
    )


def test_model_artifact_loader_rejects_missing_calibration(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
    )

    (output_dir / "calibration.json").unlink()

    with pytest.raises(FileNotFoundError):
        ModelArtifactLoader().load(output_dir)


def test_model_artifact_loader_rejects_modified_calibration(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
    )

    calibration_path = output_dir / "calibration.json"

    calibration_path.write_text(
        calibration_path.read_text(encoding="utf-8").replace(
            "1.0268501887",
            "1.5",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="integrity check failed"):
        ModelArtifactLoader().load(output_dir)


def test_model_artifact_loader_rejects_invalid_calibration_hash(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
    )

    manifest_path = output_dir / "artifact_manifest.json"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest["files"]["calibration"]["sha256"] = "0" * 64

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="integrity check failed"):
        ModelArtifactLoader().load(output_dir)


def test_model_artifact_loader_rejects_calibration_path_escape(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
    )

    manifest_path = output_dir / "artifact_manifest.json"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest["files"]["calibration"]["path"] = "../calibration.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="path escapes artifact directory",
    ):
        ModelArtifactLoader().load(output_dir)
