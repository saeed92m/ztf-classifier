from __future__ import annotations

import numpy as np
import pytest
from astropy.table import Table

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.lightcurve_fits import load_lightcurve_fits


def _write_fits(path):
    table = Table(
        {
            "TIME": np.array([1500.0, 1500.5]),
            "PDCSAP_FLUX": np.array([100.0, 101.0]),
            "PDCSAP_FLUX_ERR": np.array([1.0, 1.1]),
            "QUALITY": np.array([0, 1], dtype=np.int32),
        }
    )
    table.write(path, format="fits")


def test_load_fits_with_explicit_tess_like_columns_preserves_values(tmp_path):
    path = tmp_path / "tess_like.fits"
    _write_fits(path)

    result = load_lightcurve_fits(
        path,
        object_id="TIC-000123",
        time_column="TIME",
        band_column=None,
        value_column="PDCSAP_FLUX",
        uncertainty_column="PDCSAP_FLUX_ERR",
        time_format="BTJD",
        time_scale="TDB",
        value_kind="flux",
        value_unit="electron_per_second",
        band_value="TESS",
        quality_column="QUALITY",
    )

    assert result.observations["object_id"].tolist() == ["TIC-000123"] * 2
    assert result.observations["time_value"].tolist() == [1500.0, 1500.5]
    assert result.observations["value"].tolist() == [100.0, 101.0]
    assert result.observations["quality_flag"].tolist() == [0, 1]
    assert result.diagnostics["source_format"] == "fits"
    assert result.diagnostics["source_rows_read"] == 2
    assert result.diagnostics["time_conversion_performed"] is False


def test_fits_reader_requires_explicit_band_semantics(tmp_path):
    path = tmp_path / "tess_like.fits"
    _write_fits(path)

    with pytest.raises(ApplicationInputError, match="band_value"):
        load_lightcurve_fits(
            path,
            object_id="TIC-1",
            time_column="TIME",
            band_column=None,
            value_column="PDCSAP_FLUX",
            uncertainty_column="PDCSAP_FLUX_ERR",
            time_format="BTJD",
            time_scale="TDB",
            value_kind="flux",
            value_unit="electron_per_second",
        )


def test_fits_reader_rejects_missing_file(tmp_path):
    with pytest.raises(ApplicationInputError, match="does not exist"):
        load_lightcurve_fits(
            tmp_path / "missing.fits",
            object_id="TIC-1",
            time_column="TIME",
            band_column=None,
            value_column="PDCSAP_FLUX",
            uncertainty_column="PDCSAP_FLUX_ERR",
            time_format="BTJD",
            time_scale="TDB",
            value_kind="flux",
            value_unit="electron_per_second",
            band_value="TESS",
        )
