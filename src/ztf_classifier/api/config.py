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
    observation_cache_dir: Path = Path("data/raw/alerce")
    job_store_path: Path = Path("data/jobs/jobs.sqlite3")
    result_store_path: Path = Path("data/results/results.sqlite3")
    api_key: str | None = None

    @classmethod
    def from_environment(cls) -> ApiSettings:
        """Build settings from server-side environment variables."""
        registry = os.getenv("ZTF_API_REGISTRY_DIR")
        model_version = os.getenv("ZTF_API_DEFAULT_MODEL_VERSION")
        cache_dir = os.getenv("ZTF_API_OBSERVATION_CACHE_DIR")
        job_store = os.getenv("ZTF_API_JOB_STORE")
        result_store = os.getenv("ZTF_API_RESULT_STORE")
        api_key = os.getenv("ZTF_API_KEY")
        return cls(
            registry_dir=Path(registry).expanduser() if registry else None,
            default_model_version=model_version or None,
            job_store_path=(
                Path(job_store).expanduser()
                if job_store
                else Path("data/jobs/jobs.sqlite3")
            ),
            result_store_path=(
                Path(result_store).expanduser()
                if result_store
                else Path("data/results/results.sqlite3")
            ),
            observation_cache_dir=Path(cache_dir).expanduser()
            if cache_dir
            else Path("data/raw/alerce"),
            api_key=api_key or None,
        )
