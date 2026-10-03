"""Scientific-anomaly diagnostic contract, deliberately independent from OOD."""

from __future__ import annotations

import dataclasses

import numpy as np


VALID_SCIENTIFIC_ANOMALY_STATUSES = {
    "available",
    "unavailable",
    "not_evaluated",
}


@dataclasses.dataclass(frozen=True)
class ScientificAnomalyResult:
    """Scientific anomaly evidence; never an alias for model OOD."""

    status: str
    score: np.ndarray | None = None
    flags: np.ndarray | None = None
    method: str = ""
    evidence_version: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_SCIENTIFIC_ANOMALY_STATUSES:
            raise ValueError(
                f"Invalid scientific anomaly status: {self.status}"
            )

        if self.status == "available":
            if self.score is None or self.flags is None:
                raise ValueError(
                    "Available scientific anomaly evidence requires score and flags."
                )
            score = np.asarray(self.score, dtype=np.float64)
            flags = np.asarray(self.flags, dtype=bool)
            if score.ndim != 1 or flags.ndim != 1 or len(score) != len(flags):
                raise ValueError(
                    "Scientific anomaly score and flags must be aligned one-dimensional arrays."
                )
            if not np.isfinite(score).all():
                raise ValueError(
                    "Scientific anomaly scores must be finite."
                )
            score.setflags(write=False)
            flags.setflags(write=False)
            object.__setattr__(self, "score", score)
            object.__setattr__(self, "flags", flags)
        elif self.score is not None or self.flags is not None:
            raise ValueError(
                "Unavailable scientific anomaly evidence cannot carry score or flags."
            )

    @property
    def sample_count(self) -> int:
        """Return the number of evaluated samples."""
        return 0 if self.score is None else len(self.score)


__all__ = [
    "VALID_SCIENTIFIC_ANOMALY_STATUSES",
    "ScientificAnomalyResult",
]
