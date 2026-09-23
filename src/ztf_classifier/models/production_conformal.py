"""Production conformal prediction diagnostics from persisted artifacts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ztf_classifier.models.classes import MODEL_CLASSES, NUM_CLASSES
from ztf_classifier.models.conformal_artifact import ConformalArtifact


@dataclass(frozen=True)
class ProductionConformalResult:
    """Prediction-set diagnostics for one persisted conformal alpha."""

    alpha: float
    threshold: float
    prediction_sets: np.ndarray
    prediction_set_labels: tuple[str, ...]

    def __post_init__(self) -> None:
        prediction_sets = np.asarray(
            self.prediction_sets,
            dtype=bool,
        ).copy()
        prediction_sets.setflags(write=False)

        if prediction_sets.ndim != 2:
            raise ValueError(
                "Prediction sets must be two-dimensional."
            )

        if prediction_sets.shape[1] != NUM_CLASSES:
            raise ValueError(
                f"Prediction sets must contain {NUM_CLASSES} classes."
            )

        if not np.isfinite(self.alpha):
            raise ValueError("Alpha must be finite.")

        if not 0.0 < self.alpha < 1.0:
            raise ValueError("Alpha must be between 0 and 1.")

        if not np.isfinite(self.threshold):
            raise ValueError("Threshold must be finite.")

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(
                "Threshold must be between 0 and 1."
            )

        if len(self.prediction_set_labels) != len(prediction_sets):
            raise ValueError(
                "Prediction-set labels have invalid length."
            )

        expected_labels = tuple(
            "|".join(
                MODEL_CLASSES[index]
                for index in np.flatnonzero(row)
            )
            for row in prediction_sets
        )

        if self.prediction_set_labels != expected_labels:
            raise ValueError(
                "Prediction-set labels do not match prediction sets."
            )

        object.__setattr__(
            self,
            "prediction_sets",
            prediction_sets,
        )

    @property
    def sample_count(self) -> int:
        """Return the number of classified samples."""

        return int(self.prediction_sets.shape[0])


@dataclass(frozen=True)
class ProductionConformalDiagnostics:
    """All persisted conformal prediction-set diagnostics."""

    results: tuple[ProductionConformalResult, ...]

    def __post_init__(self) -> None:
        if not self.results:
            raise ValueError(
                "Production conformal diagnostics require at least one result."
            )

        alphas = tuple(result.alpha for result in self.results)

        if alphas != tuple(sorted(alphas)):
            raise ValueError(
                "Production conformal alphas must be sorted."
            )

        if len(set(alphas)) != len(alphas):
            raise ValueError(
                "Production conformal alphas must be unique."
            )

        sample_counts = {
            result.sample_count
            for result in self.results
        }

        if len(sample_counts) != 1:
            raise ValueError(
                "Production conformal result sample counts must match."
            )

    @property
    def sample_count(self) -> int:
        """Return the number of classified samples."""

        return self.results[0].sample_count

    def for_alpha(
        self,
        alpha: float,
    ) -> ProductionConformalResult:
        """Return the persisted result for one alpha."""

        for result in self.results:
            if result.alpha == alpha:
                return result

        raise KeyError(
            f"No persisted conformal result exists for alpha={alpha}."
        )

    @classmethod
    def predict(
        cls,
        probabilities: np.ndarray,
        artifact: ConformalArtifact,
    ) -> ProductionConformalDiagnostics:
        """Generate prediction sets from persisted conformal thresholds."""

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
                f"Probability matrix must contain {NUM_CLASSES} classes."
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

        results: list[ProductionConformalResult] = []

        for alpha in artifact.alphas:
            threshold = artifact.threshold_for(alpha)

            prediction_sets = (
                probabilities >= (1.0 - threshold)
            )

            labels = tuple(
                "|".join(
                    MODEL_CLASSES[index]
                    for index in np.flatnonzero(row)
                )
                for row in prediction_sets
            )

            results.append(
                ProductionConformalResult(
                    alpha=float(alpha),
                    threshold=float(threshold),
                    prediction_sets=prediction_sets,
                    prediction_set_labels=labels,
                )
            )

        return cls(results=tuple(results))


__all__ = [
    "ProductionConformalDiagnostics",
    "ProductionConformalResult",
]
