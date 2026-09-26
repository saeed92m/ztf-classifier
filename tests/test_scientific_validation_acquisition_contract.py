import pytest
import requests

from ztf_classifier.validation.acquisition import (
    AcquisitionError,
    AcquisitionRequest,
    acquire_source,
    request_from_benchmark,
    _resolve_star_embed_urls,
)


def test_request_from_benchmark_binds_canonical_source_and_version():
    request = request_from_benchmark(
        "configs/benchmarks",
        "ztf_periodic_781k",
        destination="/tmp/cpvs.parquet",
        urls=("https://example.test/cpvs",),
    )
    assert request.benchmark_id == "ztf_periodic_781k"
    assert request.source_id == "ztf_periodic_781k"
    assert request.source_version == "v1 published 2020-06-11"


def test_request_from_benchmark_uses_dynamic_star_embed_resolution():
    request = request_from_benchmark(
        "configs/benchmarks",
        "star_embed_ztf_40k",
        destination="/tmp/star_embed.snapshot",
    )
    assert len(request.urls) == 5
    assert request.query_manifest["revision"] == "resolve_at_acquisition"


def test_730k_request_requires_parent_evidence_binding():
    with pytest.raises(AcquisitionError, match="parent_evidence_sha256"):
        request_from_benchmark(
            "configs/benchmarks",
            "ztf_periodic_730k",
            destination="/tmp/cpvs-730k.derived",
        )


def test_acquisition_rejects_html_payload_without_creating_evidence(tmp_path):
    request = AcquisitionRequest(
        benchmark_id="ztf_periodic_781k",
        source_id="star_embed_ztf_40k",
        destination=tmp_path / "artifact.bin",
        urls=("https://example.test/landing",),
        source_version="2026-05 dataset snapshot",
    )

    def fetcher(_url: str, _timeout: float) -> bytes:
        return b"<html><body>landing page</body></html>"

    result = acquire_source(request, code_version="test", fetcher=fetcher)
    assert result.status == "BLOCKED_EXTERNAL"
    assert not request.destination.exists()
    assert result.evidence_manifest is None


def test_multi_artifact_acquisition_binds_all_artifacts(tmp_path):
    payloads = {"https://example.test/a": b"alpha", "https://example.test/b": b"beta"}
    request = AcquisitionRequest(
        benchmark_id="ztf_periodic_781k",
        source_id="star_embed_ztf_40k",
        destination=tmp_path / "snapshot",
        urls=tuple(payloads),
        artifact_names=("a.bin", "b.bin"),
        source_version="2026-05 dataset snapshot",
    )
    result = acquire_source(request, code_version="test", fetcher=lambda url, _timeout: payloads[url])
    assert result.status == "ACQUIRED"
    assert result.evidence_manifest is not None
    assert len(result.evidence_manifest.artifacts) == 2


def test_star_embed_resolution_records_resolved_revision(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "sha": "0123456789abcdef0123456789abcdef01234567",
                "siblings": [
                    {"rfilename": "data/train-00000-of-00002.parquet"},
                    {"rfilename": "data/train-00001-of-00002.parquet"},
                    {"rfilename": "data/validation-00000-of-00001.parquet"},
                    {"rfilename": "data/test-00000-of-00001.parquet"},
                    {"rfilename": "data/anom-00000-of-00001.parquet"},
                ],
            }

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())
    urls = tuple(
        f"https://huggingface.co/datasets/StarEmbed/ZTF_40k/resolve/resolve_at_acquisition/data/{name}"
        for name in (
            "train-00000-of-00002.parquet",
            "train-00001-of-00002.parquet",
            "validation-00000-of-00001.parquet",
            "test-00000-of-00001.parquet",
            "anom-00000-of-00001.parquet",
        )
    )
    resolved, manifest = _resolve_star_embed_urls(
        urls,
        {"revision": "resolve_at_acquisition"},
        10.0,
    )
    assert manifest["revision"] == "0123456789abcdef0123456789abcdef01234567"
    assert all("/resolve/0123456789abcdef0123456789abcdef01234567/" in url for url in resolved)
