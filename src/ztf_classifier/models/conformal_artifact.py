"""Serialization contract for production conformal prediction state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ztf_classifier.models.classes import MODEL_CLASSES, NUM_CLASSES

CONFORMAL_ARTIFACT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ConformalArtifact:
    """Immutable fitted state for production conformal prediction."""

    method: str
    alphas: tuple[float, ...]
    thresholds: tuple[float, ...]
    calibration_sample_count: int
    classes: tuple[str, ...] = MODEL_CLASSES

    def __post_init__(self) -> None:
        if self.method != "split_conformal_ood_diagnostic":
            raise ValueError(
                "Unsupported conformal method: "
                f"{self.method!r}"
            )

        if not self.alphas:
            raise ValueError(
                "At least one conformal alpha is required."
            )

        if len(self.alphas) != len(self.thresholds):
            raise ValueError(
                "Conformal alphas and thresholds must have equal length."
            )

        if len(set(self.alphas)) != len(self.alphas):
            raise ValueError(
                "Conformal alpha values must be unique."
            )

        if tuple(sorted(self.alphas)) != self.alphas:
            raise ValueError(
                "Conformal alpha values must be sorted ascending."
            )

        for alpha in self.alphas:
            if not np.isfinite(alpha) or not 0.0 < alpha < 1.0:
                raise ValueError(
                    "Conformal alpha values must be in (0, 1)."
                )

        for threshold in self.thresholds:
            if (
                not np.isfinite(threshold)
                or not 0.0 <= threshold <= 1.0
            ):
                raise ValueError(
                    "Conformal thresholds must be in [0, 1]."
                )

        if self.calibration_sample_count <= 0:
            raise ValueError(
                "Calibration sample count must be positive."
            )

        if len(self.classes) != NUM_CLASSES:
            raise ValueError(
                "Conformal artifact must contain exactly 15 classes."
            )

        if self.classes != MODEL_CLASSES:
            raise ValueError(
                "Conformal artifact classes must match "
                "the frozen class order."
            )

    @classmethod
    def from_results(
        cls,
        results: tuple[Any, ...],
    ) -> ConformalArtifact:
        """Build a production artifact from fitted conformal results."""

        if not results:
            raise ValueError(
                "At least one conformal result is required."
            )

        alphas = tuple(
            float(result.alpha)
            for result in results
        )

        thresholds = tuple(
            float(result.threshold)
            for result in results
        )

        sample_counts = {
            int(result.sample_count)
            for result in results
        }

        if len(sample_counts) != 1:
            raise ValueError(
                "All conformal results must use the same "
                "calibration sample count."
            )

        return cls(
            method="split_conformal_ood_diagnostic",
            alphas=alphas,
            thresholds=thresholds,
            calibration_sample_count=sample_counts.pop(),
        )

    def threshold_for(self, alpha: float) -> float:
        """Return the persisted threshold for an alpha."""

        alpha = float(alpha)

        for stored_alpha, threshold in zip(
            self.alphas,
            self.thresholds,
        ):
            if stored_alpha == alpha:
                return threshold

        raise ValueError(
            f"Unsupported conformal alpha: {alpha!r}"
        )

    def predict_sets(
        self,
        probabilities: np.ndarray,
        alpha: float,
    ) -> np.ndarray:
        """Apply the persisted conformal threshold to probabilities."""

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
                "Probability matrix must contain 15 classes."
            )

        if not np.isfinite(probabilities).all():
            raise ValueError(
                "Probability matrix contains non-finite values."
            )

        if (probabilities < 0.0).any():
            raise ValueError(
                "Probability matrix contains negative values."
            )

        if not np.allclose(
            probabilities.sum(axis=1),
            1.0,
            rtol=0.0,
            atol=1e-6,
        ):
            raise ValueError(
                "Probability rows must sum to one."
            )

        threshold = self.threshold_for(alpha)

        prediction_sets = (
            probabilities >= (1.0 - threshold)
        )

        return prediction_sets.copy()

    def prediction_set_labels(
        self,
        probabilities: np.ndarray,
        alpha: float,
    ) -> tuple[str, ...]:
        """Return pipe-delimited labels for production prediction sets."""

        prediction_sets = self.predict_sets(
            probabilities,
            alpha,
        )

        return tuple(
            "|".join(
                MODEL_CLASSES[index]
                for index in np.flatnonzero(row)
            )
            for row in prediction_sets
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the stable serialized representation."""

        return {
            "schema_version": CONFORMAL_ARTIFACT_SCHEMA_VERSION,
            "method": self.method,
            "alphas": list(self.alphas),
            "thresholds": list(self.thresholds),
            "calibration_sample_count": (
                self.calibration_sample_count
            ),
            "classes": list(self.classes),
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> ConformalArtifact:
        """Reconstruct a conformal artifact from serialized data."""

        if not isinstance(payload, dict):
            raise TypeError(
                "Conformal artifact payload must be a dictionary."
            )

        if (
            payload.get("schema_version")
            != CONFORMAL_ARTIFACT_SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported conformal artifact schema version."
            )

        method = payload.get("method")
        alphas = payload.get("alphas")
        thresholds = payload.get("thresholds")
        sample_count = payload.get("calibration_sample_count")
        classes = payload.get("classes")

        if not isinstance(method, str):
            raise TypeError(
                "Conformal method must be a string."
            )

        if not isinstance(alphas, list):
            raise TypeError(
                "Conformal alphas must be a list."
            )

        if not isinstance(thresholds, list):
            raise TypeError(
                "Conformal thresholds must be a list."
            )

        if not isinstance(sample_count, int):
            raise TypeError(
                "Calibration sample count must be an integer."
            )

        if classes != list(MODEL_CLASSES):
            raise ValueError(
                "Conformal artifact classes do not match "
                "the frozen class order."
            )

        return cls(
            method=method,
            alphas=tuple(float(value) for value in alphas),
            thresholds=tuple(
                float(value)
                for value in thresholds
            ),
            calibration_sample_count=sample_count,
            classes=tuple(classes),
        )
