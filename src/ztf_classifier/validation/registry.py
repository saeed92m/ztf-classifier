"""Filesystem-backed benchmark manifest registry."""

from __future__ import annotations

from pathlib import Path

from ztf_classifier.validation.manifest import BenchmarkManifest


class BenchmarkRegistry:
    """Discover, load, and validate versioned benchmark manifests."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def list(self) -> tuple[str, ...]:
        if not self.root.exists():
            return ()
        return tuple(sorted(path.stem for path in self.root.glob("*.json") if path.is_file()))

    def load(self, benchmark_id: str) -> BenchmarkManifest:
        path = self.root / f"{benchmark_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Benchmark manifest does not exist: {path}")
        manifest = BenchmarkManifest.from_json(path)
        if manifest.benchmark_id != benchmark_id:
            raise ValueError(
                f"Manifest ID mismatch: requested {benchmark_id!r}, found {manifest.benchmark_id!r}"
            )
        return manifest

    def validate_all(self) -> tuple[str, ...]:
        ids = self.list()
        for benchmark_id in ids:
            self.load(benchmark_id)
        return ids
