import numpy as np
import pandas as pd
import pytest

from ztf_classifier.features.periodicity import lomb_scargle_features


def test_lomb_scargle_features():
    rng = np.random.default_rng(42)

    t = np.linspace(0.0, 100.0, 100)
    period = 5.0
    mag = 20.0 + 0.5 * np.sin(2.0 * np.pi * t / period)
    mag += rng.normal(0.0, 0.01, len(t))

    lc = pd.DataFrame(
        {
            "mjd": t,
            "mag": mag,
            "magerr": np.full(len(t), 0.02),
        }
    )

    result = lomb_scargle_features(lc, "g")

    expected_keys = {
        "g_ls_best_period_days",
        "g_ls_best_frequency",
        "g_ls_best_power",
        "g_ls_fap",
        "g_ls_min_period_days",
        "g_ls_max_period_days",
    }

    assert set(result) == expected_keys
    assert np.isfinite(result["g_ls_best_period_days"])
    assert np.isfinite(result["g_ls_best_frequency"])
    assert np.isfinite(result["g_ls_best_power"])
    assert np.isfinite(result["g_ls_fap"])
    assert result["g_ls_min_period_days"] == 0.05
    assert result["g_ls_max_period_days"] == 50.0

    assert 0.05 <= result["g_ls_best_period_days"] <= 50.0


def test_lomb_scargle_filters_invalid_observations():
    t = np.linspace(0.0, 20.0, 20)

    lc = pd.DataFrame(
        {
            "mjd": np.r_[t, np.nan],
            "mag": np.r_[20.0 + np.sin(t), np.nan],
            "magerr": np.r_[np.full(20, 0.1), 0.1],
        }
    )

    result = lomb_scargle_features(lc, "r")

    assert set(result) == {
        "r_ls_best_period_days",
        "r_ls_best_frequency",
        "r_ls_best_power",
        "r_ls_fap",
        "r_ls_min_period_days",
        "r_ls_max_period_days",
    }


def test_lomb_scargle_rejects_too_few_observations():
    lc = pd.DataFrame(
        {
            "mjd": np.arange(9, dtype=float),
            "mag": np.ones(9) * 20.0,
            "magerr": np.ones(9) * 0.1,
        }
    )

    with pytest.raises(
        ValueError,
        match="Not enough observations for Lomb–Scargle",
    ):
        lomb_scargle_features(lc, "g")


def test_lomb_scargle_rejects_invalid_period_range():
    lc = pd.DataFrame(
        {
            "mjd": np.arange(10, dtype=float) * 0.001,
            "mag": np.ones(10) * 20.0,
            "magerr": np.ones(10) * 0.1,
        }
    )

    with pytest.raises(
        ValueError,
        match="Invalid period range",
    ):
        lomb_scargle_features(lc, "g")
