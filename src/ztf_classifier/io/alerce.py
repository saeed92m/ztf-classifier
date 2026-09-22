"""ALeRCE light-curve ingestion and normalization."""

from __future__ import annotations

import numpy as np
import pandas as pd


def alerce_to_internal_lc_robust(
    detections: pd.DataFrame,
) -> pd.DataFrame:
    """Convert ALeRCE ZTF detections to the internal light-curve schema.

    Photometry priority:
        1. magpsf_corr + sigmapsf_corr_ext
        2. magpsf + sigmapsf fallback

    Raw ALeRCE columns are never overwritten.
    """

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
            "dubious": lc["dubious"].astype(bool),
            "corrected": lc["corrected"].astype(bool),
            "source": "ALeRCE",
        }
    )

    return (
        internal
        .sort_values(["fid", "mjd"])
        .reset_index(drop=True)
    )
