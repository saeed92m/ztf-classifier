from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.evaluation.historical import (
    HistoricalBacktestConfig,
    HistoricalBacktestEvaluator,
)


class DummyBackend:
    pass


def make_evaluator() -> HistoricalBacktestEvaluator:
    return HistoricalBacktestEvaluator(
        acquisition_backend=DummyBackend(),
    )


def test_historical_config_rejects_invalid_cutoff() -> None:
    with pytest.raises(ValueError, match="finite"):
        HistoricalBacktestConfig(
            historical_cutoff_mjd=float("nan"),
        )


def test_historical_cohort_uses_firstmjd_cutoff_and_sorts_oid() -> None:
    evaluator = make_evaluator()

    objects = pd.DataFrame(
        {
            "oid": ["ZTF_B", "ZTF_A", "ZTF_C", "ZTF_D"],
            "firstmjd": [59400.0, 59447.224132, 59447.224133, 59300.0],
            "class": ["QSO", "AGN", "SNII", "YSO"],
            "survey": ["ZTF"] * 4,
        }
    )

    result = evaluator._select_historical_cohort(objects)

    assert result["oid"].tolist() == ["ZTF_A", "ZTF_B", "ZTF_D"]
    assert result["firstmjd"].tolist() == [59447.224132, 59400.0, 59300.0]


def test_frozen_label_map_preserves_oid_to_class_alignment() -> None:
    evaluator = make_evaluator()

    frozen = pd.DataFrame(
        {
            "oid": ["ZTF_B", "ZTF_A", "ZTF_C"],
            "class": ["QSO", "AGN", "SNII"],
        }
    )

    result = evaluator._build_frozen_label_map(frozen)

    assert result == {
        "ZTF_A": "AGN",
        "ZTF_B": "QSO",
        "ZTF_C": "SNII",
    }


def test_oid_fold_map_preserves_row_index_and_class_alignment() -> None:
    evaluator = make_evaluator()

    frozen = pd.DataFrame(
        {
            "oid": ["ZTF_B", "ZTF_A", "ZTF_C"],
            "class": ["QSO", "AGN", "SNII"],
        }
    )

    folds = pd.DataFrame(
        {
            "row_index": [0, 1, 2],
            "fold": [2, 1, 3],
            "class": ["QSO", "AGN", "SNII"],
        }
    )

    result = evaluator._build_oid_fold_map(frozen, folds)

    assert result == {
        "ZTF_A": 1,
        "ZTF_B": 2,
        "ZTF_C": 3,
    }


def test_oid_fold_map_rejects_class_mismatch() -> None:
    evaluator = make_evaluator()

    frozen = pd.DataFrame(
        {
            "oid": ["ZTF_A", "ZTF_B"],
            "class": ["AGN", "QSO"],
        }
    )

    folds = pd.DataFrame(
        {
            "row_index": [0, 1],
            "fold": [1, 2],
            "class": ["QSO", "QSO"],
        }
    )

    with pytest.raises(ValueError, match="class mismatches"):
        evaluator._build_oid_fold_map(frozen, folds)


class RecordingModel:
    def __init__(self, calls: list[dict]) -> None:
        self.calls = calls

    def fit(self, X, y):
        self.calls.append(
            {
                "train_index": list(X.index),
                "train_target": list(y),
            }
        )
        return self

    def predict_proba(self, X):
        self.calls[-1]["test_index"] = list(X.index)

        probabilities = np.zeros((len(X), 15), dtype=float)
        probabilities[:, 0] = 1.0

        return probabilities


class FakeEngine:
    def __init__(self) -> None:
        self.model_calls: list[dict] = []
        self.class_names = [
            "AGN",
            "Blazar",
            "CEP",
            "CV/Nova",
            "DSCT",
            "E",
            "LPV",
            "Periodic-Other",
            "QSO",
            "RRL",
            "SLSN",
            "SNII",
            "SNIa",
            "SNIbc",
            "YSO",
        ]

    def prepare_features(self, dataset):
        return dataset[["feature"]]

    def prepare_target(self, dataset):
        mapping = {
            "AGN": 0,
            "Blazar": 1,
        }
        return (
            dataset["class"].map(mapping).to_numpy(dtype=int),
            self.class_names,
        )

    def _build_model(self):
        return RecordingModel(self.model_calls)

    def _validate_probability_matrix(self, probabilities, expected_rows):
        assert probabilities.shape == (expected_rows, 15)


def test_evaluate_folds_keeps_train_and_test_disjoint_and_skips_test_only_class() -> None:
    evaluator = make_evaluator()
    engine = FakeEngine()
    evaluator._engine = engine

    dataset = pd.DataFrame(
        {
            "oid": ["A", "B", "C"],
            "class": ["AGN", "AGN", "Blazar"],
            "feature": [1.0, 2.0, 3.0],
        }
    )

    fold_map = {
        "A": 1,
        "B": 2,
        "C": 3,
    }

    predictions, metrics = evaluator._evaluate_folds(
        dataset,
        fold_map,
    )

    # Folds 1 and 2 are evaluated.
    assert len(engine.model_calls) == 2

    for call in engine.model_calls:
        assert set(call["train_index"]).isdisjoint(
            call["test_index"]
        )

    assert engine.model_calls[0]["train_index"] == [1, 2]
    assert engine.model_calls[0]["test_index"] == [0]

    assert engine.model_calls[1]["train_index"] == [0, 2]
    assert engine.model_calls[1]["test_index"] == [1]

    # Fold 3 has Blazar only in test, so it must be skipped.
    fold3 = metrics.loc[metrics["fold"] == 3].iloc[0]
    assert fold3["status"] == "skipped"
    assert fold3["test_only_classes"] == "Blazar"
    assert fold3["n_train"] == 2
    assert fold3["n_test"] == 1

    # Folds 4 and 5 have no test rows and are skipped.
    assert metrics["status"].tolist() == [
        "evaluated",
        "evaluated",
        "skipped",
        "skipped",
        "skipped",
    ]

    assert len(predictions) == 2
    assert predictions["oid"].tolist() == ["A", "B"]


def test_evaluate_folds_preserves_prediction_oid_fold_and_label_alignment() -> None:
    evaluator = make_evaluator()
    engine = FakeEngine()
    evaluator._engine = engine

    dataset = pd.DataFrame(
        {
            "oid": ["ZTF_B", "ZTF_A", "ZTF_C", "ZTF_D"],
            "class": ["AGN", "AGN", "Blazar", "Blazar"],
            "feature": [2.0, 1.0, 3.0, 4.0],
        }
    )

    fold_map = {
        "ZTF_A": 1,
        "ZTF_B": 2,
        "ZTF_C": 1,
        "ZTF_D": 2,
    }

    predictions, metrics = evaluator._evaluate_folds(
        dataset,
        fold_map,
    )

    assert len(predictions) == 4
    assert predictions["oid"].is_unique
    assert predictions["fold"].tolist() == [1, 1, 2, 2]
    assert predictions["oid"].tolist() == [
        "ZTF_A",
        "ZTF_C",
        "ZTF_B",
        "ZTF_D",
    ]

    expected_labels = {
        "ZTF_A": "AGN",
        "ZTF_B": "AGN",
        "ZTF_C": "Blazar",
        "ZTF_D": "Blazar",
    }

    for _, row in predictions.iterrows():
        oid = row["oid"]

        assert row["fold"] == fold_map[oid]
        assert row["true_class"] == expected_labels[oid]

        probabilities = [
            row[f"prob_{class_name}"]
            for class_name in engine.class_names
        ]

        assert all(np.isfinite(probabilities))
        assert np.isclose(sum(probabilities), 1.0)

    assert metrics.loc[metrics["status"] == "evaluated", "fold"].tolist() == [
        1,
        2,
    ]
