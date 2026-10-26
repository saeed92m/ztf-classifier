from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.smoke_dr24_lightcurve_pipeline import normalize_api_frame


def test_normalize_dr24_hmjd_filter_ids_and_flags() -> None:
    source = pd.DataFrame(
        {
            "HMJD": [60002.0, 60001.0, 60003.0],
            "filterid": [2, 1, 3],
            "mag": [18.2, 18.0, 17.5],
            "magerr": [0.03, 0.02, 0.04],
            "catflags": [0, 4096, 0],
        }
    )
    result, metadata = normalize_api_frame(source)

    assert list(result["fid"]) == [1, 2]
    assert metadata["time_semantics"] == "heliocentric_modified_julian_date"
    assert metadata["g_rows"] == 1
    assert metadata["r_rows"] == 1
    assert metadata["i_or_other_rows_excluded"] == 1
    assert metadata["catflags_nonzero_rows"] == 1


def test_normalize_dr24_accepts_filter_codes() -> None:
    source = pd.DataFrame(
        {
            "hjd": [2460000.5, 2460001.5],
            "filtercode": ["zg", "zr"],
            "mag": [18.2, 18.1],
            "magerr": [0.03, 0.04],
        }
    )
    result, metadata = normalize_api_frame(source)

    assert list(result["fid"]) == [1, 2]
    assert result["mjd"].tolist() == [60000.0, 60001.0]
    assert metadata["time_semantics"] == "hjd_minus_2400000.5"
    assert metadata["catflags_missing_rows"] == 2


def test_normalize_dr24_fails_closed_on_missing_required_columns() -> None:
    source = pd.DataFrame({"HMJD": [60000.0], "mag": [18.0]})
    with pytest.raises(ValueError, match="missing"):
        normalize_api_frame(source)
