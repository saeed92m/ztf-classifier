from pathlib import Path

import pytest

from ztf_classifier.reproducibility.checksums import sha256_file


def test_sha256_file_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"ztf-classifier\\x00payload")
    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64


def test_sha256_file_missing_path_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        sha256_file(tmp_path / "missing.bin")


def test_sha256_file_rejects_invalid_chunk_size(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"payload")
    with pytest.raises(ValueError, match="chunk_size"):
        sha256_file(path, chunk_size=0)
