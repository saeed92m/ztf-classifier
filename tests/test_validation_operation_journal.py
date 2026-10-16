import json

import pytest

from ztf_classifier.validation.operation_journal import (
    append_operation_event,
    run_logged_operation,
)


def _events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_operation_journal_records_start_and_success_with_counts(tmp_path):
    journal = tmp_path / "runs" / "events.jsonl"
    result = run_logged_operation(
        journal,
        stage="parse",
        operation="parse-catalog",
        function=lambda: {"rows": 3},
        input_artifacts=[{"path": "catalog.tsv", "sha256": "a" * 64}],
        counts_before={"bytes": 12},
        output_summary=lambda value: {
            "counts_after": {"rows": value["rows"], "unique_objects": 2},
            "hashes": {"parsed": "b" * 64},
        },
    )

    assert result == {"rows": 3}
    events = _events(journal)
    assert [event["sequence"] for event in events] == [1, 2]
    assert [event["status"] for event in events] == ["STARTED", "PASS"]
    assert events[1]["counts_after"] == {"rows": 3, "unique_objects": 2}
    assert events[0]["timestamp_utc"].endswith("+00:00")


def test_operation_journal_preserves_failure_and_reraises(tmp_path):
    journal = tmp_path / "events.jsonl"

    def fail():
        raise ValueError("bad schema")

    with pytest.raises(ValueError, match="bad schema"):
        run_logged_operation(
            journal,
            stage="parse",
            operation="parse-catalog",
            function=fail,
            parameters={"input_path": "catalog.tsv"},
        )

    events = _events(journal)
    assert [event["status"] for event in events] == ["STARTED", "FAIL"]
    assert events[1]["error_type"] == "ValueError"
    assert "bad schema" in events[1]["stack_trace"]


def test_operation_journal_redacts_secret_fields_and_url_parameters(tmp_path):
    journal = tmp_path / "events.jsonl"
    event = append_operation_event(
        journal,
        stage="acquire",
        operation="fetch",
        status="PASS",
        command_or_api_query="https://example.org/data?access_token=do-not-log&limit=5",
        parameters={
            "api_key": "do-not-log",
            "headers": {"Authorization": "Bearer abc.def.ghi"},
        },
    )

    serialized = journal.read_text(encoding="utf-8")
    assert "do-not-log" not in serialized
    assert "abc.def.ghi" not in serialized
    assert event["parameters"]["api_key"] == "[REDACTED]"
    assert "access_token=%5BREDACTED%5D" in event["command_or_api_query"]
    assert "Bearer [REDACTED]" in event["parameters"]["headers"]["Authorization"]


def test_operation_journal_rejects_invalid_status_and_missing_stage(tmp_path):
    journal = tmp_path / "events.jsonl"
    with pytest.raises(ValueError, match="stage"):
        append_operation_event(journal, stage=" ", operation="parse", status="PASS")
    with pytest.raises(ValueError, match="unsupported operation status"):
        append_operation_event(journal, stage="parse", operation="parse", status="SUCCESS")
    assert not journal.exists()
