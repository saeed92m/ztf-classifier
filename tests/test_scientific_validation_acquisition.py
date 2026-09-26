from io import BytesIO
from pathlib import Path
import zipfile

import pytest

from ztf_classifier.validation.acquisition import (
    AcquisitionError,
    AcquisitionRequest,
    acquire_source,
)


def _cpvs_payload(*source_ids: str) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "Table2.txt",
            "SourceID\n" + "".join(f"{source_id}\n" for source_id in source_ids),
        )
    return buffer.getvalue()


def test_acquisition_is_content_addressed_and_emits_evidence(tmp_path: Path):
    payload = _cpvs_payload("1", "2", "3")
    destination = tmp_path / "snapshot.zip"

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
    assert result.evidence_manifest.row_count == 3
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
    with pytest.raises(AcquisitionError):
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


def test_star_embed_revision_resolution_uses_supported_expand_parameters(monkeypatch):
    from ztf_classifier.validation import acquisition

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "sha": "a" * 40,
                "siblings": [
                    {"rfilename": "data/train-00000-of-00002.parquet"},
                    {"rfilename": "data/train-00001-of-00002.parquet"},
                ],
            }

    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs["params"]
        return Response()

    monkeypatch.setattr(acquisition.requests, "get", fake_get)
    urls, manifest = acquisition._resolve_star_embed_urls(
        (
            "https://huggingface.co/datasets/StarEmbed/ZTF_40k/resolve/resolve_at_acquisition/data/train-00000-of-00002.parquet",
            "https://huggingface.co/datasets/StarEmbed/ZTF_40k/resolve/resolve_at_acquisition/data/train-00001-of-00002.parquet",
        ),
        {
            "provider": "huggingface",
            "dataset": "StarEmbed/ZTF_40k",
            "revision": "resolve_at_acquisition",
            "artifact_names": [
                "train-00000-of-00002.parquet",
                "train-00001-of-00002.parquet",
            ],
        },
        5.0,
    )

    assert captured["params"] == [("expand", "sha"), ("expand", "siblings")]
    assert urls[0].endswith("/resolve/" + "a" * 40 + "/data/train-00000-of-00002.parquet")
    assert manifest["revision"] == "a" * 40
