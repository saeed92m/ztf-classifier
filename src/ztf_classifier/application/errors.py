"""Application-layer exceptions."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base exception for application-layer failures."""


class ApplicationInputError(ApplicationError):
    """Raised when an application request is invalid."""


class ApplicationInferenceError(ApplicationError):
    """Raised when production inference cannot be completed."""


class ObservationAcquisitionError(ApplicationError):
    """Raised when a source-backed observation request cannot be completed."""
