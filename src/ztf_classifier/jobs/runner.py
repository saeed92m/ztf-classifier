"""Default persistent analysis-job worker runner."""

from __future__ import annotations

from alerce.core import Alerce

from ztf_classifier.api.config import ApiSettings
from ztf_classifier.application.observations import ObservationService
from ztf_classifier.jobs.executor import SourceBackedAnalysisExecutor
from ztf_classifier.jobs.store import JobStore
from ztf_classifier.jobs.worker import AnalysisJobWorker


def create_worker(settings: ApiSettings | None = None) -> AnalysisJobWorker:
    """Build a production worker wired to ALeRCE and the scientific pipeline."""
    api_settings = settings or ApiSettings.from_environment()
    observations = ObservationService(
        client=Alerce(),
        cache_dir=api_settings.observation_cache_dir,
    )
    executor = SourceBackedAnalysisExecutor(
        api_settings,
        observation_service=observations,
    )
    return AnalysisJobWorker(
        JobStore(api_settings.job_store_path),
        executor,
    )


def main() -> None:
    """Drain the durable queue once and exit."""
    create_worker().drain()


__all__ = ["create_worker", "main"]
