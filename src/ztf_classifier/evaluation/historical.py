"""Canonical strict historical backtesting for frozen v0.2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    log_loss,
)

from ztf_classifier.features.pipeline import (
    V0_2_FEATURES,
    extract_v0_2_features,
    validate_v0_2_feature_vector,
)
from ztf_classifier.io.alerce import alerce_to_internal_lc_robust
from ztf_classifier.io.detection_acquisition import (
    DetectionAcquisitionBackend,
    DetectionAcquisitionRequest,
)
from ztf_classifier.models.classes import (
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.config import ModelConfig
from ztf_classifier.models.xgboost import XGBoostTrainingEngine


@dataclass(frozen=True)
class HistoricalBacktestConfig:
    """Frozen strict historical-backtest configuration."""

    historical_cutoff_mjd: float = 59447.224132
    cohort_rule: str = "firstmjd <= cutoff"
    observation_rule: str = "mjd <= cutoff"
    feature_schema_path: Path = Path(
        "reports/tables/final_feature_set_v0.2.parquet"
    )
    object_path: Path = Path(
        "data/processed/alerc_objects_v0.1.parquet"
    )
    feature_label_path: Path = Path(
        "data/processed/features_v0.2.parquet"
    )
    fold_path: Path = Path(
        "reports/tables/stratified_cv_fold_assignments_v0.1.parquet"
    )

    def __post_init__(self) -> None:
        if not np.isfinite(self.historical_cutoff_mjd):
            raise ValueError("historical_cutoff_mjd must be finite.")

        if self.cohort_rule != "firstmjd <= cutoff":
            raise ValueError("Unsupported historical cohort rule.")

        if self.observation_rule != "mjd <= cutoff":
            raise ValueError("Unsupported historical observation rule.")


@dataclass(frozen=True)
class HistoricalBacktestResult:
    """Strict historical predictions, metrics and reproducibility metadata."""

    predictions: pd.DataFrame
    fold_metrics: pd.DataFrame
    extraction_errors: pd.DataFrame
    metadata: dict[str, object]

    @property
    def evaluated_objects(self) -> int:
        return len(self.predictions)

    @property
    def evaluated_folds(self) -> int:
        return int(
            (self.fold_metrics["status"] == "evaluated").sum()
        )

    @property
    def skipped_folds(self) -> int:
        return int(
            (self.fold_metrics["status"] == "skipped").sum()
        )


class HistoricalBacktestEvaluator:
    """Run the canonical strict historical v0.2 evaluation.

    The evaluator deliberately does not modify the production feature
    builder or production XGBoost OOF engine. Historical evaluation has
    different fold eligibility semantics because a historical training
    fold may not contain all frozen classes.
    """

    def __init__(
        self,
        *,
        acquisition_backend: DetectionAcquisitionBackend,
        config: HistoricalBacktestConfig | None = None,
        model_config: ModelConfig | None = None,
    ) -> None:
        self._backend = acquisition_backend
        self._config = config or HistoricalBacktestConfig()
        self._model_config = model_config or ModelConfig()

        self._engine = XGBoostTrainingEngine(
            config=self._model_config,
            feature_schema_path=self._config.feature_schema_path,
        )

    def evaluate(self) -> HistoricalBacktestResult:
        """Execute the complete strict historical backtest."""

        objects = self._load_objects()
        frozen_features = self._load_frozen_features()
        folds = self._load_folds()

        historical_objects = self._select_historical_cohort(objects)

        labels = self._build_frozen_label_map(frozen_features)
        fold_map = self._build_oid_fold_map(
            frozen_features,
            folds,
        )

        historical_dataset, extraction_errors = (
            self._extract_historical_features(
                historical_objects,
                labels,
            )
        )

        if extraction_errors:
            extraction_error_df = pd.DataFrame(
                extraction_errors,
                columns=["oid", "error"],
            )
        else:
            extraction_error_df = pd.DataFrame(
                columns=["oid", "error"]
            )

        predictions, fold_metrics = self._evaluate_folds(
            historical_dataset,
            fold_map,
        )

        metadata = {
            "status": "FINALIZED",
            "historical_cutoff_mjd": self._config.historical_cutoff_mjd,
            "cohort_rule": self._config.cohort_rule,
            "observation_rule": self._config.observation_rule,
            "historical_cohort_objects": len(historical_objects),
            "historical_feature_rows": len(historical_dataset),
            "evaluated_objects": len(predictions),
            "evaluated_folds": int(
                (fold_metrics["status"] == "evaluated").sum()
            ),
            "skipped_folds": int(
                (fold_metrics["status"] == "skipped").sum()
            ),
            "feature_count": len(V0_2_FEATURES),
            "class_count": NUM_CLASSES,
            "model_version": self._model_config.version,
            "model_family": self._model_config.family,
        }

        return HistoricalBacktestResult(
            predictions=predictions,
            fold_metrics=fold_metrics,
            extraction_errors=extraction_error_df,
            metadata=metadata,
        )

    def _load_objects(self) -> pd.DataFrame:
        path = self._config.object_path
        if not path.exists():
            raise FileNotFoundError(
                f"Historical object artifact not found: {path}"
            )

        objects = pd.read_parquet(path)

        required = {"oid", "firstmjd", "class", "survey"}
        missing = required - set(objects.columns)

        if missing:
            raise ValueError(
                f"Object artifact missing columns: {sorted(missing)}"
            )

        objects = objects.copy()
        objects["oid"] = objects["oid"].astype(str)

        if objects["oid"].duplicated().any():
            raise ValueError("Object artifact contains duplicate OIDs.")

        return objects

    def _load_frozen_features(self) -> pd.DataFrame:
        path = self._config.feature_label_path
        if not path.exists():
            raise FileNotFoundError(
                f"Frozen feature artifact not found: {path}"
            )

        features = pd.read_parquet(path)

        required = {"oid", "class"}
        missing = required - set(features.columns)

        if missing:
            raise ValueError(
                f"Frozen feature artifact missing columns: {sorted(missing)}"
            )

        if len(features) != 150:
            raise ValueError(
                "Frozen v0.2 feature artifact must contain 150 objects."
            )

        if features["oid"].astype(str).duplicated().any():
            raise ValueError(
                "Frozen feature artifact contains duplicate OIDs."
            )

        features = features.copy()
        features["oid"] = features["oid"].astype(str)

        return features

    def _load_folds(self) -> pd.DataFrame:
        path = self._config.fold_path
        if not path.exists():
            raise FileNotFoundError(
                f"Frozen fold artifact not found: {path}"
            )

        folds = pd.read_parquet(path)

        required = {"row_index", "fold", "class"}
        missing = required - set(folds.columns)

        if missing:
            raise ValueError(
                f"Fold artifact missing columns: {sorted(missing)}"
            )

        if len(folds) != 150:
            raise ValueError(
                "Frozen fold artifact must contain 150 rows."
            )

        if folds["row_index"].duplicated().any():
            raise ValueError(
                "Frozen fold artifact contains duplicate row_index values."
            )

        folds = folds.copy()
        folds["row_index"] = folds["row_index"].astype(int)
        folds["fold"] = folds["fold"].astype(int)

        expected = set(range(1, 6))
        actual = set(folds["fold"].unique())

        if actual != expected:
            raise ValueError(
                f"Frozen fold artifact must contain folds 1-5, got {actual}."
            )

        return folds

    def _select_historical_cohort(
        self,
        objects: pd.DataFrame,
    ) -> pd.DataFrame:
        firstmjd = pd.to_numeric(
            objects["firstmjd"],
            errors="coerce",
        )

        selected = objects.loc[
            firstmjd <= self._config.historical_cutoff_mjd
        ].copy()

        selected = selected.sort_values("oid").reset_index(drop=True)

        return selected

    @staticmethod
    def _build_frozen_label_map(
        frozen_features: pd.DataFrame,
    ) -> dict[str, str]:
        return dict(
            zip(
                frozen_features["oid"].astype(str),
                frozen_features["class"].astype(str),
                strict=True,
            )
        )

    @staticmethod
    def _build_oid_fold_map(
        frozen_features: pd.DataFrame,
        folds: pd.DataFrame,
    ) -> dict[str, int]:
        indexed = frozen_features.reset_index(
            names="row_index"
        )

        merged = indexed[
            ["row_index", "oid", "class"]
        ].merge(
            folds,
            on="row_index",
            how="inner",
            validate="one_to_one",
            suffixes=("_feature", "_fold"),
        )

        if len(merged) != len(frozen_features):
            raise ValueError(
                "Frozen fold mapping does not cover every feature row."
            )

        class_mismatch = (
            merged["class_feature"].astype(str)
            != merged["class_fold"].astype(str)
        )

        if class_mismatch.any():
            raise ValueError(
                "Frozen fold mapping contains class mismatches."
            )

        return dict(
            zip(
                merged["oid"].astype(str),
                merged["fold"].astype(int),
                strict=True,
            )
        )

    def _extract_historical_features(
        self,
        historical_objects: pd.DataFrame,
        labels: dict[str, str],
    ) -> tuple[pd.DataFrame, list[dict[str, str]]]:
        rows: list[dict[str, object]] = []
        errors: list[dict[str, str]] = []

        for record in historical_objects.to_dict(orient="records"):
            oid = str(record["oid"])
            survey = str(record["survey"])

            try:
                request = DetectionAcquisitionRequest(
                    oid=oid,
                    survey=survey,
                )

                result = self._backend.acquire(request)

                internal = alerce_to_internal_lc_robust(
                    result.detections
                )

                features = extract_v0_2_features(
                    internal,
                    cutoff_mjd=self._config.historical_cutoff_mjd,
                )

                validate_v0_2_feature_vector(features)

                frozen_label = labels.get(oid)

                if frozen_label is None:
                    raise ValueError(
                        f"OID {oid} is missing from frozen labels."
                    )

                row: dict[str, object] = {
                    "oid": oid,
                    "class": frozen_label,
                }
                row.update(features)
                rows.append(row)

            except Exception as exc:  # noqa: BLE001
                errors.append(
                    {
                        "oid": oid,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        columns = ["oid", "class", *V0_2_FEATURES]

        dataset = pd.DataFrame(rows, columns=columns)

        if dataset["oid"].duplicated().any():
            raise ValueError(
                "Historical feature dataset contains duplicate OIDs."
            )

        return dataset, errors

    def _evaluate_folds(
        self,
        dataset: pd.DataFrame,
        fold_map: dict[str, int],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if dataset.empty:
            raise ValueError("Historical feature dataset is empty.")

        missing_fold = sorted(
            set(dataset["oid"].astype(str)) - set(fold_map)
        )

        if missing_fold:
            raise ValueError(
                f"Historical OIDs missing frozen fold assignments: "
                f"{missing_fold}"
            )

        fold_ids = dataset["oid"].astype(str).map(fold_map)

        if fold_ids.isna().any():
            raise ValueError(
                "Historical fold mapping produced missing assignments."
            )

        fold_ids = fold_ids.to_numpy(dtype=int)

        X = self._engine.prepare_features(dataset)
        y, class_names = self._engine.prepare_target(dataset)

        prediction_records: list[dict[str, object]] = []
        metric_records: list[dict[str, object]] = []

        for fold in range(1, 6):
            train_idx = np.where(fold_ids != fold)[0]
            test_idx = np.where(fold_ids == fold)[0]

            if len(test_idx) == 0:
                metric_records.append(
                    {
                        "fold": fold,
                        "status": "skipped",
                        "n_train": len(train_idx),
                        "n_test": 0,
                        "accuracy": np.nan,
                        "balanced_accuracy": np.nan,
                        "macro_f1": np.nan,
                        "weighted_f1": np.nan,
                        "log_loss": np.nan,
                        "test_only_classes": "",
                    }
                )
                continue

            train_classes = set(y[train_idx].tolist())
            test_classes = set(y[test_idx].tolist())

            missing_from_train = sorted(
                test_classes - train_classes
            )

            if missing_from_train:
                test_only_names = ",".join(
                    class_names[index]
                    for index in missing_from_train
                )

                metric_records.append(
                    {
                        "fold": fold,
                        "status": "skipped",
                        "n_train": len(train_idx),
                        "n_test": len(test_idx),
                        "accuracy": np.nan,
                        "balanced_accuracy": np.nan,
                        "macro_f1": np.nan,
                        "weighted_f1": np.nan,
                        "log_loss": np.nan,
                        "test_only_classes": test_only_names,
                    }
                )
                continue

            model = self._engine._build_model()

            model.fit(
                X.iloc[train_idx],
                y[train_idx],
            )

            probabilities = model.predict_proba(
                X.iloc[test_idx]
            )

            self._engine._validate_probability_matrix(
                probabilities,
                len(test_idx),
            )

            predicted = np.argmax(
                probabilities,
                axis=1,
            )

            y_test = y[test_idx]

            metric_records.append(
                {
                    "fold": fold,
                    "status": "evaluated",
                    "n_train": len(train_idx),
                    "n_test": len(test_idx),
                    "accuracy": float(
                        accuracy_score(y_test, predicted)
                    ),
                    "balanced_accuracy": float(
                        balanced_accuracy_score(
                            y_test,
                            predicted,
                        )
                    ),
                    "macro_f1": float(
                        f1_score(
                            y_test,
                            predicted,
                            average="macro",
                            zero_division=0,
                        )
                    ),
                    "weighted_f1": float(
                        f1_score(
                            y_test,
                            predicted,
                            average="weighted",
                            zero_division=0,
                        )
                    ),
                    "log_loss": float(
                        log_loss(
                            y_test,
                            probabilities,
                            labels=np.arange(NUM_CLASSES),
                        )
                    ),
                    "test_only_classes": "",
                }
            )

            for position, sample_idx in enumerate(test_idx):
                true_index = int(y[sample_idx])
                predicted_index = int(predicted[position])

                record: dict[str, object] = {
                    "fold": fold,
                    "oid": str(dataset.iloc[sample_idx]["oid"]),
                    "true_class": class_names[true_index],
                    "predicted_class": class_names[predicted_index],
                }

                for class_index, class_name in enumerate(class_names):
                    record[f"prob_{class_name}"] = float(
                        probabilities[position, class_index]
                    )

                prediction_records.append(record)

        predictions = pd.DataFrame(
            prediction_records,
            columns=[
                "fold",
                "oid",
                "true_class",
                "predicted_class",
                *[
                    f"prob_{name}"
                    for name in MODEL_CLASSES
                ],
            ],
        )

        if not predictions.empty:
            predictions = predictions.sort_values(
                ["fold", "oid"]
            ).reset_index(drop=True)

        fold_metrics = pd.DataFrame(
            metric_records,
            columns=[
                "fold",
                "status",
                "n_train",
                "n_test",
                "accuracy",
                "balanced_accuracy",
                "macro_f1",
                "weighted_f1",
                "log_loss",
                "test_only_classes",
            ],
        )

        return predictions, fold_metrics
