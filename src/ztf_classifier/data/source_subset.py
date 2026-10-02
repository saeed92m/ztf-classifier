"""Normalization, QC, and temporal controls for operational source subsets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

SOURCE_SUBSET_NORMALIZATION_CONTRACT = "ztf.object.v1"
REQUIRED_OBJECT_COLUMNS = ("oid", "ra", "dec", "ngoodobsrel")


class SourceSubsetValidationError(ValueError):
    """Raised when a source subset violates its executable contract."""


@dataclass(frozen=True)
class SourceSubsetQC:
    input_rows: int
    output_rows: int
    dropped_rows: int

    def to_dict(self) -> dict[str, int]:
        return {
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "dropped_rows": self.dropped_rows,
        }


def normalize_source_subset(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize an object subset and fail closed on identity/schema/QC violations."""
    normalized = frame.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]

    missing = [column for column in REQUIRED_OBJECT_COLUMNS if column not in normalized.columns]
    if missing:
        raise SourceSubsetValidationError(
            "source subset missing required columns: " + ", ".join(missing)
        )

    normalized["oid"] = normalized["oid"].astype(str).str.strip()
    if normalized["oid"].eq("").any() or normalized["oid"].eq("nan").any():
        raise SourceSubsetValidationError("oid contains empty/null values")
    if normalized["oid"].duplicated().any():
        raise SourceSubsetValidationError("oid contains duplicate values")

    for column in ("ra", "dec", "ngoodobsrel"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    if normalized[list(REQUIRED_OBJECT_COLUMNS)].isna().any().any():
        raise SourceSubsetValidationError("required source columns contain null/non-numeric values")
    if not normalized["ra"].between(0.0, 360.0, inclusive="both").all():
        raise SourceSubsetValidationError("ra is outside [0, 360]")
    if not normalized["dec"].between(-90.0, 90.0, inclusive="both").all():
        raise SourceSubsetValidationError("dec is outside [-90, 90]")
    if (normalized["ngoodobsrel"] < 0).any():
        raise SourceSubsetValidationError("ngoodobsrel cannot be negative")

    return normalized.sort_values("oid", kind="mergesort").reset_index(drop=True)


def apply_temporal_cutoff(
    frame: pd.DataFrame,
    time_column: str,
    cutoff_mjd: float,
) -> pd.DataFrame:
    """Apply an inclusive MJD cutoff; missing time provenance fails closed."""
    if cutoff_mjd <= 0:
        raise SourceSubsetValidationError("cutoff_mjd must be positive")
    if time_column not in frame.columns:
        raise SourceSubsetValidationError(
            f"temporal control requires observation time column: {time_column}"
        )

    result = frame.copy()
    result[time_column] = pd.to_numeric(result[time_column], errors="coerce")
    if result[time_column].isna().any():
        raise SourceSubsetValidationError(
            f"observation time column contains null/non-numeric values: {time_column}"
        )
    if (result[time_column] < 0).any():
        raise SourceSubsetValidationError(
            f"observation time column contains negative MJD values: {time_column}"
        )

    return result.loc[result[time_column] <= cutoff_mjd].reset_index(drop=True)


def qc_source_subset(before: pd.DataFrame, after: pd.DataFrame) -> SourceSubsetQC:
    """Return measured QC counts without silently dropping invalid source rows."""
    if len(after) > len(before):
        raise SourceSubsetValidationError("QC output cannot contain more rows than input")
    return SourceSubsetQC(
        input_rows=len(before),
        output_rows=len(after),
        dropped_rows=len(before) - len(after),
    )
