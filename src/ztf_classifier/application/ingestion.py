"""Local tabular data ingestion with explicit limits and provenance.

This module is an application boundary: it reads user-selected CSV/Parquet files
without changing scientific artifacts or silently fetching external datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal

import pandas as pd

from ztf_classifier.application.contracts import DataSourceRef
from ztf_classifier.application.errors import ApplicationInputError

_SUPPORTED_FORMATS = {"csv", "parquet"}


@dataclass(frozen=True)
class ImportRequest:
    """Validated intent to import one local tabular file."""

    path: Path
    format: Literal["csv", "parquet"] | None = None
    max_bytes: int = 250 * 1024 * 1024
    required_columns: tuple[str, ...] = ()
    source_id: str | None = None

    def __post_init__(self) -> None:
        path = Path(self.path).expanduser()
        object.__setattr__(self, "path", path)
        if self.format is not None and self.format not in _SUPPORTED_FORMATS:
            raise ApplicationInputError(
                f"Unsupported import format: {self.format!r}."
            )
        if not isinstance(self.max_bytes, int) or isinstance(self.max_bytes, bool):
            raise ApplicationInputError("max_bytes must be a positive integer.")
        if self.max_bytes <= 0:
            raise ApplicationInputError("max_bytes must be a positive integer.")
        if any(
            not isinstance(column, str) or not column.strip()
            for column in self.required_columns
        ):
            raise ApplicationInputError(
                "required_columns must contain non-empty names."
            )
        if self.source_id is not None and not self.source_id.strip():
            raise ApplicationInputError("source_id must be non-empty when provided.")


@dataclass(frozen=True)
class ImportResult:
    """Imported table plus source identity and content evidence."""

    data: pd.DataFrame
    source: DataSourceRef
    row_count: int
    columns: tuple[str, ...]
    content_sha256: str


class DataIngestionService:
    """Import local CSV/Parquet tables under explicit size and schema checks."""

    def import_file(self, request: ImportRequest) -> ImportResult:
        path = request.path.resolve()
        if not path.exists() or not path.is_file():
            raise ApplicationInputError(f"Input file does not exist: {path}")
        size = path.stat().st_size
        if size <= 0:
            raise ApplicationInputError("Input file is empty.")
        if size > request.max_bytes:
            raise ApplicationInputError(
                f"Input file exceeds max_bytes ({size} > {request.max_bytes})."
            )

        file_format = request.format or path.suffix.lower().lstrip(".")
        if file_format not in _SUPPORTED_FORMATS:
            raise ApplicationInputError(
                "Unsupported file format; choose CSV or Parquet."
            )

        try:
            if file_format == "csv":
                data = pd.read_csv(path)
            else:
                data = pd.read_parquet(path)
        except Exception as exc:
            raise ApplicationInputError(
                f"Could not read {file_format.upper()} input."
            ) from exc

        if data.empty:
            raise ApplicationInputError("Input contains no data rows.")
        if not data.columns.is_unique:
            raise ApplicationInputError("Input contains duplicate column names.")

        missing = sorted(set(request.required_columns) - set(data.columns))
        if missing:
            raise ApplicationInputError(
                f"Input is missing required columns: {', '.join(missing)}."
            )

        digest = _sha256_file(path)
        source_id = request.source_id or path.stem
        source = DataSourceRef(
            source_id=source_id,
            source_type=f"local_{file_format}",
            locator=path.as_uri(),
            schema_version="tabular-v1",
            content_hash=digest,
            metadata={
                "byte_size": size,
                "row_count": len(data),
                "columns": list(data.columns),
                "format": file_format,
            },
        )
        return ImportResult(
            data=data,
            source=source,
            row_count=len(data),
            columns=tuple(str(column) for column in data.columns),
            content_sha256=digest,
        )


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["DataIngestionService", "ImportRequest", "ImportResult"]
