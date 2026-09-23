"""Production model contract for frozen v0.2."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ztf_classifier.models.classes import (
    CLASS_TO_INDEX,
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.config import (
    CalibrationConfig,
    ConformalConfig,
    CrossValidationConfig,
    ModelConfig,
    OODConfig,
    XGBoostConfig,
)


class ModelContract:
    """Serializable production model contract."""

    def __init__(
        self,
        config: ModelConfig | None = None,
    ) -> None:
        self.config = config or ModelConfig()

        if self.config.xgboost.num_class != NUM_CLASSES:
            raise ValueError(
                "Model class count does not match XGBoost config."
            )

    @property
    def classes(self) -> tuple[str, ...]:
        """Return the frozen model class order."""
        return MODEL_CLASSES

    @property
    def class_to_index(self) -> dict[str, int]:
        """Return the frozen class-to-index mapping."""
        return dict(CLASS_TO_INDEX)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete model contract."""

        return {
            "model_version": self.config.version,
            "model_family": self.config.family,
            "classes": list(self.classes),
            "class_to_index": self.class_to_index,
            "xgboost": asdict(self.config.xgboost),
            "cross_validation": asdict(
                self.config.cross_validation
            ),
            "calibration": asdict(
                self.config.calibration
            ),
            "conformal": asdict(
                self.config.conformal
            ),
            "ood": asdict(self.config.ood),
            "missing_value_strategy": (
                self.config.missing_value_strategy
            ),
            "hyperparameter_tuning": (
                self.config.hyperparameter_tuning
            ),
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> ModelContract:
        """Deserialize a complete model contract."""

        if not isinstance(payload, dict):
            raise TypeError(
                "Model contract payload must be a dictionary."
            )

        required = {
            "model_version",
            "model_family",
            "classes",
            "class_to_index",
            "xgboost",
            "cross_validation",
            "calibration",
            "conformal",
            "ood",
            "missing_value_strategy",
            "hyperparameter_tuning",
        }

        missing = sorted(
            required - set(payload)
        )

        if missing:
            raise ValueError(
                f"Model contract is missing fields: {missing}"
            )

        classes = tuple(
            str(value)
            for value in payload["classes"]
        )

        if classes != MODEL_CLASSES:
            raise ValueError(
                "Model contract classes do not match "
                "the frozen class order."
            )

        class_to_index = {
            str(key): int(value)
            for key, value in payload["class_to_index"].items()
        }

        if class_to_index != CLASS_TO_INDEX:
            raise ValueError(
                "Model contract class mapping does not match "
                "the frozen class mapping."
            )

        config = ModelConfig(
            version=str(payload["model_version"]),
            family=str(payload["model_family"]),
            xgboost=XGBoostConfig(
                **payload["xgboost"]
            ),
            cross_validation=CrossValidationConfig(
                **payload["cross_validation"]
            ),
            calibration=CalibrationConfig(
                **payload["calibration"]
            ),
            conformal=ConformalConfig(
                **{
                    **payload["conformal"],
                    "alphas": tuple(payload["conformal"]["alphas"]),
                }
            ),
            ood=OODConfig(
                **{
                    **payload["ood"],
                    "anomaly_thresholds": tuple(
                        payload["ood"]["anomaly_thresholds"]
                    ),
                }
            ),
            missing_value_strategy=str(
                payload["missing_value_strategy"]
            ),
            hyperparameter_tuning=bool(
                payload["hyperparameter_tuning"]
            ),
        )

        return cls(config=config)

    def to_json(self, path: Path) -> None:
        """Write the model contract as JSON."""

        path = Path(path)

        path.write_text(
            json.dumps(
                self.to_dict(),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


DEFAULT_MODEL_CONTRACT = ModelContract()


__all__ = [
    "DEFAULT_MODEL_CONTRACT",
    "ModelContract",
]
