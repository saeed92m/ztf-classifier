"""Release-blocking benchmark regression comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compare_metrics(
    current: dict[str, Any],
    baseline: dict[str, Any],
    *,
    tolerances: dict[str, float],
) -> dict[str, Any]:
    """Compare scalar metrics and return explicit regression disposition."""
    regressions: dict[str, dict[str, float]] = {}
    checked: dict[str, dict[str, float]] = {}
    for name, tolerance in tolerances.items():
        if name not in current or name not in baseline:
            continue
        current_value = float(current[name])
        baseline_value = float(baseline[name])
        delta = current_value - baseline_value
        checked[name] = {
            "baseline": baseline_value,
            "current": current_value,
            "delta": delta,
            "tolerance": float(tolerance),
        }
        # Higher-is-better metrics are the default scientific classification
        # convention. Lower-is-better metrics can be encoded with a negative
        # tolerance in the manifest/configuration.
        if tolerance >= 0 and delta < -tolerance:
            regressions[name] = checked[name]
        elif tolerance < 0 and delta > abs(tolerance):
            regressions[name] = checked[name]
    return {
        "status": "REGRESSION" if regressions else "PASS",
        "checked": checked,
        "regressions": regressions,
    }


def compare_report_files(
    current_path: str | Path,
    baseline_path: str | Path,
    *,
    tolerances: dict[str, float],
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare two machine-readable benchmark reports."""
    current = json.loads(Path(current_path).read_text(encoding="utf-8"))
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    result = compare_metrics(
        current["metrics"], baseline["metrics"], tolerances=tolerances
    )
    if output_path is not None:
        Path(output_path).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result
