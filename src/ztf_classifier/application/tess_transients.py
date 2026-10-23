"""Adapter for the public TESS Transients text light-curve products.

Source format documented at:
https://tess.mit.edu/public/tesstransients/pages/readme.html

The adapter preserves the selected source measurement and does not correct the
background, recalibrate photometry, or claim cross-survey model compatibility.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.lightcurve_schema import (
    LightCurveColumnMap,
    LightCurveNormalizationResult,
    normalize_lightcurve_table,
)

TESS_TRANSIENT_COLUMNS = (
    "BTJD",
    "TJD",
    "cts_per_s",
    "e_cts_per_s",
    "mag",
    "e_mag",
    "bkg",
    "bkg_model",
    "bkg2",
    "e_bkg2",
)


def load_tess_transient(
    path: str | Path,
    *,
    object_id: str,
    measurement: str = "flux",
) -> LightCurveNormalizationResult:
    """Load one TESS Transients text file with explicit TESS semantics.

    measurement may be flux (counts/s) or magnitude (TESS mag). The source's
    e_mag == 99.9 upper-limit sentinel is retained as a quality flag. No rows
    are dropped and no flux/magnitude conversion is performed.
    """
    source = Path(path)
    if not source.is_file():
        raise ApplicationInputError(f"TESS Transients file does not exist: {source}")
    if not object_id.strip():
        raise ApplicationInputError("object_id must be explicitly provided.")
    if measurement not in {"flux", "magnitude"}:
        raise ApplicationInputError("measurement must be 'flux' or 'magnitude'.")

    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ApplicationInputError(f"Could not read TESS Transients file: {exc}") from exc
    if len(lines) < 3:
        raise ApplicationInputError("TESS Transients file must contain two header lines and data.")

    header = lines[0]
    reference_match = re.search(r"reference_flux\s*:\s*([-+0-9.eE]+)", header)
    if not header.lstrip().startswith("#") or reference_match is None:
        raise ApplicationInputError("Missing documented TESS 'reference_flux:' header.")
    column_header = lines[1].lstrip()
    if not column_header.startswith("#"):
        raise ApplicationInputError("Missing TESS column-header line.")
    declared_columns = column_header.lstrip("#").split()
    if tuple(declared_columns) != TESS_TRANSIENT_COLUMNS:
        raise ApplicationInputError(
            "Unexpected TESS Transients columns; expected the documented 10-column schema."
        )

    try:
        table = pd.read_csv(
            source,
            sep=r"\s+",
            skiprows=2,
            header=None,
            names=list(TESS_TRANSIENT_COLUMNS),
            comment="#",
        )
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise ApplicationInputError(f"Could not parse TESS Transients observations: {exc}") from exc
    if table.empty:
        raise ApplicationInputError("TESS Transients file contains no observation rows.")

    table.insert(0, "object_id", object_id.strip())
    # The source marks 3-sigma magnitude upper limits with e_mag == 99.9.
    table["tess_upper_limit"] = pd.to_numeric(table["e_mag"], errors="coerce").eq(99.9).map(
        {True: "magnitude_upper_limit_3sigma", False: "not_marked_as_upper_limit"}
    )
    if measurement == "flux":
        value_column, error_column = "cts_per_s", "e_cts_per_s"
        value_unit = "counts_per_second"
    else:
        value_column, error_column = "mag", "e_mag"
        value_unit = "TESS_magnitude_Vega_like"

    table["tess_band"] = "TESS"
    mapping = LightCurveColumnMap(
        object_id="object_id",
        time="BTJD",
        band="tess_band",
        value=value_column,
        uncertainty=error_column,
        time_format="BTJD",
        time_scale="TDB_spacecraft_frame",
        value_kind=measurement,  # type: ignore[arg-type]
        value_unit=value_unit,
        quality_flag="tess_upper_limit",
        band_map={"TESS": "TESS"},
    )
    result = normalize_lightcurve_table(table, mapping)
    diagnostics: Mapping[str, object] = {
        **result.diagnostics,
        "source_survey": "TESS Transients",
        "source_file_name": source.name,
        "source_format": "whitespace_text",
        "source_rows_read": len(table),
        "reference_flux_counts_per_second": float(reference_match.group(1)),
        "measurement_selected": measurement,
        "magnitude_upper_limit_sentinel": "e_mag == 99.9",
        "magnitude_upper_limit_rows": int(
            table["tess_upper_limit"].eq("magnitude_upper_limit_3sigma").sum()
        ),
        "background_correction_performed": False,
        "photometric_recalibration_performed": False,
        "model_compatibility_asserted": False,
    }
    return LightCurveNormalizationResult(
        observations=result.observations,
        schema_version=result.schema_version,
        diagnostics=diagnostics,
    )


__all__ = ["TESS_TRANSIENT_COLUMNS", "load_tess_transient"]
