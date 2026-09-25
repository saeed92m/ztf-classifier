"""ALeRCE light-curve ingestion and normalization."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

@dataclass(frozen=True)
class ALeRCEIngestionDiagnostics:
    """Row-level validation and provenance counters for ALeRCE ingestion."""

    rows_input: int
    rows_output: int
    rows_dropped: int
    invalid_mjd: int
    invalid_fid: int
    invalid_mag: int
    invalid_magerr: int
    invalid_coordinates: int
    duplicate_rows: int
    corrected_photometry_count: int
    raw_fallback_count: int

    def to_dict(self) -> dict[str, int]:
        """Return JSON-compatible diagnostics."""
        return asdict(self)


_REQUIRED_COLUMNS = {
    "mjd",
    "fid",
    "magpsf_corr",
    "sigmapsf_corr_ext",
    "magpsf",
    "sigmapsf",
    "ra",
    "dec",
    "dubious",
    "corrected",
}


def _coerce_bool_series(
    series: pd.Series,
    *,
    column_name: str,
) -> pd.Series:
    """Parse boolean-like ALeRCE values without silent string coercion."""
    values = series.astype("string").str.strip().str.lower()
    truthy = values.isin({"true", "1", "yes", "y", "t"})
    falsy = values.isin({"false", "0", "no", "n", "f", ""})
    unknown = ~(truthy | falsy | values.isna())

    if unknown.any():
        bad_values = values[unknown].dropna().unique()[:10]
        raise ValueError(
            f"Column '{column_name}' contains non-boolean values: "
            f"{bad_values.tolist()}"
        )

    return pd.Series(
        truthy.fillna(False).to_numpy(dtype=bool),
        index=series.index,
        dtype=bool,
    )


def alerce_to_internal_lc_robust(
    detections: pd.DataFrame,
    *,
    return_diagnostics: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, ALeRCEIngestionDiagnostics]:
    """Convert ALeRCE ZTF detections to the internal light-curve schema.

    Photometry priority:
        1. magpsf_corr + sigmapsf_corr_ext
        2. magpsf + sigmapsf fallback

    Raw ALeRCE columns are never overwritten.
    """

    missing = _REQUIRED_COLUMNS - set(detections.columns)
    if missing:
        raise ValueError(
            "ALeRCE detections are missing required columns: "
            f"{sorted(missing)}"
        )

    lc = detections.copy()

    mjd = pd.to_numeric(lc["mjd"], errors="coerce")
    fid = pd.to_numeric(lc["fid"], errors="coerce")

    mag_corr = pd.to_numeric(
        lc["magpsf_corr"],
        errors="coerce",
    )

    magerr_corr = pd.to_numeric(
        lc["sigmapsf_corr_ext"],
        errors="coerce",
    )

    mag_raw = pd.to_numeric(
        lc["magpsf"],
        errors="coerce",
    )

    magerr_raw = pd.to_numeric(
        lc["sigmapsf"],
        errors="coerce",
    )

    use_corrected = (
        mag_corr.notna()
        & magerr_corr.notna()
        & (magerr_corr > 0)
    )

    mag = mag_corr.where(use_corrected, mag_raw)
    magerr = magerr_corr.where(use_corrected, magerr_raw)

    photometry_source = np.where(
        use_corrected,
        "corrected",
        "raw_fallback",
    )

    internal = pd.DataFrame(
        {
            "mjd": mjd.astype(float),
            "fid": fid.astype("Int64"),
            "mag": mag.astype(float),
            "magerr": magerr.astype(float),
            "mag_raw": mag_raw.astype(float),
            "magerr_raw": magerr_raw.astype(float),
            "mag_corr": mag_corr.astype(float),
            "magerr_corr": magerr_corr.astype(float),
            "photometry_source": photometry_source,
            "ra": pd.to_numeric(
                lc["ra"],
                errors="coerce",
            ).astype(float),
            "dec": pd.to_numeric(
                lc["dec"],
                errors="coerce",
            ).astype(float),
            "dubious": _coerce_bool_series(
                lc["dubious"],
                column_name="dubious",
            ),
            "corrected": _coerce_bool_series(
                lc["corrected"],
                column_name="corrected",
            ),
            "source": "ALeRCE",
        }
    )

    valid_mjd = mjd.notna() & np.isfinite(mjd) & (mjd >= 0.0)
    valid_fid = fid.notna() & fid.isin({1, 2, 3})
    valid_mag = mag.notna() & np.isfinite(mag)
    valid_magerr = magerr.notna() & np.isfinite(magerr) & (magerr > 0.0)

    ra = internal["ra"]
    dec = internal["dec"]
    valid_coordinates = (
        ra.notna()
        & np.isfinite(ra)
        & (ra >= 0.0)
        & (ra <= 360.0)
        & dec.notna()
        & np.isfinite(dec)
        & (dec >= -90.0)
        & (dec <= 90.0)
    )

    valid_rows = (
        valid_mjd
        & valid_fid
        & valid_mag
        & valid_magerr
        & valid_coordinates
    )

    invalid_counts = {
        "invalid_mjd": int((~valid_mjd).sum()),
        "invalid_fid": int((~valid_fid).sum()),
        "invalid_mag": int((~valid_mag).sum()),
        "invalid_magerr": int((~valid_magerr).sum()),
        "invalid_coordinates": int((~valid_coordinates).sum()),
    }

    filtered = internal.loc[valid_rows].copy()
    duplicate_mask = filtered.duplicated(keep="first")
    duplicate_rows = int(duplicate_mask.sum())
    filtered = filtered.loc[~duplicate_mask].copy()

    diagnostics = ALeRCEIngestionDiagnostics(
        rows_input=len(internal),
        rows_output=len(filtered),
        rows_dropped=len(internal) - len(filtered),
        duplicate_rows=duplicate_rows,
        corrected_photometry_count=int(use_corrected.sum()),
        raw_fallback_count=int((~use_corrected).sum()),
        **invalid_counts,
    )

    filtered = (
        filtered
        .sort_values(["fid", "mjd"])
        .reset_index(drop=True)
    )

    if return_diagnostics:
        return filtered, diagnostics
    return filtered
