"""Object-acquisition backend contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ztf_classifier.dataset.selector import ObjectSelectionRequest


@dataclass(frozen=True)
class ObjectAcquisitionResult:
    """Result returned by an object-acquisition backend."""

    request: ObjectSelectionRequest
    objects: tuple[Any, ...]


class ObjectAcquisitionBackend(ABC):
    """Abstract interface for object-acquisition backends."""

    @abstractmethod
    def acquire(
        self,
        request: ObjectSelectionRequest,
    ) -> ObjectAcquisitionResult:
        """Acquire objects matching one selection request."""
        raise NotImplementedError
