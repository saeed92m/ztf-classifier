"""Light-curve preprocessing utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def prepare_band_lightcurve(
    internal_lc: pd.DataFrame,
    fid: int,
) -> pd.DataFrame:
    """Extract and validate one ZTF filter.

    Rows with non-finite mjd, mag, or magerr values, or with
    non-positive magerr, are removed.
    """

    band = internal_lc[
        internal_lc["fid"] == fid
    ].copy()

    if len(band) == 0:
        return band

    valid = (
        np.isfinite(band["mjd"].to_numpy(dtype=float))
        & np.isfinite(band["mag"].to_numpy(dtype=float))
        & np.isfinite(band["magerr"].to_numpy(dtype=float))
        & (band["magerr"].to_numpy(dtype=float) > 0)
    )

    return (
        band.loc[valid]
        .sort_values("mjd")
        .reset_index(drop=True)
    )
