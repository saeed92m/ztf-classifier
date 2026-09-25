"""Source-backed acquisition contracts for scientific-validation evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

from ztf_classifier.validation.adapters import build_adapter_plan
from ztf_classifier.validation.evidence import EvidenceArtifact, EvidenceManifest, write_evidence_manifest
from ztf_classifier.validation.registry import BenchmarkRegistry
from ztf_classifier.validation.sources import get_source


class AcquisitionError(RuntimeError):
    """Raised when a source-backed acquisition cannot produce valid evidence."""


@dataclass(frozen=True)
class AcquisitionRequest:
    benchmark_id: str
    source_id: str
    destination: Path
    urls: tuple[str, ...]
    artifact_role: str = "benchmark_snapshot"
    timeout_seconds: float = 60.0
    expected_sha256: str | None = None
    parent_evidence_sha256: str | None = None
    query_manifest: dict[str, object] | None = None
    source_version: str | None = None


@dataclass(frozen=True)
class AcquisitionResult:
    benchmark_id: str
    source_id: str
    status: str
    artifact: EvidenceArtifact | None
    evidence_manifest: EvidenceManifest | None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_id": self.benchmark_id,
            "source_id": self.source_id,
            "status": self.status,
            "artifact": self.artifact.to_dict() if self.artifact else None,
            "evidence_manifest": self.evidence_manifest.to_dict() if self.evidence_manifest else None,
            "error": self.error,
        }


Fetcher = Callable[[str, float], bytes]


def _requests_fetch(url: str, timeout_seconds: float) -> bytes:
    import requests

    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type.lower():
        raise AcquisitionError(f"source returned HTML instead of a data artifact: {url}")
    return response.content


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _query_manifest_hash(payload: dict[str, object] | None) -> str | None:
    if payload is None:
        return None
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(canonical)


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AcquisitionError(f"unsupported acquisition URL: {url!r}")


def acquire_source(
    request: AcquisitionRequest,
    *,
    code_version: str,
    fetcher: Fetcher = _requests_fetch,
) -> AcquisitionResult:
    """Acquire one source artifact and bind it to an immutable evidence manifest."""
    source = get_source(request.source_id)
    if request.source_version is not None and request.source_version != source.version:
        raise AcquisitionError(
            f"canonical source version mismatch: expected {source.version!r}, got {request.source_version!r}"
        )
    if not request.urls:
        raise AcquisitionError("at least one acquisition URL is required")
    for url in request.urls:
        _validate_url(url)

    destination = request.destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: str | None = None

    for url in request.urls:
        try:
            payload = fetcher(url, request.timeout_seconds)
            if not payload:
                raise AcquisitionError(f"empty response from {url}")
            digest = _sha256_bytes(payload)
            if request.expected_sha256 and digest != request.expected_sha256:
                raise AcquisitionError(
                    f"SHA-256 mismatch for {url}: expected {request.expected_sha256}, got {digest}"
                )
            temporary = destination.with_suffix(destination.suffix + ".part")
            temporary.write_bytes(payload)
            temporary.replace(destination)

            artifact = EvidenceArtifact.from_path(destination, request.artifact_role)
            query_hash = _query_manifest_hash(request.query_manifest)
            manifest = write_evidence_manifest(
                destination.with_name(destination.name + ".evidence.json"),
                benchmark_id=request.benchmark_id,
                source_id=source.source_id,
                acquisition_timestamp=datetime.now(timezone.utc).isoformat(),
                code_version=code_version,
                artifacts=(artifact,),
                parent_evidence_sha256=request.parent_evidence_sha256,
                query_manifest_sha256=query_hash,
            )
            return AcquisitionResult(
                benchmark_id=request.benchmark_id,
                source_id=source.source_id,
                status="ACQUIRED",
                artifact=artifact,
                evidence_manifest=manifest,
            )
        except Exception as exc:  # noqa: BLE001 - acquisition must try fallbacks
            last_error = f"{url}: {exc}"

    return AcquisitionResult(
        benchmark_id=request.benchmark_id,
        source_id=source.source_id,
        status="BLOCKED_EXTERNAL",
        artifact=None,
        evidence_manifest=None,
        error=last_error or "all acquisition URLs failed",
    )


def acquire_all(
    requests: Iterable[AcquisitionRequest],
    *,
    code_version: str,
    fetcher: Fetcher = _requests_fetch,
) -> tuple[AcquisitionResult, ...]:
    return tuple(acquire_source(item, code_version=code_version, fetcher=fetcher) for item in requests)


def request_from_benchmark(
    registry_dir: str | Path,
    benchmark_id: str,
    *,
    destination: str | Path,
    urls: tuple[str, ...] = (),
    query_manifest: dict[str, object] | None = None,
    expected_sha256: str | None = None,
    parent_evidence_sha256: str | None = None,
) -> AcquisitionRequest:
    """Construct an acquisition request from the canonical benchmark manifest.

    Caller-supplied URLs are accepted only as explicit fallback endpoints; the
    canonical source identity/version always come from the adapter contract.
    """
    manifest = BenchmarkRegistry(registry_dir).load(benchmark_id)
    try:
        plan = build_adapter_plan(manifest)
    except (KeyError, ValueError) as exc:
        raise AcquisitionError(
            f"invalid canonical adapter contract for {benchmark_id}: {exc}"
        ) from exc

    if parent_evidence_sha256 is None and plan.parent_benchmark_id:
        raise AcquisitionError(
            f"{benchmark_id} requires parent_evidence_sha256 for {plan.parent_benchmark_id}"
        )

    return AcquisitionRequest(
        benchmark_id=manifest.benchmark_id,
        source_id=plan.source_id,
        source_version=plan.source_version,
        destination=Path(destination),
        urls=urls or plan.urls,
        expected_sha256=expected_sha256,
        parent_evidence_sha256=parent_evidence_sha256,
        query_manifest=query_manifest if query_manifest is not None else plan.query_manifest,
    )
