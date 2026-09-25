"""Scientific validation and external benchmark infrastructure."""

from ztf_classifier.validation.manifest import BenchmarkManifest
from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.runner import BenchmarkRunResult, run_table_benchmark

__all__ = ["BenchmarkManifest", "BenchmarkRegistry", "BenchmarkRunResult", "run_table_benchmark"]
