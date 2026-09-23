"""High-level frozen v0.2 model contract."""

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
from ztf_classifier.models.config import ModelConfig


class ModelContract:
    """Immutable scientific contract for the v0.2 model stack."""

    def __init__(
        self,
        config: ModelConfig | None = None,
    ) -> None:
        self.config = config or ModelConfig()

        if self.config.xgboost.num_class != NUM_CLASSES:
            raise ValueError("Model class count does not match XGBoost config.")

    @property
    def classes(self) -> tuple[str, ...]:
        return MODEL_CLASSES

    @property
    def class_to_index(self) -> dict[str, int]:
        return dict(CLASS_TO_INDEX)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_version": self.config.version,
            "model_family": self.config.family,
            "classes": list(self.classes),
            "class_to_index": self.class_to_index,
            "xgboost": asdict(self.config.xgboost),
            "cross_validation": asdict(self.config.cross_validation),
            "calibration": asdict(self.config.calibration),
            "conformal": asdict(self.config.conformal),
            "ood": asdict(self.config.ood),
            "missing_value_strategy": self.config.missing_value_strategy,
            "hyperparameter_tuning": self.config.hyperparameter_tuning,
        }

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
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
