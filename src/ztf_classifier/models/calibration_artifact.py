"""Serialization of fitted production calibration state."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CALIBRATION_ARTIFACT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class CalibrationArtifact:
    """Immutable fitted state for production temperature scaling."""

    method: str
    temperature: float

    def __post_init__(self) -> None:
        if self.method != "temperature_scaling":
            raise ValueError(
                "Unsupported calibration method: "
                f"{self.method!r}"
            )

        if (
            not isinstance(self.temperature, float)
            or not self.temperature > 0.0
        ):
            raise ValueError(
                "Calibration temperature must be a positive float."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the stable serialized representation."""

        return {
            "schema_version": CALIBRATION_ARTIFACT_SCHEMA_VERSION,
            "method": self.method,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> CalibrationArtifact:
        """Reconstruct a calibration artifact from serialized data."""

        if not isinstance(payload, dict):
            raise TypeError(
                "Calibration artifact payload must be a dictionary."
            )

        if (
            payload.get("schema_version")
            != CALIBRATION_ARTIFACT_SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported calibration artifact schema version."
            )

        method = payload.get("method")
        temperature = payload.get("temperature")

        if not isinstance(method, str) or not method:
            raise ValueError(
                "Calibration method must be a non-empty string."
            )

        if (
            isinstance(temperature, bool)
            or not isinstance(temperature, (int, float))
        ):
            raise TypeError(
                "Calibration temperature must be numeric."
            )

        return cls(
            method=method,
            temperature=float(temperature),
        )

    def write(self, path: Path) -> Path:
        """Write the calibration state as stable JSON."""

        path = Path(path)

        if path.exists():
            raise FileExistsError(
                f"Calibration artifact already exists: {path}"
            )

        path.write_text(
            json.dumps(
                self.to_dict(),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return path

    @classmethod
    def read(cls, path: Path) -> CalibrationArtifact:
        """Read and validate a calibration artifact."""

        path = Path(path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Calibration artifact does not exist: {path}"
            )

        payload = json.loads(
            path.read_text(encoding="utf-8")
        )

        return cls.from_dict(payload)
