"""Worker orchestration for persistent scientific analysis jobs."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from typing import Any

from ztf_classifier.jobs.errors import AnalysisJobExecutionError
from ztf_classifier.jobs.store import JobRecord, JobStore
from ztf_classifier.results import ScientificResultStore

JobExecutor = Callable[[JobRecord], dict[str, Any]]


class AnalysisJobWorker:
    """Consume queued jobs and persist execution outcomes."""

    def __init__(
        self,
        store: JobStore,
        executor: JobExecutor,
        result_store: ScientificResultStore | None = None,
    ) -> None:
        self.store = store
        self.executor = executor
        self.result_store = result_store

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

        if self.result_store is not None:
            try:
                model_version = job.model_version or str(
                    result.get("model_version") or ""
                )
                if not model_version:
                    raise ValueError("Scientific result has no model version.")
                stored = self.result_store.save(
                    job_id=job.job_id,
                    oid=job.oid,
                    survey=job.survey,
                    model_version=model_version,
                    schema_version=str(result.get("schema_version") or "1.0"),
                    payload=result,
                )
            except (sqlite3.Error, TypeError, ValueError, KeyError):
                return self.store.transition(
                    job.job_id,
                    status="failed",
                    error={
                        "code": "scientific_result_persistence_failed",
                        "message": "The scientific result could not be persisted.",
                    },
                )
            result = {
                "result_id": stored.result_id,
                "schema_version": stored.schema_version,
            }
            return self.store.transition(
                job.job_id,
                status="succeeded",
                result=result,
                scientific_result_id=stored.result_id,
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
