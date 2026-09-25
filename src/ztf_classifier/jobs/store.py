"""SQLite-backed persistent analysis job store."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar
from uuid import uuid4


@dataclass(frozen=True)
class JobRecord:
    """Persistent state for one submitted analysis job."""

    job_id: str
    oid: str
    survey: str
    model_version: str | None
    status: str
    created_at: str
    updated_at: str
    result: dict | None = None
    error: dict | None = None

    def to_dict(self) -> dict:
        """Return a JSON-safe job representation."""
        return {
            "job_id": self.job_id,
            "oid": self.oid,
            "survey": self.survey,
            "model_version": self.model_version,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
        }


class JobStore:
    """Durable local job store with explicit state transitions."""

    _STATUSES: ClassVar[frozenset[str]] = frozenset({"queued", "running", "succeeded", "failed"})

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    job_id TEXT PRIMARY KEY,
                    oid TEXT NOT NULL,
                    survey TEXT NOT NULL,
                    model_version TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_json TEXT,
                    error_json TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status_created
                ON analysis_jobs(status, created_at)
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def create(
        self,
        *,
        oid: str,
        survey: str,
        model_version: str | None,
    ) -> JobRecord:
        """Create a queued job."""
        now = self._now()
        record = JobRecord(
            job_id=str(uuid4()),
            oid=oid,
            survey=survey,
            model_version=model_version,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO analysis_jobs
                (job_id, oid, survey, model_version, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.job_id,
                    record.oid,
                    record.survey,
                    record.model_version,
                    record.status,
                    record.created_at,
                    record.updated_at,
                ),
            )
        return record

    def get(self, job_id: str) -> JobRecord:
        """Load a job or raise KeyError."""
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT job_id, oid, survey, model_version, status,
                       created_at, updated_at, result_json, error_json
                FROM analysis_jobs WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return JobRecord(
            job_id=row[0],
            oid=row[1],
            survey=row[2],
            model_version=row[3],
            status=row[4],
            created_at=row[5],
            updated_at=row[6],
            result=json.loads(row[7]) if row[7] else None,
            error=json.loads(row[8]) if row[8] else None,
        )

    def claim_next(self) -> JobRecord | None:
        """Atomically claim the oldest queued job for execution."""
        connection = sqlite3.connect(self.path, timeout=30.0)
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT job_id
                FROM analysis_jobs
                WHERE status = 'queued'
                ORDER BY created_at ASC, job_id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                connection.commit()
                return None

            now = self._now()
            updated = connection.execute(
                """
                UPDATE analysis_jobs
                SET status = 'running', updated_at = ?
                WHERE job_id = ? AND status = 'queued'
                """,
                (now, row[0]),
            ).rowcount
            if updated != 1:
                connection.rollback()
                return None
            connection.commit()
            return self.get(row[0])
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def transition(
        self,
        job_id: str,
        *,
        status: str,
        result: dict | None = None,
        error: dict | None = None,
    ) -> JobRecord:
        """Persist an explicit job state transition."""
        if status not in self._STATUSES:
            raise ValueError(f"Unsupported job status: {status}")
        now = self._now()
        with sqlite3.connect(self.path) as connection:
            updated = connection.execute(
                """
                UPDATE analysis_jobs
                SET status = ?, updated_at = ?, result_json = ?, error_json = ?
                WHERE job_id = ?
                """,
                (
                    status,
                    now,
                    json.dumps(result) if result is not None else None,
                    json.dumps(error) if error is not None else None,
                    job_id,
                ),
            ).rowcount
        if updated != 1:
            raise KeyError(job_id)
        return self.get(job_id)


__all__ = ["JobRecord", "JobStore"]
