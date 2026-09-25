"""Worker orchestration for persistent scientific analysis jobs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ztf_classifier.jobs.errors import AnalysisJobExecutionError
from ztf_classifier.jobs.store import JobRecord, JobStore

JobExecutor = Callable[[JobRecord], dict[str, Any]]


class AnalysisJobWorker:
    """Consume queued jobs and persist execution outcomes."""

    def __init__(self, store: JobStore, executor: JobExecutor) -> None:
        self.store = store
        self.executor = executor

    def run_once(self) -> JobRecord | None:
        """Claim and execute one queued job."""
        job = self.store.claim_next()
        if job is None:
            return None

        try:
            result = self.executor(job)
        except AnalysisJobExecutionError:
            return self.store.transition(
                job.job_id,
                status="failed",
                error={
                    "code": "analysis_job_failed",
                    "message": "The analysis job could not be completed.",
                },
            )

        if not isinstance(result, dict):
            return self.store.transition(
                job.job_id,
                status="failed",
                error={
                    "code": "analysis_job_invalid_result",
                    "message": "The analysis executor returned an invalid result.",
                },
            )

        return self.store.transition(
            job.job_id,
            status="succeeded",
            result=result,
        )

    def drain(self, *, max_jobs: int | None = None) -> list[JobRecord]:
        """Process queued jobs until empty or the optional limit is reached."""
        completed: list[JobRecord] = []
        while max_jobs is None or len(completed) < max_jobs:
            result = self.run_once()
            if result is None:
                break
            completed.append(result)
        return completed


__all__ = ["AnalysisJobWorker", "JobExecutor"]
