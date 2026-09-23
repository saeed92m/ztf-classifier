from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.ood import IsolationForestOOD


ROOT = Path(__file__).resolve().parents[1]

FEATURE_PATH = ROOT / "data/processed/features_v0.2.parquet"
OOD_PATH = ROOT / "reports/tables/xgboost_ood_v0.2_scores.parquet"


def _load_inputs():
    features = pd.read_parquet(FEATURE_PATH)
    historical = pd.read_parquet(OOD_PATH)

    feature_columns = [
        column
        for column in features.columns
        if column.startswith(("g_", "r_", "mean_", "median_"))
    ]

    assert len(feature_columns) == 42

    X = features[feature_columns].to_numpy(dtype=np.float64)

    folds = (
        historical
        .sort_values("row_index")["fold"]
        .to_numpy(dtype=np.int64)
    )

    return X, folds, historical.sort_values("row_index").reset_index(drop=True)


def test_ood_frozen_v02_parity():
    X, folds, historical = _load_inputs()

    result = IsolationForestOOD().fit_predict(X, folds)

    np.testing.assert_allclose(
        result.anomaly_score,
        historical["anomaly_score"].to_numpy(),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.normality_score,
        historical["normality_score"].to_numpy(),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.anomaly_percentile,
        historical["anomaly_percentile"].to_numpy(),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_array_equal(
        result.isolation_forest_label,
        historical["isolation_forest_label"].to_numpy(),
    )

    np.testing.assert_array_equal(
        result.anomaly_rank,
        historical["anomaly_rank"].to_numpy(),
    )

    np.testing.assert_array_equal(
        result.is_top_1pct_anomaly,
        historical["is_top_1pct_anomaly"].to_numpy(),
    )

    np.testing.assert_array_equal(
        result.is_top_5pct_anomaly,
        historical["is_top_5pct_anomaly"].to_numpy(),
    )

    np.testing.assert_array_equal(
        result.is_top_10pct_anomaly,
        historical["is_top_10pct_anomaly"].to_numpy(),
    )


def test_ood_result_shape_and_finiteness():
    X, folds, _ = _load_inputs()

    result = IsolationForestOOD().fit_predict(X, folds)

    assert result.sample_count == 150
    assert result.anomaly_score.shape == (150,)
    assert result.normality_score.shape == (150,)
    assert result.anomaly_percentile.shape == (150,)
    assert result.isolation_forest_label.shape == (150,)
    assert np.isfinite(result.anomaly_score).all()
    assert np.isfinite(result.normality_score).all()
    assert np.isfinite(result.anomaly_percentile).all()


def test_ood_anomaly_score_is_negative_normality_score():
    X, folds, _ = _load_inputs()

    result = IsolationForestOOD().fit_predict(X, folds)

    np.testing.assert_allclose(
        result.anomaly_score,
        -result.normality_score,
        rtol=0.0,
        atol=0.0,
    )


def test_ood_is_deterministic():
    X, folds, _ = _load_inputs()

    first = IsolationForestOOD().fit_predict(X, folds)
    second = IsolationForestOOD().fit_predict(X, folds)

    np.testing.assert_array_equal(
        first.anomaly_score,
        second.anomaly_score,
    )

    np.testing.assert_array_equal(
        first.anomaly_percentile,
        second.anomaly_percentile,
    )

    np.testing.assert_array_equal(
        first.isolation_forest_label,
        second.isolation_forest_label,
    )


def test_ood_requires_42_features():
    X, folds, _ = _load_inputs()

    invalid = X[:, :-1]

    try:
        IsolationForestOOD().fit_predict(invalid, folds)
    except ValueError as exc:
        assert "42 features" in str(exc)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_ood_frozen_v02_summary_parity():
    X, folds, historical = _load_inputs()

    result = IsolationForestOOD().fit_predict(X, folds)

    summary = pd.read_parquet(
        ROOT / "reports/tables/xgboost_ood_v0.2_summary.parquet"
    ).iloc[0]

    assert len(X) == int(summary["n_samples"])
    assert X.shape[1] == int(summary["n_features"])
    assert len(np.unique(folds)) == int(summary["n_folds"])

    config = IsolationForestOOD().config

    assert config.n_estimators == int(summary["n_estimators"])
    assert config.contamination == summary["contamination"]
    assert config.random_state == int(summary["random_state"])

    assert int(
        np.sum(result.isolation_forest_label == -1)
    ) == int(summary["iforest_anomaly_count"])

    assert int(
        np.sum(result.is_top_1pct_anomaly)
    ) == int(summary["top_1pct_count"])

    assert int(
        np.sum(result.is_top_5pct_anomaly)
    ) == int(summary["top_5pct_count"])

    assert int(
        np.sum(result.is_top_10pct_anomaly)
    ) == int(summary["top_10pct_count"])

    np.testing.assert_allclose(
        result.anomaly_score.mean(),
        float(summary["mean_anomaly_score"]),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        np.median(result.anomaly_score),
        float(summary["median_anomaly_score"]),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.anomaly_score.max(),
        float(summary["max_anomaly_score"]),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.anomaly_percentile.mean(),
        float(summary["mean_anomaly_percentile"]),
        rtol=0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        np.median(result.anomaly_percentile),
        float(summary["median_anomaly_percentile"]),
        rtol=0.0,
        atol=1e-12,
    )
