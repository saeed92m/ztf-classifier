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


def test_operation_journal_records_output_summary_failure(tmp_path):
    journal = tmp_path / "events.jsonl"

    def bad_summary(_result):
        raise RuntimeError("cannot summarize output")

    with pytest.raises(RuntimeError, match="cannot summarize output"):
        run_logged_operation(
            journal,
            stage="report",
            operation="summarize",
            function=lambda: {"rows": 1},
            output_summary=bad_summary,
        )

    events = _events(journal)
    assert [event["status"] for event in events] == ["STARTED", "FAIL"]
    assert events[1]["error_type"] == "RuntimeError"
    assert "cannot summarize output" in events[1]["error_message"]


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
    assert event["parameters"]["headers"]["Authorization"] == "[REDACTED]"


def test_operation_journal_rejects_invalid_status_and_missing_stage(tmp_path):
    journal = tmp_path / "events.jsonl"
    with pytest.raises(ValueError, match="stage"):
        append_operation_event(journal, stage=" ", operation="parse", status="PASS")
    with pytest.raises(ValueError, match="unsupported operation status"):
        append_operation_event(journal, stage="parse", operation="parse", status="SUCCESS")
    assert not journal.exists()


def test_operation_journal_redacts_inline_secrets_in_error_text_and_traceback(tmp_path):
    journal = tmp_path / "events.jsonl"

    def fail():
        raise RuntimeError("request failed api_key=inline-secret token:another-secret")

    with pytest.raises(RuntimeError):
        run_logged_operation(
            journal,
            stage="acquire",
            operation="request",
            function=fail,
        )

    serialized = journal.read_text(encoding="utf-8")
    assert "inline-secret" not in serialized
    assert "another-secret" not in serialized
    events = _events(journal)
    assert events[1]["status"] == "FAIL"
    assert "[REDACTED]" in events[1]["error_message"]
    assert "[REDACTED]" in events[1]["stack_trace"]
