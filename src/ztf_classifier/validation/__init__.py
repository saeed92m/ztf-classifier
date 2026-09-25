"""Scientific validation and external benchmark infrastructure."""

from ztf_classifier.validation.gate import (
    evaluate_release_gate,
    write_release_gate_report,
)
from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.runner import BenchmarkRunResult, run_table_benchmark

__all__ = [
    "BenchmarkManifest",
    "BenchmarkRegistry",
    "BenchmarkRunResult",
    "evaluate_release_gate",
    "run_table_benchmark",
    "write_release_gate_report",
]
