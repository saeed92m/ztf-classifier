"""Source-native descriptive summaries for ZTF DR24 light curves.

These statistics support inspection only. They do not normalize photometry,
convert HMJD, apply a catflags mask, generate model features, or classify sources.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from itertools import pairwise
from statistics import median
from typing import Any


SUMMARY_SCHEMA_VERSION = "ztf-dr24-descriptive-summary-v1"
SUMMARY_POLICY_STATUS = "DESCRIPTIVE_NOT_CLASSIFICATION"


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def summarize_dr24_epochs(epochs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return descriptive statistics without filtering or mutating source epochs.

    Magnitude statistics use every row with finite HMJD and magnitude, regardless
    of catflags or magerr. Uncertainty statistics are reported separately for
    finite, non-negative magerr values. HMJD remains in its source-native scale.
    """
    pairs = [
        (float(epoch["hmjd"]), float(epoch["mag"]))
        for epoch in epochs
        if _finite_number(epoch.get("hmjd")) and _finite_number(epoch.get("mag"))
    ]
    times = [item[0] for item in pairs]
    magnitudes = [item[1] for item in pairs]
    errors = [
        float(epoch["magerr"])
        for epoch in epochs
        if _finite_number(epoch.get("magerr")) and float(epoch["magerr"]) >= 0
    ]
    unique_times = sorted(set(times))
    intervals = [
        right - left
        for left, right in pairwise(unique_times)
    ]
    mag_p05 = _percentile(magnitudes, 0.05)
    mag_p95 = _percentile(magnitudes, 0.95)

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "policy_status": SUMMARY_POLICY_STATUS,
        "percentile_method": "linear_interpolation_type_7",
        "sampling_interval_definition": (
            "Median difference between sorted unique finite HMJD values."
        ),
        "raw_epoch_count": len(epochs),
        "finite_hmjd_mag_pair_count": len(pairs),
        "invalid_hmjd_mag_pair_count": len(epochs) - len(pairs),
        "finite_nonnegative_magerr_count": len(errors),
        "invalid_or_negative_magerr_count": len(epochs) - len(errors),
        "hmjd_min": min(times) if times else None,
        "hmjd_max": max(times) if times else None,
        "hmjd_span_days": max(times) - min(times) if times else None,
        "unique_hmjd_count": len(unique_times),
        "duplicate_hmjd_count": len(times) - len(unique_times),
        "median_sampling_interval_days": median(intervals) if intervals else None,
        "mag_min": min(magnitudes) if magnitudes else None,
        "mag_median": median(magnitudes) if magnitudes else None,
        "mag_max": max(magnitudes) if magnitudes else None,
        "mag_p05": mag_p05,
        "mag_p95": mag_p95,
        "mag_p95_minus_p05": (
            mag_p95 - mag_p05 if mag_p05 is not None and mag_p95 is not None else None
        ),
        "magerr_median": median(errors) if errors else None,
        "catflags_used_for_selection": False,
        "epoch_filtering_applied": False,
        "time_conversion_applied": False,
        "photometry_conversion_applied": False,
        "interpretation": (
            "Descriptive statistics only. Magnitude summaries include all finite "
            "HMJD/magnitude pairs, regardless of catflags or magerr. HMJD and "
            "native DR24 photometry are unchanged. No feature generation or "
            "classification was performed."
        ),
    }


def summarize_dr24_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize each OID independently; never group different OIDs."""
    summaries = []
    for record in records:
        summaries.append(
            {
                "objectid": record["objectid"],
                "filterid": record["filterid"],
                "summary": summarize_dr24_epochs(record.get("epochs", ())),
            }
        )
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "policy_status": SUMMARY_POLICY_STATUS,
        "summaries": summaries,
        "grouping_applied": False,
    }


__all__ = [
    "SUMMARY_POLICY_STATUS",
    "SUMMARY_SCHEMA_VERSION",
    "summarize_dr24_epochs",
    "summarize_dr24_records",
]
