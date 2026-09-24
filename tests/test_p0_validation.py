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


def _feature_schema() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_order": list(range(1, 43)),
            "feature": [f"feature_{index}" for index in range(1, 43)],
        }
    )


def _inference_engine(tmp_path):
    from ztf_classifier.models.inference import XGBoostInferenceEngine

    schema_path = tmp_path / "feature_schema.parquet"
    _feature_schema().to_parquet(schema_path, index=False)
    return XGBoostInferenceEngine(
        model=object(),
        feature_schema_path=schema_path,
    )


def test_inference_rejects_rows_with_all_features_missing(tmp_path) -> None:
    engine = _inference_engine(tmp_path)
    dataset = pd.DataFrame(
        {
            f"feature_{index}": [np.nan]
            for index in range(1, 43)
        }
    )

    with pytest.raises(
        ValueError,
        match="all model features missing",
    ):
        engine.prepare_features(dataset)


def test_inference_rejects_duplicate_feature_order(tmp_path) -> None:
    schema = _feature_schema()
    schema.loc[1, "feature_order"] = schema.loc[0, "feature_order"]

    schema_path = tmp_path / "duplicate_order.parquet"
    schema.to_parquet(schema_path, index=False)

    from ztf_classifier.models.inference import XGBoostInferenceEngine

    engine = XGBoostInferenceEngine(
        model=object(),
        feature_schema_path=schema_path,
    )

    dataset = pd.DataFrame(
        {
            f"feature_{index}": [float(index)]
            for index in range(1, 43)
        }
    )

    with pytest.raises(
        ValueError,
        match="duplicate feature_order",
    ):
        engine.prepare_features(dataset)


def test_inference_rejects_non_contract_feature_order(tmp_path) -> None:
    schema = _feature_schema()
    schema.loc[0, "feature_order"] = 0

    schema_path = tmp_path / "invalid_order.parquet"
    schema.to_parquet(schema_path, index=False)

    from ztf_classifier.models.inference import XGBoostInferenceEngine

    engine = XGBoostInferenceEngine(
        model=object(),
        feature_schema_path=schema_path,
    )

    dataset = pd.DataFrame(
        {
            f"feature_{index}": [float(index)]
            for index in range(1, 43)
        }
    )

    with pytest.raises(
        ValueError,
        match="1 through 42",
    ):
        engine.prepare_features(dataset)
