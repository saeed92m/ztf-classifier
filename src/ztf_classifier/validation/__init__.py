"""Scientific validation and external benchmark infrastructure."""

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
from ztf_classifier.validation.runner import BenchmarkRunResult, run_table_benchmark
from ztf_classifier.validation.sources import ValidationSource, get_source, source_ids

__all__ = [
    "BenchmarkManifest",
    "BenchmarkRegistry",
    "BenchmarkRunResult",
    "ValidationSource",
    "evaluate_release_gate",
    "render_scientific_validation_report",
    "run_table_benchmark",
    "get_source",
    "source_ids",
    "write_release_gate_report",
    "write_scientific_validation_report",
]
