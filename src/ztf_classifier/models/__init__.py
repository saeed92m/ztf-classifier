"""Production ML model contracts and inference components."""

from ztf_classifier.models.calibration import (
    CalibrationResult,
    TemperatureScaler,
)
from ztf_classifier.models.classes import (
    CLASS_TO_INDEX,
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.conformal import (
    ConformalResult,
    ConformalSummary,
    EmpiricalConformalPredictor,
)
from ztf_classifier.models.contracts import (
    DEFAULT_MODEL_CONTRACT,
    ModelContract,
)
from ztf_classifier.models.inference import (
    InferenceResult,
    XGBoostInferenceEngine,
)

__all__ = [
    "CLASS_TO_INDEX",
    "DEFAULT_MODEL_CONTRACT",
    "MODEL_CLASSES",
    "NUM_CLASSES",
    "CalibrationResult",
    "ConformalResult",
    "ConformalSummary",
    "EmpiricalConformalPredictor",
    "InferenceResult",
    "ModelContract",
    "TemperatureScaler",
    "XGBoostInferenceEngine",
]
