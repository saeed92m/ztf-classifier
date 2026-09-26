"""Persistent scientific analysis jobs."""

from .errors import AnalysisJobExecutionError
from .store import JobRecord, JobStore
from .worker import AnalysisJobWorker, JobExecutor

__all__ = [
    "AnalysisJobExecutionError",
    "AnalysisJobWorker",
    "JobExecutor",
    "JobRecord",
    "JobStore",
    "SourceBackedAnalysisExecutor",
    "create_worker",
]


def __getattr__(name: str):
    """Load optional job integrations lazily to avoid package import cycles."""
    if name == "SourceBackedAnalysisExecutor":
        from .executor import SourceBackedAnalysisExecutor

        return SourceBackedAnalysisExecutor
    if name == "create_worker":
        from .runner import create_worker

        return create_worker
    raise AttributeError(name)
