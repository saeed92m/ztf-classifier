import numpy as np
import pandas as pd
import pytest

from ztf_classifier.io.alerce import alerce_to_internal_lc_robust


def _detections(**overrides: object) -> pd.DataFrame:
    values: dict[str, object] = {
        "mjd": [59001, 59002],
        "fid": [1, 1],
        "magpsf_corr": [20.0, 21.0],
        "sigmapsf_corr_ext": [0.1, 0.2],
        "magpsf": [20.5, 21.5],
        "sigmapsf": [0.15, 0.25],
        "ra": [10.0, 10.0],
        "dec": [20.0, 20.0],
        "dubious": [False, False],
        "corrected": [True, True],
    }
    values.update(overrides)
    return pd.DataFrame(values)


def test_alerce_boolean_strings_are_parsed_safely() -> None:
    result = alerce_to_internal_lc_robust(
        _detections(
            dubious=["False", "True"],
            corrected=["true", "false"],
        )
    )

    assert result["dubious"].tolist() == [False, True]
    assert result["corrected"].tolist() == [True, False]


def test_alerce_rejects_unknown_boolean_values() -> None:
    with pytest.raises(ValueError, match="non-boolean values"):
        alerce_to_internal_lc_robust(
            _detections(dubious=["not-a-bool", "False"])
        )


def test_alerce_rejects_missing_required_columns() -> None:
    detections = _detections().drop(columns=["corrected"])

    with pytest.raises(ValueError, match="missing required columns"):
        alerce_to_internal_lc_robust(detections)


def test_alerce_preserves_nan_boolean_as_false() -> None:
    result = alerce_to_internal_lc_robust(
        _detections(dubious=[np.nan, "0"])
    )

    assert result["dubious"].tolist() == [False, False]
