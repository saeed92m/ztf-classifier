#!/usr/bin/env python3
"""Rebuild a separately identified v0.2 model from frozen local inputs.

This does NOT recover or reproduce the original model binary. It creates a
new, traceable reconstruction and never writes to the legacy production path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.artifact_io import ModelArtifactLoader, ModelArtifactWriter
from ztf_classifier.models.calibration import TemperatureScaler
from ztf_classifier.models.calibration_artifact import CalibrationArtifact
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.config import ModelConfig
from ztf_classifier.models.provenance import ModelProvenanceBuilder
from ztf_classifier.models.xgboost import XGBoostTrainingEngine
from ztf_classifier.pipeline.model import ModelPipeline

FROZEN_INPUTS = {
    "dataset": ("data/processed/features_v0.2.parquet", "d08543cffe5db141d6a7e4ee429264acdaa50c6e4fd01f1b0fa2a36aa42a6a85"),
    "feature_schema": ("reports/tables/final_feature_set_v0.2.parquet", "fed07fc291070ecbdc7bbc597fad5aac6a3f4a1746feb12a9f4c2407108af329"),
    "model_config": ("reports/tables/final_model_config_v0.2.json", "c01c3e9c27b4d8170082c6c755b4361d21c9706063bc83a4cc2509aff971fdd7"),
    "fold_assignments": ("reports/tables/stratified_cv_fold_assignments_v0.1.parquet", "6289a728a597c9bb7a2ed9e06e52f66ad886a65e031f5c30c1309b0f2b65976a"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    root = args.project_root.resolve()
    paths = {key: root / value[0] for key, value in FROZEN_INPUTS.items()}
    expected = {key: value[1] for key, value in FROZEN_INPUTS.items()}

    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing frozen inputs:\n" + "\n".join(missing))

    actual = {key: sha256_file(path) for key, path in paths.items()}
    mismatches = {
        key: {"expected": expected[key], "actual": actual[key]}
        for key in paths
        if actual[key] != expected[key]
    }
    if mismatches:
        raise ValueError(
            "Frozen input hash mismatch. No model was trained. "
            + json.dumps(mismatches, sort_keys=True)
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else root / "runs" / f"reconstructed-baseline-v0.2-{timestamp}"
    )
    legacy_path = (root / "runs/model_baseline_v0.2_production").resolve()
    if output_dir == legacy_path or legacy_path in output_dir.parents:
        raise ValueError("Refusing to write into the frozen production path.")
    if output_dir.exists():
        raise FileExistsError(f"Output already exists: {output_dir}")

    dataset = pd.read_parquet(paths["dataset"])
    folds = pd.read_parquet(paths["fold_assignments"])
    config = ModelConfig()

    validator = ModelPipeline(
        project_root=root,
        dataset_path=paths["dataset"],
        fold_assignments_path=paths["fold_assignments"],
        feature_schema_path=paths["feature_schema"],
        model_config_path=paths["model_config"],
        output_dir=output_dir,
        dataset_version="features_v0.2-reconstructed",
        artifact_version="reconstructed-1.0",
    )
    validator._validate_model_config()
    validator._validate_training_dataset(dataset)
    validator._validate_feature_schema(dataset)
    fold_values = validator._validate_fold_assignments(dataset, folds)

    engine = XGBoostTrainingEngine(
        feature_schema_path=paths["feature_schema"],
        config=config,
    )
    oof = engine.train_oof(dataset, fold_assignments=fold_values)
    calibration_fit = TemperatureScaler().fit(oof.probabilities, oof.true_indices)
    calibration = CalibrationArtifact(
        method="temperature_scaling",
        temperature=float(calibration_fit.temperature),
    )
    fitted_model = engine.fit_full(dataset)
    features = engine.prepare_features(dataset)

    output_dir.mkdir(parents=True)
    oof_path = output_dir / "oof_predictions.parquet"
    oof.predictions.to_parquet(oof_path, index=False)

    model_artifact = ModelArtifact(
        model=fitted_model,
        model_version=config.version,
        model_family=config.family,
        classes=MODEL_CLASSES,
        feature_schema_version="v0.2",
        feature_names=tuple(features.columns),
        configuration=config,
        dataset_sha256=actual["dataset"],
        feature_schema_sha256=actual["feature_schema"],
    )
    provenance = ModelProvenanceBuilder(project_root=root).build(
        artifact_version="reconstructed-1.0",
        model_version=config.version,
        model_family=config.family,
        dataset_version="features_v0.2-reconstructed",
        dataset_path=paths["dataset"],
        feature_schema_version="v0.2",
        feature_schema_path=paths["feature_schema"],
        model_config_path=paths["model_config"],
        calibration_method=calibration.method,
        calibration_temperature=calibration.temperature,
        calibration_source_path=oof_path,
    )

    artifact_dir = output_dir / "artifact"
    ModelArtifactWriter().write(
        artifact=model_artifact,
        output_dir=artifact_dir,
        feature_schema_path=paths["feature_schema"],
        calibration=calibration,
        provenance=provenance,
    )

    loaded = ModelArtifactLoader().load(artifact_dir)
    expected_probabilities = fitted_model.predict_proba(features)
    actual_probabilities = loaded.model_artifact.model.predict_proba(features)
    np.testing.assert_array_equal(actual_probabilities, expected_probabilities)

    record = {
        "record_schema": "ztf-model-reconstruction-v1",
        "status": "RECONSTRUCTED_NOT_ORIGINAL",
        "original_artifact_recovered": False,
        "production_eligible": False,
        "model_version": config.version,
        "artifact_schema_version": "1.0",
        "object_count": int(len(dataset)),
        "feature_count": int(len(features.columns)),
        "class_order": list(MODEL_CLASSES),
        "input_sha256": actual,
        "output_artifact": str(artifact_dir.relative_to(root)),
        "artifact_manifest_sha256": sha256_file(artifact_dir / "artifact_manifest.json"),
        "model_sha256": sha256_file(artifact_dir / "model.json"),
        "oof_predictions": str(oof_path.relative_to(root)),
        "oof_sha256": sha256_file(oof_path),
        "calibration_temperature": calibration.temperature,
        "reload_prediction_parity": "EXACT",
        "git_commit": provenance.git_commit,
        "git_dirty": provenance.git_dirty,
        "limitations": [
            "This is a new fit, not recovery of the original frozen model binary.",
            "The ALeRCE benchmark labels are not independent ground truth.",
            "Historical model predictions and performance are not presumed identical.",
            "Conformal and OOD production outputs are not included.",
        ],
    }
    (output_dir / "reconstruction_record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
