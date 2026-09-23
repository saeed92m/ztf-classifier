"""Out-of-distribution diagnostic engine matching the frozen v0.2 protocol."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

from ztf_classifier.models.config import OODConfig


@dataclass(frozen=True)
class OODResult:
    """Per-sample OOD diagnostic results."""

    anomaly_score: np.ndarray
    normality_score: np.ndarray
    anomaly_percentile: np.ndarray
    isolation_forest_label: np.ndarray
    anomaly_rank: np.ndarray
    is_top_1pct_anomaly: np.ndarray
    is_top_5pct_anomaly: np.ndarray
    is_top_10pct_anomaly: np.ndarray

    @property
    def sample_count(self) -> int:
        """Return the number of evaluated samples."""

        return int(self.anomaly_score.shape[0])


class IsolationForestOOD:
    """Compute leakage-safe fold-based IsolationForest diagnostics."""

    def __init__(self, config: OODConfig | None = None) -> None:
        self.config = config or OODConfig()

    def fit_predict(
        self,
        X: np.ndarray,
        folds: np.ndarray,
    ) -> OODResult:
        """Evaluate OOD scores using train-fitted preprocessing per fold."""

        X = np.asarray(X, dtype=np.float64)
        folds = np.asarray(folds, dtype=np.int64)

        self._validate_inputs(X, folds)

        n_samples = X.shape[0]

        anomaly_score = np.empty(n_samples, dtype=np.float64)
        normality_score = np.empty(n_samples, dtype=np.float64)
        anomaly_percentile = np.empty(n_samples, dtype=np.float64)
        isolation_forest_label = np.empty(n_samples, dtype=np.int64)

        for fold in np.unique(folds):
            test_mask = folds == fold
            train_mask = ~test_mask

            X_train = X[train_mask]
            X_test = X[test_mask]

            imputer = SimpleImputer(strategy="median")
            X_train_imputed = imputer.fit_transform(X_train)
            X_test_imputed = imputer.transform(X_test)

            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train_imputed)
            X_test_scaled = scaler.transform(X_test_imputed)

            model = IsolationForest(
                n_estimators=self.config.n_estimators,
                contamination=self.config.contamination,
                random_state=self.config.random_state,
                n_jobs=self.config.n_jobs,
            )

            model.fit(X_train_scaled)

            test_normality = model.score_samples(X_test_scaled)
            test_anomaly = -test_normality
            test_labels = model.predict(X_test_scaled)

            train_normality = model.score_samples(X_train_scaled)
            train_anomaly = -train_normality

            test_indices = np.flatnonzero(test_mask)

            for position, index in enumerate(test_indices):
                score = test_anomaly[position]

                anomaly_score[index] = score
                normality_score[index] = -score

                anomaly_percentile[index] = (
                    100.0
                    * np.mean(train_anomaly <= score)
                )

                isolation_forest_label[index] = test_labels[position]

        anomaly_rank = self._rank_descending(anomaly_score)

        is_top_1pct_anomaly = anomaly_percentile >= 99.0
        is_top_5pct_anomaly = anomaly_percentile >= 95.0
        is_top_10pct_anomaly = anomaly_percentile >= 90.0

        return OODResult(
            anomaly_score=anomaly_score,
            normality_score=normality_score,
            anomaly_percentile=anomaly_percentile,
            isolation_forest_label=isolation_forest_label,
            anomaly_rank=anomaly_rank,
            is_top_1pct_anomaly=is_top_1pct_anomaly,
            is_top_5pct_anomaly=is_top_5pct_anomaly,
            is_top_10pct_anomaly=is_top_10pct_anomaly,
        )

    @staticmethod
    def _rank_descending(values: np.ndarray) -> np.ndarray:
        """Return zero-based descending anomaly ranks."""

        order = np.argsort(
            -values,
            kind="mergesort",
        )

        ranks = np.empty(
            len(values),
            dtype=np.int64,
        )
        ranks[order] = np.arange(len(values)) + 1

        return ranks

    @staticmethod
    def _validate_inputs(
        X: np.ndarray,
        folds: np.ndarray,
    ) -> None:
        """Validate the frozen OOD input contract."""

        if X.ndim != 2:
            raise ValueError(
                "Feature matrix must be two-dimensional."
            )

        if X.shape[1] != 42:
            raise ValueError(
                "Frozen v0.2 OOD detection requires 42 features."
            )

        if len(X) == 0:
            raise ValueError(
                "OOD detection requires at least one sample."
            )

        if folds.ndim != 1:
            raise ValueError(
                "Fold assignments must be one-dimensional."
            )

        if len(folds) != len(X):
            raise ValueError(
                "Fold assignments must match feature rows."
            )

        if not np.isfinite(folds).all():
            raise ValueError(
                "Fold assignments must be finite."
            )

        if not np.isfinite(X).any():
            raise ValueError(
                "Feature matrix contains no finite values."
            )
