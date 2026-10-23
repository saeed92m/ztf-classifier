"""File-based entry point for survey-neutral light-curve normalization.

CSV identifiers are read as strings to preserve leading zeros. Parquet is
read with its stored schema. This loader does not fetch remote data, infer
column mappings, or perform scientific unit/time conversions.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.lightcurve_schema import (
    LightCurveColumnMap,
    LightCurveNormalizationResult,
    normalize_lightcurve_table,
)


SUPPORTED_SUFFIXES = {".csv", ".parquet", ".pq"}


def load_lightcurve_file(
    path: str | Path,
    mapping: LightCurveColumnMap,
) -> LightCurveNormalizationResult:
    """Read a local CSV/Parquet table and normalize it using explicit mapping."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ApplicationInputError(
            f"Unsupported light-curve file extension {suffix!r}; "
            "supported extensions are .csv, .parquet, and .pq."
        )
    if not source.is_file():
        raise ApplicationInputError(f"Light-curve input file does not exist: {source}")

    try:
        if suffix == ".csv":
            # Avoid numeric inference corrupting identifiers such as "00123".
            table = pd.read_csv(source, dtype="string")
        else:
            table = pd.read_parquet(source)
    except (OSError, ValueError, ImportError) as exc:
        raise ApplicationInputError(
            f"Could not read light-curve file {source.name!r}: {exc}"
        ) from exc

    result = normalize_lightcurve_table(table, mapping)
    diagnostics = dict(result.diagnostics)
    diagnostics.update(
        {
            "source_file_name": source.name,
            "source_format": suffix.lstrip("."),
            "source_file_rows_read": len(table),
        }
    )
    return LightCurveNormalizationResult(
        observations=result.observations,
        schema_version=result.schema_version,
        diagnostics=diagnostics,
    )


__all__ = ["SUPPORTED_SUFFIXES", "load_lightcurve_file"]
