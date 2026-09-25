from pathlib import Path

import pytest

from ztf_classifier.incremental import (
    IncrementalCheckpointStore,
    IncrementalResultCursor,
)
from ztf_classifier.results import ScientificResultStore


def test_incremental_cursor_reads_and_acknowledges_once(tmp_path: Path) -> None:
    results = ScientificResultStore(tmp_path / "results.sqlite3")
    checkpoints = IncrementalCheckpointStore(tmp_path / "checkpoints.sqlite3")
    result = results.save(
        job_id="job-1",
        oid="ZTF17incremental",
        survey="ztf",
        model_version="baseline_v0.2",
        payload={"value": 1},
    )
    cursor = IncrementalResultCursor(results, checkpoints, stream_id="analysis")

    batch = cursor.read(limit=10)
    assert [item.result_id for item in batch.records] == [result.result_id]

    cursor.acknowledge(result)
    assert cursor.read(limit=10).records == []


def test_incremental_checkpoint_cannot_move_backwards(tmp_path: Path) -> None:
    checkpoints = IncrementalCheckpointStore(tmp_path / "checkpoints.sqlite3")
    checkpoints.advance(
        "analysis",
        created_at="2026-09-25T12:00:00+00:00",
        result_id="result-2",
    )

    with pytest.raises(ValueError, match="move backwards"):
        checkpoints.advance(
            "analysis",
            created_at="2026-09-25T11:00:00+00:00",
            result_id="result-1",
        )


def test_incremental_cursor_requires_matching_cursor_fields(tmp_path: Path) -> None:
    results = ScientificResultStore(tmp_path / "results.sqlite3")

    with pytest.raises(ValueError, match="provided together"):
        results.query_after_cursor(created_at="2026-09-25T12:00:00+00:00")


def test_incremental_checkpoint_equal_cursor_is_idempotent(tmp_path: Path) -> None:
    checkpoints = IncrementalCheckpointStore(tmp_path / "checkpoints.sqlite3")
    first = checkpoints.advance(
        "analysis",
        created_at="2026-09-25T12:00:00+00:00",
        result_id="result-2",
    )
    second = checkpoints.advance(
        "analysis",
        created_at="2026-09-25T12:00:00+00:00",
        result_id="result-2",
    )

    assert second.created_at == first.created_at
    assert second.result_id == first.result_id


def test_incremental_checkpoint_store_does_not_overwrite_newer_cursor(tmp_path: Path) -> None:
    checkpoints = IncrementalCheckpointStore(tmp_path / "checkpoints.sqlite3")
    checkpoints.advance(
        "analysis",
        created_at="2026-09-25T12:00:00+00:00",
        result_id="result-2",
    )

    with pytest.raises(ValueError, match="move backwards"):
        checkpoints.advance(
            "analysis",
            created_at="2026-09-25T11:00:00+00:00",
            result_id="result-9",
        )

    current = checkpoints.get("analysis")
    assert current.created_at == "2026-09-25T12:00:00+00:00"
    assert current.result_id == "result-2"
