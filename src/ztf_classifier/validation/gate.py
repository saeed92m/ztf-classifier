"""Fail-closed scientific validation release gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ztf_classifier.validation.adapters import AdapterContractError, build_adapter_plan
from ztf_classifier.validation.evidence import EvidenceManifest
from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry

# Product validation proves the platform's ability to ingest, analyze, and
# produce reproducible scientific outputs. Historical benchmark reconstruction
# is separate evidence for a narrower external-reproduction claim.
PRODUCT_BENCHMARKS = (
    "star_embed_ztf_40k",
    "ztf_dr24_source_subset",
    "alerce_reference",
)
EXTERNAL_REPRODUCTION_BENCHMARKS = (
    "ztf_periodic_730k",
    "ztf_periodic_781k",
)
REQUIRED_BENCHMARKS = PRODUCT_BENCHMARKS + EXTERNAL_REPRODUCTION_BENCHMARKS

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
    product_blockers: list[str] = []
    external_blockers: list[str] = []
    benchmarks: list[dict[str, Any]] = []

    for benchmark_id in REQUIRED_BENCHMARKS:
        try:
            manifest = registry.load(benchmark_id)
        except (FileNotFoundError, ValueError) as exc:
            blockers.append(f"{benchmark_id}: manifest unavailable: {exc}")
            continue

        manifest_blockers = _manifest_blockers(manifest)
        manifest_blockers.extend(_evidence_blockers(benchmark_id, evidence_root))
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
            items = [f"{benchmark_id}: {item}" for item in manifest_blockers]
            blockers.extend(items)
            if benchmark_id in PRODUCT_BENCHMARKS:
                product_blockers.extend(items)
            else:
                external_blockers.extend(items)

        benchmarks.append({
            "benchmark_id": benchmark_id,
            "evaluation_role": manifest.evaluation_role,
            "validation_scope": (
                "product"
                if benchmark_id in PRODUCT_BENCHMARKS
                else "external_reproduction"
            ),
            "status": "PASS" if not manifest_blockers else "BLOCKED",
            "blockers": manifest_blockers,
        })

    # Only product-scope evidence blocks the product release gate.
    # External reconstruction remains fail-closed for its own claim, but does
    # not block development/testing of the actual ingestion/analysis path.
    product_status = "PASS" if not product_blockers else "NOT_VERIFIED"
    external_status = "PASS" if not external_blockers else "NOT_VERIFIED"
    return {
        "status": product_status,
        "release_blocking": True,
        "required_checks": list(REQUIRED_SCIENTIFIC_CHECKS),
        "product_gate": {
            "status": product_status,
            "release_blocking": True,
            "benchmarks": list(PRODUCT_BENCHMARKS),
            "blockers": product_blockers,
        },
        "external_reproduction": {
            "status": external_status,
            "release_blocking": False,
            "claim": "exact historical CPVS membership reconstruction",
            "benchmarks": list(EXTERNAL_REPRODUCTION_BENCHMARKS),
            "blockers": external_blockers,
        },
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
    blockers.extend(manifest.validate_release_contract())
    try:
        build_adapter_plan(manifest)
    except (AdapterContractError, KeyError, ValueError) as exc:
        blockers.append(f"canonical adapter contract is not executable: {exc}")
    if manifest.evaluation_role == "ground_truth" and not manifest.ground_truth_provenance:
        blockers.append("ground-truth provenance is missing")
    if manifest.evaluation_role == "reference_system" and not manifest.reference_system_provenance:
        blockers.append("reference-system provenance is missing")
    return blockers


def _evidence_blockers(benchmark_id: str, evidence_root: Path) -> list[str]:
    """Require immutable source evidence when registry values are resolved at runtime.

    Static registry hashes/object IDs are appropriate for frozen manifests, but some
    adapters (for example revision-resolved sources and derived benchmarks) can only
    bind exact artifacts at acquisition/derivation time. Their immutable evidence
    manifests are therefore the authoritative artifact-level binding.
    """
    benchmark_dir = evidence_root / benchmark_id
    candidates = sorted(benchmark_dir.glob("*.evidence.json"))
    if not candidates:
        return ["immutable evidence manifest is missing"]

    errors: list[str] = []
    valid = False
    for evidence_path in candidates:
        try:
            evidence = EvidenceManifest.from_dict(
                json.loads(evidence_path.read_text(encoding="utf-8"))
            )
            errors.extend(
                f"{evidence_path.name}: {item}"
                for item in evidence.verify(evidence_root)
            )
            if evidence.benchmark_id != benchmark_id:
                errors.append(
                    f"{evidence_path.name}: evidence benchmark ID is {evidence.benchmark_id!r}"
                )
            if evidence.immutable and evidence.benchmark_id == benchmark_id:
                valid = True
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{evidence_path.name}: invalid evidence manifest: {exc}")

    if not valid:
        errors.append("no valid immutable evidence manifest was found")
    return errors


def write_release_gate_report(
    output_path: str | Path,
    registry_dir: str | Path = "configs/benchmarks",
    evidence_dir: str | Path = "reports/scientific_validation",
) -> dict[str, Any]:
    result = evaluate_release_gate(registry_dir, evidence_dir)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
