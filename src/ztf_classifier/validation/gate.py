"""Fail-closed scientific validation release gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry

REQUIRED_BENCHMARKS = (
    "star_embed_ztf_40k",
    "ztf_periodic_730k",
    "ztf_periodic_781k",
    "ztf_dr24_source_subset",
    "alerce_reference",
)

REQUIRED_SCIENTIFIC_CHECKS = (
    "object_overlap",
    "duplicate_objects",
    "target_leakage",
    "future_data_leakage",
    "benchmark_trained_artifacts",
    "preprocessing_consistency",
    "schema_compatibility",
    "feature_generation_determinism",
    "qc_acceptance",
    "inference_reproducibility",
    "failure_code_correctness",
    "provenance",
)


def evaluate_release_gate(
    registry_dir: str | Path = "configs/benchmarks",
    evidence_dir: str | Path = "reports/scientific_validation",
) -> dict[str, Any]:
    """Evaluate the product scientific gate without weakening missing evidence."""
    registry = BenchmarkRegistry(registry_dir)
    evidence_root = Path(evidence_dir)
    blockers: list[str] = []
    benchmarks: list[dict[str, Any]] = []

    for benchmark_id in REQUIRED_BENCHMARKS:
        try:
            manifest = registry.load(benchmark_id)
        except (FileNotFoundError, ValueError) as exc:
            blockers.append(f"{benchmark_id}: manifest unavailable: {exc}")
            continue

        manifest_blockers = _manifest_blockers(manifest)
        report_path = evidence_root / benchmark_id / "benchmark_result.json"
        report: dict[str, Any] | None = None
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                manifest_blockers.append(f"invalid evidence report: {exc}")
        else:
            manifest_blockers.append("benchmark evidence report is missing")

        if report is not None:
            if report.get("status") != "PASS":
                manifest_blockers.append(f"benchmark status is {report.get('status', 'UNKNOWN')}")
            checks = report.get("checks", {})
            if not isinstance(checks, dict):
                manifest_blockers.append("scientific checks are missing or invalid")
                checks = {}
            for check in REQUIRED_SCIENTIFIC_CHECKS:
                value = checks.get(check, "NOT_EXECUTED")
                status = value.get("status") if isinstance(value, dict) else value
                if status != "PASS":
                    manifest_blockers.append(f"scientific check {check} is {status}")
            if not report.get("provenance_complete", False):
                manifest_blockers.append("provenance is incomplete")

        if manifest_blockers:
            blockers.extend(f"{benchmark_id}: {item}" for item in manifest_blockers)

        benchmarks.append({
            "benchmark_id": benchmark_id,
            "evaluation_role": manifest.evaluation_role,
            "status": "PASS" if not manifest_blockers else "BLOCKED",
            "blockers": manifest_blockers,
        })

    status = "PASS" if not blockers else "NOT_VERIFIED"
    return {
        "status": status,
        "release_blocking": True,
        "required_checks": list(REQUIRED_SCIENTIFIC_CHECKS),
        "benchmarks": benchmarks,
        "blockers": blockers,
        "interpretation": (
            "Benchmark success is not proof of universal correctness; it is quantitative "
            "and reproducible evidence for the declared population, source/version, labels, "
            "preprocessing, and evaluation conditions."
        ),
    }


def _manifest_blockers(manifest: BenchmarkManifest) -> list[str]:
    blockers: list[str] = []
    if not manifest.hashes:
        blockers.append("source/object hashes are not recorded")
    if not manifest.file_object_ids and manifest.evaluation_role != "reference_system":
        blockers.append("benchmark object/file identifiers are not pinned")
    blockers.extend(manifest.validate_release_contract())
    if manifest.evaluation_role == "ground_truth" and not manifest.ground_truth_provenance:
        blockers.append("ground-truth provenance is missing")
    if manifest.evaluation_role == "reference_system" and not manifest.reference_system_provenance:
        blockers.append("reference-system provenance is missing")
    return blockers


def write_release_gate_report(
    output_path: str | Path,
    registry_dir: str | Path = "configs/benchmarks",
    evidence_dir: str | Path = "reports/scientific_validation",
) -> dict[str, Any]:
    result = evaluate_release_gate(registry_dir, evidence_dir)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "
", encoding="utf-8")
    return result
