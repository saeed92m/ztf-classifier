"""Production inference orchestration for serialized model artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ztf_classifier.models.artifact_io import (
    LoadedModelArtifact,
    ModelArtifactLoader,
)
from ztf_classifier.models.calibration import TemperatureScaler
from ztf_classifier.models.inference import XGBoostInferenceEngine
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
        """Predict classes and calibrated probabilities for a dataset."""

        model_artifact = self.loaded_artifact.model_artifact
        calibration = self.loaded_artifact.calibration

        engine = XGBoostInferenceEngine(
            model=model_artifact.model,
            feature_schema_path=(
                self.artifact_dir / "feature_schema.parquet"
            ),
        )

        inference = engine.predict(dataset)

        calibrated_probabilities = TemperatureScaler().transform(
            inference.probabilities,
            calibration.temperature,
        )

        return PredictionResultBuilder.build(
            inference,
            calibrated_probabilities=calibrated_probabilities,
        )


__all__ = ["ProductionInferenceService"]
