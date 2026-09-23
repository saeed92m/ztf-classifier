"""Detection-acquisition backend contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DetectionAcquisitionRequest:
    """Request for retrieving one object's ZTF light-curve data."""

    oid: str
    survey: str


@dataclass(frozen=True)
class DetectionAcquisitionResult:
    """Result returned by a detection-acquisition backend."""

    request: DetectionAcquisitionRequest
    detections: Any
    non_detections: Any
    cache_hit: bool


class DetectionAcquisitionBackend(ABC):
    """Abstract interface for light-curve acquisition backends."""

    @abstractmethod
    def acquire(
        self,
        request: DetectionAcquisitionRequest,
    ) -> DetectionAcquisitionResult:
        """Acquire detections and non-detections for one object."""
        raise NotImplementedError
