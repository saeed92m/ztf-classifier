"""Configuration for the production HTTP API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ApiSettings:
    """Runtime configuration kept outside HTTP request payloads."""

    registry_dir: Path | None = None
    default_model_version: str | None = None

    @classmethod
    def from_environment(cls) -> ApiSettings:
        """Build settings from server-side environment variables."""
        registry = os.getenv("ZTF_API_REGISTRY_DIR")
        model_version = os.getenv("ZTF_API_DEFAULT_MODEL_VERSION")
        return cls(
            registry_dir=Path(registry).expanduser() if registry else None,
            default_model_version=model_version or None,
        )
