from pathlib import Path

import numpy as np
import pandas as pd

from ztf_classifier.models.calibration import TemperatureScaler

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


def test_temperature_scaler_matches_frozen_v0_2() -> None:
    probabilities, y_true = _load_oof()

    result = TemperatureScaler().fit(
        probabilities,
        y_true,
    )

    assert result.sample_count == 150

    assert abs(
        result.temperature - 1.02685019
    ) < 1e-6

    assert abs(
        result.raw_log_loss - 1.320906597
    ) < 1e-8

    assert abs(
        result.calibrated_log_loss - 1.320350124
    ) < 1e-8


def test_temperature_scaler_probability_simplex() -> None:
    probabilities, y_true = _load_oof()

    result = TemperatureScaler().fit(
        probabilities,
        y_true,
    )

    calibrated = result.calibrated_probabilities

    assert calibrated.shape == (150, 15)
    assert np.isfinite(calibrated).all()
    assert (calibrated >= 0.0).all()

    np.testing.assert_allclose(
        calibrated.sum(axis=1),
        1.0,
        rtol=0.0,
        atol=1e-12,
    )


def test_temperature_scaler_is_deterministic() -> None:
    probabilities, y_true = _load_oof()

    scaler = TemperatureScaler()

    first = scaler.fit(
        probabilities,
        y_true,
    )

    second = scaler.fit(
        probabilities,
        y_true,
    )

    assert first.temperature == second.temperature

    np.testing.assert_array_equal(
        first.calibrated_probabilities,
        second.calibrated_probabilities,
    )


def test_temperature_transform_matches_fit() -> None:
    probabilities, y_true = _load_oof()

    scaler = TemperatureScaler()

    result = scaler.fit(
        probabilities,
        y_true,
    )

    transformed = scaler.transform(
        probabilities,
        result.temperature,
    )

    np.testing.assert_array_equal(
        transformed,
        result.calibrated_probabilities,
    )


def test_temperature_scaler_rejects_invalid_class_count() -> None:
    probabilities = np.ones(
        (10, 14),
        dtype=np.float64,
    )

    y_true = np.zeros(
        10,
        dtype=np.int64,
    )

    try:
        TemperatureScaler().fit(
            probabilities,
            y_true,
        )
    except ValueError as exc:
        assert str(exc) == (
            "Frozen v0.2 calibration requires 15 classes."
        )
    else:
        raise AssertionError(
            "Calibration must reject non-15-class input."
        )


def test_temperature_scaler_rejects_invalid_temperature() -> None:
    probabilities, _ = _load_oof()

    for temperature in (
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
    ):
        try:
            TemperatureScaler().transform(
                probabilities,
                temperature,
            )
        except ValueError as exc:
            assert str(exc) == (
                "Temperature must be finite and positive."
            )
        else:
            raise AssertionError(
                "Invalid temperature must be rejected."
            )
