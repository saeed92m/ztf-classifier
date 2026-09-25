from pathlib import Path

import pytest

from ztf_classifier.validation.acquisition import AcquisitionRequest, acquire_source


def test_acquisition_is_content_addressed_and_emits_evidence(tmp_path: Path):
    payload = b"immutable benchmark bytes"
    destination = tmp_path / "snapshot.bin"

    def fetcher(url: str, timeout: float) -> bytes:
        assert url == "https://example.test/snapshot"
        assert timeout == 5
        return payload

    result = acquire_source(
        AcquisitionRequest(
            benchmark_id="ztf_periodic_781k",
            source_id="ztf_periodic_781k",
            destination=destination,
            urls=("https://example.test/snapshot",),
            timeout_seconds=5,
        ),
        code_version="test",
        fetcher=fetcher,
    )

    assert result.status == "ACQUIRED"
    assert result.artifact is not None
    assert result.evidence_manifest is not None
    assert destination.read_bytes() == payload
    assert result.evidence_manifest.verify(tmp_path) == []


def test_acquisition_rejects_expected_hash_mismatch(tmp_path: Path):
    result = acquire_source(
        AcquisitionRequest(
            benchmark_id="star_embed_ztf_40k",
            source_id="star_embed_ztf_40k",
            destination=tmp_path / "snapshot.bin",
            urls=("https://example.test/snapshot",),
            expected_sha256="0" * 64,
        ),
        code_version="test",
        fetcher=lambda url, timeout: b"actual",
    )

    assert result.status == "BLOCKED_EXTERNAL"
    assert result.artifact is None
    assert "SHA-256 mismatch" in (result.error or "")
    assert not (tmp_path / "snapshot.bin").exists()


def test_acquisition_tries_fallback_urls(tmp_path: Path):
    calls: list[str] = []

    def fetcher(url: str, timeout: float) -> bytes:
        calls.append(url)
        if url.endswith("/primary"):
            raise OSError("temporary outage")
        return b"fallback"

    result = acquire_source(
        AcquisitionRequest(
            benchmark_id="ztf_dr24_source_subset",
            source_id="ztf_dr24_source_subset",
            destination=tmp_path / "snapshot.bin",
            urls=("https://example.test/primary", "https://example.test/fallback"),
        ),
        code_version="test",
        fetcher=fetcher,
    )

    assert result.status == "ACQUIRED"
    assert calls == [
        "https://example.test/primary",
        "https://example.test/fallback",
    ]


def test_acquisition_rejects_non_http_urls(tmp_path: Path):
    with pytest.raises(Exception):
        acquire_source(
            AcquisitionRequest(
                benchmark_id="alerce_reference",
                source_id="alerce_reference",
                destination=tmp_path / "snapshot.bin",
                urls=("file:///etc/passwd",),
            ),
            code_version="test",
            fetcher=lambda url, timeout: b"never",
        )
