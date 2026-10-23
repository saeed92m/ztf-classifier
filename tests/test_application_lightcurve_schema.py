import numpy as np
import pandas as pd
import pytest

from ztf_classifier.application.errors import ApplicationInputError
from ztf_classifier.application.lightcurve_schema import (
    CANONICAL_OBSERVATION_COLUMNS,
    LightCurveColumnMap,
    normalize_lightcurve_table,
)


def _mapping(**overrides):
    values = {
        "object_id": "source",
        "time": "btjd",
        "band": "filter",
        "value": "flux_uJy",
        "uncertainty": "fluxerr_uJy",
        "time_format": "BTJD",
        "time_scale": "TDB",
        "value_kind": "flux",
        "value_unit": "uJy",
        "band_map": {"T": "TESS"},
        "quality_flag": "quality",
    }
    values.update(overrides)
    return LightCurveColumnMap(**values)


def test_normalizes_different_survey_column_names_without_unit_or_time_conversion():
    frame = pd.DataFrame(
        {
            "source": ["Gaia DR3 123", "Gaia DR3 123", "TIC 42"],
            "btjd": [2000.1, 2000.2, 2001.0],
            "filter": ["T", "T", "T"],
            "flux_uJy": [12.0, 11.5, 5.0],
            "fluxerr_uJy": [0.5, 0.4, 0.2],
            "quality": [0, 0, 1],
            "extra_metadata": ["kept in source", "also kept", "kept"],
        },
        index=[10, 20, 30],
    )

    result = normalize_lightcurve_table(frame, _mapping())

    assert tuple(result.observations.columns) == CANONICAL_OBSERVATION_COLUMNS
    assert result.schema_version == "lightcurve-observations-v1"
    assert result.observations["object_id"].tolist() == [
        "Gaia DR3 123", "Gaia DR3 123", "TIC 42"
    ]
    assert result.observations["band"].tolist() == ["TESS"] * 3
    assert result.observations["measurement_type"].tolist() == ["flux"] * 3
    assert result.observations["time_format"].tolist() == ["BTJD"] * 3
    assert result.observations["time_scale"].tolist() == ["TDB"] * 3
    assert result.observations["value_unit"].tolist() == ["uJy"] * 3
    assert result.observations["source_row"].tolist() == [0, 1, 2]
    assert result.diagnostics["input_rows"] == result.diagnostics["output_rows"] == 3
    assert result.diagnostics["dropped_rows"] == 0
    assert result.diagnostics["time_conversion_performed"] is False
    assert result.diagnostics["unit_conversion_performed"] is False
    assert "extra_metadata" in frame.columns


def test_normalization_retains_missing_numeric_values_and_reports_them():
    frame = pd.DataFrame(
        {
            "source": ["obj-1", "obj-1"],
            "time": [60000.0, 60001.0],
            "band": ["g", "r"],
            "mag": [18.2, np.nan],
            "magerr": [0.1, 0.2],
        }
    )
    mapping = _mapping(
        time="time",
        band="band",
        value="mag",
        uncertainty="magerr",
        time_format="MJD",
        time_scale="UTC",
        value_kind="magnitude",
        value_unit="mag",
        quality_flag=None,
        band_map=None,
    )

    result = normalize_lightcurve_table(frame, mapping)

    assert len(result.observations) == 2
    assert result.diagnostics["dropped_rows"] == 0
    assert result.diagnostics["nonfinite_numeric_values"]["value"] == 1
    assert result.observations["quality_flag"].isna().all()


@pytest.mark.parametrize(
    ("frame", "mapping", "message"),
    [
        (
            pd.DataFrame({"id": ["x"], "t": [1], "b": ["g"], "v": [1], "e": [0.1]}),
            _mapping(object_id="id", time="t", band="b", value="v", uncertainty="e"),
            "Mapped source columns are missing",
        ),
        (
            pd.DataFrame({"id": [""], "t": [1], "b": ["g"], "v": [1], "e": [0.1]}),
            _mapping(object_id="id", time="t", band="b", value="v", uncertainty="e", quality_flag=None),
            "identifiers contain missing/blank",
        ),
        (
            pd.DataFrame({"id": ["x"], "t": ["bad"], "b": ["g"], "v": [1], "e": [0.1]}),
            _mapping(object_id="id", time="t", band="b", value="v", uncertainty="e", quality_flag=None),
            "non-numeric values",
        ),
    ],
)
def test_rejects_ambiguous_or_malformed_inputs(frame, mapping, message):
    with pytest.raises(ApplicationInputError, match=message):
        normalize_lightcurve_table(frame, mapping)


def test_rejects_duplicated_source_field_mapping_and_empty_input():
    with pytest.raises(ApplicationInputError, match="distinct column"):
        _mapping(uncertainty="value").validate()

    mapping = _mapping()
    with pytest.raises(ApplicationInputError, match="no observation rows"):
        normalize_lightcurve_table(pd.DataFrame(), mapping)


def test_duplicate_observations_are_reported_not_silently_dropped():
    frame = pd.DataFrame(
        {
            "source": ["obj", "obj"],
            "btjd": [2000.0, 2000.0],
            "filter": ["T", "T"],
            "flux_uJy": [10.0, 10.0],
            "fluxerr_uJy": [0.2, 0.2],
            "quality": [0, 0],
        }
    )
    result = normalize_lightcurve_table(frame, _mapping())

    assert len(result.observations) == 2
    assert result.diagnostics["duplicate_observation_rows"] == 2
