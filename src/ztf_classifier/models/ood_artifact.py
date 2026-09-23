"""Serialization contract for production OOD detection state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ztf_classifier.models.config import OODConfig

OOD_ARTIFACT_SCHEMA_VERSION = "1.0"
OOD_FEATURE_COUNT = 42


@dataclass(frozen=True)
class OODArtifact:
    """Immutable production OOD reference state."""

    method: str
    n_estimators: int
    contamination: str
    random_state: int
    n_jobs: int
    anomaly_thresholds: tuple[float, ...]
    feature_count: int
    reference_anomaly_scores: tuple[float, ...]

    def __post_init__(self) -> None:
        if self.method != "IsolationForest":
            raise ValueError(
                "Unsupported OOD method: "
                f"{self.method!r}"
            )

        if self.n_estimators <= 0:
            raise ValueError(
                "OOD n_estimators must be positive."
            )

        if self.contamination != "auto":
            raise ValueError(
                "Frozen OOD contamination must be auto."
            )

        if self.n_jobs <= 0:
            raise ValueError(
                "OOD n_jobs must be positive."
            )

        if self.feature_count != OOD_FEATURE_COUNT:
            raise ValueError(
                "OOD artifact must contain exactly 42 features."
            )

        if not self.anomaly_thresholds:
            raise ValueError(
                "At least one OOD anomaly threshold is required."
            )

        if (
            tuple(sorted(self.anomaly_thresholds))
            != self.anomaly_thresholds
        ):
            raise ValueError(
                "OOD anomaly thresholds must be sorted ascending."
            )

        if len(set(self.anomaly_thresholds)) != len(
            self.anomaly_thresholds
        ):
            raise ValueError(
                "OOD anomaly thresholds must be unique."
            )

        for threshold in self.anomaly_thresholds:
            if (
                not np.isfinite(threshold)
                or not 0.0 <= threshold <= 100.0
            ):
                raise ValueError(
                    "OOD anomaly thresholds must be "
                    "percentages in [0, 100]."
                )

        scores = np.asarray(
            self.reference_anomaly_scores,
            dtype=np.float64,
        )

        if scores.ndim != 1:
            raise ValueError(
                "Reference anomaly scores must be one-dimensional."
            )

        if len(scores) == 0:
            raise ValueError(
                "Reference anomaly scores must not be empty."
            )

        if not np.isfinite(scores).all():
            raise ValueError(
                "Reference anomaly scores must be finite."
            )

    @classmethod
    def from_config(
        cls,
        config: OODConfig,
        reference_anomaly_scores: np.ndarray,
    ) -> OODArtifact:
        """Build an artifact from frozen OOD configuration and scores."""

        scores = np.asarray(
            reference_anomaly_scores,
            dtype=np.float64,
        )

        return cls(
            method=config.method,
            n_estimators=config.n_estimators,
            contamination=config.contamination,
            random_state=config.random_state,
            n_jobs=config.n_jobs,
            anomaly_thresholds=tuple(
                float(value)
                for value in config.anomaly_thresholds
            ),
            feature_count=OOD_FEATURE_COUNT,
            reference_anomaly_scores=tuple(
                float(value)
                for value in scores
            ),
        )

    def anomaly_percentile(
        self,
        anomaly_scores: np.ndarray,
    ) -> np.ndarray:
        """Return reference-relative anomaly percentiles."""

        scores = np.asarray(
            anomaly_scores,
            dtype=np.float64,
        )

        if scores.ndim != 1:
            raise ValueError(
                "Anomaly scores must be one-dimensional."
            )

        if not np.isfinite(scores).all():
            raise ValueError(
                "Anomaly scores must be finite."
            )

        reference = np.asarray(
            self.reference_anomaly_scores,
            dtype=np.float64,
        )

        return (
            100.0
            * np.mean(
                reference[None, :] <= scores[:, None],
                axis=1,
            )
        )

    def anomaly_rank(
        self,
        anomaly_scores: np.ndarray,
    ) -> np.ndarray:
        """Return reference-relative one-based anomaly ranks."""

        scores = np.asarray(
            anomaly_scores,
            dtype=np.float64,
        )

        if scores.ndim != 1:
            raise ValueError(
                "Anomaly scores must be one-dimensional."
            )

        if not np.isfinite(scores).all():
            raise ValueError(
                "Anomaly scores must be finite."
            )

        reference = np.asarray(
            self.reference_anomaly_scores,
            dtype=np.float64,
        )

        return (
            1
            + np.sum(
                reference[None, :] > scores[:, None],
                axis=1,
                dtype=np.int64,
            )
        ).astype(np.int64)

    def anomaly_flags(
        self,
        anomaly_percentiles: np.ndarray,
    ) -> dict[float, np.ndarray]:
        """Return anomaly flags for configured percentile thresholds."""

        percentiles = np.asarray(
            anomaly_percentiles,
            dtype=np.float64,
        )

        if percentiles.ndim != 1:
            raise ValueError(
                "Anomaly percentiles must be one-dimensional."
            )

        if not np.isfinite(percentiles).all():
            raise ValueError(
                "Anomaly percentiles must be finite."
            )

        return {
            threshold: (
                percentiles >= threshold
            ).copy()
            for threshold in self.anomaly_thresholds
        }

    def to_dict(self) -> dict[str, Any]:
        """Return the stable serialized representation."""

        return {
            "schema_version": OOD_ARTIFACT_SCHEMA_VERSION,
            "method": self.method,
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
            "anomaly_thresholds": list(
                self.anomaly_thresholds
            ),
            "feature_count": self.feature_count,
            "reference_anomaly_scores": list(
                self.reference_anomaly_scores
            ),
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> OODArtifact:
        """Reconstruct an OOD artifact from serialized data."""

        if not isinstance(payload, dict):
            raise TypeError(
                "OOD artifact payload must be a dictionary."
            )

        if (
            payload.get("schema_version")
            != OOD_ARTIFACT_SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported OOD artifact schema version."
            )

        thresholds = payload.get(
            "anomaly_thresholds"
        )
        reference_scores = payload.get(
            "reference_anomaly_scores"
        )

        if not isinstance(thresholds, list):
            raise TypeError(
                "OOD anomaly thresholds must be a list."
            )

        if not isinstance(reference_scores, list):
            raise TypeError(
                "OOD reference anomaly scores must be a list."
            )

        return cls(
            method=str(payload.get("method")),
            n_estimators=int(
                payload.get("n_estimators")
            ),
            contamination=str(
                payload.get("contamination")
            ),
            random_state=int(
                payload.get("random_state")
            ),
            n_jobs=int(
                payload.get("n_jobs")
            ),
            anomaly_thresholds=tuple(
                float(value)
                for value in thresholds
            ),
            feature_count=int(
                payload.get("feature_count")
            ),
            reference_anomaly_scores=tuple(
                float(value)
                for value in reference_scores
            ),
        )
