"""Production ML model contracts."""

from ztf_classifier.models.classes import (
    CLASS_TO_INDEX,
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.contracts import (
    DEFAULT_MODEL_CONTRACT,
    ModelContract,
)

__all__ = [
    "CLASS_TO_INDEX",
    "DEFAULT_MODEL_CONTRACT",
    "MODEL_CLASSES",
    "NUM_CLASSES",
    "ModelContract",
]
