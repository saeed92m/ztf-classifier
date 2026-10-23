"""Regression tests for the explicit local light-curve file loader."""
import pandas as pd
import pytest

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.lightcurve_file import load_lightcurve_file
from ztf_classifier.application.lightcurve_schema import LightCurveColumnMap


def _mapping() -> LightCurveColumnMap:
    return LightCurveColumnMap(
        object_id="target_id",
        time="time_mjd",
        band="filter_name",
        value="flux",
        uncertainty="flux_err",
        time_format="MJD",
        time_scale="UTC",
        value_kind="flux",
        value_unit="electron/s",
    )


def test_csv_loader_preserves_leading_zero_ids_missing_values_and_order(tmp_path) -> None:
    source = tmp_path / "lightcurve.csv"
    source.write_text(
        "target_id,time_mjd,filter_name,flux,flux_err\n"
        "00123,60000.1,g,12.5,0.3\n"
        "00123,60000.2,r,,0.4\n"
        "00456,60000.3,g,8.1,\n",
        encoding="utf-8",
    )

    result = load_lightcurve_file(source, _mapping())

    assert result.observations["object_id"].tolist() == ["00123", "00123", "00456"]
    assert result.observations["source_row"].tolist() == [0, 1, 2]
    assert pd.isna(result.observations.loc[1, "value"])
    assert pd.isna(result.observations.loc[2, "uncertainty"])
    assert result.diagnostics["input_rows"] == 3
    assert result.diagnostics["output_rows"] == 3
    assert result.diagnostics["dropped_rows"] == 0
    assert result.diagnostics["source_format"] == "csv"


def test_loader_rejects_unsupported_extension(tmp_path) -> None:
    source = tmp_path / "lightcurve.fits"
    source.write_text("not parsed implicitly", encoding="utf-8")

    with pytest.raises(ApplicationInputError, match="Unsupported light-curve file extension"):
        load_lightcurve_file(source, _mapping())


def test_loader_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(ApplicationInputError, match="does not exist"):
        load_lightcurve_file(tmp_path / "missing.csv", _mapping())


def test_parquet_loader_preserves_source_schema_and_row_order(tmp_path) -> None:
    pytest.importorskip("pyarrow")
    source = tmp_path / "lightcurve.parquet"
    pd.DataFrame(
        {
            "target_id": ["obj-b", "obj-a"],
            "time_mjd": [60002.0, 60001.0],
            "filter_name": ["r", "g"],
            "flux": [4.0, 5.0],
            "flux_err": [0.2, 0.3],
        }
    ).to_parquet(source, index=False)

    result = load_lightcurve_file(source, _mapping())

    assert result.observations["object_id"].tolist() == ["obj-b", "obj-a"]
    assert result.observations["source_row"].tolist() == [0, 1]
    assert result.diagnostics["source_format"] == "parquet"
