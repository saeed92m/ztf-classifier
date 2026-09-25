"""Deterministic SHA-256 helpers used by ZTF Classifier."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of path."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["sha256_file"]
