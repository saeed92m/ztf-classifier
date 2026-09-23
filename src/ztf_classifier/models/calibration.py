"""Probability calibration for the frozen v0.2 model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.metrics import log_loss


@dataclass(frozen=True)
class CalibrationResult:
    """Temperature-scaling calibration result."""

    temperature: float
    raw_probabilities: np.ndarray
    calibrated_probabilities: np.ndarray
    raw_log_loss: float
    calibrated_log_loss: float

    @property
    def sample_count(self) -> int:
        """Return the number of calibrated samples."""

        return int(self.raw_probabilities.shape[0])


class TemperatureScaler:
    """Fit and apply multiclass temperature scaling."""

    EPSILON = 1e-12
    LOWER_BOUND = 0.05
    UPPER_BOUND = 10.0
    XATOL = 1e-8
    MAX_ITER = 500

    def fit(
        self,
        probabilities: np.ndarray,
        y_true: np.ndarray,
    ) -> CalibrationResult:
        """Fit temperature scaling on probability predictions."""

        probabilities = self._normalize_probabilities(probabilities)
        y_true = np.asarray(y_true, dtype=np.int64)

        self._validate_targets(y_true, len(probabilities))

        logits = np.log(
            np.clip(
                probabilities,
                self.EPSILON,
                1.0,
            )
        )

        optimization = minimize_scalar(
            lambda temperature: self._objective(
                logits,
                y_true,
                temperature,
            ),
            bounds=(
                self.LOWER_BOUND,
                self.UPPER_BOUND,
            ),
            method="bounded",
            options={
                "xatol": self.XATOL,
                "maxiter": self.MAX_ITER,
            },
        )

        if not optimization.success:
            raise RuntimeError(
                "Temperature optimization failed: "
                f"{optimization.message}"
            )

        temperature = float(optimization.x)

        if not np.isfinite(temperature) or temperature <= 0.0:
            raise ValueError(
                "Temperature must be finite and positive."
            )

        calibrated = self._softmax_from_logits(
            logits,
            temperature,
        )

        labels = np.arange(
            probabilities.shape[1],
            dtype=np.int64,
        )

        raw_log_loss = float(
            log_loss(
                y_true,
                probabilities,
                labels=labels,
            )
        )

        calibrated_log_loss = float(
            log_loss(
                y_true,
                calibrated,
                labels=labels,
            )
        )

        return CalibrationResult(
            temperature=temperature,
            raw_probabilities=probabilities.copy(),
            calibrated_probabilities=calibrated,
            raw_log_loss=raw_log_loss,
            calibrated_log_loss=calibrated_log_loss,
        )

    def transform(
        self,
        probabilities: np.ndarray,
        temperature: float,
    ) -> np.ndarray:
        """Apply an already-fitted temperature."""

        probabilities = self._normalize_probabilities(probabilities)

        if not np.isfinite(temperature) or temperature <= 0.0:
            raise ValueError(
                "Temperature must be finite and positive."
            )

        logits = np.log(
            np.clip(
                probabilities,
                self.EPSILON,
                1.0,
            )
        )

        return self._softmax_from_logits(
            logits,
            float(temperature),
        )

    @staticmethod
    def _objective(
        logits: np.ndarray,
        y_true: np.ndarray,
        temperature: float,
    ) -> float:
        """Return multiclass log loss for one temperature."""

        calibrated = TemperatureScaler._softmax_from_logits(
            logits,
            temperature,
        )

        return float(
            log_loss(
                y_true,
                calibrated,
                labels=np.arange(
                    logits.shape[1],
                    dtype=np.int64,
                ),
            )
        )

    @staticmethod
    def _softmax_from_logits(
        logits: np.ndarray,
        temperature: float,
    ) -> np.ndarray:
        """Convert logits to temperature-scaled probabilities."""

        if not np.isfinite(temperature) or temperature <= 0.0:
            raise ValueError(
                "Temperature must be finite and positive."
            )

        scaled = logits / temperature
        scaled = scaled - np.max(
            scaled,
            axis=1,
            keepdims=True,
        )

        exp_scaled = np.exp(scaled)

        return exp_scaled / exp_scaled.sum(
            axis=1,
            keepdims=True,
        )

    @staticmethod
    def _normalize_probabilities(
        probabilities: np.ndarray,
    ) -> np.ndarray:
        """Normalize probability rows as in historical v0.2."""

        probabilities = np.asarray(
            probabilities,
            dtype=np.float64,
        )

        if probabilities.ndim != 2:
            raise ValueError(
                "Probability matrix must be two-dimensional."
            )

        if probabilities.shape[1] != 15:
            raise ValueError(
                "Frozen v0.2 calibration requires 15 classes."
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
            1.0 - normalized[:, :-1].sum(axis=1)
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
            np.arange(15),
        ).all():
            raise ValueError(
                "Target indices must be in the range 0..14."
            )
