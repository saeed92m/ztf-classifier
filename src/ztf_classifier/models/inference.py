"""Deterministic XGBoost inference engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ztf_classifier.models.classes import (
    MODEL_CLASSES,
    NUM_CLASSES,
)


@dataclass(frozen=True)
class InferenceResult:
    """Deterministic multiclass inference result."""

    probabilities: np.ndarray
    predicted_class_indices: np.ndarray
    predicted_labels: tuple[str, ...]

    @property
    def row_count(self) -> int:
        """Return the number of inferred rows."""
        return int(self.probabilities.shape[0])


class XGBoostInferenceEngine:
    """Run deterministic inference with a fitted XGBoost model."""

    def __init__(
        self,
        *,
        model: Any,
        feature_schema_path: Path,
    ) -> None:
        if model is None:
            raise ValueError(
                "XGBoostInferenceEngine requires a fitted model."
            )

        self._model = model
        self._feature_schema_path = Path(feature_schema_path)

    def predict(
        self,
        dataset: pd.DataFrame,
    ) -> InferenceResult:
        """Predict class probabilities and labels."""

        X = self.prepare_features(dataset)

        probabilities = np.asarray(
            self._model.predict_proba(X),
            dtype=float,
        )

        self._validate_probability_matrix(
            probabilities,
            len(X),
        )

        predicted_indices = np.argmax(
            probabilities,
            axis=1,
        ).astype(int)

        predicted_labels = tuple(
            MODEL_CLASSES[index]
            for index in predicted_indices
        )

        return InferenceResult(
            probabilities=probabilities,
            predicted_class_indices=predicted_indices,
            predicted_labels=predicted_labels,
        )

    def prepare_features(
        self,
        dataset: pd.DataFrame,
    ) -> pd.DataFrame:
        """Prepare exactly the frozen 42 model features."""

        feature_names = self._load_feature_names(dataset)

        X = dataset.loc[:, feature_names].copy()
        X = X.apply(pd.to_numeric, errors="coerce")
        X = X.replace([np.inf, -np.inf], np.nan)

        if X.shape[1] != 42:
            raise ValueError(
                "Frozen v0.2 model requires exactly 42 features."
            )

        return X

    def _load_feature_names(
        self,
        dataset: pd.DataFrame,
    ) -> list[str]:
        """Load and validate the frozen feature schema."""

        if not self._feature_schema_path.exists():
            raise FileNotFoundError(
                "Feature schema does not exist: "
                f"{self._feature_schema_path}"
            )

        schema = pd.read_parquet(
            self._feature_schema_path
        )

        required = {"feature_order", "feature"}

        if not required.issubset(schema.columns):
            raise ValueError(
                "Feature schema must contain "
                "feature_order and feature columns."
            )

        ordered = schema.sort_values(
            "feature_order"
        )

        feature_names = ordered["feature"].astype(str).tolist()

        if len(feature_names) != 42:
            raise ValueError(
                "Frozen v0.2 feature schema must contain "
                "exactly 42 features."
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
                f"Dataset is missing model features: {missing}"
            )

        return feature_names

    @staticmethod
    def _validate_probability_matrix(
        probabilities: np.ndarray,
        expected_rows: int,
    ) -> None:
        """Validate the XGBoost probability matrix."""

        if probabilities.shape != (
            expected_rows,
            NUM_CLASSES,
        ):
            raise ValueError(
                "Probability matrix has invalid shape: "
                f"{probabilities.shape}"
            )

        if not np.isfinite(probabilities).all():
            raise ValueError(
                "XGBoost probabilities contain non-finite values."
            )

        if (probabilities < 0.0).any():
            raise ValueError(
                "XGBoost probabilities contain negative values."
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
