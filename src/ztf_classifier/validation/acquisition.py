
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
    expected_sha256s: tuple[str, ...] = ()
    parent_evidence_sha256: str | None = None
    query_manifest: dict[str, object] | None = None
    source_version: str | None = None
    artifact_names: tuple[str, ...] = ()


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

    response = requests.get(url, timeout=timeout_seconds, allow_redirects=True)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type.lower():
        raise AcquisitionError(f"source returned HTML instead of a data artifact: {url}")
    return response.content


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _md5_bytes(payload: bytes) -> str:
    return hashlib.md5(payload, usedforsecurity=False).hexdigest()


def _looks_like_html(payload: bytes) -> bool:
    sample = payload.lstrip()[:512].lower()
    return sample.startswith((b"<!doctype html", b"<html", b"<head", b"<body"))


def _query_manifest_hash(payload: dict[str, object] | None) -> str | None:
    if payload is None:
        return None
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(canonical)


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AcquisitionError(f"unsupported acquisition URL: {url!r}")


def _artifact_names(request: AcquisitionRequest) -> tuple[str, ...]:
    if request.artifact_names:
        if len(request.artifact_names) != len(request.urls):
            raise AcquisitionError("artifact_names must align one-to-one with acquisition URLs")
        names = request.artifact_names
    elif len(request.urls) == 1:
        names = (request.destination.name,)
    else:
        raise AcquisitionError("multiple acquisition URLs require explicit artifact_names")
    if any(not name or Path(name).name != name for name in names):
        raise AcquisitionError("invalid artifact name")
    return names


def _expected_hashes(request: AcquisitionRequest) -> tuple[str | None, ...]:
    if request.expected_sha256s:
        if len(request.expected_sha256s) != len(request.urls):
            raise AcquisitionError("expected_sha256s must align one-to-one with acquisition URLs")
        return tuple(request.expected_sha256s)
    if len(request.urls) == 1:
        return (request.expected_sha256,)
    return tuple(None for _ in request.urls)




def _resolve_star_embed_urls(
    urls: tuple[str, ...],
    query_manifest: dict[str, object] | None,
    timeout_seconds: float,
) -> tuple[tuple[str, ...], dict[str, object] | None]:
    if not query_manifest or query_manifest.get("revision") != "resolve_at_acquisition":
        return urls, query_manifest
    import requests

    response = requests.get(
        "https://huggingface.co/api/datasets/StarEmbed/ZTF_40k",
        timeout=timeout_seconds,
        params={"expand": "sha,siblings"},
    )
    response.raise_for_status()
    payload = response.json()
    revision = payload.get("sha")
    siblings = payload.get("siblings")
    if not isinstance(revision, str) or len(revision) != 40:
        raise AcquisitionError("Hugging Face did not return a valid dataset commit SHA")
    names = tuple(query_manifest.get("artifact_names", ()))
    if not names:
        names = tuple(Path(url).name for url in urls)
    available = {item.get("rfilename") for item in siblings or [] if isinstance(item, dict)}
    missing = [name for name in names if name not in available]
    if missing:
        raise AcquisitionError("StarEmbed source artifacts missing from resolved revision: " + ", ".join(missing))
    resolved = tuple(
        f"https://huggingface.co/datasets/StarEmbed/ZTF_40k/resolve/{revision}/data/{name}"
        for name in names
    )
    manifest = dict(query_manifest)
    manifest["revision"] = revision
    manifest["resolution"] = "Hugging Face dataset_info API"
    manifest["artifact_names"] = list(names)
    return resolved, manifest

def acquire_source(
    request: AcquisitionRequest,
    *,
    code_version: str,
    fetcher: Fetcher = _requests_fetch,
) -> AcquisitionResult:
    """Acquire all artifacts in a source-backed plan and bind them to one evidence manifest."""
    source = get_source(request.source_id)
    if request.source_version is not None and request.source_version != source.version:
        raise AcquisitionError(
            f"canonical source version mismatch: expected {source.version!r}, got {request.source_version!r}"
        )
    if not request.urls:
        return AcquisitionResult(
            request.benchmark_id,
            request.source_id,
            "BLOCKED_EXTERNAL",
            None,
            None,
            "canonical adapter is derived and requires a dedicated derivation runner",
        )
    resolved_urls, resolved_query_manifest = (_resolve_star_embed_urls(request.urls, request.query_manifest, request.timeout_seconds) if request.source_id == "star_embed_ztf_40k" else (request.urls, request.query_manifest))
    for url in resolved_urls:
        _validate_url(url)

    request = AcquisitionRequest(**{**request.__dict__, "urls": resolved_urls, "query_manifest": resolved_query_manifest})
    names = _artifact_names(request)
    expected_hashes = _expected_hashes(request)
    root = request.destination
    multi = len(request.urls) > 1
    if multi:
        root.mkdir(parents=True, exist_ok=True)
        destinations = tuple(root / name for name in names)
    else:
        destinations = (root,)

    temporary: list[Path] = []
    try:
        for url, destination, expected in zip(request.urls, destinations, expected_hashes, strict=True):
            payload = fetcher(url, request.timeout_seconds)
            if not payload:
                raise AcquisitionError(f"empty response from {url}")
            if _looks_like_html(payload):
                raise AcquisitionError(f"source returned HTML instead of a data artifact: {url}")
            digest = _sha256_bytes(payload)
            if expected and digest != expected:
                raise AcquisitionError(f"SHA-256 mismatch for {url}: expected {expected}, got {digest}")
            if source.expected_md5 and _md5_bytes(payload) != source.expected_md5:
                raise AcquisitionError(f"MD5 mismatch for {url}: expected {source.expected_md5}, got {_md5_bytes(payload)}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            part = destination.with_suffix(destination.suffix + ".part")
            part.write_bytes(payload)
            temporary.append(part)

        for part, destination in zip(temporary, destinations, strict=True):
            part.replace(destination)

        if request.query_manifest is not None:
            query_path = (root / (root.name + ".evidence.query.json") if multi else root.with_name(root.name + ".evidence.query.json"))
            query_path.write_text(json.dumps(request.query_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        manifest = write_evidence_manifest(
            root / (root.name + ".evidence.json") if multi else root.with_name(root.name + ".evidence.json"),
            benchmark_id=request.benchmark_id,
            source_id=source.source_id,
            acquisition_timestamp=datetime.now(timezone.utc).isoformat(),
            code_version=code_version,
            artifacts=tuple(EvidenceArtifact.from_path(path, request.artifact_role) for path in destinations),
            parent_evidence_sha256=request.parent_evidence_sha256,
            query_manifest_sha256=_query_manifest_hash(request.query_manifest),
        )
        return AcquisitionResult(
            request.benchmark_id,
            source.source_id,
            "ACQUIRED",
            manifest.artifacts[0],
            manifest,
        )
    except Exception as exc:
        for part in temporary:
            part.unlink(missing_ok=True)
        return AcquisitionResult(
            request.benchmark_id,
            source.source_id,
            "BLOCKED_EXTERNAL",
            None,
            None,
            str(exc),
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
    """Construct an acquisition request from the canonical benchmark manifest."""
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

    selected_urls = urls or plan.urls
    if urls and len(urls) != len(plan.urls):
        raise AcquisitionError("explicit URL override must preserve the canonical artifact count")

    return AcquisitionRequest(
        benchmark_id=manifest.benchmark_id,
        source_id=plan.source_id,
        source_version=plan.source_version,
        destination=Path(destination),
        urls=selected_urls,
        expected_sha256=expected_sha256,
        expected_sha256s=plan.expected_sha256 if not urls else (),
        parent_evidence_sha256=parent_evidence_sha256,
        query_manifest=query_manifest if query_manifest is not None else plan.query_manifest,
        artifact_names=plan.artifact_names,
    )
