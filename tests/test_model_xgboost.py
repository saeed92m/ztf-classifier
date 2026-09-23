from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.classes import MODEL_CLASSES
from ztf_classifier.models.xgboost import XGBoostTrainingEngine

DATASET = Path("data/processed/features_v0.2.parquet")
SCHEMA = Path("reports/tables/final_feature_set_v0.2.parquet")
FOLDS = Path(
    "reports/tables/stratified_cv_fold_assignments_v0.1.parquet"
)
FROZEN_OOF = Path(
    "reports/tables/xgboost_baseline_v0.2_oof_predictions.parquet"
)


def _load_engine() -> XGBoostTrainingEngine:
    return XGBoostTrainingEngine(
        feature_schema_path=SCHEMA,
    )


def _load_dataset() -> pd.DataFrame:
    return pd.read_parquet(DATASET)


def _load_historical_folds() -> np.ndarray:
    frame = pd.read_parquet(FOLDS)
    return (
        frame.sort_values("row_index")["fold"]
        .to_numpy(dtype=int)
    )


def test_prepare_features_matches_frozen_schema() -> None:
    dataset = _load_dataset()
    engine = _load_engine()

    features = engine.prepare_features(dataset)

    assert features.shape == (150, 42)
    assert features.index.equals(dataset.index)
    assert int(np.isinf(features.to_numpy()).sum()) == 0
    assert int(features.isna().sum().sum()) == 1612


def test_prepare_target_uses_frozen_class_mapping() -> None:
    dataset = _load_dataset()
    engine = _load_engine()

    target, classes = engine.prepare_target(dataset)

    assert tuple(classes) == MODEL_CLASSES
    assert target.shape == (150,)
    assert set(target) == set(range(15))


def test_oof_training_preserves_historical_folds() -> None:
    dataset = _load_dataset()
    folds = _load_historical_folds()
    engine = _load_engine()

    result = engine.train_oof(
        dataset,
        fold_assignments=folds,
    )

    assert result.predictions.shape == (150, 21)
    assert result.fold_metrics.shape == (5, 8)
    assert np.array_equal(
        result.predictions["fold"].to_numpy(),
        folds,
    )


def test_oof_predictions_match_frozen_structure_and_values() -> None:
    dataset = _load_dataset()
    folds = _load_historical_folds()
    frozen = pd.read_parquet(FROZEN_OOF)

    engine = _load_engine()
    result = engine.train_oof(
        dataset,
        fold_assignments=folds,
    ).predictions

    assert list(result.columns) == list(frozen.columns)
    assert result.shape == frozen.shape

    exact_columns = [
        "row_index",
        "true_label",
        "true_class_index",
        "predicted_label",
        "predicted_class_index",
        "fold",
    ]

    for column in exact_columns:
        assert result[column].equals(frozen[column])

    probability_columns = [
        column
        for column in frozen.columns
        if column.startswith("proba_")
    ]

    production = result[probability_columns].to_numpy(
        dtype=float
    )
    reference = frozen[probability_columns].to_numpy(
        dtype=float
    )

    assert np.allclose(
        production,
        reference,
        rtol=0.0,
        atol=1e-6,
    )

    assert np.array_equal(
        result["predicted_class_index"].to_numpy(),
        np.argmax(production, axis=1),
    )


def test_probability_matrix_is_valid() -> None:
    dataset = _load_dataset()
    folds = _load_historical_folds()
    engine = _load_engine()

    result = engine.train_oof(
        dataset,
        fold_assignments=folds,
    )

    probabilities = result.probabilities

    assert probabilities.shape == (150, 15)
    assert np.isfinite(probabilities).all()
    assert (probabilities >= 0.0).all()
    assert np.allclose(
        probabilities.sum(axis=1),
        1.0,
        rtol=0.0,
        atol=1e-6,
    )
