"""SQLite-backed repository for durable scientific analysis results."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

RESULT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ScientificResultRecord:
    """Durable scientific result with immutable payload metadata."""

    result_id: str
    job_id: str
    oid: str
    survey: str
    model_version: str
    schema_version: str
    created_at: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "result_id": self.result_id,
            "job_id": self.job_id,
            "oid": self.oid,
            "survey": self.survey,
            "model_version": self.model_version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "payload": self.payload,
        }


class ScientificResultStore:
    """Durable repository for completed scientific analysis payloads.

    Results are keyed by job ID for idempotent worker retries and by result ID
    for stable API retrieval. The job queue remains responsible for lifecycle
    state; this repository is the canonical persistence boundary for the
    scientific payload itself.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scientific_results (
                    result_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL UNIQUE,
                    oid TEXT NOT NULL,
                    survey TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scientific_results_oid_created
                ON scientific_results(oid, created_at DESC)
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _decode(row: tuple[Any, ...]) -> ScientificResultRecord:
        return ScientificResultRecord(
            result_id=row[0],
            job_id=row[1],
            oid=row[2],
            survey=row[3],
            model_version=row[4],
            schema_version=row[5],
            created_at=row[6],
            payload=json.loads(row[7]),
        )

    def save(
        self,
        *,
        job_id: str,
        oid: str,
        survey: str,
        model_version: str,
        payload: dict[str, Any],
        schema_version: str = RESULT_SCHEMA_VERSION,
    ) -> ScientificResultRecord:
        """Persist one result idempotently for a job."""
        if not job_id or not oid or not survey or not model_version:
            raise ValueError("job_id, oid, survey, and model_version are required")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")
        if not schema_version:
            raise ValueError("schema_version is required")

        with sqlite3.connect(self.path) as connection:
            existing = connection.execute(
                """
                SELECT result_id, job_id, oid, survey, model_version,
                       schema_version, created_at, payload_json
                FROM scientific_results WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            if existing is not None:
                record = self._decode(existing)
                if (
                    record.oid != oid
                    or record.survey != survey
                    or record.model_version != model_version
                    or record.schema_version != schema_version
                    or record.payload != payload
                ):
                    raise ValueError(
                        f"Scientific result already exists for job: {job_id}"
                    )
                return record

            record = ScientificResultRecord(
                result_id=str(uuid4()),
                job_id=job_id,
                oid=oid,
                survey=survey,
                model_version=model_version,
                schema_version=schema_version,
                created_at=self._now(),
                payload=payload,
            )
            connection.execute(
                """
                INSERT INTO scientific_results
                (result_id, job_id, oid, survey, model_version,
                 schema_version, created_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.result_id,
                    record.job_id,
                    record.oid,
                    record.survey,
                    record.model_version,
                    record.schema_version,
                    record.created_at,
                    json.dumps(
                        record.payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
            return record

    def get(self, result_id: str) -> ScientificResultRecord:
        """Load a result by stable result ID."""
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT result_id, job_id, oid, survey, model_version,
                       schema_version, created_at, payload_json
                FROM scientific_results WHERE result_id = ?
                """,
                (result_id,),
            ).fetchone()
        if row is None:
            raise KeyError(result_id)
        return self._decode(row)

    def get_by_job_id(self, job_id: str) -> ScientificResultRecord:
        """Load the result associated with a job."""
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT result_id, job_id, oid, survey, model_version,
                       schema_version, created_at, payload_json
                FROM scientific_results WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._decode(row)

    def latest_for_object(
        self,
        oid: str,
        *,
        survey: str | None = None,
    ) -> ScientificResultRecord:
        """Return the newest durable result for an object."""
        query = """
            SELECT result_id, job_id, oid, survey, model_version,
                   schema_version, created_at, payload_json
            FROM scientific_results
            WHERE oid = ?
        """
        parameters: list[Any] = [oid]
        if survey is not None:
            query += " AND survey = ?"
            parameters.append(survey)
        query += " ORDER BY created_at DESC, result_id DESC LIMIT 1"

        with sqlite3.connect(self.path) as connection:
            row = connection.execute(query, parameters).fetchone()
        if row is None:
            raise KeyError(oid)
        return self._decode(row)


__all__ = ["RESULT_SCHEMA_VERSION", "ScientificResultRecord", "ScientificResultStore"]
