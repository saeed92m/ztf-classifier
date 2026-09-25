"""Executable contract for cumulative learning stage records.

The contract is intentionally strict: lifecycle evidence must be machine-readable
so cumulative learning cannot remain a documentation-only convention.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

KNOWLEDGE_STATUSES = {
    "FACT",
    "VERIFIED",
    "SUPPORTED",
    "HYPOTHESIS",
    "ASSUMPTION",
    "UNRESOLVED",
    "REJECTED",
}

REQUIRED_FIELDS = (
    "stage_id",
    "objective",
    "previous_knowledge_consumed",
    "baseline",
    "expected_improvement",
    "measurement",
    "validation",
    "failure_analysis",
    "knowledge_extraction",
    "regression",
    "decision",
    "knowledge_carried_forward",
)

METRIC_NAMES = {
    "accuracy",
    "correctness",
    "speed",
    "efficiency",
    "reliability",
    "robustness",
    "coverage",
    "reproducibility",
    "scientific_validity",
    "runtime",
    "throughput",
    "latency",
    "memory",
    "cpu_utilization",
    "gpu_utilization",
    "io",
    "batch_efficiency",
    "feature_generation_time",
    "inference_time",
    "lifecycle_contract_coverage",
    "knowledge_artifact_count",
    "regression_protection_count",
    "audit_time",
    "implementation_time",
    "debugging_time",
    "regression_fix_time",
    "rework_count",
    "repeated_failure_count",
    "pr_cycle_time",
    "test_execution_efficiency",
}

ACCEPTED_DECISIONS = {"ACCEPT", "REVISE", "BLOCKED"}


def validate_cycle_record(record: dict[str, Any]) -> list[str]:
    """Return contract violations for a cumulative-learning cycle record."""
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or value == "" or value == [] or value == {}:
            errors.append(f"missing required lifecycle field: {field}")

    consumed = record.get("previous_knowledge_consumed")
    if consumed is not None and not isinstance(consumed, list):
        errors.append("previous_knowledge_consumed must be a list")

    expected = record.get("expected_improvement")
    if expected is not None and (
        not isinstance(expected, list) or not expected
    ):
        errors.append("expected_improvement must be a non-empty list")

    carried = record.get("knowledge_carried_forward")
    if carried is not None and not isinstance(carried, list):
        errors.append("knowledge_carried_forward must be a list")

    extraction = record.get("knowledge_extraction")
    if isinstance(extraction, dict):
        status = extraction.get("status")
        if status not in KNOWLEDGE_STATUSES:
            errors.append(
                "knowledge_extraction.status must use an allowed knowledge status"
            )
        if not extraction.get("findings"):
            errors.append("knowledge_extraction.findings must be non-empty")
    elif extraction is not None:
        errors.append("knowledge_extraction must be an object")

    measurement = record.get("measurement")
    metrics = measurement.get("metrics", {}) if isinstance(measurement, dict) else {}
    if not isinstance(measurement, dict):
        errors.append("measurement must be an object")
    elif not isinstance(metrics, dict) or not metrics:
        errors.append("measurement.metrics must be a non-empty object")
    else:
        for name, value in metrics.items():
            if name not in METRIC_NAMES:
                errors.append(f"unsupported metric name: {name}")
            if not isinstance(value, dict):
                errors.append(f"metric {name} must be an object")
                continue
            before = value.get("before")
            after = value.get("after")
            measured = before is not None and after is not None
            if not measured and value.get("status") != "NOT_MEASURED":
                errors.append(
                    f"metric {name} needs before/after or status=NOT_MEASURED"
                )

    validation = record.get("validation")
    if isinstance(validation, dict):
        if validation.get("scientific_gate_affected") is True:
            evidence = validation.get("evidence")
            blocker = validation.get("blocker")
            if not evidence and not blocker:
                errors.append(
                    "scientific-gate changes require validation evidence or an explicit blocker"
                )
            if blocker and validation.get("status") not in {"BLOCKED", "NOT_VERIFIED"}:
                errors.append(
                    "scientific blocker requires validation.status=BLOCKED or NOT_VERIFIED"
                )
    elif validation is not None:
        errors.append("validation must be an object")

    regression = record.get("regression")
    if isinstance(regression, dict):
        status = regression.get("status")
        blockers = regression.get("open_blockers", [])
        if status not in {"PASS", "FAIL", "BLOCKED", "NOT_VERIFIED"}:
            errors.append("regression.status must be an allowed status")
        if not isinstance(blockers, list):
            errors.append("regression.open_blockers must be a list")
        if record.get("decision") == "ACCEPT" and (status != "PASS" or blockers):
            errors.append(
                "ACCEPT decisions require regression.status=PASS and no open blockers"
            )
    elif regression is not None:
        errors.append("regression must be an object")

    decision = record.get("decision")
    if decision not in ACCEPTED_DECISIONS:
        errors.append("decision must be ACCEPT, REVISE, or BLOCKED")

    return errors


def assert_valid_cycle_record(record: dict[str, Any]) -> None:
    """Raise ValueError when a cycle record violates the lifecycle contract."""
    errors = validate_cycle_record(record)
    if errors:
        raise ValueError("; ".join(errors))


def validate_cycle_file(path: str | Path) -> None:
    """Validate one JSON lifecycle record from disk."""
    file_path = Path(path)
    record = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise TypeError(f"{file_path}: lifecycle record must be a JSON object")
    assert_valid_cycle_record(record)


def _main() -> int:
    parser = argparse.ArgumentParser(description="Validate cumulative lifecycle records")
    parser.add_argument("command", choices=("validate",))
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    for path in args.paths:
        validate_cycle_file(path)
        print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
