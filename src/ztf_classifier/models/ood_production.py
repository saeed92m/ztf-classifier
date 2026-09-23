"""Production OOD model with persisted fitted preprocessing and estimator."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

from ztf_classifier.models.config import OODConfig

OOD_FEATURE_COUNT = 42
OOD_PRODUCTION_STATE_VERSION = "1.0"


class OODProductionModel:
    """Production OOD model with optional fitted state."""

    def __init__(
        self,
        config: OODConfig | None = None,
    ) -> None:
        self.config = config or OODConfig()
        self.imputer: SimpleImputer | None = None
        self.scaler: RobustScaler | None = None
        self.model: IsolationForest | None = None
        self.reference_anomaly_scores: np.ndarray | None = None

    def fit(
        self,
        X: np.ndarray,
    ) -> OODProductionModel:
        """Fit preprocessing and IsolationForest on reference data."""

        X = self._validate_features(X)

        imputer = SimpleImputer(strategy="median")
        X_imputed = imputer.fit_transform(X)

        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X_imputed)

        model = IsolationForest(
            n_estimators=self.config.n_estimators,
            contamination=self.config.contamination,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs,
        )
        model.fit(X_scaled)

        reference_normality = model.score_samples(X_scaled)
        reference_anomaly = -reference_normality

        self.imputer = imputer
        self.scaler = scaler
        self.model = model

        self.reference_anomaly_scores = np.array(
            reference_anomaly,
            dtype=np.float64,
            copy=True,
        )
        self.reference_anomaly_scores.setflags(write=False)

        return self

    def _require_fitted(self) -> None:
        """Require a complete fitted state."""

        if (
            self.imputer is None
            or self.scaler is None
            or self.model is None
            or self.reference_anomaly_scores is None
        ):
            raise RuntimeError(
                "OOD production model has not been fitted."
            )

    def _transform(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """Apply persisted preprocessing to production features."""

        self._require_fitted()
        X = self._validate_features(X)

        return self.scaler.transform(
            self.imputer.transform(X)
        )

    def anomaly_scores(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """Return positive anomaly scores."""

        self._require_fitted()

        return -self.model.score_samples(
            self._transform(X)
        )

    def normality_scores(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """Return IsolationForest normality scores."""

        self._require_fitted()

        return self.model.score_samples(
            self._transform(X)
        )

    def labels(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """Return IsolationForest labels."""

        self._require_fitted()

        return self.model.predict(
            self._transform(X)
        )

    def save(
        self,
        path: Path,
    ) -> Path:
        """Persist the complete fitted production state."""

        self._require_fitted()

        path = Path(path)

        if path.exists():
            raise FileExistsError(
                f"OOD production model already exists: {path}"
            )

        payload = {
            "state_version": OOD_PRODUCTION_STATE_VERSION,
            "config": self.config,
            "imputer": self.imputer,
            "scaler": self.scaler,
            "model": self.model,
            "reference_anomaly_scores": np.array(
                self.reference_anomaly_scores,
                dtype=np.float64,
                copy=True,
            ),
        }

        joblib.dump(
            payload,
            path,
        )

        return path

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> OODProductionModel:
        """Load and validate persisted production OOD state."""

        path = Path(path)

        if not path.is_file():
            raise FileNotFoundError(
                f"OOD production model does not exist: {path}"
            )

        payload = joblib.load(path)

        if not isinstance(payload, dict):
            raise TypeError(
                "OOD production model state must be a dictionary."
            )

        if (
            payload.get("state_version")
            != OOD_PRODUCTION_STATE_VERSION
        ):
            raise ValueError(
                "Unsupported OOD production model state version."
            )

        required = {
            "config",
            "imputer",
            "scaler",
            "model",
            "reference_anomaly_scores",
        }

        missing = required.difference(payload)

        if missing:
            raise ValueError(
                "OOD production model state is missing: "
                + ", ".join(sorted(missing))
            )

        config = payload["config"]

        if not isinstance(config, OODConfig):
            raise TypeError(
                "Persisted OOD configuration has an invalid type."
            )

        imputer = payload["imputer"]
        scaler = payload["scaler"]
        model = payload["model"]

        if not isinstance(imputer, SimpleImputer):
            raise TypeError(
                "Persisted OOD imputer has an invalid type."
            )

        if not isinstance(scaler, RobustScaler):
            raise TypeError(
                "Persisted OOD scaler has an invalid type."
            )

        if not isinstance(model, IsolationForest):
            raise TypeError(
                "Persisted OOD model has an invalid type."
            )

        reference = np.asarray(
            payload["reference_anomaly_scores"],
            dtype=np.float64,
        )

        if reference.ndim != 1:
            raise ValueError(
                "Reference anomaly scores must be one-dimensional."
            )

        if len(reference) == 0:
            raise ValueError(
                "Reference anomaly scores must not be empty."
            )

        if not np.isfinite(reference).all():
            raise ValueError(
                "Reference anomaly scores must be finite."
            )

        instance = cls(config)
        instance.imputer = imputer
        instance.scaler = scaler
        instance.model = model

        instance.reference_anomaly_scores = np.array(
            reference,
            dtype=np.float64,
            copy=True,
        )
        instance.reference_anomaly_scores.setflags(write=False)

        return instance

    @staticmethod
    def _validate_features(
        X: np.ndarray,
    ) -> np.ndarray:
        """Validate the frozen production feature contract."""

        X = np.asarray(
            X,
            dtype=np.float64,
        )

        if X.ndim != 2:
            raise ValueError(
                "Feature matrix must be two-dimensional."
            )

        if X.shape[1] != OOD_FEATURE_COUNT:
            raise ValueError(
                "Production OOD detection requires exactly "
                "42 features."
            )

        if len(X) == 0:
            raise ValueError(
                "Production OOD detection requires at least one sample."
            )

        if not np.isfinite(X).any():
            raise ValueError(
                "Feature matrix contains no finite values."
            )

        return X


__all__ = [
    "OOD_PRODUCTION_STATE_VERSION",
    "OODProductionModel",
]
