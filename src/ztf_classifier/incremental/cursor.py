"""Restart-safe incremental consumption of scientific result history."""

from __future__ import annotations

from dataclasses import dataclass

from ztf_classifier.incremental.checkpoints import (
    CheckpointRecord,
    IncrementalCheckpointStore,
)
from ztf_classifier.results import ScientificResultRecord, ScientificResultStore


@dataclass(frozen=True)
class IncrementalBatch:
    """A batch of new results and the cursor at its end."""

    records: list[ScientificResultRecord]
    checkpoint: CheckpointRecord


class IncrementalResultCursor:
    """Read new durable results without reprocessing an acknowledged cursor."""

    def __init__(
        self,
        results: ScientificResultStore,
        checkpoints: IncrementalCheckpointStore,
        *,
        stream_id: str,
    ) -> None:
        self.results = results
        self.checkpoints = checkpoints
        self.stream_id = stream_id

    def read(self, *, limit: int = 100) -> IncrementalBatch:
        checkpoint = self.checkpoints.get(self.stream_id)
        records = self.results.query_after_cursor(
            created_at=checkpoint.created_at,
            result_id=checkpoint.result_id,
            limit=limit,
        )
        return IncrementalBatch(records=records, checkpoint=checkpoint)

    def acknowledge(self, record: ScientificResultRecord) -> CheckpointRecord:
        """Commit a cursor only after downstream processing succeeds."""
        return self.checkpoints.advance(
            self.stream_id,
            created_at=record.created_at,
            result_id=record.result_id,
        )


__all__ = ["IncrementalBatch", "IncrementalResultCursor"]
