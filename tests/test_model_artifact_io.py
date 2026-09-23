import json
from dataclasses import replace
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
from ztf_classifier.models.provenance import ModelProvenanceBuilder
from ztf_classifier.models.xgboost import XGBoostTrainingEngine

DATASET_PATH = Path(
    "data/processed/benchmark_v0.2/features.parquet"
)

FEATURE_SCHEMA_PATH = Path(
    "reports/tables/final_feature_set_v0.2.parquet"
)


MODEL_CONFIG_PATH = Path(
    "reports/tables/final_model_config_v0.2.json"
)

CALIBRATION_SOURCE_PATH = Path(
    "reports/tables/xgboost_baseline_v0.2_oof_predictions.parquet"
)


def _build_provenance():
    return ModelProvenanceBuilder(
        project_root=Path.cwd(),
    ).build(
        artifact_version="1.0",
        model_version="baseline_v0.2",
        model_family="XGBoost",
        dataset_version="benchmark_v0.2",
        dataset_path=DATASET_PATH.resolve(),
        feature_schema_version="v0.2",
        feature_schema_path=FEATURE_SCHEMA_PATH.resolve(),
        model_config_path=MODEL_CONFIG_PATH.resolve(),
        calibration_method="temperature_scaling",
        calibration_temperature=1.0268501887,
        calibration_source_path=CALIBRATION_SOURCE_PATH.resolve(),
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

    dataset_digest = hashlib.sha256()

    with DATASET_PATH.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            dataset_digest.update(chunk)

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
        dataset_sha256=dataset_digest.hexdigest(),
        feature_schema_sha256=digest.hexdigest(),
    )

    return artifact, dataset


def _build_writer_inputs():
    artifact, _ = _build_artifact()

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    return artifact, calibration, provenance


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

    provenance = _build_provenance()

    writer.write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    expected_files = {
        "model.json",
        "model_contract.json",
        "feature_schema.parquet",
        "calibration.json",
        "provenance.json",
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
    assert loaded_package.provenance == provenance

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


def test_model_artifact_writer_rejects_model_version_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        model_version="other_model",
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Model artifact model_version does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_writer_rejects_model_family_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        model_family="OtherFamily",
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Model artifact model_family does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_writer_rejects_feature_schema_version_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        feature_schema_version="v999",
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Model artifact feature_schema_version "
        "does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_writer_rejects_dataset_sha256_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        dataset_sha256="0" * 64,
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Model artifact dataset SHA-256 does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_writer_rejects_feature_schema_sha256_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        feature_schema_sha256="0" * 64,
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Model artifact feature schema SHA-256 "
        "does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_writer_rejects_calibration_method_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        calibration_method="other",
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Calibration method does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_writer_rejects_calibration_temperature_mismatch(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs()
    provenance = replace(
        provenance,
        calibration_temperature=1.5,
    )
    output_dir = tmp_path / "artifact"

    with pytest.raises(
        ValueError,
        match="Calibration temperature does not match provenance.",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=output_dir,
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
        )

    assert not output_dir.exists()


def test_model_artifact_loader_rejects_missing_calibration(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
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

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
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

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
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

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
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


def test_model_artifact_loader_rejects_missing_provenance(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    (output_dir / "provenance.json").unlink()

    with pytest.raises(FileNotFoundError):
        ModelArtifactLoader().load(output_dir)


def test_model_artifact_loader_rejects_modified_provenance(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    provenance_path = output_dir / "provenance.json"

    provenance_path.write_text(
        provenance_path.read_text(encoding="utf-8").replace(
            '"baseline_v0.2"',
            '"tampered_model"',
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="integrity check failed"):
        ModelArtifactLoader().load(output_dir)


def test_model_artifact_loader_rejects_invalid_provenance_hash(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    manifest_path = output_dir / "artifact_manifest.json"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest["files"]["provenance"]["sha256"] = "0" * 64

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


def test_model_artifact_loader_rejects_provenance_path_escape(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    manifest_path = output_dir / "artifact_manifest.json"

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest["files"]["provenance"]["path"] = "../provenance.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="path escapes artifact directory"):
        ModelArtifactLoader().load(output_dir)

def _rewrite_manifest_file_hash(
    output_dir: Path,
    file_key: str,
) -> None:
    import hashlib

    manifest_path = output_dir / "artifact_manifest.json"
    target_path = output_dir / f"{file_key}.json"

    digest = hashlib.sha256()

    with target_path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    manifest["files"][file_key]["sha256"] = digest.hexdigest()

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_model_artifact_loader_rejects_semantically_tampered_provenance(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    provenance_path = output_dir / "provenance.json"

    data = json.loads(
        provenance_path.read_text(encoding="utf-8")
    )

    data["model"]["version"] = "tampered_model"

    provenance_path.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    _rewrite_manifest_file_hash(
        output_dir,
        "provenance",
    )

    with pytest.raises(
        ValueError,
        match="Provenance model_version does not match artifact.",
    ):
        ModelArtifactLoader().load(output_dir)


def test_model_artifact_loader_rejects_semantically_tampered_calibration_provenance(
    tmp_path: Path,
) -> None:
    artifact, _dataset = _build_artifact()

    output_dir = tmp_path / "baseline_v0.2"

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance()

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    provenance_path = output_dir / "provenance.json"

    data = json.loads(
        provenance_path.read_text(encoding="utf-8")
    )

    data["calibration"]["temperature"] = 1.5

    provenance_path.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    _rewrite_manifest_file_hash(
        output_dir,
        "provenance",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Provenance calibration temperature does not match "
            "calibration artifact."
        ),
    ):
        ModelArtifactLoader().load(output_dir)
