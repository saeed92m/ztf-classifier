"""Production XGBoost training engine for frozen v0.2."""

from __future__ import annotations

from collections.abc import Sequence
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
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

from ztf_classifier.models.classes import (
    CLASS_TO_INDEX,
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.config import ModelConfig


@dataclass(frozen=True)
class OOFTrainingResult:
    """OOF predictions and fold-level metrics."""

    predictions: pd.DataFrame
    fold_metrics: pd.DataFrame

    @property
    def probabilities(self) -> np.ndarray:
        """Return probabilities in frozen class order."""

        columns = [
            f"proba_{name}"
            for name in MODEL_CLASSES
        ]
        return self.predictions[columns].to_numpy(dtype=float)

    @property
    def true_indices(self) -> np.ndarray:
        """Return true class indices."""

        return self.predictions[
            "true_class_index"
        ].to_numpy(dtype=int)

    @property
    def predicted_indices(self) -> np.ndarray:
        """Return predicted class indices."""

        return self.predictions[
            "predicted_class_index"
        ].to_numpy(dtype=int)


class XGBoostTrainingEngine:
    """Deterministic XGBoost OOF training engine."""

    def __init__(
        self,
        *,
        config: ModelConfig | None = None,
        feature_schema_path: Path | None = None,
    ) -> None:
        self._config = config or ModelConfig()
        self._feature_schema_path = feature_schema_path

    def prepare_features(
        self,
        dataset: pd.DataFrame,
    ) -> pd.DataFrame:
        """Select exactly the frozen 42 model features."""

        feature_names = self._load_feature_names(dataset)

        X = dataset.loc[:, feature_names].copy()
        X = X.apply(pd.to_numeric, errors="coerce")
        X = X.replace([np.inf, -np.inf], np.nan)

        if X.shape[1] != 42:
            raise ValueError(
                "Frozen v0.2 model requires exactly 42 features."
            )

        return X

    def prepare_target(
        self,
        dataset: pd.DataFrame,
    ) -> tuple[np.ndarray, tuple[str, ...]]:
        """Encode target labels using the frozen class mapping."""

        if "class" not in dataset.columns:
            raise ValueError(
                "Dataset must contain a class column."
            )

        labels = dataset["class"].astype(str)

        unknown = sorted(
            set(labels.unique()) - set(MODEL_CLASSES)
        )
        if unknown:
            raise ValueError(
                f"Unknown model classes: {unknown}"
            )

        encoded = labels.map(CLASS_TO_INDEX)

        if encoded.isna().any():
            raise ValueError(
                "Target encoding produced missing values."
            )

        return encoded.to_numpy(dtype=int), MODEL_CLASSES

    def train_oof(
        self,
        dataset: pd.DataFrame,
        *,
        fold_assignments: Sequence[int] | None = None,
    ) -> OOFTrainingResult:
        """Train five deterministic folds and collect OOF predictions."""

        X = self.prepare_features(dataset)
        y, class_names = self.prepare_target(dataset)

        if len(X) != len(y):
            raise ValueError(
                "Feature and target row counts do not match."
            )

        if fold_assignments is None:
            fold_ids = self._generate_fold_assignments(y)
        else:
            fold_ids = np.asarray(
                fold_assignments,
                dtype=int,
            )

        self._validate_fold_assignments(
            fold_ids,
            len(dataset),
        )

        prediction_records: list[dict[str, object]] = []
        metric_records: list[dict[str, object]] = []

        for fold in sorted(np.unique(fold_ids)):
            train_idx = np.where(fold_ids != fold)[0]
            valid_idx = np.where(fold_ids == fold)[0]

            model = self._build_model()

            model.fit(
                X.iloc[train_idx],
                y[train_idx],
            )

            valid_proba = model.predict_proba(
                X.iloc[valid_idx]
            )

            valid_pred = np.argmax(
                valid_proba,
                axis=1,
            )

            self._validate_probability_matrix(
                valid_proba,
                len(valid_idx),
            )

            metric_records.append(
                self._fold_metrics(
                    fold=fold,
                    train_n=len(train_idx),
                    y_true=y[valid_idx],
                    y_pred=valid_pred,
                    probabilities=valid_proba,
                )
            )

            for position, sample_idx in enumerate(valid_idx):
                true_index = int(y[sample_idx])
                predicted_index = int(valid_pred[position])

                record: dict[str, object] = {
                    "row_index": int(sample_idx),
                    "true_label": class_names[true_index],
                    "true_class_index": true_index,
                    "predicted_label": (
                        class_names[predicted_index]
                    ),
                    "predicted_class_index": predicted_index,
                    "fold": int(fold),
                }

                for class_index, class_name in enumerate(
                    class_names
                ):
                    record[f"proba_{class_name}"] = float(
                        valid_proba[position, class_index]
                    )

                prediction_records.append(record)

        predictions = (
            pd.DataFrame(prediction_records)
            .sort_values("row_index")
            .reset_index(drop=True)
        )

        fold_metrics = pd.DataFrame(metric_records)

        self._validate_oof_predictions(
            predictions,
            len(dataset),
        )

        return OOFTrainingResult(
            predictions=predictions,
            fold_metrics=fold_metrics,
        )

    def _load_feature_names(
        self,
        dataset: pd.DataFrame,
    ) -> list[str]:
        """Load and validate the frozen feature schema."""

        if self._feature_schema_path is None:
            raise ValueError("feature_schema_path is required.")

        schema = pd.read_parquet(self._feature_schema_path)

        required = {"feature_order", "feature"}
        if not required.issubset(schema.columns):
            raise ValueError(
                "Feature schema must contain "
                "'feature_order' and 'feature'."
            )

        schema = schema.sort_values(
            "feature_order"
        ).reset_index(drop=True)

        feature_names = schema["feature"].astype(str).tolist()

        if len(feature_names) != 42:
            raise ValueError(
                "Frozen v0.2 feature schema must contain exactly 42 features."
            )

        if len(set(feature_names)) != 42:
            raise ValueError(
                "Frozen feature schema contains duplicates."
            )

        missing = [
            name
            for name in feature_names
            if name not in dataset.columns
        ]

        if missing:
            raise ValueError(
                f"Dataset is missing frozen features: {missing}"
            )

        return feature_names

    def _generate_fold_assignments(
        self,
        y: np.ndarray,
    ) -> np.ndarray:
        """Generate the frozen deterministic CV partition."""

        cv_config = self._config.cross_validation

        cv = StratifiedKFold(
            n_splits=cv_config.n_splits,
            shuffle=cv_config.shuffle,
            random_state=cv_config.random_state,
        )

        fold_assignments = np.full(
            len(y),
            -1,
            dtype=int,
        )

        X_dummy = np.zeros(
            (len(y), 1),
            dtype=float,
        )

        for fold_id, (_, valid_idx) in enumerate(
            cv.split(X_dummy, y),
            start=1,
        ):
            fold_assignments[valid_idx] = fold_id

        return fold_assignments

    @staticmethod
    def _validate_fold_assignments(
        fold_ids: np.ndarray,
        expected_rows: int,
    ) -> None:
        """Validate one fold assignment for every row."""

        if len(fold_ids) != expected_rows:
            raise ValueError(
                "Fold-assignment length does not match dataset."
            )

        if np.any(fold_ids < 1):
            raise ValueError(
                "Fold assignments must start at 1."
            )

        unique_folds = np.unique(fold_ids)

        if len(unique_folds) != 5:
            raise ValueError(
                "Frozen v0.2 CV requires exactly five folds."
            )

        if not np.array_equal(
            unique_folds,
            np.arange(1, 6),
        ):
            raise ValueError(
                "Fold assignments must be exactly 1, 2, 3, 4, 5."
            )

        counts = np.bincount(fold_ids)

        if np.any(counts[1:] == 0):
            raise ValueError(
                "Every fold must contain at least one row."
            )

    def _build_model(self) -> XGBClassifier:
        """Build XGBoost using the frozen v0.2 configuration."""

        cfg = self._config.xgboost

        return XGBClassifier(
            n_estimators=cfg.n_estimators,
            max_depth=cfg.max_depth,
            learning_rate=cfg.learning_rate,
            subsample=cfg.subsample,
            colsample_bytree=cfg.colsample_bytree,
            min_child_weight=cfg.min_child_weight,
            reg_alpha=cfg.reg_alpha,
            reg_lambda=cfg.reg_lambda,
            objective=cfg.objective,
            num_class=cfg.num_class,
            eval_metric=cfg.eval_metric,
            tree_method=cfg.tree_method,
            random_state=cfg.random_state,
            n_jobs=cfg.n_jobs,
        )

    @staticmethod
    def _validate_probability_matrix(
        probabilities: np.ndarray,
        expected_rows: int,
    ) -> None:
        """Validate multiclass probability output."""

        if probabilities.shape != (
            expected_rows,
            NUM_CLASSES,
        ):
            raise ValueError(
                "Unexpected XGBoost probability matrix shape."
            )

        if not np.isfinite(probabilities).all():
            raise ValueError(
                "XGBoost produced non-finite probabilities."
            )

        if np.any(probabilities < 0.0):
            raise ValueError(
                "XGBoost produced negative probabilities."
            )

        row_sums = probabilities.sum(axis=1)

        if not np.allclose(
            row_sums,
            1.0,
            rtol=0.0,
            atol=1e-6,
        ):
            raise ValueError(
                "XGBoost probabilities do not sum to one."
            )

    @staticmethod
    def _fold_metrics(
        *,
        fold: int,
        train_n: int,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        probabilities: np.ndarray,
    ) -> dict[str, object]:
        """Calculate historical fold-level classification metrics."""

        labels = np.arange(NUM_CLASSES)

        return {
            "fold": int(fold),
            "train_n": int(train_n),
            "validation_n": len(y_true),
            "accuracy": float(
                accuracy_score(y_true, y_pred)
            ),
            "balanced_accuracy": float(
                balanced_accuracy_score(
                    y_true,
                    y_pred,
                )
            ),
            "macro_f1": float(
                f1_score(
                    y_true,
                    y_pred,
                    average="macro",
                    zero_division=0,
                )
            ),
            "weighted_f1": float(
                f1_score(
                    y_true,
                    y_pred,
                    average="weighted",
                    zero_division=0,
                )
            ),
            "log_loss": float(
                log_loss(
                    y_true,
                    probabilities,
                    labels=labels,
                )
            ),
        }

    @staticmethod
    def _validate_oof_predictions(
        predictions: pd.DataFrame,
        expected_rows: int,
    ) -> None:
        """Validate the canonical OOF prediction table."""

        probability_columns = [
            f"proba_{name}"
            for name in MODEL_CLASSES
        ]

        required_columns = [
            "row_index",
            "true_label",
            "true_class_index",
            "predicted_label",
            "predicted_class_index",
            "fold",
            *probability_columns,
        ]

        if list(predictions.columns) != required_columns:
            raise ValueError(
                "OOF prediction schema does not match "
                "the frozen v0.2 contract."
            )

        if len(predictions) != expected_rows:
            raise ValueError(
                "OOF prediction row count does not match dataset."
            )

        if predictions["row_index"].duplicated().any():
            raise ValueError(
                "OOF predictions contain duplicate row indices."
            )

        expected_indices = np.arange(
            expected_rows,
            dtype=int,
        )

        actual_indices = predictions[
            "row_index"
        ].to_numpy(dtype=int)

        if not np.array_equal(
            actual_indices,
            expected_indices,
        ):
            raise ValueError(
                "OOF row indices are not a complete ordered range."
            )

        if not np.array_equal(
            predictions["true_class_index"].to_numpy(dtype=int),
            predictions["true_label"].map(CLASS_TO_INDEX).to_numpy(
                dtype=int
            ),
        ):
            raise ValueError(
                "OOF true labels do not match frozen class indices."
            )

        if not np.array_equal(
            predictions["predicted_class_index"].to_numpy(dtype=int),
            predictions["predicted_label"].map(
                CLASS_TO_INDEX
            ).to_numpy(dtype=int),
        ):
            raise ValueError(
                "OOF predicted labels do not match class indices."
            )

        XGBoostTrainingEngine._validate_probability_matrix(
            predictions[probability_columns].to_numpy(
                dtype=float
            ),
            expected_rows,
        )

        expected_predictions = np.argmax(
            predictions[probability_columns].to_numpy(
                dtype=float
            ),
            axis=1,
        )

        actual_predictions = predictions[
            "predicted_class_index"
        ].to_numpy(dtype=int)

        if not np.array_equal(
            expected_predictions,
            actual_predictions,
        ):
            raise ValueError(
                "OOF predicted classes do not match "
                "maximum-probability classes."
            )

        fold_ids = predictions["fold"].to_numpy(dtype=int)

        XGBoostTrainingEngine._validate_fold_assignments(
            fold_ids,
            expected_rows,
        )
