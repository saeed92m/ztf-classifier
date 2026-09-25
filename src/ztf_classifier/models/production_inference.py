"""Production inference orchestration for serialized model artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.artifact_io import (
    LoadedModelArtifact,
    ModelArtifactLoader,
)
from ztf_classifier.models.calibration import TemperatureScaler
from ztf_classifier.models.inference import XGBoostInferenceEngine
from ztf_classifier.models.ood import OODResult
from ztf_classifier.models.production_conformal import (
    ProductionConformalDiagnostics,
)
from ztf_classifier.models.result_builder import PredictionResultBuilder
from ztf_classifier.models.results import PredictionResult


@dataclass(frozen=True)
class ProductionInferenceService:
    """Run deterministic inference from a validated production artifact."""

    artifact_dir: Path
    loaded_artifact: LoadedModelArtifact

    def __init__(self, artifact_dir: Path) -> None:
        artifact_dir = Path(artifact_dir)

        loaded_artifact = ModelArtifactLoader().load(
            artifact_dir
        )

        object.__setattr__(
            self,
            "artifact_dir",
            artifact_dir.resolve(),
        )
        object.__setattr__(
            self,
            "loaded_artifact",
            loaded_artifact,
        )

    def predict(
        self,
        dataset: pd.DataFrame,
    ) -> PredictionResult:
        """Predict classes and attach persisted production diagnostics."""

        model_artifact = self.loaded_artifact.model_artifact
        calibration = self.loaded_artifact.calibration

        engine = XGBoostInferenceEngine(
            model=model_artifact.model,
            feature_schema_path=(
                self.artifact_dir / "feature_schema.parquet"
            ),
        )

        inference = engine.predict(dataset)

        conformal = None
        ood = None

        if self.loaded_artifact.conformal is not None:
            conformal = ProductionConformalDiagnostics.predict(
                inference.probabilities,
                self.loaded_artifact.conformal,
            )

        if (
            self.loaded_artifact.ood is not None
            and self.loaded_artifact.ood_model is not None
        ):
            features = engine.prepare_features(dataset)
            feature_matrix = features.to_numpy(
                dtype=np.float64
            )

            ood_model = self.loaded_artifact.ood_model

            anomaly_score = ood_model.anomaly_scores(
                feature_matrix
            )
            normality_score = ood_model.normality_scores(
                feature_matrix
            )
            isolation_forest_label = ood_model.labels(
                feature_matrix
            )

            anomaly_percentile = (
                self.loaded_artifact.ood.anomaly_percentile(
                    anomaly_score
                )
            )
            anomaly_rank = (
                self.loaded_artifact.ood.anomaly_rank(
                    anomaly_score
                )
            )
            anomaly_flags = (
                self.loaded_artifact.ood.anomaly_flags(
                    anomaly_percentile
                )
            )

            ood = OODResult(
                anomaly_score=anomaly_score,
                normality_score=normality_score,
                anomaly_percentile=anomaly_percentile,
                isolation_forest_label=isolation_forest_label,
                anomaly_rank=anomaly_rank,
                is_top_1pct_anomaly=anomaly_flags[99.0],
                is_top_5pct_anomaly=anomaly_flags[95.0],
                is_top_10pct_anomaly=anomaly_flags[90.0],
            )

        calibrated_probabilities = None
        calibration_status = "unavailable"
        if calibration is not None:
            calibrated_probabilities = TemperatureScaler().transform(
                inference.probabilities,
                calibration.temperature,
            )
            calibration_status = "available"

        try:
            software_version = version("ztf-classifier")
        except PackageNotFoundError:
            software_version = "unknown"

        warnings = self.loaded_artifact.integrity_warnings

        return PredictionResultBuilder.build(
            inference,
            calibrated_probabilities=calibrated_probabilities,
            conformal=conformal,
            ood=ood,
            calibration_status=calibration_status,
            conformal_status=(
                "available" if conformal is not None else "unavailable"
            ),
            ood_status="available" if ood is not None else "unavailable",
            warnings=warnings,
            artifact_schema_version=(
                "1.1" if self.loaded_artifact.conformal is not None
                or self.loaded_artifact.ood is not None
                else "1.0"
            ),
            artifact_hash=self.loaded_artifact.artifact_hash,
            feature_schema_hash=model_artifact.feature_schema_sha256,
            software_version=software_version,
            model_version=model_artifact.model_version,
        )


__all__ = ["ProductionInferenceService"]
