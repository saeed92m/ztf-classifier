from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.artifact_io import (
    ARTIFACT_SCHEMA_VERSION,
    LEGACY_ARTIFACT_SCHEMA_VERSION,
    ModelArtifactLoader,
    ModelArtifactWriter,
)
from ztf_classifier.models.calibration_artifact import CalibrationArtifact
from ztf_classifier.models.conformal import EmpiricalConformalPredictor
from ztf_classifier.models.conformal_artifact import ConformalArtifact
from ztf_classifier.models.ood_artifact import OODArtifact
from ztf_classifier.models.ood_production import OODProductionModel
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _build_artifact() -> ModelArtifact:
    dataset = pd.read_parquet(DATASET_PATH)

    engine = XGBoostTrainingEngine(
        feature_schema_path=FEATURE_SCHEMA_PATH,
    )

    model = engine.fit_full(dataset)

    feature_names = tuple(
        engine.prepare_features(dataset).columns
    )

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
        dataset_sha256=_sha256(DATASET_PATH),
        feature_schema_sha256=_sha256(
            FEATURE_SCHEMA_PATH
        ),
    )

    return artifact


def _build_provenance(
    *,
    artifact_version: str,
):
    return ModelProvenanceBuilder(
        project_root=Path.cwd(),
    ).build(
        artifact_version=artifact_version,
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


def _build_diagnostics():
    rng = np.random.default_rng(42)

    X = rng.normal(
        size=(150, 42),
    )

    ood_model = OODProductionModel().fit(X)

    assert (
        ood_model.reference_anomaly_scores
        is not None
    )

    ood = OODArtifact.from_config(
        ood_model.config,
        ood_model.reference_anomaly_scores,
    )

    probabilities = rng.random(
        (150, 15),
    )

    probabilities /= probabilities.sum(
        axis=1,
        keepdims=True,
    )

    true_indices = np.argmax(
        probabilities,
        axis=1,
    )

    conformal_results = (
        EmpiricalConformalPredictor().fit_all(
            probabilities,
            true_indices,
        )
    )

    conformal = ConformalArtifact.from_results(
        conformal_results,
    )

    return conformal, ood, ood_model


def _build_writer_inputs(
    *,
    artifact_version: str,
):
    artifact = _build_artifact()

    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=1.0268501887,
    )

    provenance = _build_provenance(
        artifact_version=artifact_version,
    )

    return artifact, calibration, provenance


def _write_diagnostic_artifact(
    tmp_path: Path,
) -> Path:
    (
        artifact,
        calibration,
        provenance,
    ) = _build_writer_inputs(
        artifact_version="1.1",
    )

    conformal, ood, ood_model = (
        _build_diagnostics()
    )

    output_dir = tmp_path / "artifact"

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
        conformal=conformal,
        ood=ood,
        ood_model=ood_model,
    )

    return output_dir


def test_diagnostic_artifact_uses_schema_1_1_and_expected_files(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(
        tmp_path,
    )

    manifest = json.loads(
        (
            artifact_dir
            / "artifact_manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest["artifact_schema_version"]
        == ARTIFACT_SCHEMA_VERSION
        == "1.1"
    )

    assert set(manifest["files"]) == {
        "model",
        "model_contract",
        "feature_schema",
        "calibration",
        "conformal",
        "ood",
        "ood_model",
        "provenance",
    }

    expected_files = {
        "model.json",
        "model_contract.json",
        "feature_schema.parquet",
        "calibration.json",
        "conformal.json",
        "ood.json",
        "ood_model.joblib",
        "provenance.json",
        "artifact_manifest.json",
    }

    assert {
        path.name
        for path in artifact_dir.iterdir()
    } == expected_files


def test_diagnostic_artifact_loader_roundtrip(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(
        tmp_path,
    )

    loaded = ModelArtifactLoader().load(
        artifact_dir,
    )

    assert loaded.conformal is not None
    assert loaded.ood is not None
    assert loaded.ood_model is not None

    assert loaded.conformal.alphas == (
        0.05,
        0.10,
        0.20,
    )

    assert loaded.ood.feature_count == 42

    np.testing.assert_array_equal(
        loaded.ood.reference_anomaly_scores,
        loaded.ood_model.reference_anomaly_scores,
    )


def test_diagnostic_artifact_loads_without_conformal(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(tmp_path)
    (artifact_dir / "conformal.json").unlink()

    manifest_path = artifact_dir / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["files"]["conformal"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = ModelArtifactLoader().load(artifact_dir)
    assert loaded.conformal is None
    assert loaded.ood is not None
    assert loaded.ood_model is not None


def test_diagnostic_artifact_loads_without_ood(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(tmp_path)
    (artifact_dir / "ood.json").unlink()
    (artifact_dir / "ood_model.joblib").unlink()

    manifest_path = artifact_dir / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["files"]["ood"]
    del manifest["files"]["ood_model"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    loaded = ModelArtifactLoader().load(artifact_dir)
    assert loaded.conformal is not None
    assert loaded.ood is None
    assert loaded.ood_model is None


def test_diagnostic_artifact_rejects_partial_ood_metadata(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(tmp_path)
    (artifact_dir / "ood_model.joblib").unlink()

    manifest_path = artifact_dir / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["files"]["ood_model"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="OOD artifact and OOD production model metadata",
    ):
        ModelArtifactLoader().load(artifact_dir)


def test_diagnostic_artifact_rejects_tampered_ood_model(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(tmp_path)

    path = artifact_dir / "ood_model.joblib"
    payload = path.read_bytes()
    path.write_bytes(payload + b"tampered")

    with pytest.raises(
        ValueError,
        match="Artifact integrity check failed for .ood_model.",
    ):
        ModelArtifactLoader().load(artifact_dir)


def test_diagnostic_artifact_rejects_path_escape(
    tmp_path: Path,
) -> None:
    artifact_dir = _write_diagnostic_artifact(tmp_path)

    manifest_path = artifact_dir / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["ood_model"]["path"] = "../ood_model.joblib"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Artifact path escapes artifact directory",
    ):
        ModelArtifactLoader().load(artifact_dir)


def test_legacy_writer_still_emits_schema_1_0(
    tmp_path: Path,
) -> None:
    (
        artifact,
        calibration,
        provenance,
    ) = _build_writer_inputs(
        artifact_version="1.0",
    )

    output_dir = tmp_path / "legacy_artifact"

    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
    )

    manifest = json.loads(
        (output_dir / "artifact_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest["artifact_schema_version"]
        == LEGACY_ARTIFACT_SCHEMA_VERSION
        == "1.0"
    )
    assert not (output_dir / "conformal.json").exists()
    assert not (output_dir / "ood.json").exists()
    assert not (output_dir / "ood_model.joblib").exists()


def test_writer_allows_conformal_without_ood(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs(
        artifact_version="1.1",
    )
    conformal, _, _ = _build_diagnostics()

    output_dir = tmp_path / "conformal_only"
    ModelArtifactWriter().write(
        artifact=artifact,
        output_dir=output_dir,
        feature_schema_path=FEATURE_SCHEMA_PATH,
        calibration=calibration,
        provenance=provenance,
        conformal=conformal,
    )

    loaded = ModelArtifactLoader().load(output_dir)
    assert loaded.conformal is not None
    assert loaded.ood is None
    assert loaded.ood_model is None


def test_writer_rejects_partial_ood_pair(
    tmp_path: Path,
) -> None:
    artifact, calibration, provenance = _build_writer_inputs(
        artifact_version="1.1",
    )
    _, ood, ood_model = _build_diagnostics()

    with pytest.raises(
        ValueError,
        match="OOD artifact and OOD production model must be provided together",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=tmp_path / "partial",
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
            ood=ood,
        )

    with pytest.raises(
        ValueError,
        match="OOD artifact and OOD production model must be provided together",
    ):
        ModelArtifactWriter().write(
            artifact=artifact,
            output_dir=tmp_path / "partial-2",
            feature_schema_path=FEATURE_SCHEMA_PATH,
            calibration=calibration,
            provenance=provenance,
            ood_model=ood_model,
        )
