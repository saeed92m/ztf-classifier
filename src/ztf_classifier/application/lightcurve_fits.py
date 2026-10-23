"""Explicit-column FITS light-curve ingestion for mission/survey products.

FITS column names and scientific semantics must be supplied by the caller.
This is a format reader, not an automatic TESS/TGLC schema guesser.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from astropy.table import Table

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.lightcurve_schema import (
    LightCurveColumnMap,
    LightCurveNormalizationResult,
    normalize_lightcurve_table,
)


def load_lightcurve_fits(
    path: str | Path,
    *,
    object_id: str,
    time_column: str,
    band_column: str | None,
    value_column: str,
    uncertainty_column: str,
    time_format: str,
    time_scale: str,
    value_kind: str,
    value_unit: str,
    band_value: str | None = None,
    quality_column: str | None = None,
    hdu: int | str = 1,
    band_map: Mapping[str, str] | None = None,
) -> LightCurveNormalizationResult:
    """Read one FITS table with explicit columns, units, time and measurement.

    If a product has no band column (for example, a single-band TESS product),
    the caller must explicitly provide band_value. No time or unit conversion
    is performed. HDU selection is explicit and defaults to extension 1.
    """
    source = Path(path)
    if not source.is_file():
        raise ApplicationInputError(f"FITS light-curve file does not exist: {source}")
    if not object_id.strip():
        raise ApplicationInputError("object_id must be explicitly provided.")
    if band_column is None and (band_value is None or not band_value.strip()):
        raise ApplicationInputError("Provide band_column or an explicit band_value.")
    if band_column is not None and band_value is not None:
        raise ApplicationInputError("Use band_column or band_value, not both.")

    try:
        table = Table.read(source, format="fits", hdu=hdu)
        frame = table.to_pandas()
    except Exception as exc:
        raise ApplicationInputError(f"Could not read FITS table {source.name!r}: {exc}") from exc
    if frame.empty:
        raise ApplicationInputError("FITS light-curve table contains no observation rows.")

    frame.insert(0, "canonical_object_id", object_id.strip())
    if band_column is None:
        frame["canonical_band"] = band_value
        mapped_band_column = "canonical_band"
    else:
        mapped_band_column = band_column
    if quality_column is None:
        frame["canonical_quality"] = "not_provided"
        mapped_quality_column = None
    else:
        mapped_quality_column = quality_column

    mapping = LightCurveColumnMap(
        object_id="canonical_object_id",
        time=time_column,
        band=mapped_band_column,
        value=value_column,
        uncertainty=uncertainty_column,
        time_format=time_format,
        time_scale=time_scale,
        value_kind=value_kind,  # type: ignore[arg-type]
        value_unit=value_unit,
        quality_flag=mapped_quality_column,
        band_map=band_map,
    )
    result = normalize_lightcurve_table(frame, mapping)
    diagnostics = {
        **result.diagnostics,
        "source_file_name": source.name,
        "source_format": "fits",
        "source_hdu": str(hdu),
        "source_rows_read": len(frame),
        "source_columns": list(frame.columns),
        "unit_conversion_performed": False,
        "time_conversion_performed": False,
        "model_compatibility_asserted": False,
    }
    return LightCurveNormalizationResult(
        observations=result.observations,
        schema_version=result.schema_version,
        diagnostics=diagnostics,
    )


__all__ = ["load_lightcurve_fits"]
