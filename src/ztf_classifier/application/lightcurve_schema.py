"""Explicit, loss-aware mapping into the survey-neutral light-curve schema.

This module does not convert units, time systems, magnitudes, or fluxes. Those
operations require a separate, named, tested transformation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

import numpy as np
import pandas as pd

from ztf_classifier.application.errors import ApplicationInputError

CANONICAL_OBSERVATION_COLUMNS = (
    "object_id",
    "time_value",
    "time_format",
    "time_scale",
    "band",
    "measurement_type",
    "value",
    "uncertainty",
    "value_unit",
    "quality_flag",
    "source_row",
)


@dataclass(frozen=True)
class LightCurveColumnMap:
    """User-confirmed mapping from source columns and declared semantics."""

    object_id: str
    time: str
    band: str
    value: str
    uncertainty: str
    time_format: str
    time_scale: str
    value_kind: Literal["magnitude", "flux"]
    value_unit: str
    band_map: Mapping[str, str] | None = None
    quality_flag: str | None = None

    def validate(self) -> None:
        for name in (
            "object_id", "time", "band", "value", "uncertainty",
            "time_format", "time_scale", "value_unit",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ApplicationInputError(f"{name} must be explicitly declared.")
        if self.value_kind not in {"magnitude", "flux"}:
            raise ApplicationInputError("value_kind must be 'magnitude' or 'flux'.")
        columns = [self.object_id, self.time, self.band, self.value, self.uncertainty]
        if self.quality_flag is not None:
            columns.append(self.quality_flag)
        if len(columns) != len(set(columns)):
            raise ApplicationInputError("Each mapped source field must use a distinct column.")
        if self.band_map is not None:
            if any(not str(k).strip() or not str(v).strip() for k, v in self.band_map.items()):
                raise ApplicationInputError("band_map keys and values must be non-empty.")


@dataclass(frozen=True)
class LightCurveNormalizationResult:
    """Normalized observations plus diagnostics; no rows are silently dropped."""

    observations: pd.DataFrame
    schema_version: str
    diagnostics: Mapping[str, object]


def normalize_lightcurve_table(
    data: pd.DataFrame,
    mapping: LightCurveColumnMap,
) -> LightCurveNormalizationResult:
    """Map a tabular light curve into a canonical schema without implicit science.

    Numeric parse failures are rejected. Existing missing/non-finite numeric
    values are retained and counted for downstream QC. Source row order and
    duplicate observations are preserved. No unit or time-system conversion
    occurs here.
    """
    mapping.validate()
    if not isinstance(data, pd.DataFrame):
        raise ApplicationInputError("Input must be a pandas DataFrame.")
    if data.empty:
        raise ApplicationInputError("Input contains no observation rows.")
    if not data.columns.is_unique:
        raise ApplicationInputError("Input contains duplicate column names.")

    data = data.reset_index(drop=True)
    required = [
        mapping.object_id, mapping.time, mapping.band, mapping.value,
        mapping.uncertainty,
    ]
    if mapping.quality_flag is not None:
        required.append(mapping.quality_flag)
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ApplicationInputError(
            "Mapped source columns are missing: " + ", ".join(sorted(missing))
        )

    object_ids = data[mapping.object_id]
    bands = data[mapping.band]
    if object_ids.isna().any() or object_ids.astype(str).str.strip().eq("").any():
        raise ApplicationInputError("Object identifiers contain missing/blank values.")
    if bands.isna().any() or bands.astype(str).str.strip().eq("").any():
        raise ApplicationInputError("Passband values contain missing/blank values.")

    numeric: dict[str, pd.Series] = {}
    for target, source_column in (
        ("time_value", mapping.time),
        ("value", mapping.value),
        ("uncertainty", mapping.uncertainty),
    ):
        parsed = pd.to_numeric(data[source_column], errors="coerce")
        invalid_parse = data[source_column].notna() & parsed.isna()
        if invalid_parse.any():
            rows = [int(i) for i in np.flatnonzero(invalid_parse.to_numpy())[:5]]
            raise ApplicationInputError(
                f"Column {source_column!r} contains non-numeric values at zero-based "
                f"row indices {rows}."
            )
        numeric[target] = parsed.astype(float)

    normalized_bands = bands.astype(str).str.strip()
    if mapping.band_map is not None:
        normalized_bands = normalized_bands.map(
            lambda band: mapping.band_map.get(band, band)
        )

    observations = pd.DataFrame(
        {
            "object_id": object_ids.astype(str).str.strip(),
            "time_value": numeric["time_value"],
            "time_format": mapping.time_format.strip(),
            "time_scale": mapping.time_scale.strip(),
            "band": normalized_bands,
            "measurement_type": mapping.value_kind,
            "value": numeric["value"],
            "uncertainty": numeric["uncertainty"],
            "value_unit": mapping.value_unit.strip(),
            "quality_flag": (
                data[mapping.quality_flag].to_numpy(copy=True)
                if mapping.quality_flag is not None
                else None
            ),
            "source_row": np.arange(len(data), dtype=np.int64),
        },
        columns=CANONICAL_OBSERVATION_COLUMNS,
    )

    nonfinite = {
        column: int((~np.isfinite(observations[column].to_numpy(dtype=float))).sum())
        for column in ("time_value", "value", "uncertainty")
    }
    diagnostics = {
        "input_rows": int(len(data)),
        "output_rows": int(len(observations)),
        "unique_objects": int(observations["object_id"].nunique()),
        "bands": sorted(observations["band"].astype(str).unique().tolist()),
        "nonfinite_numeric_values": nonfinite,
        "duplicate_observation_rows": int(
            observations.duplicated(
                subset=["object_id", "time_value", "band", "value", "uncertainty"],
                keep=False,
            ).sum()
        ),
        "dropped_rows": 0,
        "unit_conversion_performed": False,
        "time_conversion_performed": False,
    }
    return LightCurveNormalizationResult(
        observations=observations,
        schema_version="lightcurve-observations-v1",
        diagnostics=diagnostics,
    )


__all__ = [
    "CANONICAL_OBSERVATION_COLUMNS",
    "LightCurveColumnMap",
    "LightCurveNormalizationResult",
    "normalize_lightcurve_table",
]
