from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.conformal import (
    EmpiricalConformalPredictor,
)

OOF_PATH = Path(
    "reports/tables/xgboost_baseline_v0.2_oof_predictions.parquet"
)

CLASS_NAMES = (
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
)


def _load_oof() -> tuple[np.ndarray, np.ndarray]:
    oof = pd.read_parquet(OOF_PATH)

    probabilities = oof[
        [
            f"proba_{name}"
            for name in CLASS_NAMES
        ]
    ].to_numpy(dtype=np.float64)

    y_true = oof[
        "true_class_index"
    ].to_numpy(dtype=np.int64)

    return probabilities, y_true


def test_conformal_matches_frozen_v0_2() -> None:
    probabilities, y_true = _load_oof()

    results = EmpiricalConformalPredictor().fit_all(
        probabilities,
        y_true,
    )

    expected = {
        0.05: (
            0.978004645,
            0.953333333,
            4.84,
            0.073333333,
        ),
        0.10: (
            0.963176780,
            0.906666667,
            3.44,
            0.140000000,
        ),
        0.20: (
            0.918114396,
            0.806666667,
            2.14,
            0.313333333,
        ),
    }

    for result in results:
        threshold, coverage, set_size, singleton = (
            expected[result.alpha]
        )

        assert result.sample_count == 150

        assert abs(
            result.threshold - threshold
        ) < 1e-8

        assert abs(
            result.summary.coverage - coverage
        ) < 1e-8

        assert abs(
            result.summary.mean_set_size - set_size
        ) < 1e-12

        assert abs(
            result.summary.singleton_rate - singleton
        ) < 1e-8


def test_conformal_prediction_sets_are_valid() -> None:
    probabilities, y_true = _load_oof()

    results = EmpiricalConformalPredictor().fit_all(
        probabilities,
        y_true,
    )

    for result in results:
        assert result.prediction_sets.shape == (
            150,
            15,
        )

        assert result.covered.shape == (150,)
        assert result.set_sizes.shape == (150,)

        assert result.prediction_sets.dtype == bool
        assert result.covered.dtype == bool

        np.testing.assert_array_equal(
            result.covered,
            result.prediction_sets[
                np.arange(150),
                y_true,
            ],
        )

        np.testing.assert_array_equal(
            result.set_sizes,
            result.prediction_sets.sum(
                axis=1
            ),
        )

        assert (result.set_sizes >= 0).all()
        assert (result.set_sizes <= 15).all()


def test_conformal_prediction_labels_preserve_class_order() -> None:
    probabilities, y_true = _load_oof()

    result = EmpiricalConformalPredictor().fit(
        probabilities,
        y_true,
        0.05,
    )

    labels = (
        EmpiricalConformalPredictor.prediction_set_labels(
            result.prediction_sets
        )
    )

    assert len(labels) == 150

    for label_string in labels:
        labels = label_string.split("|")

        assert len(labels) >= 1
        assert len(labels) == len(set(labels))


def test_conformal_is_deterministic() -> None:
    probabilities, y_true = _load_oof()

    predictor = EmpiricalConformalPredictor()

    first = predictor.fit_all(
        probabilities,
        y_true,
    )

    second = predictor.fit_all(
        probabilities,
        y_true,
    )

    assert len(first) == len(second) == 3

    for left, right in zip(first, second):
        assert left.threshold == right.threshold

        np.testing.assert_array_equal(
            left.prediction_sets,
            right.prediction_sets,
        )

        np.testing.assert_array_equal(
            left.covered,
            right.covered,
        )


def test_conformal_rejects_invalid_alpha() -> None:
    probabilities, y_true = _load_oof()

    predictor = EmpiricalConformalPredictor()

    for alpha in (
        0.0,
        1.0,
        -0.1,
        1.1,
        float("nan"),
        float("inf"),
    ):
        try:
            predictor.fit(
                probabilities,
                y_true,
                alpha,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Invalid alpha must be rejected."
            )


def test_conformal_rejects_invalid_probability_shape() -> None:
    probabilities = np.ones(
        (10, 14),
        dtype=np.float64,
    )

    y_true = np.zeros(
        10,
        dtype=np.int64,
    )

    try:
        EmpiricalConformalPredictor().fit(
            probabilities,
            y_true,
            0.05,
        )
    except ValueError as exc:
        assert str(exc) == (
            "Frozen v0.2 conformal prediction "
            "requires 15 classes."
        )
    else:
        raise AssertionError(
            "Invalid class count must be rejected."
        )
