"""Immutable scientific-validation evidence manifests.

Evidence manifests bind a benchmark to exact artifacts, hashes, source metadata,
and the code/provenance used to produce the evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ztf_classifier.validation.sources import get_source


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class EvidenceArtifact:
    path: str
    sha256: str
    size_bytes: int
    role: str

    @classmethod
    def from_path(cls, path: str | Path, role: str) -> "EvidenceArtifact":
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(p)
        return cls(str(p), sha256_file(p), p.stat().st_size, role)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "size_bytes": self.size_bytes, "role": self.role}


@dataclass(frozen=True)
class EvidenceManifest:
    benchmark_id: str
    source_id: str
    source_version: str
    acquisition_timestamp: str
    code_version: str
    artifacts: tuple[EvidenceArtifact, ...]
    parent_evidence_sha256: str | None = None
    query_manifest_sha256: str | None = None
    immutable: bool = True

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceManifest":
        required = ("benchmark_id","source_id","source_version","acquisition_timestamp","code_version","artifacts")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError("Evidence manifest missing required fields: " + ", ".join(missing))
        source = get_source(str(payload["source_id"]))
        if payload["source_version"] != source.version:
            raise ValueError(
                f"source version mismatch for {source.source_id}: expected {source.version!r}, got {payload['source_version']!r}"
            )
        artifacts = tuple(EvidenceArtifact(str(item["path"]), str(item["sha256"]), int(item["size_bytes"]), str(item["role"])) for item in payload["artifacts"])
        if not artifacts:
            raise ValueError("Evidence manifest must contain at least one artifact")
        if payload.get("immutable", True) is not True:
            raise ValueError("Scientific benchmark evidence must be immutable")
        return cls(
            benchmark_id=str(payload["benchmark_id"]), source_id=source.source_id,
            source_version=source.version, acquisition_timestamp=str(payload["acquisition_timestamp"]),
            code_version=str(payload["code_version"]), artifacts=artifacts,
            parent_evidence_sha256=payload.get("parent_evidence_sha256"),
            query_manifest_sha256=payload.get("query_manifest_sha256"), immutable=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "scientific-evidence-manifest-v1",
            "benchmark_id": self.benchmark_id, "source_id": self.source_id,
            "source_version": self.source_version, "acquisition_timestamp": self.acquisition_timestamp,
            "code_version": self.code_version, "immutable": self.immutable,
            "parent_evidence_sha256": self.parent_evidence_sha256,
            "query_manifest_sha256": self.query_manifest_sha256,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }

    def verify(self, root: str | Path = ".") -> list[str]:
        root = Path(root)
        errors: list[str] = []
        source = get_source(self.source_id)
        if self.immutable is not True or not source.immutable_evidence_required:
            errors.append("evidence is not declared immutable")
        for artifact in self.artifacts:
            path = root / artifact.path
            if not path.is_file():
                errors.append(f"artifact missing: {artifact.path}")
                continue
            if path.stat().st_size != artifact.size_bytes:
                errors.append(f"artifact size mismatch: {artifact.path} expected={artifact.size_bytes} actual={path.stat().st_size}")
            if sha256_file(path) != artifact.sha256:
                errors.append(f"artifact hash mismatch: {artifact.path} expected={artifact.sha256}")
        return errors


def write_evidence_manifest(
    output_path: str | Path,
    *,
    benchmark_id: str,
    source_id: str,
    acquisition_timestamp: str,
    code_version: str,
    artifacts: Iterable[EvidenceArtifact],
    parent_evidence_sha256: str | None = None,
    query_manifest_sha256: str | None = None,
) -> EvidenceManifest:
    source = get_source(source_id)
    manifest = EvidenceManifest(
        benchmark_id=benchmark_id, source_id=source.source_id, source_version=source.version,
        acquisition_timestamp=acquisition_timestamp, code_version=code_version,
        artifacts=tuple(artifacts), parent_evidence_sha256=parent_evidence_sha256,
        query_manifest_sha256=query_manifest_sha256,
    )
    if not manifest.artifacts:
        raise ValueError("Evidence manifest requires at least one artifact")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
