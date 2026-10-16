"""Append-only JSONL journal for auditable scientific operations.

This module complements the existing EvidenceManifest and SourceSubsetManifest:
those bind immutable artifacts, while this journal records ordered operations,
their inputs/outputs, counts, status, warnings, and failure evidence.
"""

from __future__ import annotations

import json
import re
import traceback
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SECRET_KEY = re.compile(
    r"(?:token|secret|password|passwd|api[_-]?key|authorization|cookie|private[_-]?key)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*")
_ALLOWED_STATUSES = {
    "STARTED",
    "PASS",
    "FAIL",
    "BLOCKED",
    "NOT_RUN",
    "NOT_MEASURED",
}


def redact_sensitive(value: Any, *, key: str = "") -> Any:
    """Recursively redact secret-like fields and URL query parameters."""
    if _SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(k): redact_sensitive(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item) for item in value]
    if not isinstance(value, str):
        return value

    text = _BEARER.sub(r"\1[REDACTED]", value)
    try:
        parts = urlsplit(text)
        if parts.scheme and parts.netloc and parts.query:
            query = [
                (name, "[REDACTED]" if _SECRET_KEY.search(name) else val)
                for name, val in parse_qsl(parts.query, keep_blank_values=True)
            ]
            text = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
            )
    except ValueError:
        # A malformed URL should still be retained as text after bearer redaction.
        pass
    return text


def append_operation_event(
    journal_path: str | Path,
    *,
    stage: str,
    operation: str,
    status: str,
    input_artifacts: list[dict[str, Any]] | None = None,
    output_artifacts: list[dict[str, Any]] | None = None,
    command_or_api_query: str | None = None,
    parameters: Mapping[str, Any] | None = None,
    counts_before: Mapping[str, Any] | None = None,
    counts_after: Mapping[str, Any] | None = None,
    hashes: Mapping[str, Any] | None = None,
    warnings: list[str] | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    stack_trace: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    """Append one redacted, timestamped event to a JSON Lines journal.

    This assumes a single writer per journal file. Use a separate journal per
    run/process if operations are executed concurrently.
    """
    if not isinstance(stage, str) or not stage.strip():
        raise ValueError("stage must be a non-empty string")
    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("operation must be a non-empty string")
    normalized_status = str(status).upper()
    if normalized_status not in _ALLOWED_STATUSES:
        raise ValueError(f"unsupported operation status: {status!r}")

    path = Path(journal_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sequence = 1
    if path.exists():
        with path.open("r", encoding="utf-8") as existing:
            sequence = sum(1 for line in existing if line.strip()) + 1

    event = {
        "sequence": sequence,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "stage": stage,
        "operation": operation,
        "status": normalized_status,
        "input_artifacts": input_artifacts or [],
        "output_artifacts": output_artifacts or [],
        "command_or_api_query": command_or_api_query,
        "parameters": dict(parameters or {}),
        "counts_before": dict(counts_before or {}),
        "counts_after": dict(counts_after or {}),
        "hashes": dict(hashes or {}),
        "warnings": warnings or [],
        "error_type": error_type,
        "error_message": error_message,
        "stack_trace": stack_trace,
        "notes": notes or [],
    }
    safe_event = redact_sensitive(event)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(safe_event, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
    return safe_event


def run_logged_operation(
    journal_path: str | Path,
    *,
    stage: str,
    operation: str,
    function: Callable[[], Any],
    input_artifacts: list[dict[str, Any]] | None = None,
    command_or_api_query: str | None = None,
    parameters: Mapping[str, Any] | None = None,
    counts_before: Mapping[str, Any] | None = None,
    output_summary: Callable[[Any], Mapping[str, Any]] | None = None,
) -> Any:
    """Run a callable and persist STARTED plus PASS/FAIL evidence.

    Exceptions during either the operation or output summarization are logged
    (with a redacted traceback) and re-raised unchanged. Logging never converts
    a failed operation into success.
    """
    append_operation_event(
        journal_path,
        stage=stage,
        operation=operation,
        status="STARTED",
        input_artifacts=input_artifacts,
        command_or_api_query=command_or_api_query,
        parameters=parameters,
        counts_before=counts_before,
    )
    try:
        result = function()
        summary = dict(output_summary(result)) if output_summary else {}
    except BaseException as exc:
        append_operation_event(
            journal_path,
            stage=stage,
            operation=operation,
            status="FAIL",
            input_artifacts=input_artifacts,
            command_or_api_query=command_or_api_query,
            parameters=parameters,
            counts_before=counts_before,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace="".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
            notes=["Exception re-raised after journal append."],
        )
        raise

    append_operation_event(
        journal_path,
        stage=stage,
        operation=operation,
        status="PASS",
        input_artifacts=input_artifacts,
        output_artifacts=summary.get("output_artifacts"),
        command_or_api_query=command_or_api_query,
        parameters=parameters,
        counts_before=counts_before,
        counts_after=summary.get("counts_after"),
        hashes=summary.get("hashes"),
        warnings=summary.get("warnings"),
        notes=summary.get("notes"),
    )
    return result
