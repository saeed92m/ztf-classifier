"""Unified production prediction result contract."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ztf_classifier.models.classes import (
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.ood import OODResult
from ztf_classifier.models.production_conformal import (
    ProductionConformalDiagnostics,
)


@dataclass(frozen=True)
class PredictionResult:
    """Structured classification result with independent diagnostics."""

    raw_probabilities: np.ndarray
    raw_predicted_class_indices: np.ndarray
    raw_predicted_labels: tuple[str, ...]

    calibrated_probabilities: np.ndarray | None = None
    calibrated_predicted_class_indices: np.ndarray | None = None
    calibrated_predicted_labels: tuple[str, ...] | None = None

    conformal: ProductionConformalDiagnostics | None = None
    ood: OODResult | None = None
    calibration_status: str = "unavailable"
    conformal_status: str = "unavailable"
    ood_status: str = "unavailable"
    warnings: tuple[str, ...] = ()
    artifact_schema_version: str = ""
    artifact_hash: str = ""
    feature_schema_hash: str = ""
    software_version: str = ""
    model_version: str = ""

    def __post_init__(self) -> None:
        """Validate the result contract."""

        raw_probabilities = np.array(
            self.raw_probabilities,
            dtype=np.float64,
            copy=True,
        )
        raw_probabilities.setflags(write=False)

        raw_indices = np.array(
            self.raw_predicted_class_indices,
            dtype=np.int64,
            copy=True,
        )
        raw_indices.setflags(write=False)

        object.__setattr__(
            self,
            "raw_probabilities",
            raw_probabilities,
        )
        object.__setattr__(
            self,
            "raw_predicted_class_indices",
            raw_indices,
        )

        self._validate_probability_matrix(
            raw_probabilities,
            "raw",
        )

        self._validate_predictions(
            raw_indices,
            self.raw_predicted_labels,
            len(raw_probabilities),
            "raw",
        )

        if (
            self.calibrated_probabilities is None
            and (
                self.calibrated_predicted_class_indices is not None
                or self.calibrated_predicted_labels is not None
            )
        ):
            raise ValueError(
                "Calibrated predictions require calibrated probabilities."
            )

        if self.calibrated_probabilities is not None:
            calibrated = np.array(
                self.calibrated_probabilities,
                dtype=np.float64,
                copy=True,
            )
            calibrated.setflags(write=False)

            object.__setattr__(
                self,
                "calibrated_probabilities",
                calibrated,
            )

            self._validate_probability_matrix(
                calibrated,
                "calibrated",
            )

            if (
                self.calibrated_predicted_class_indices is None
                or self.calibrated_predicted_labels is None
            ):
                raise ValueError(
                    "Calibrated probabilities require calibrated "
                    "predictions."
                )

            calibrated_indices = np.array(
                self.calibrated_predicted_class_indices,
                dtype=np.int64,
                copy=True,
            )
            calibrated_indices.setflags(write=False)

            object.__setattr__(
                self,
                "calibrated_predicted_class_indices",
                calibrated_indices,
            )

            self._validate_predictions(
                calibrated_indices,
                self.calibrated_predicted_labels,
                len(calibrated),
                "calibrated",
            )

        self._validate_optional_diagnostics()
        self._validate_status_metadata()

    @property
    def sample_count(self) -> int:
        """Return the number of classified samples."""

        return int(self.raw_probabilities.shape[0])

    @property
    def has_calibration(self) -> bool:
        """Return whether calibrated probabilities are available."""

        return self.calibrated_probabilities is not None

    @property
    def has_conformal(self) -> bool:
        """Return whether conformal diagnostics are attached."""

        return self.conformal is not None

    @property
    def has_ood(self) -> bool:
        """Return whether OOD diagnostics are attached."""

        return self.ood is not None

    @property
    def top1_labels(self) -> tuple[str, ...]:
        """Return the preferred top-1 labels."""

        if self.calibrated_predicted_labels is not None:
            return self.calibrated_predicted_labels

        return self.raw_predicted_labels

    @property
    def top1_class_indices(self) -> np.ndarray:
        """Return the preferred top-1 class indices."""

        if self.calibrated_predicted_class_indices is not None:
            return self.calibrated_predicted_class_indices

        return self.raw_predicted_class_indices

    @staticmethod
    def _validate_probability_matrix(
        probabilities: np.ndarray,
        name: str,
    ) -> None:
        """Validate a multiclass probability matrix."""

        if probabilities.ndim != 2:
            raise ValueError(
                f"{name.capitalize()} probabilities must be two-dimensional."
            )

        if probabilities.shape[1] != NUM_CLASSES:
            raise ValueError(
                f"{name.capitalize()} probabilities must contain "
                f"{NUM_CLASSES} classes."
            )

        if not np.isfinite(probabilities).all():
            raise ValueError(
                f"{name.capitalize()} probabilities contain non-finite values."
            )

        if (probabilities < 0.0).any():
            raise ValueError(
                f"{name.capitalize()} probabilities contain negative values."
            )

        if not np.allclose(
            probabilities.sum(axis=1),
            1.0,
            rtol=0.0,
            atol=1e-6,
        ):
            raise ValueError(
                f"{name.capitalize()} probabilities do not sum to one."
            )

    @staticmethod
    def _validate_predictions(
        indices: np.ndarray,
        labels: tuple[str, ...],
        expected_rows: int,
        name: str,
    ) -> None:
        """Validate class indices and labels."""

        if indices.ndim != 1:
            raise ValueError(
                f"{name.capitalize()} class indices must be one-dimensional."
            )

        if len(indices) != expected_rows:
            raise ValueError(
                f"{name.capitalize()} class indices have invalid length."
            )

        if len(labels) != expected_rows:
            raise ValueError(
                f"{name.capitalize()} labels have invalid length."
            )

        if not np.isin(
            indices,
            np.arange(NUM_CLASSES),
        ).all():
            raise ValueError(
                f"{name.capitalize()} class indices are out of range."
            )

        expected_labels = tuple(
            MODEL_CLASSES[index]
            for index in indices
        )

        if labels != expected_labels:
            raise ValueError(
                f"{name.capitalize()} labels do not match class indices."
            )

    def _validate_status_metadata(self) -> None:
        """Validate additive production diagnostic status metadata."""
        valid = {"available", "unavailable", "uncalibrated"}
        for name, value in (
            ("calibration_status", self.calibration_status),
            ("conformal_status", self.conformal_status),
            ("ood_status", self.ood_status),
        ):
            if value not in valid:
                raise ValueError(f"{name} has an invalid status: {value}")
        if not isinstance(self.warnings, tuple):
            raise TypeError("warnings must be a tuple of strings.")
        if not all(isinstance(item, str) for item in self.warnings):
            raise ValueError("warnings must contain only strings.")

    def _validate_optional_diagnostics(self) -> None:
        """Validate alignment of optional diagnostic results."""

        if (
            self.conformal is not None
            and self.conformal.sample_count != self.sample_count
        ):
            raise ValueError(
                "Conformal result sample count does not match "
                "prediction result."
            )

        if (
            self.ood is not None
            and self.ood.sample_count != self.sample_count
        ):
            raise ValueError(
                "OOD result sample count does not match "
                "prediction result."
            )


__all__ = ["PredictionResult"]
