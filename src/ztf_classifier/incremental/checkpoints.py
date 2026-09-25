"""Durable checkpoints for deterministic incremental analysis."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class CheckpointRecord:
    """One named stream checkpoint."""

    stream_id: str
    created_at: str | None
    result_id: str | None
    updated_at: str


class IncrementalCheckpointStore:
    """SQLite-backed checkpoint store for restart-safe incremental consumers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incremental_checkpoints (
                    stream_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    result_id TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def get(self, stream_id: str) -> CheckpointRecord:
        if not stream_id:
            raise ValueError("stream_id is required")
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT stream_id, created_at, result_id, updated_at
                FROM incremental_checkpoints
                WHERE stream_id = ?
                """,
                (stream_id,),
            ).fetchone()
        if row is None:
            return CheckpointRecord(
                stream_id=stream_id,
                created_at=None,
                result_id=None,
                updated_at=self._now(),
            )
        return CheckpointRecord(
            stream_id=row[0],
            created_at=row[1],
            result_id=row[2],
            updated_at=row[3],
        )

    def advance(
        self,
        stream_id: str,
        *,
        created_at: str,
        result_id: str,
    ) -> CheckpointRecord:
        """Advance a checkpoint monotonically."""
        if not stream_id or not created_at or not result_id:
            raise ValueError("stream_id, created_at, and result_id are required")
        current = self.get(stream_id)
        if current.created_at is not None and current.result_id is not None:
            if (created_at, result_id) < (current.created_at, current.result_id):
                raise ValueError("checkpoint cannot move backwards")
        updated_at = self._now()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO incremental_checkpoints
                (stream_id, created_at, result_id, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(stream_id) DO UPDATE SET
                    created_at = excluded.created_at,
                    result_id = excluded.result_id,
                    updated_at = excluded.updated_at
                """,
                (stream_id, created_at, result_id, updated_at),
            )
        return CheckpointRecord(
            stream_id=stream_id,
            created_at=created_at,
            result_id=result_id,
            updated_at=updated_at,
        )


__all__ = ["CheckpointRecord", "IncrementalCheckpointStore"]
