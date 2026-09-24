"""Phase-folded morphology features."""

import numpy as np


def phase_fold(lc, period):
    df = lc.copy()
    t = df["mjd"].to_numpy(dtype=float)
    df["phase"] = ((t - t.min()) / period) % 1.0
    return df.sort_values("phase").reset_index(drop=True)


def phase_morphology_features(lc, period, band):
    df = phase_fold(lc, period)
    phase = df["phase"].to_numpy(dtype=float)
    mag = df["mag"].to_numpy(dtype=float)

    valid = np.isfinite(phase) & np.isfinite(mag)
    phase = phase[valid]
    mag = mag[valid]

    if len(mag) < 10:
        raise ValueError(
            f"Not enough points for morphology: {band}"
        )

    amplitude = np.max(mag) - np.min(mag)
    p05, p25, _p50, p75, p95 = np.percentile(
        mag,
        [5, 25, 50, 75, 95],
    )
    std = np.std(mag, ddof=1)

    skewness = (
        np.mean(((mag - np.mean(mag)) / std) ** 3)
        if std > 0
        else np.nan
    )

    return {
        f"{band}_phase_amplitude": amplitude,
        f"{band}_phase_robust_amplitude": p95 - p05,
        f"{band}_phase_iqr": p75 - p25,
        f"{band}_phase_skewness": skewness,
        f"{band}_phase_min_mag_phase": phase[np.argmin(mag)],
        f"{band}_phase_max_mag_phase": phase[np.argmax(mag)],
        f"{band}_phase_bright_fraction": np.mean(
            mag <= np.median(mag)
        ),
    }
