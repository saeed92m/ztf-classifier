from __future__ import annotations

import hashlib
import io
import zipfile

from scripts import acquire_frozen_reference_evidence as evidence


def _valid_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("sample.csv", "id,value\n1,2\n")
    return buffer.getvalue()


def test_invalid_cached_archive_is_retried_and_replaced(tmp_path, monkeypatch):
    payload = _valid_zip()
    monkeypatch.setitem(
        evidence.SOURCES,
        "test_reference",
        {
            "url": "https://example.invalid/sample.zip",
            "filename": "sample.zip",
            "md5": hashlib.md5(payload).hexdigest(),
            "archive_type": "zip",
            "required_members": set(),
        },
    )
    target = tmp_path / "sample.zip"
    target.write_bytes(b"stale-corrupt-cache")
    downloads = iter((b"first-transfer-corrupt", payload))
    attempts = []

    def fake_download(url, path):
        attempts.append(url)
        path.write_bytes(next(downloads))

    monkeypatch.setattr(evidence, "_download", fake_download)

    manifest_path = evidence.acquire("test_reference", tmp_path)

    assert len(attempts) == 2
    assert target.read_bytes() == payload
    assert manifest_path.exists()
    assert zipfile.is_zipfile(target)
