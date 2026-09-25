"""Scientific validation dashboard/report rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_scientific_validation_report(gate: dict[str, Any]) -> str:
    """Render a release-oriented Markdown report from a gate result."""
    lines = [
        "# Scientific Validation Report",
        "",
        f"**Gate status:** {gate.get('status', 'UNKNOWN')}",
        f"**Release blocking:** {gate.get('release_blocking', True)}",
        "",
        "## Benchmark status",
        "",
        "| Benchmark | Role | Status | Blockers |",
        "|---|---|---|---|",
    ]
    for item in gate.get("benchmarks", []):
        blockers = "<br>".join(item.get("blockers", [])) or "—"
        lines.append(
            f"| {item.get('benchmark_id', 'unknown')} | "
            f"{item.get('evaluation_role', 'unknown')} | "
            f"{item.get('status', 'UNKNOWN')} | {blockers} |"
        )
    lines.extend(
        [
            "",
            "## Release blockers",
            "",
        ]
    )
    blockers = gate.get("blockers", [])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Scientific interpretation boundary",
            "",
            gate.get(
                "interpretation",
                "Benchmark success is not proof of universal correctness.",
            ),
            "",
            "## Scope",
            "",
            (
                "This report is evidence for the declared benchmark populations, "
                "source versions, labels, preprocessing, and evaluation conditions. "
                "It does not establish global correctness outside those conditions."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_scientific_validation_report(
    gate_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Render a human-readable report from a machine-readable gate result."""
    gate = json.loads(Path(gate_path).read_text(encoding="utf-8"))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_scientific_validation_report(gate), encoding="utf-8")
    return output
