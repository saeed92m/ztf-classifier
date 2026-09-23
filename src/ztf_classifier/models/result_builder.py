"""Assembly of independent model outputs into a production result."""

from __future__ import annotations

import numpy as np

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.conformal import ConformalResult
from ztf_classifier.models.inference import InferenceResult
from ztf_classifier.models.ood import OODResult
from ztf_classifier.models.results import PredictionResult


class PredictionResultBuilder:
    """Assemble independent inference and diagnostic results."""

    @staticmethod
    def build(
        inference: InferenceResult,
        *,
        calibrated_probabilities: np.ndarray | None = None,
        conformal: ConformalResult | None = None,
        ood: OODResult | None = None,
    ) -> PredictionResult:
        """Build a unified prediction result."""

        calibrated_indices: np.ndarray | None = None
        calibrated_labels: tuple[str, ...] | None = None

        if calibrated_probabilities is not None:
            calibrated_probabilities = np.asarray(
                calibrated_probabilities,
                dtype=np.float64,
            )

            calibrated_indices = np.argmax(
                calibrated_probabilities,
                axis=1,
            ).astype(np.int64)

            calibrated_labels = tuple(
                MODEL_CLASSES[index]
                for index in calibrated_indices
            )

        return PredictionResult(
            raw_probabilities=inference.probabilities,
            raw_predicted_class_indices=(
                inference.predicted_class_indices
            ),
            raw_predicted_labels=inference.predicted_labels,
            calibrated_probabilities=calibrated_probabilities,
            calibrated_predicted_class_indices=calibrated_indices,
            calibrated_predicted_labels=calibrated_labels,
            conformal=conformal,
            ood=ood,
        )


__all__ = ["PredictionResultBuilder"]
