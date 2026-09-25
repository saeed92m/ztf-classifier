"""Temporal leakage invariance tests for the scientific feature engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ztf_classifier.features.pipeline import extract_v0_2_features


def _light_curve() -> pd.DataFrame:
    """Build a deterministic two-band light curve with enough observations."""
    times = np.arange(0.0, 60.0, 1.0)
    rows: list[dict[str, float | int]] = []
    for index, mjd in enumerate(times):
        for fid, offset in ((1, 0.0), (2, 0.35)):
            rows.append(
                {
                    "mjd": mjd,
                    "fid": fid,
                    "mag": (
                        19.0
                        + offset
                        + 0.2 * np.sin(mjd / 5.0)
                        + 0.01 * np.cos(index)
                    ),
                    "magerr": 0.05,
                }
            )
    return pd.DataFrame(rows)


@pytest.mark.parametrize("cutoff_mjd", [20.0, 40.0])
def test_v0_2_features_are_invariant_to_observations_after_cutoff(
    cutoff_mjd: float,
) -> None:
    """Future rows must not change features computed at a fixed cutoff."""
    observations = _light_curve()
    historical = observations.loc[
        observations["mjd"] <= cutoff_mjd
    ].copy()

    baseline = extract_v0_2_features(
        historical,
        cutoff_mjd=cutoff_mjd,
    )
    with_future_rows = extract_v0_2_features(
        observations,
        cutoff_mjd=cutoff_mjd,
    )

    assert tuple(baseline) == tuple(with_future_rows)

    for name in baseline:
        left = baseline[name]
        right = with_future_rows[name]
        if np.isfinite(left) and np.isfinite(right):
            assert left == pytest.approx(right, rel=0.0, abs=1e-12)
        else:
            assert np.isnan(left)
            assert np.isnan(right)


def test_v0_2_cutoff_rejects_nonfinite_cutoff() -> None:
    """A temporal cutoff must be a finite scalar."""
    with pytest.raises(ValueError, match="cutoff_mjd must be finite"):
        extract_v0_2_features(
            _light_curve(),
            cutoff_mjd=float("nan"),
        )


def test_v0_2_insufficient_history_remains_nan() -> None:
    """Eligibility rules must remain explicit under short histories."""
    observations = _light_curve()

    features = extract_v0_2_features(
        observations,
        cutoff_mjd=5.0,
    )

    assert np.isnan(features["g_ls_best_frequency"])
    assert np.isnan(features["r_ls_best_frequency"])
    assert np.isnan(features["mean_color_gr"])
