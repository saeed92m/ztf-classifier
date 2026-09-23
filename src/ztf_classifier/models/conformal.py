"""Empirical OOF conformal prediction diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ztf_classifier.models.classes import (
    MODEL_CLASSES,
    NUM_CLASSES,
)


@dataclass(frozen=True)
class ConformalSummary:
    """Summary statistics for one conformal alpha."""

    alpha: float
    nominal_coverage: float
    sample_count: int
    n_classes: int
    threshold: float
    coverage: float
    mean_set_size: float
    singleton_rate: float
    empty_rate: float
    multi_class_rate: float


@dataclass(frozen=True)
class ConformalResult:
    """Prediction-set result for one conformal alpha."""

    alpha: float
    threshold: float
    probabilities: np.ndarray
    true_class_indices: np.ndarray
    prediction_sets: np.ndarray
    covered: np.ndarray
    set_sizes: np.ndarray
    summary: ConformalSummary

    @property
    def sample_count(self) -> int:
        """Return the number of evaluated samples."""

        return int(self.probabilities.shape[0])


class EmpiricalConformalPredictor:
    """Compute empirical OOF conformal prediction sets."""

    ALPHAS = (0.05, 0.10, 0.20)

    def fit(
        self,
        probabilities: np.ndarray,
        y_true: np.ndarray,
        alpha: float,
    ) -> ConformalResult:
        """Fit an empirical conformal diagnostic from OOF probabilities."""

        probabilities = self._normalize_probabilities(probabilities)
        y_true = np.asarray(y_true, dtype=np.int64)

        self._validate_targets(
            y_true,
            len(probabilities),
        )
        self._validate_alpha(alpha)

        true_probabilities = probabilities[
            np.arange(len(y_true)),
            y_true,
        ]

        scores = 1.0 - true_probabilities

        threshold = self._conformal_quantile(
            scores,
            alpha,
        )

        prediction_sets = (
            probabilities >= (1.0 - threshold)
        )

        covered = prediction_sets[
            np.arange(len(y_true)),
            y_true,
        ]

        set_sizes = prediction_sets.sum(
            axis=1,
            dtype=np.int64,
        )

        sample_count = len(y_true)

        coverage = float(
            covered.mean()
        )

        mean_set_size = float(
            set_sizes.mean()
        )

        singleton_rate = float(
            (set_sizes == 1).mean()
        )

        empty_rate = float(
            (set_sizes == 0).mean()
        )

        multi_class_rate = float(
            (set_sizes > 1).mean()
        )

        summary = ConformalSummary(
            alpha=float(alpha),
            nominal_coverage=float(1.0 - alpha),
            sample_count=sample_count,
            n_classes=NUM_CLASSES,
            threshold=float(threshold),
            coverage=coverage,
            mean_set_size=mean_set_size,
            singleton_rate=singleton_rate,
            empty_rate=empty_rate,
            multi_class_rate=multi_class_rate,
        )

        return ConformalResult(
            alpha=float(alpha),
            threshold=float(threshold),
            probabilities=probabilities.copy(),
            true_class_indices=y_true.copy(),
            prediction_sets=prediction_sets,
            covered=covered,
            set_sizes=set_sizes,
            summary=summary,
        )

    def fit_all(
        self,
        probabilities: np.ndarray,
        y_true: np.ndarray,
    ) -> tuple[ConformalResult, ...]:
        """Compute diagnostics for all historical alpha values."""

        return tuple(
            self.fit(
                probabilities,
                y_true,
                alpha,
            )
            for alpha in self.ALPHAS
        )

    @staticmethod
    def prediction_set_labels(
        prediction_sets: np.ndarray,
    ) -> tuple[str, ...]:
        """Convert boolean prediction sets to ordered class labels."""

        prediction_sets = np.asarray(
            prediction_sets,
            dtype=bool,
        )

        if prediction_sets.ndim != 2:
            raise ValueError(
                "Prediction sets must be two-dimensional."
            )

        if prediction_sets.shape[1] != NUM_CLASSES:
            raise ValueError(
                "Prediction sets must contain 15 classes."
            )

        return tuple(
            "|".join(
                MODEL_CLASSES[index]
                for index in np.flatnonzero(row)
            )
            for row in prediction_sets
        )

    @staticmethod
    def _conformal_quantile(
        scores: np.ndarray,
        alpha: float,
    ) -> float:
        """Return the exact finite-sample empirical quantile."""

        scores = np.asarray(
            scores,
            dtype=np.float64,
        )

        if scores.ndim != 1:
            raise ValueError(
                "Conformal scores must be one-dimensional."
            )

        n_samples = len(scores)

        if n_samples == 0:
            raise ValueError(
                "Conformal calibration requires at least one sample."
            )

        k = int(
            np.ceil(
                (n_samples + 1)
                * (1.0 - alpha)
            )
        )

        k = min(
            max(k, 1),
            n_samples,
        )

        sorted_scores = np.sort(scores)

        return float(
            sorted_scores[k - 1]
        )

    @staticmethod
    def _normalize_probabilities(
        probabilities: np.ndarray,
    ) -> np.ndarray:
        """Normalize probability rows using the historical contract."""

        probabilities = np.asarray(
            probabilities,
            dtype=np.float64,
        )

        if probabilities.ndim != 2:
            raise ValueError(
                "Probability matrix must be two-dimensional."
            )

        if probabilities.shape[1] != NUM_CLASSES:
            raise ValueError(
                "Frozen v0.2 conformal prediction requires "
                "15 classes."
            )

        if not np.isfinite(probabilities).all():
            raise ValueError(
                "Probability matrix contains non-finite values."
            )

        if (probabilities < 0.0).any():
            raise ValueError(
                "Probability matrix contains negative values."
            )

        row_sums = probabilities.sum(axis=1)

        if (row_sums <= 0.0).any():
            raise ValueError(
                "Probability rows must have positive sums."
            )

        normalized = probabilities / row_sums[:, None]

        normalized[:, -1] = (
            1.0
            - normalized[:, :-1].sum(axis=1)
        )

        if (normalized < 0.0).any():
            raise ValueError(
                "Normalized probabilities contain negative values."
            )

        if not np.allclose(
            normalized.sum(axis=1),
            1.0,
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError(
                "Normalized probabilities do not sum to one."
            )

        return normalized

    @staticmethod
    def _validate_targets(
        y_true: np.ndarray,
        expected_rows: int,
    ) -> None:
        """Validate frozen multiclass target indices."""

        if y_true.ndim != 1:
            raise ValueError(
                "Target array must be one-dimensional."
            )

        if len(y_true) != expected_rows:
            raise ValueError(
                "Target length does not match probability rows."
            )

        if not np.isin(
            y_true,
            np.arange(NUM_CLASSES),
        ).all():
            raise ValueError(
                "Target indices must be in the range 0..14."
            )

    @classmethod
    def _validate_alpha(cls, alpha: float) -> None:
        """Validate a supported conformal miscoverage level."""

        if not np.isfinite(alpha):
            raise ValueError(
                "Alpha must be finite."
            )

        if alpha <= 0.0 or alpha >= 1.0:
            raise ValueError(
                "Alpha must be between 0 and 1."
            )
