"""Scientific validation and external benchmark infrastructure."""

from ztf_classifier.validation.adapters import (
    AdapterContractError,
    AdapterPlan,
    build_adapter_plan,
)
from ztf_classifier.validation.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    acquire_all,
    acquire_source,
    request_from_benchmark,
)
from ztf_classifier.validation.checks import CheckResult, run_scientific_checks
from ztf_classifier.validation.derivation import (
    DerivationConfig,
    DerivationResult,
    derive_730k,
)
from ztf_classifier.validation.evidence import (
    EvidenceArtifact,
    EvidenceManifest,
    sha256_file,
    write_evidence_manifest,
)
from ztf_classifier.validation.gate import (
    evaluate_release_gate,
    write_release_gate_report,
)
from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.report import (
    render_scientific_validation_report,
    write_scientific_validation_report,
)
from ztf_classifier.validation.runner import (
    BenchmarkRunResult,
    run_table_benchmark,
)
from ztf_classifier.validation.sources import (
    ValidationSource,
    get_source,
    source_ids,
)

__all__ = [
    "AcquisitionRequest",
    "AcquisitionResult",
    "AdapterContractError",
    "AdapterPlan",
    "BenchmarkManifest",
    "BenchmarkRegistry",
    "BenchmarkRunResult",
    "CheckResult",
    "DerivationConfig",
    "DerivationResult",
    "EvidenceArtifact",
    "EvidenceManifest",
    "ValidationSource",
    "acquire_all",
    "acquire_source",
    "build_adapter_plan",
    "derive_730k",
    "evaluate_release_gate",
    "get_source",
    "render_scientific_validation_report",
    "request_from_benchmark",
    "run_scientific_checks",
    "run_table_benchmark",
    "sha256_file",
    "source_ids",
    "write_evidence_manifest",
    "write_release_gate_report",
    "write_scientific_validation_report",
]
