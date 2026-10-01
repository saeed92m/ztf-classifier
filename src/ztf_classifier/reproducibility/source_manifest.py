"""Immutable source-subset acquisition and replay contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ztf_classifier.dataset.artifact import sha256_file

SOURCE_SUBSET_MANIFEST_SCHEMA_VERSION = "1.0"


def _require_nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


@dataclass(frozen=True)
class SourceArtifact:
    """One immutable artifact referenced by a source-subset manifest."""

    path: str
    sha256: str

    def __post_init__(self) -> None:
        _require_nonempty(self.path, "artifact path")
        digest = _require_nonempty(self.sha256, "artifact sha256").lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("artifact sha256 must be a 64-character hexadecimal digest.")

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256.lower()}


@dataclass(frozen=True)
class SourceSubsetManifest:
    """Auditable, replayable declaration of a source-derived subset."""

    source: str
    source_version: str
    retrieval_utc: str
    selection: dict[str, Any]
    object_ids: tuple[str, ...]
    artifacts: tuple[SourceArtifact, ...]
    normalization_contract: str
    temporal_cutoff_mjd: float | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.source, "source")
        _require_nonempty(self.source_version, "source_version")
        _require_nonempty(self.retrieval_utc, "retrieval_utc")
        _require_nonempty(self.normalization_contract, "normalization_contract")

        try:
            datetime.fromisoformat(self.retrieval_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("retrieval_utc must be ISO-8601.") from exc

        if not isinstance(self.selection, dict) or not self.selection:
            raise ValueError("selection must be a non-empty mapping.")

        ids = tuple(str(value) for value in self.object_ids)
        if any(not value for value in ids):
            raise ValueError("object_ids cannot contain empty values.")
        if len(ids) != len(set(ids)):
            raise ValueError("object_ids must be unique.")
        if ids != tuple(sorted(ids)):
            raise ValueError("object_ids must be deterministically sorted.")

        if self.temporal_cutoff_mjd is not None and self.temporal_cutoff_mjd <= 0:
            raise ValueError("temporal_cutoff_mjd must be positive.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SOURCE_SUBSET_MANIFEST_SCHEMA_VERSION,
            "source": {
                "name": self.source,
                "version": self.source_version,
                "retrieval_utc": self.retrieval_utc,
            },
            "selection": self.selection,
            "object_ids": list(self.object_ids),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "normalization_contract": self.normalization_contract,
            "temporal_cutoff_mjd": self.temporal_cutoff_mjd,
        }

    def write(self, path: Path) -> Path:
        """Write canonical JSON suitable for version control/evidence bundles."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def verify_artifacts(self, root: Path) -> None:
        """Fail closed if any declared source artifact is missing or changed."""
        root = root.resolve()
        for artifact in self.artifacts:
            path = (root / artifact.path).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"Artifact escapes manifest root: {artifact.path}") from exc
            if not path.is_file():
                raise ValueError(f"Declared source artifact is missing: {artifact.path}")
            actual = sha256_file(path)
            if actual.lower() != artifact.sha256.lower():
                raise ValueError(
                    f"Source artifact checksum mismatch: {artifact.path}; "
                    f"expected {artifact.sha256}, got {actual}"
                )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceSubsetManifest":
        if data.get("schema_version") != SOURCE_SUBSET_MANIFEST_SCHEMA_VERSION:
            raise ValueError("Unsupported source-subset manifest schema version.")
        source = data.get("source") or {}
        artifacts = tuple(
            SourceArtifact(path=item["path"], sha256=item["sha256"])
            for item in data.get("artifacts", [])
        )
        return cls(
            source=source["name"],
            source_version=source["version"],
            retrieval_utc=source["retrieval_utc"],
            selection=dict(data["selection"]),
            object_ids=tuple(str(value) for value in data["object_ids"]),
            artifacts=artifacts,
            normalization_contract=data["normalization_contract"],
            temporal_cutoff_mjd=data.get("temporal_cutoff_mjd"),
        )
