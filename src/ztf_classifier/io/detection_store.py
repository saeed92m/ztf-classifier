"""Storage contracts for raw light-curve acquisition data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DetectionStorePaths:
    """Filesystem paths for one object's raw light-curve data."""

    detections: Path
    non_detections: Path


class DetectionStore(ABC):
    """Abstract storage interface for raw detection data."""

    @abstractmethod
    def paths(self, oid: str) -> DetectionStorePaths:
        """Return storage paths for one object."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, oid: str) -> bool:
        """Return whether all required cached files exist."""
        raise NotImplementedError

    @abstractmethod
    def load(self, oid: str) -> tuple[Any, Any]:
        """Load cached detections and non-detections."""
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        oid: str,
        detections: Any,
        non_detections: Any,
    ) -> None:
        """Persist detections and non-detections."""
        raise NotImplementedError
