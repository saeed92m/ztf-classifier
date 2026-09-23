"""Frozen v0.2 model class definitions."""

from __future__ import annotations

MODEL_CLASSES: tuple[str, ...] = (
    "AGN",
    "Blazar",
    "CEP",
    "CV/Nova",
    "DSCT",
    "E",
    "LPV",
    "Periodic-Other",
    "QSO",
    "RRL",
    "SLSN",
    "SNII",
    "SNIa",
    "SNIbc",
    "YSO",
)

CLASS_TO_INDEX: dict[str, int] = {
    name: index for index, name in enumerate(MODEL_CLASSES)
}

NUM_CLASSES = len(MODEL_CLASSES)

if NUM_CLASSES != 15:
    raise RuntimeError("Frozen v0.2 model must contain exactly 15 classes.")
