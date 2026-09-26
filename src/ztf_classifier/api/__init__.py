"""Versioned HTTP API for the ZTF Classifier platform."""

__all__ = ["create_app"]


def __getattr__(name: str):
    """Load the FastAPI application lazily to avoid import-time cycles."""
    if name == "create_app":
        from ztf_classifier.api.app import create_app

        return create_app
    raise AttributeError(name)
