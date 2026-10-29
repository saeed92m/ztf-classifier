"""Non-mutating eligibility diagnostics for the frozen v0.2 feature contract.

These diagnostics explain why a feature may be unavailable. They never impute
values, change the 42-feature vector, or decide whether an astronomical object
is scientifically valid.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ztf_classifier.preprocessing.lightcurve import prepare_band_lightcurve

BASIC_MIN_OBSERVATIONS = 10
LS_MIN_OBSERVATIONS = 30
V0_2_SCHEMA_VERSION = "v0.2"


def diagnose_v0_2_feature_eligibility(
    observations: pd.DataFrame,
    features: dict[str, Any] | None = None,
    cutoff_mjd: float | None = None,
) -> dict[str, Any]:
    """Return JSON-safe counts and reasons for unavailable v0.2 features.

    cutoff_mjd mirrors the canonical feature pipeline's historical cutoff.
    Counts and reasons use rows at or before the cutoff, while
    input_rows_before_cutoff and rows_excluded_by_cutoff preserve the amount
    of input data excluded from this analysis. Inputs are never mutated.
    Non-finite values not explained by known eligibility rules are reported
    conservatively rather than imputed.
    """
    if not isinstance(observations, pd.DataFrame):
        raise TypeError("observations must be a pandas DataFrame.")

    required = {"mjd", "fid", "mag", "magerr"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    working = observations
    if cutoff_mjd is not None:
        cutoff_mjd = float(cutoff_mjd)
        if not np.isfinite(cutoff_mjd):
            raise ValueError("cutoff_mjd must be finite.")
        mjd = pd.to_numeric(observations["mjd"], errors="coerce")
        working = observations.loc[mjd <= cutoff_mjd].copy()

    band_data: dict[str, dict[str, int | bool]] = {}
    for band_name, fid in (("g", 1), ("r", 2)):
        before_cutoff = int((observations["fid"] == fid).sum())
        input_count = int((working["fid"] == fid).sum())
        valid = prepare_band_lightcurve(working, fid=fid)
        valid_count = len(valid)
        band_data[band_name] = {
            "fid": fid,
            "input_rows_before_cutoff": before_cutoff,
            "rows_excluded_by_cutoff": before_cutoff - input_count,
            "input_rows": input_count,
            "valid_observations": valid_count,
            "rejected_rows": input_count - valid_count,
            "basic_features_eligible": valid_count >= BASIC_MIN_OBSERVATIONS,
            "periodicity_features_eligible": valid_count >= LS_MIN_OBSERVATIONS,
            "sample_std_eligible": valid_count >= 2,
        }

    g_count = int(band_data["g"]["valid_observations"])
    r_count = int(band_data["r"]["valid_observations"])
    feature_reasons: dict[str, str] = {}

    if features is not None:
        for name, value in features.items():
            try:
                finite = bool(np.isfinite(value))
            except (TypeError, ValueError):
                finite = False
            if finite:
                continue

            reason = "non_finite_despite_eligibility_or_backend_issue"
            if name in {"mean_color_gr", "median_color_gr"}:
                if g_count == 0 or r_count == 0:
                    reason = "missing_valid_observations_in_one_or_both_bands"
                else:
                    reason = "non_finite_despite_valid_observations"
            elif (
                name == "g_variability_ratio" and g_count < 2
            ) or (
                name == "r_variability_ratio" and r_count < 2
            ):
                reason = "insufficient_observations_for_sample_std"
            elif (
                name.startswith("g_ls_") and g_count < LS_MIN_OBSERVATIONS
            ) or (
                name.startswith("r_ls_") and r_count < LS_MIN_OBSERVATIONS
            ):
                reason = "insufficient_observations_for_periodicity_features"
            elif (
                name.startswith("g_") and g_count < BASIC_MIN_OBSERVATIONS
            ) or (
                name.startswith("r_") and r_count < BASIC_MIN_OBSERVATIONS
            ):
                reason = "insufficient_observations_for_basic_features"
            feature_reasons[name] = reason

    return {
        "diagnostic_schema_version": "1.0",
        "feature_schema_version": V0_2_SCHEMA_VERSION,
        "policy": "report_missingness_without_imputation",
        "cutoff_mjd": cutoff_mjd,
        "thresholds": {
            "basic_features_min_observations_per_band": BASIC_MIN_OBSERVATIONS,
            "periodicity_features_min_observations_per_band": LS_MIN_OBSERVATIONS,
            "sample_standard_deviation_min_observations": 2,
        },
        "bands": band_data,
        "cross_band": {
            "color_features_eligible": g_count >= 1 and r_count >= 1,
            "variability_ratio_g_eligible": g_count >= 2,
            "variability_ratio_r_eligible": r_count >= 2,
        },
        "non_finite_feature_reasons": feature_reasons,
    }


__all__ = ["diagnose_v0_2_feature_eligibility"]
