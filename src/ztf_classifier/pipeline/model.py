"""Production orchestration for frozen model training and packaging."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.artifact import ModelArtifact
from ztf_classifier.models.artifact_io import (
    LoadedModelArtifact,
    ModelArtifactLoader,
    ModelArtifactWriter,
)
from ztf_classifier.models.calibration import TemperatureScaler
from ztf_classifier.models.calibration_artifact import CalibrationArtifact
from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.config import ModelConfig
from ztf_classifier.models.provenance import (
    ModelProvenance,
    ModelProvenanceBuilder,
)
from ztf_classifier.models.xgboost import (
    OOFTrainingResult,
    XGBoostTrainingEngine,
)


@dataclass(frozen=True)
class ModelPipelineResult:
    """Complete result of one production model-training run."""

    config: ModelConfig
    dataset_path: Path
    fold_assignments_path: Path
    dataset: pd.DataFrame
    oof_result: OOFTrainingResult
    calibration: CalibrationArtifact
    model_artifact: ModelArtifact
    provenance: ModelProvenance
    artifact_dir: Path
    loaded_artifact: LoadedModelArtifact


class ModelPipeline:
    """Orchestrate frozen model training, calibration, and packaging."""

    def __init__(
        self,
        *,
        project_root: Path,
        dataset_path: Path,
        fold_assignments_path: Path,
        feature_schema_path: Path,
        model_config_path: Path,
        output_dir: Path,
        dataset_version: str = "features_v0.2",
        artifact_version: str = "1.0",
    ) -> None:
        self._project_root = Path(project_root).resolve()
        self._dataset_path = Path(dataset_path).resolve()
        self._fold_assignments_path = (
            Path(fold_assignments_path).resolve()
        )
        self._feature_schema_path = Path(
            feature_schema_path
        ).resolve()
        self._model_config_path = Path(
            model_config_path
        ).resolve()
        self._output_dir = Path(output_dir).resolve()
        self._dataset_version = dataset_version
        self._artifact_version = artifact_version
        self._config = ModelConfig()

    def run(self) -> ModelPipelineResult:
        """Train, calibrate, package, reload, and verify one model."""

        self._validate_inputs()
        self._validate_model_config()

        dataset = pd.read_parquet(self._dataset_path)
        fold_assignments = pd.read_parquet(
            self._fold_assignments_path
        )

        self._validate_training_dataset(dataset)
        self._validate_feature_schema(dataset)
        fold_values = self._validate_fold_assignments(
            dataset,
            fold_assignments,
        )

        engine = XGBoostTrainingEngine(
            feature_schema_path=self._feature_schema_path,
            config=self._config,
        )

        oof_result = engine.train_oof(
            dataset,
            fold_assignments=fold_values,
        )

        self._output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        oof_path = self._output_dir / "oof_predictions.parquet"
        if oof_path.exists():
            raise FileExistsError(
                f"Run OOF output already exists: {oof_path}"
            )

        oof_result.predictions.to_parquet(
            oof_path,
            index=False,
        )

        calibration_result = TemperatureScaler().fit(
            oof_result.probabilities,
            oof_result.true_indices,
        )

        calibration = CalibrationArtifact(
            method="temperature_scaling",
            temperature=float(
                calibration_result.temperature
            ),
        )

        model = engine.fit_full(dataset)

        feature_names = tuple(
            engine.prepare_features(dataset).columns
        )

        dataset_sha256 = self._sha256(self._dataset_path)
        feature_schema_sha256 = self._sha256(
            self._feature_schema_path
        )

        model_artifact = ModelArtifact(
            model=model,
            model_version=self._config.version,
            model_family=self._config.family,
            classes=MODEL_CLASSES,
            feature_schema_version="v0.2",
            feature_names=feature_names,
            configuration=self._config,
            dataset_sha256=dataset_sha256,
            feature_schema_sha256=feature_schema_sha256,
        )

        provenance = ModelProvenanceBuilder(
            project_root=self._project_root
        ).build(
            artifact_version=self._artifact_version,
            model_version=self._config.version,
            model_family=self._config.family,
            dataset_version=self._dataset_version,
            dataset_path=self._dataset_path,
            feature_schema_version="v0.2",
            feature_schema_path=self._feature_schema_path,
            model_config_path=self._model_config_path,
            calibration_method=calibration.method,
            calibration_temperature=calibration.temperature,
            calibration_source_path=oof_path,
        )

        artifact_dir = self._output_dir / "artifact"

        ModelArtifactWriter().write(
            artifact=model_artifact,
            output_dir=artifact_dir,
            feature_schema_path=self._feature_schema_path,
            calibration=calibration,
            provenance=provenance,
        )

        loaded_artifact = ModelArtifactLoader().load(
            artifact_dir
        )

        self._verify_loaded_model(
            dataset=dataset,
            engine=engine,
            model_artifact=model_artifact,
            calibration=calibration,
            loaded_artifact=loaded_artifact,
        )

        return ModelPipelineResult(
            config=self._config,
            dataset_path=self._dataset_path,
            fold_assignments_path=self._fold_assignments_path,
            dataset=dataset,
            oof_result=oof_result,
            calibration=calibration,
            model_artifact=model_artifact,
            provenance=provenance,
            artifact_dir=artifact_dir,
            loaded_artifact=loaded_artifact,
        )

    def _validate_inputs(self) -> None:
        """Validate all immutable training inputs before fitting."""

        for path in (
            self._dataset_path,
            self._fold_assignments_path,
            self._feature_schema_path,
            self._model_config_path,
        ):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Model pipeline input does not exist: {path}"
                )

        if self._output_dir.exists():
            raise FileExistsError(
                f"Model pipeline output already exists: "
                f"{self._output_dir}"
            )

    def _validate_model_config(self) -> None:
        """Validate the frozen historical model configuration."""

        payload = json.loads(
            self._model_config_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(payload, dict):
            raise TypeError(
                "Frozen model configuration must be a JSON object."
            )

        expected = {
            "model_version": self._config.version,
            "model_family": self._config.family,
            "n_estimators": self._config.xgboost.n_estimators,
            "max_depth": self._config.xgboost.max_depth,
            "learning_rate": self._config.xgboost.learning_rate,
            "subsample": self._config.xgboost.subsample,
            "colsample_bytree": self._config.xgboost.colsample_bytree,
            "min_child_weight": self._config.xgboost.min_child_weight,
            "reg_alpha": self._config.xgboost.reg_alpha,
            "reg_lambda": self._config.xgboost.reg_lambda,
            "objective": self._config.xgboost.objective,
            "num_classes": self._config.xgboost.num_class,
            "eval_metric": self._config.xgboost.eval_metric,
            "tree_method": self._config.xgboost.tree_method,
            "random_state": self._config.xgboost.random_state,
            "n_jobs": self._config.xgboost.n_jobs,
            "missing_value_strategy": (
                self._config.missing_value_strategy
            ),
            "hyperparameter_tuning": (
                self._config.hyperparameter_tuning
            ),
        }

        if payload != expected:
            raise ValueError(
                "Frozen model configuration does not match "
                "the runtime ModelConfig."
            )

    @staticmethod
    def _validate_training_dataset(
        dataset: pd.DataFrame,
    ) -> None:
        """Validate the frozen model-training dataset identity."""

        if dataset.shape != (150, 56):
            raise ValueError(
                "Frozen training dataset must have shape "
                "(150, 56)."
            )

        if "oid" not in dataset.columns:
            raise ValueError(
                "Frozen training dataset must contain 'oid'."
            )

        if "class" not in dataset.columns:
            raise ValueError(
                "Frozen training dataset must contain 'class'."
            )

        if dataset["oid"].isna().any():
            raise ValueError(
                "Frozen training dataset contains null OIDs."
            )

        if not dataset["oid"].is_unique:
            raise ValueError(
                "Frozen training dataset contains duplicate OIDs."
            )

        if dataset["class"].isna().any():
            raise ValueError(
                "Frozen training dataset contains null classes."
            )

        if set(dataset["class"]) != set(MODEL_CLASSES):
            raise ValueError(
                "Frozen training dataset classes do not match "
                "the frozen model classes."
            )

        counts = dataset["class"].value_counts()
        expected = pd.Series(
            10,
            index=list(MODEL_CLASSES),
        )

        if not counts.sort_index().equals(
            expected.sort_index()
        ):
            raise ValueError(
                "Frozen training dataset must contain exactly "
                "10 samples per class."
            )

    def _validate_feature_schema(
        self,
        dataset: pd.DataFrame,
    ) -> None:
        """Validate the frozen v0.2 feature schema against the dataset."""

        schema = pd.read_parquet(self._feature_schema_path)

        required_columns = {
            "feature_order",
            "feature",
            "scientific_group",
            "feature_set",
        }

        if set(schema.columns) != required_columns:
            raise ValueError(
                "Feature schema must contain exactly "
                "'feature_order', 'feature', 'scientific_group', "
                "and 'feature_set'."
            )

        if schema.shape != (42, 4):
            raise ValueError(
                "Frozen feature schema must have shape (42, 4)."
            )

        ordered = (
            schema
            .sort_values("feature_order")
            .reset_index(drop=True)
        )

        expected_order = np.arange(1, 43)

        if not np.array_equal(
            ordered["feature_order"].to_numpy(dtype=int),
            expected_order,
        ):
            raise ValueError(
                "Feature schema order must contain exactly "
                "1 through 42."
            )

        feature_names = ordered["feature"].astype(str).tolist()

        if len(set(feature_names)) != 42:
            raise ValueError(
                "Frozen feature schema contains duplicate features."
            )

        if not all(feature_names):
            raise ValueError(
                "Frozen feature schema contains empty feature names."
            )

        if set(ordered["feature_set"]) != {"v0.2_frozen"}:
            raise ValueError(
                "Frozen feature schema must use feature_set "
                "'v0.2_frozen'."
            )

        if ordered["scientific_group"].isna().any():
            raise ValueError(
                "Frozen feature schema contains null scientific groups."
            )

        missing = [
            name
            for name in feature_names
            if name not in dataset.columns
        ]

        if missing:
            raise ValueError(
                "Training dataset is missing schema features: "
                f"{missing}"
            )

    @staticmethod
    def _validate_fold_assignments(
        dataset: pd.DataFrame,
        fold_assignments: pd.DataFrame,
    ) -> np.ndarray:
        """Validate fold identity against the exact dataset row order."""

        required = {"row_index", "fold", "class"}

        if set(fold_assignments.columns) != required:
            raise ValueError(
                "Fold assignments must contain exactly "
                "'row_index', 'fold', and 'class'."
            )

        if fold_assignments.shape[0] != len(dataset):
            raise ValueError(
                "Fold assignments must contain exactly one "
                "row per training sample."
            )

        rows = (
            fold_assignments
            .sort_values("row_index")
            .reset_index(drop=True)
        )

        expected_indices = np.arange(len(dataset))

        if not np.array_equal(
            rows["row_index"].to_numpy(dtype=int),
            expected_indices,
        ):
            raise ValueError(
                "Fold row_index must contain the complete "
                "range 0..149 exactly once."
            )

        folds = rows["fold"].to_numpy(dtype=int)

        if set(folds) != {1, 2, 3, 4, 5}:
            raise ValueError(
                "Fold assignments must contain folds 1 through 5."
            )

        if not np.array_equal(
            rows["class"].to_numpy(dtype=str),
            dataset["class"].to_numpy(dtype=str),
        ):
            raise ValueError(
                "Fold assignment classes do not match the "
                "training dataset row-by-row."
            )

        counts = pd.Series(folds).value_counts()

        if set(counts.index) != {1, 2, 3, 4, 5}:
            raise ValueError(
                "Fold assignments must contain all five folds."
            )

        if not (counts == 30).all():
            raise ValueError(
                "Frozen fold assignments must contain exactly "
                "30 samples per fold."
            )

        return folds

    @staticmethod
    def _verify_loaded_model(
        *,
        dataset: pd.DataFrame,
        engine: XGBoostTrainingEngine,
        model_artifact: ModelArtifact,
        calibration: CalibrationArtifact,
        loaded_artifact: LoadedModelArtifact,
    ) -> None:
        """Verify that the serialized model preserves predictions."""

        features = engine.prepare_features(dataset)

        expected = model_artifact.model.predict_proba(
            features
        )

        actual = (
            loaded_artifact.model_artifact.model.predict_proba(
                features
            )
        )

        if expected.shape != (150, len(MODEL_CLASSES)):
            raise ValueError(
                "Fitted model returned an unexpected probability shape."
            )

        if not np.allclose(
            expected,
            actual,
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError(
                "Reloaded model predictions do not match "
                "the in-memory model."
            )

        if (
            loaded_artifact.calibration.method
            != "temperature_scaling"
        ):
            raise ValueError(
                "Reloaded calibration method is invalid."
            )

        if (
            loaded_artifact.calibration.method
            != calibration.method
        ):
            raise ValueError(
                "Reloaded calibration method does not match "
                "the in-memory calibration."
            )

        if (
            loaded_artifact.calibration.temperature
            != calibration.temperature
        ):
            raise ValueError(
                "Reloaded calibration temperature does not match "
                "the in-memory calibration."
            )

    @staticmethod
    def _sha256(path: Path) -> str:
        """Return the SHA-256 digest of a file."""

        import hashlib

        digest = hashlib.sha256()

        with path.open("rb") as handle:
            for chunk in iter(
                lambda: handle.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()


__all__ = [
    "ModelPipeline",
    "ModelPipelineResult",
]
