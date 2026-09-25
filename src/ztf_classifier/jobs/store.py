"""SQLite-backed persistent analysis job store."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    feature_backend: str = "native"
    feature_parameters: dict | None = None
    result: dict | None = None
    error: dict | None = None
    lease_expires_at: str | None = None
    scientific_result_id: str | None = None

    def to_dict(self) -> dict:
        """Return a JSON-safe job representation."""
        return {
            "job_id": self.job_id,
            "oid": self.oid,
            "survey": self.survey,
            "model_version": self.model_version,
            "feature_backend": self.feature_backend,
            "feature_parameters": self.feature_parameters,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
            "lease_expires_at": self.lease_expires_at,
            "scientific_result_id": self.scientific_result_id,
        }


class JobStore:
    """Durable local job store with explicit state transitions."""

    _STATUSES: ClassVar[frozenset[str]] = frozenset(
        {"queued", "running", "succeeded", "failed"}
    )

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
                    feature_backend TEXT NOT NULL DEFAULT 'native',
                    feature_parameters_json TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_json TEXT,
                    error_json TEXT,
                    lease_expires_at TEXT,
                    scientific_result_id TEXT
                )
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(analysis_jobs)")
            }
            if "lease_expires_at" not in columns:
                connection.execute(
                    "ALTER TABLE analysis_jobs ADD COLUMN lease_expires_at TEXT"
                )
            if "feature_backend" not in columns:
                connection.execute(
                    "ALTER TABLE analysis_jobs ADD COLUMN feature_backend TEXT NOT NULL DEFAULT 'native'"
                )
            if "feature_parameters_json" not in columns:
                connection.execute(
                    "ALTER TABLE analysis_jobs ADD COLUMN feature_parameters_json TEXT"
                )
            if "scientific_result_id" not in columns:
                connection.execute(
                    "ALTER TABLE analysis_jobs ADD COLUMN scientific_result_id TEXT"
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
        feature_backend: str = "native",
        feature_parameters: dict | None = None,
    ) -> JobRecord:
        """Create a queued job."""
        now = self._now()
        record = JobRecord(
            job_id=str(uuid4()),
            oid=oid,
            survey=survey,
            model_version=model_version,
            feature_backend=feature_backend,
            feature_parameters=feature_parameters,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO analysis_jobs
                (job_id, oid, survey, model_version, feature_backend, feature_parameters_json,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.job_id,
                    record.oid,
                    record.survey,
                    record.model_version,
                    record.feature_backend,
                    json.dumps(record.feature_parameters)
                    if record.feature_parameters is not None
                    else None,
                    record.status,
                    record.created_at,
                    record.updated_at,
                ),
            )
        return record

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobRecord]:
        """Return deterministic durable jobs for operational views."""
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if status is not None and status not in self._STATUSES:
            raise ValueError(f"Unsupported job status: {status}")

        query = """
            SELECT job_id, oid, survey, model_version, feature_backend,
                   feature_parameters_json, status, created_at, updated_at, result_json,
                   error_json, lease_expires_at, scientific_result_id
            FROM analysis_jobs
        """
        parameters: list[str | int] = []
        if status is not None:
            query += " WHERE status = ?"
            parameters.append(status)
        query += " ORDER BY created_at DESC, job_id DESC LIMIT ? OFFSET ?"
        parameters.extend((limit, offset))
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            JobRecord(
                job_id=row[0],
                oid=row[1],
                survey=row[2],
                model_version=row[3],
                feature_backend=row[4] or "native",
                feature_parameters=json.loads(row[5]) if row[5] else None,
                status=row[6],
                created_at=row[7],
                updated_at=row[8],
                result=json.loads(row[9]) if row[9] else None,
                error=json.loads(row[10]) if row[10] else None,
                lease_expires_at=row[11],
                scientific_result_id=row[12],
            )
            for row in rows
        ]

    def get(self, job_id: str) -> JobRecord:
        """Load a job or raise KeyError."""
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT job_id, oid, survey, model_version, feature_backend,
                       feature_parameters_json, status, created_at, updated_at, result_json,
                       error_json, lease_expires_at, scientific_result_id
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
            feature_backend=row[4] or "native",
            feature_parameters=json.loads(row[5]) if row[5] else None,
            status=row[6],
            created_at=row[7],
            updated_at=row[8],
            result=json.loads(row[9]) if row[9] else None,
            error=json.loads(row[10]) if row[10] else None,
            lease_expires_at=row[11],
            scientific_result_id=row[12],
        )

    def requeue_expired(self) -> int:
        """Return interrupted running jobs to the queue when their lease expires."""
        now = self._now()
        with sqlite3.connect(self.path) as connection:
            return connection.execute(
                """
                UPDATE analysis_jobs
                SET status = 'queued', updated_at = ?, lease_expires_at = NULL
                WHERE status = 'running' AND lease_expires_at IS NOT NULL
                  AND lease_expires_at <= ?
                """,
                (now, now),
            ).rowcount

    def claim_next(self, *, lease_seconds: int = 900) -> JobRecord | None:
        """Atomically claim the oldest queued job and assign an execution lease."""
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        self.requeue_expired()
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
            lease_expires_at = (
                datetime.fromisoformat(now) + timedelta(seconds=lease_seconds)
            ).isoformat()
            updated = connection.execute(
                """
                UPDATE analysis_jobs
                SET status = 'running', updated_at = ?, lease_expires_at = ?
                WHERE job_id = ? AND status = 'queued'
                """,
                (now, lease_expires_at, row[0]),
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
        scientific_result_id: str | None = None,
    ) -> JobRecord:
        """Persist an explicit job state transition."""
        if status not in self._STATUSES:
            raise ValueError(f"Unsupported job status: {status}")
        now = self._now()
        with sqlite3.connect(self.path) as connection:
            updated = connection.execute(
                """
                UPDATE analysis_jobs
                SET status = ?, updated_at = ?, result_json = ?, error_json = ?, lease_expires_at = NULL, scientific_result_id = ?
                WHERE job_id = ?
                """,
                (
                    status,
                    now,
                    json.dumps(result) if result is not None else None,
                    json.dumps(error) if error is not None else None,
                    scientific_result_id,
                    job_id,
                ),
            ).rowcount
        if updated != 1:
            raise KeyError(job_id)
        return self.get(job_id)


__all__ = ["JobRecord", "JobStore"]
