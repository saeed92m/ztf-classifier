from __future__ import annotations

from copy import deepcopy

import pytest

from ztf_classifier.validation.dr24_descriptive import (
    SUMMARY_POLICY_STATUS,
    SUMMARY_SCHEMA_VERSION,
    summarize_dr24_epochs,
    summarize_dr24_records,
)


def test_summary_reports_source_native_descriptive_statistics_without_filtering() -> None:
    epochs = [
        {"hmjd": 60000.0, "mag": 18.0, "magerr": 0.1, "catflags": 0},
        {"hmjd": 60001.0, "mag": 19.0, "magerr": 0.2, "catflags": 32768},
        {"hmjd": 60002.0, "mag": 20.0, "magerr": -1.0, "catflags": 0},
        {"hmjd": None, "mag": 99.0, "magerr": 0.3, "catflags": 0},
    ]
    original = deepcopy(epochs)

    result = summarize_dr24_epochs(epochs)

    assert epochs == original
    assert result["schema_version"] == SUMMARY_SCHEMA_VERSION
    assert result["policy_status"] == SUMMARY_POLICY_STATUS
    assert result["raw_epoch_count"] == 4
    assert result["finite_hmjd_mag_pair_count"] == 3
    assert result["invalid_hmjd_mag_pair_count"] == 1
    assert result["finite_nonnegative_magerr_count"] == 3
    assert result["invalid_or_negative_magerr_count"] == 1
    assert result["hmjd_min"] == 60000.0
    assert result["hmjd_max"] == 60002.0
    assert result["hmjd_span_days"] == 2.0
    assert result["median_sampling_interval_days"] == 1.0
    assert result["mag_median"] == 19.0
    assert result["mag_p95"] == pytest.approx(19.9)
    assert result["mag_p95_minus_p05"] == pytest.approx(1.8)
    assert result["catflags_used_for_selection"] is False
    assert result["epoch_filtering_applied"] is False
    assert result["time_conversion_applied"] is False
    assert result["photometry_conversion_applied"] is False


def test_summary_handles_empty_and_invalid_epochs() -> None:
    result = summarize_dr24_epochs(
        [{"hmjd": None, "mag": float("nan"), "magerr": None, "catflags": None}]
    )

    assert result["finite_hmjd_mag_pair_count"] == 0
    assert result["hmjd_span_days"] is None
    assert result["median_sampling_interval_days"] is None
    assert result["mag_median"] is None
    assert result["mag_p95_minus_p05"] is None
    assert result["magerr_median"] is None


def test_summary_reports_duplicate_times_without_treating_them_as_cadence() -> None:
    result = summarize_dr24_epochs(
        [
            {"hmjd": 60000.0, "mag": 18.0, "magerr": 0.1},
            {"hmjd": 60000.0, "mag": 18.1, "magerr": 0.1},
            {"hmjd": 60002.0, "mag": 18.2, "magerr": 0.1},
        ]
    )

    assert result["unique_hmjd_count"] == 2
    assert result["duplicate_hmjd_count"] == 1
    assert result["median_sampling_interval_days"] == 2.0


def test_record_summary_keeps_oid_records_separate() -> None:
    result = summarize_dr24_records(
        [
            {"objectid": 11, "filterid": 1, "epochs": []},
            {"objectid": 22, "filterid": 2, "epochs": []},
        ]
    )

    assert result["grouping_applied"] is False
    assert [item["objectid"] for item in result["summaries"]] == [11, 22]
