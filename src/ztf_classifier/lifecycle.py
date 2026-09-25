"""Executable contract for cumulative learning stage records."""

from __future__ import annotations

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
}


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
    if isinstance(measurement, dict):
        metrics = measurement.get("metrics", {})
        if not isinstance(metrics, dict):
            errors.append("measurement.metrics must be an object")
        else:
            for name, value in metrics.items():
                if name not in METRIC_NAMES:
                    errors.append(f"unsupported metric name: {name}")
                if isinstance(value, dict):
                    before = value.get("before")
                    after = value.get("after")
                    measured = before is not None and after is not None
                    if not measured and value.get("status") != "NOT_MEASURED":
                        errors.append(
                            f"metric {name} needs before/after or "
                            "status=NOT_MEASURED"
                        )
    elif measurement is not None:
        errors.append("measurement must be an object")

    validation = record.get("validation")
    if isinstance(validation, dict) and validation.get(
        "scientific_gate_affected"
    ) is True and not validation.get("evidence"):
        errors.append(
            "scientific-gate changes require validation evidence or an explicit "
            "blocker"
        )

    return errors


def assert_valid_cycle_record(record: dict[str, Any]) -> None:
    """Raise ValueError when a cycle record violates the lifecycle contract."""
    errors = validate_cycle_record(record)
    if errors:
        raise ValueError("; ".join(errors))
