from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.config import ModelConfig
from ztf_classifier.models.inference import XGBoostInferenceEngine

DATASET = Path("data/processed/features_v0.2.parquet")
SCHEMA = Path("reports/tables/final_feature_set_v0.2.parquet")


def _load_dataset() -> pd.DataFrame:
    return pd.read_parquet(DATASET)


def _feature_names() -> list[str]:
    schema = pd.read_parquet(SCHEMA)
    return (
        schema.sort_values("feature_order")["feature"]
        .astype(str)
        .tolist()
    )


def _build_model(dataset: pd.DataFrame) -> XGBClassifier:
    config = ModelConfig().xgboost
    feature_names = _feature_names()

    X = dataset.loc[:, feature_names].copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan)

    labels = (
        dataset["class"]
        .map(
            {
                name: index
                for index, name in enumerate(MODEL_CLASSES)
            }
        )
        .to_numpy(dtype=int)
    )

    model = XGBClassifier(
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        learning_rate=config.learning_rate,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        min_child_weight=config.min_child_weight,
        reg_alpha=config.reg_alpha,
        reg_lambda=config.reg_lambda,
        objective=config.objective,
        num_class=config.num_class,
        eval_metric=config.eval_metric,
        tree_method=config.tree_method,
        random_state=config.random_state,
        n_jobs=config.n_jobs,
    )

    model.fit(X, labels)

    return model


def test_inference_returns_frozen_class_contract() -> None:
    dataset = _load_dataset()
    model = _build_model(dataset)

    engine = XGBoostInferenceEngine(
        model=model,
        feature_schema_path=SCHEMA,
    )

    result = engine.predict(dataset)

    assert result.probabilities.shape == (150, 15)
    assert result.predicted_class_indices.shape == (150,)
    assert len(result.predicted_labels) == 150

    assert set(result.predicted_class_indices).issubset(
        set(range(15))
    )

    assert all(
        label in MODEL_CLASSES
        for label in result.predicted_labels
    )


def test_inference_probability_matrix_is_valid() -> None:
    dataset = _load_dataset()
    model = _build_model(dataset)

    engine = XGBoostInferenceEngine(
        model=model,
        feature_schema_path=SCHEMA,
    )

    result = engine.predict(dataset)

    probabilities = result.probabilities

    assert np.isfinite(probabilities).all()
    assert (probabilities >= 0.0).all()

    assert np.allclose(
        probabilities.sum(axis=1),
        1.0,
        rtol=0.0,
        atol=1e-6,
    )


def test_inference_is_deterministic() -> None:
    dataset = _load_dataset()
    model = _build_model(dataset)

    engine = XGBoostInferenceEngine(
        model=model,
        feature_schema_path=SCHEMA,
    )

    first = engine.predict(dataset)
    second = engine.predict(dataset)

    np.testing.assert_array_equal(
        first.predicted_class_indices,
        second.predicted_class_indices,
    )

    np.testing.assert_array_equal(
        first.predicted_labels,
        second.predicted_labels,
    )

    np.testing.assert_array_equal(
        first.probabilities,
        second.probabilities,
    )


def test_inference_uses_exact_feature_schema() -> None:
    dataset = _load_dataset()
    model = _build_model(dataset)

    engine = XGBoostInferenceEngine(
        model=model,
        feature_schema_path=SCHEMA,
    )

    features = engine.prepare_features(dataset)

    assert features.shape == (150, 42)
    assert list(features.columns) == _feature_names()


def test_inference_rejects_missing_model() -> None:
    try:
        XGBoostInferenceEngine(
            model=None,
            feature_schema_path=SCHEMA,
        )
    except ValueError as exc:
        assert str(exc) == (
            "XGBoostInferenceEngine requires a fitted model."
        )
    else:
        raise AssertionError(
            "Inference engine must reject a missing model."
        )
